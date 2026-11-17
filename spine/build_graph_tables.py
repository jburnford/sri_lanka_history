"""Build the load tables for the lean Ceylon graph from source files and decision files. No database needed.

Model (see MODEL.md):
  Article -[MENTIONS {records, surfaces, roles, polity}]-> Name          what the journal printed, per article
  Name -[RESOLVES_TO {status, confidence, source, rule}]-> Entity        a reviewable, reversible decision
  Article -[MENTIONS_PERSON {records, methods}]-> Profile                journal person profiles (proposed groupings)
  Profile -[IDENTIFIED_AS {source, review_status}]-> WikidataPerson | ColPerson
  ColPerson -[HELD]-> Posting -[AT]-> Place, Posting -[IN_POLITY]-> Territory
  Territory -[lineage]-> Territory                                        Empire Evolution graph
  Taxon(name record) -[SYNONYM_OF]-> Taxon(accepted)                      Catalogue of Life
Names are kept apart from entities so the printed form, the decision and the entity never overwrite each other.
Output: graph/*.tsv.gz and graph/_counts.json.
"""
import collections, csv, glob, gzip, json, re, sys
from common import *
from empire import Empire
csv.field_size_limit(sys.maxsize)
TA = Path("/mnt/data/jic823/tropical-agriculturist")
OUT = HERE / "graph"
TYPES_WITH_NAMES = ["PLACE", "TAXON", "COMMODITY", "ORG", "PUBLICATION", "ESTATE", "PRODUCT", "GROUP", "EVENT"]

def w(name, header, rows):
    n = 0
    with gzip.open(OUT / f"{name}.tsv.gz", "wt", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        wr.writerow(header)
        for r in rows: wr.writerow(["" if v is None else v for v in r]); n += 1
    return n

def year_of(issue):
    m = re.match(r"(\d{4})", issue or ""); return int(m.group(1)) if m else None

def acc(d):
    """The accepted name a decision points to, only when its own status is a synonym status (see common.is_synonym_status)."""
    return d.get("col_accepted") if is_synonym_status(d.get("col_status")) else None

def main():
    OUT.mkdir(exist_ok=True); counts = {}
    E = Empire()
    # ---- articles (canonical copies only)
    arts = {}
    for f in sorted(glob.glob(str(TA / "articles/by_year/*.jsonl.gz"))):
        for line in gzip.open(f, "rt"):
            a = json.loads(line)
            if not a.get("canonical"): continue
            p0 = (a.get("pages") or [{}])[0]
            arts[a["id"]] = (a["id"], year_of(a.get("issue")), a.get("issue"), a.get("volume"), a.get("part"), a.get("section"),
                             (a.get("title") or "")[:300], (a.get("byline") or "")[:200], a.get("words"), a.get("kind"),
                             p0.get("page"), p0.get("folio"), p0.get("viewer_url"), len(a.get("pages") or []))
    counts["articles"] = w("articles", ["id", "year", "issue", "volume", "part", "section", "title", "byline", "words", "kind",
                                       "first_scan_page", "first_folio", "viewer_url", "n_pages"], arts.values())
    # ---- decisions: name -> entity
    res, places, taxa = [], {}, {}
    dec = {}
    for f in ("places_tier1", "places_tier1b", "places_tier2"):      # later files override earlier ones for a name
        p = HERE / f"grounding/{f}.jsonl"
        if not p.exists(): continue
        for d in read_jsonl(p): dec[d["key"]] = d
    def add_place(qid, label, c):
        places.setdefault(qid, {"qid": qid, "label": label, "description": c.get("description"),
                                "lat": c.get("lat"), "lon": c.get("lon"), "territory": bool(E.by_qid.get(qid))})
    for d in dec.values():
        if d["status"] != "matched":
            res.append(("PLACE", d["key"], "", d["status"], "", d["source"], d.get("reason") or "", json.dumps([c["qid"] for c in d.get("candidates", [])[:5]])))
            continue
        if d.get("senses"):                                           # two readings kept side by side
            for sn in d["senses"]:
                add_place(sn["qid"], sn["label"], sn)
                res.append(("PLACE", d["key"], "wd:" + sn["qid"], "matched", d.get("confidence"), d["source"],
                            f"sense:{sn['sense']}" + (" (primary)" if sn.get("primary") else ""), ""))
            continue
        c = next((c for c in d.get("candidates", []) if c["qid"] == d["qid"]), {})
        add_place(d["qid"], d.get("label"), c)
        res.append(("PLACE", d["key"], "wd:" + d["qid"], "matched", d.get("confidence"), d["source"], d.get("rule") or d.get("reason") or "", ""))
        if d.get("polity_qid"):                                       # place + the colony the CO List recorded under the same name
            pc = next((c for c in d.get("candidates", []) if c["qid"] == d["polity_qid"]), {})
            add_place(d["polity_qid"], d.get("polity_label"), pc)
            res.append(("PLACE", d["key"], "wd:" + d["polity_qid"], "matched", d.get("confidence"), d["source"], "sense:polity", ""))
    polity_hint = {d["key"]: d["polity_qid"] for d in dec.values() if d.get("polity_qid")}
    place_of = {}
    for r in res:                                                     # one QID per name for polity lookup: the polity sense if there is one
        if r[0] == "PLACE" and r[3] == "matched": place_of.setdefault(r[1], r[2][3:])
    place_of.update(polity_hint)
    p = HERE / "grounding/taxa_col.jsonl"
    if p.exists():
        for d in read_jsonl(p):
            if d["status"] != "matched":
                res.append(("TAXON", d["key"], "", d["status"], "", d["source"], d.get("reason") or "", "")); continue
            tid = "cl:" + d["col_usage_id"]
            taxa[tid] = (tid, d["col_name"], d.get("col_authorship"), d.get("col_rank"), d.get("col_status"), d.get("family"), d.get("kingdom"),
                         "cl:" + d["col_accepted"]["id"] if acc(d) else "")
            if acc(d):
                a = d["col_accepted"]; taxa.setdefault("cl:" + a["id"], ("cl:" + a["id"], a.get("name"), a.get("authorship"), a.get("rank"), a.get("status"), d.get("family"), d.get("kingdom"), ""))
            res.append(("TAXON", d["key"], tid, "matched", "high" if d.get("col_match_type") == "exact" else "medium", d["source"], d.get("col_match_type") or "", ""))
    # ---- Wikidata tier for vernacular taxa, commodities and organisations (ground_names_wd.py)
    concepts, clinks = {}, set()
    wdcol = {d["qid"]: d for d in read_jsonl(HERE / "grounding/wd_taxon_col.jsonl")} if (HERE / "grounding/wd_taxon_col.jsonl").exists() else {}
    def add_concept(qid, label, desc, kind, taxon_name=None):
        if qid in places: return                                      # already a Place node with the same identifier
        concepts.setdefault(qid, ("wd:" + qid, qid, label, desc, kind, taxon_name or ""))
        j = wdcol.get(qid)
        if j and j["status"] == "matched":                            # same taxon in the Catalogue of Life
            tid = "cl:" + j["col_usage_id"]
            taxa.setdefault(tid, (tid, j["col_name"], j.get("col_authorship"), j.get("col_rank"), j.get("col_status"), j.get("family"), j.get("kingdom"),
                                  "cl:" + j["col_accepted"]["id"] if acc(j) else ""))
            if acc(j):
                a = j["col_accepted"]; taxa.setdefault("cl:" + a["id"], ("cl:" + a["id"], a.get("name"), a.get("authorship"), a.get("rank"), a.get("status"), j.get("family"), j.get("kingdom"), ""))
            clinks.add(("wd:" + qid, tid, "SAME_TAXON"))
    for t in ("taxon", "commodity", "org"):
        p = HERE / f"grounding/{t}_wd.jsonl"
        if not p.exists(): continue
        for d in read_jsonl(p):
            T = d["type"]
            if d["status"] != "matched":
                if T != "TAXON":                                      # taxa already carry their Catalogue of Life outcome
                    res.append((T, d["key"], "", d["status"], "", d["source"], d.get("reason") or "", json.dumps([c["qid"] for c in d.get("candidates", []) if c.get("near") and c.get("kind")][:5])))
                continue
            if T == "TAXON": res[:] = [r for r in res if not (r[0] == "TAXON" and r[1] == d["key"])]
            add_concept(d["qid"], d.get("label"), d.get("description"), d.get("kind"), d.get("taxon_name"))
            res.append((T, d["key"], "wd:" + d["qid"], "matched", d.get("confidence"), d["source"], d.get("rule") or "", ""))
            for st in d.get("source_taxa", []):
                add_concept(st["qid"], st.get("label"), "", "taxon", st.get("taxon_name"))
                if d["qid"] not in places and st["qid"] not in places: clinks.add(("wd:" + d["qid"], "wd:" + st["qid"], "PRODUCT_OF"))
    counts["concepts"] = w("concepts", ["id", "qid", "label", "description", "kind", "taxon_name"], concepts.values())
    counts["concept_links"] = w("concept_links", ["from", "to", "type"], sorted(clinks))
    counts["resolutions"] = w("resolutions", ["type", "key", "entity_id", "status", "confidence", "source", "rule", "candidates"], res)
    counts["places"] = w("places", ["id", "qid", "label", "description", "lat", "lon", "is_empire_territory"],
                         [("wd:" + p["qid"], p["qid"], p["label"], p["description"], p["lat"], p["lon"], int(p["territory"])) for p in places.values()])
    counts["taxa"] = w("taxa", ["id", "name", "authorship", "rank", "status", "family", "kingdom", "accepted_id"], taxa.values())
    # ---- names and article->name mentions
    names = collections.defaultdict(lambda: [0, set(), collections.Counter()])
    def mention_rows():
        for f in sorted(glob.glob(str(TA / "ner/mentions/part_*.jsonl.gz"))):
            for line in gzip.open(f, "rt"):
                a = json.loads(line)
                if a["id"] not in arts: continue
                yr = arts[a["id"]][1]
                agg = collections.defaultdict(lambda: [0, collections.Counter(), collections.Counter()])
                for m in a.get("mentions", []):
                    t = m.get("type")
                    if t not in TYPES_WITH_NAMES: continue
                    k = key(m.get("norm") or m.get("text") or "")
                    if not k: continue
                    g = agg[(t, k)]; g[0] += 1; g[1][m.get("text", "")] += 1
                    if m.get("role"): g[2][m["role"].lower()] += 1
                for (t, k), (n, surf, roles) in agg.items():
                    nm = names[(t, k)]; nm[0] += n; nm[1].add(a["id"]); nm[2].update(surf)
                    polity = ""
                    if t == "PLACE" and yr and k in place_of and place_of[k] in E.by_qid:
                        terr, _, hops = E.polity_at(place_of[k], yr)
                        if terr: polity = terr["id"]
                    yield (a["id"], t, k, n, " | ".join(s for s, _ in surf.most_common(3)), " | ".join(r for r, _ in roles.most_common(3)), polity)
    counts["mentions"] = w("mentions", ["article", "type", "key", "records", "surfaces", "roles", "polity_at_date"], mention_rows())
    counts["names"] = w("names", ["type", "key", "label", "records", "articles"],
                        [(t, k, v[2].most_common(1)[0][0], v[0], len(v[1])) for (t, k), v in names.items()])
    # ---- people
    people = {p["profile_id"]: p for p in read_jsonl(HERE / "grounding/people.jsonl")}
    pid2tap, prof = {}, []
    for r in csv.DictReader(open(TA / "ner/persons/out/persons.tsv"), delimiter="\t"):
        pid2tap[r["pid"]] = r["id"]
        p = people.get(r["id"], {})
        prof.append((r["id"], r["display"], r["kind"], r["mentions"], r["articles"], r["first"], r["last"], r["roles"][:300],
                     p.get("review_status", "unreviewed"), int(bool(p.get("mixed_profile"))), r["flags"]))
    counts["profiles"] = w("profiles", ["id", "name", "kind", "records", "articles", "first", "last", "roles", "review_status", "mixed_profile", "flags"], prof)
    pm = collections.defaultdict(lambda: [0, collections.Counter(), collections.Counter()])
    for r in csv.DictReader(gzip.open(TA / "ner/persons/out/mentions.tsv.gz", "rt"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if not r["pid"] or r["article"] not in arts or r["pid"] not in pid2tap: continue
        g = pm[(r["article"], pid2tap[r["pid"]])]; g[0] += 1; g[1][r["method"]] += 1
        if r["role"]: g[2][r["role"].lower()] += 1
    counts["profile_mentions"] = w("profile_mentions", ["article", "profile", "records", "methods", "roles"],
        [(a, t, n, " | ".join(f"{m} ({c})" for m, c in meth.most_common()), " | ".join(r for r, _ in roles.most_common(3))) for (a, t), (n, meth, roles) in pm.items()])
    ident, wdp, colids = [], {}, set()
    for p in people.values():
        if p.get("wikidata_qid"):
            ident.append((p["profile_id"], "wd:" + p["wikidata_qid"], "wikidata", p.get("qid_source"), p.get("qid_confidence"), p.get("review_status")))
            wdp["wd:" + p["wikidata_qid"]] = p["wikidata_qid"]
        if p.get("colist_person_id"):
            ident.append((p["profile_id"], "col:" + p["colist_person_id"], "colonial_office_list", p.get("colist_decision"), "", p.get("review_status")))
            colids.add(p["colist_person_id"])
    counts["identities"] = w("identities", ["profile", "target", "authority", "source", "confidence", "review_status"], ident)
    counts["wikidata_persons"] = w("wikidata_persons", ["id", "qid"], wdp.items())
    # ---- Colonial Office List: every person with a Ceylon posting, plus every linked person; all their postings
    ev = collections.defaultdict(list)
    for e in read_jsonl(COL / "career_events.jsonl"): ev[e["person_id"]].append(e)
    for pid, es in ev.items():
        if any(e.get("colony_qid") == "Q918153" for e in es): colids.add(pid)
    colq = {g["person_id"]: g["qid"] for g in read_jsonl(COL / "person_grounding.final.jsonl")}
    cp, posts, colplaces = [], [], {}
    for p in read_jsonl(COL / "persons.jsonl"):
        if p["person_id"] not in colids: continue
        cp.append(("col:" + p["person_id"], p["person_id"], p.get("surname"), p.get("given_names"), p.get("birth_year"),
                   colq.get(p["person_id"]), min(p.get("editions") or [None]), max(p.get("editions") or [None])))
        for e in ev.get(p["person_id"], []):
            ys = e.get("year_start"); polity = lineage = cover = ""
            q = e.get("colony_qid") or e.get("place_qid")
            if ys and q and q in E.by_qid:
                terr, _, hops = E.polity_at(q, ys, e.get("year_end") or ys)
                if terr:
                    polity, lineage = terr["id"], int(bool(hops))
                    cover = "whole" if E.contains(terr["id"], ys, e.get("year_end") or ys) else "part"   # part: the posting runs outside the polity's dates
            posts.append((f"col:{p['person_id']}#{e.get('seq')}", "col:" + p["person_id"], e.get("position"), e.get("position_norm"), ys, e.get("year_end"),
                          int(bool(e.get("is_acting"))), e.get("place_raw"), ("wd:" + e["place_qid"]) if e.get("place_qid") else "", e.get("place_label"),
                          ("wd:" + e["colony_qid"]) if e.get("colony_qid") else "", e.get("colony_label"), polity, lineage, cover))
            for qf, lf in (("place_qid", "place_label"), ("colony_qid", "colony_label")):
                if e.get(qf): colplaces.setdefault(e[qf], e.get(lf))
    counts["col_persons"] = w("col_persons", ["id", "person_id", "surname", "given_names", "birth_year", "wikidata_qid", "first_edition", "last_edition"], cp)
    counts["postings"] = w("postings", ["id", "person", "position", "position_norm", "start", "end", "acting", "place_as_recorded", "place", "place_label",
                                        "colony", "colony_label", "polity_at_date", "polity_by_lineage", "polity_coverage"], posts)
    counts["col_places"] = w("col_places", ["id", "qid", "label"], [("wd:" + q, q, l) for q, l in colplaces.items()])
    # ---- Empire Evolution
    counts["territories"] = w("territories", ["id", "name", "qid", "start", "end", "type"], [(t["id"], t["name"], t["qid"], t["start"], t["end"], t["type"]) for t in E.terr.values()])
    edges = {(a, b, rel) for a, lst in E.adj.items() for b, rel, d in lst if d == "out"}
    dangling = sorted(e for e in edges if e[0] not in E.terr or e[1] not in E.terr)       # an end that is not a territory in the manifest
    counts["territory_edges"] = w("territory_edges", ["from", "to", "type"], sorted(edges - set(dangling)))
    counts["territory_edges_dropped"] = len(dangling)
    with open(HERE / "analysis/territory_edges_dropped.tsv", "w") as fh:
        fh.write("from\tto\ttype\tmissing_end\n")
        for a_, b_, rel in dangling: fh.write(f"{a_}\t{b_}\t{rel}\t{' '.join(x for x in (a_, b_) if x not in E.terr)}\n")
    json.dump(counts, open(OUT / "_counts.json", "w"), indent=1)
    print(json.dumps(counts, indent=1))

if __name__ == "__main__":
    main()
