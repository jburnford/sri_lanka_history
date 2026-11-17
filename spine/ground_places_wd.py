"""Tier 2/3 place grounding: frequent journal place names not settled by the CO List gazetteer.

Candidates come only from cached WikidataMCP vector searches (cache/wd_search.jsonl) and are verified against
entity details read back by QID (gazetteer/*.jsonl). A decision is per NAME. Rules:
  - a candidate must be a place (has coordinates and a place class) and its label or an alias must equal the name
  - exactly one such candidate                      -> matched (high if it ranks top-3 in the hinted search)
  - several, exactly one in Sri Lanka (common.in_sri_lanka), and either the journal context is Ceylon or no rival
    outside Sri Lanka has >=100 sitelinks           -> matched/medium "sri_lanka_preferred"; otherwise the rules below
  - several, one dominant by sitelinks (>=40, and >=5x the next, or >=3x when it has >=200) -> matched/medium "dominant"
  - several, exactly one of the journal's kind (settlement/area) with >=50 sitelinks -> matched/medium "kind_match"
  - otherwise                                        -> review (candidates kept) or unmatched
Guards applied to every match (match() below): a person's rejection; the journal places the name in Ceylon
("garden in colombo") but the candidate is elsewhere; Ceylon context and an obscure foreign item; an obscure item
for a frequent name; the journal's kind (settlement/area) contradicts the candidate's.
Output grounding/places_tier2.jsonl. Usage: ground_places_wd.py [min_articles=15]
"""
import collections, json, sys
from common import *
from search_places_wd import queries

GENERIC = re.compile(r"^((north|south|east|west|central|upper|lower|interior|low|up)(ern)?( |$))*(coast|coasts|provinces|districts|islands|continent|colonies|colony|interior|hills|tropics|country|plains|highlands|lowlands|states|mainland|settlements|low country|up country)?$")
# names GENERIC would skip that are proper names of polities (British India's provinces), not relative references
PROPER_REGIONS = {"central provinces", "north western provinces", "north west provinces"}
SETTLEMENT_CLASS = re.compile(r"\b(city|town|village|suburb|settlement|locality|municipality|commune|comune|hamlet|neighbou?rhood|capital)\b", re.I)
PLACE_CLASSES = {q: (v.get("label") or "") for q, v in json.load(open("/home/jic823/Documents/ceylon/col_matching/data/whg/wikidata_places.json"))["classes"].items()}
NOT_PLACE = re.compile(r"\b(template|disambiguation|category|family name|given name|film|album|song|painting|ship|novel|journal|newspaper|company|genus|species|human)\b", re.I)

def main():
    min_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    ent, sl = {}, set()
    for f in ("col_places_wikidata", "place_candidates_wikidata", "sri_lanka_wikidata"):
        p = HERE / f"gazetteer/{f}.jsonl"
        if not p.exists(): continue
        for r in read_jsonl(p):
            if r.get("missing"): continue
            ent[r["requested"]] = r; ent[r["qid"]] = r
            if f == "sri_lanka_wikidata": sl.add(r["qid"])
    rejected = {(d["key"], d["qid"]) for d in read_jsonl(HERE / "grounding/name_rejections.jsonl") if d["type"] == "PLACE"}
    search = {d["query"]: d["results"] for d in read_jsonl(HERE / "cache/wd_search.jsonl")}
    done = {d["key"] for d in read_jsonl(HERE / "grounding/places_tier1.jsonl") if d["status"] == "matched"}
    if (HERE / "grounding/places_tier1b.jsonl").exists():   # names settled in the review pass; the rest go on to Wikidata search
        done |= {d["key"] for d in read_jsonl(HERE / "grounding/places_tier1b.jsonl") if d["status"] == "matched"}
    out, tally, rec, total = [], collections.Counter(), collections.Counter(), 0
    for r in read_names("PLACE"):
        total += r["records"]
        if r["articles"] < min_articles or r["key"] in done: continue
        qs = queries(r)
        rank, unfetched = {}, 0
        for qi, q in enumerate(qs):
            for i, (qid, lab, desc) in enumerate(search.get(q, [])[:6]):
                if qid not in ent: unfetched += 1; continue
                rank.setdefault(ent[qid]["qid"], (qi, i))
        cands = []
        for qid, (qi, i) in rank.items():
            w = ent[qid]
            desc = w.get("description") or ""
            classes = [PLACE_CLASSES[q] for q in w.get("instance_of", []) if q in PLACE_CLASSES]
            is_place = "lat" in w and bool(classes) and not NOT_PLACE.search(desc)
            kind = "settlement" if any(SETTLEMENT_CLASS.search(c) for c in classes) else "area"
            cands.append({"qid": qid, "label": w.get("labels", {}).get("en"), "description": desc,
                          "exact": r["key"] in wd_names(w), "place": bool(is_place), "in_sri_lanka": in_sri_lanka(w), "kind": kind, "classes": classes[:3],
                          "sitelinks": w.get("sitelinks", 0), "hinted_rank": i + 1 if qi == 0 else None,
                          "lat": w.get("lat"), "lon": w.get("lon")})
        good = sorted([c for c in cands if c["exact"] and c["place"]], key=lambda c: -c["sitelinks"])
        d = {"type": "PLACE", "key": r["key"], "records": r["records"], "articles": r["articles"], "first": r["first"],
             "last": r["last"], "surfaces": r["surfaces"], "roles": r["roles"], "source": "wikidata_mcp_search",
             "queries": qs, "candidates": sorted(cands, key=lambda c: (not c["exact"], not c["place"], -c["sitelinks"]))[:6]}
        sl_signal = "Sri Lanka" in qs[0]
        use = role_class(r["roles"])
        def match(c, conf, why):
            # guards: a plausible-looking exact match is still refused when the context contradicts it
            if (d["key"], c["qid"]) in rejected:
                d.update(status="review", reason="match rejected by a person", rejected=c["qid"]); return
            if ceylon_context(r["roles"]) and not c["in_sri_lanka"]:     # "garden in colombo" -> not a park in Berlin
                d.update(status="review", reason="journal places it in Ceylon; candidate is elsewhere", proposed=c["qid"]); return
            if sl_signal and not c["in_sri_lanka"] and c["sitelinks"] < 150:
                d.update(status="review", reason="journal context is Ceylon; best candidate is elsewhere", proposed=c["qid"]); return
            if not c["in_sri_lanka"] and c["sitelinks"] < 10 and r["articles"] >= 50:
                d.update(status="review", reason="obscure item for a frequent name", proposed=c["qid"]); return
            if (use == "area" and c["kind"] == "settlement" and not c["in_sri_lanka"]) or (use == "settlement" and c["kind"] == "area" and c["sitelinks"] < 50):
                d.update(status="review", reason=f"journal uses it as {use}; candidate is a {c['kind']}", proposed=c["qid"]); return
            if conf == "high" and not (c["sitelinks"] >= 20 or c["in_sri_lanka"]): conf = "medium"
            d.update(status="matched", confidence=conf, qid=c["qid"], label=c["label"], rule=why)
        sl_good = [c for c in good if c["in_sri_lanka"]]
        if GENERIC.match(r["key"]) and r["key"] not in PROPER_REGIONS:
            d.update(status="skip", reason="generic or relative reference, not a nameable place")
        elif not search.get(qs[0]) and not search.get(qs[-1]):
            d.update(status="unmatched", reason="search returned nothing")
        elif len(good) == 1:
            c = good[0]
            match(c, "high" if (c["hinted_rank"] or 9) <= 3 else "medium", "single exact place")
        elif len(good) > 1 and len(sl_good) == 1 and (sl_signal or not any(c["sitelinks"] >= 100 for c in good if not c["in_sri_lanka"])):
            match(sl_good[0], "medium", "sri_lanka_preferred")
        elif len(good) > 1 and good[0]["sitelinks"] >= 40 and good[0]["sitelinks"] >= (3 if good[0]["sitelinks"] >= 200 else 5) * max(1, good[1]["sitelinks"]):
            match(good[0], "medium", "dominant")
        elif len(good) > 1 and use in ("settlement", "area") and len([c for c in good if c["kind"] == use and c["sitelinks"] >= 50]) == 1 \
                and not [c for c in good if c["kind"] == use and c["sitelinks"] < 50 and c["sitelinks"] >= 20]:
            match(next(c for c in good if c["kind"] == use and c["sitelinks"] >= 50), "medium", f"kind_match:{use}")
        elif good:
            d.update(status="review", reason="several exact places")
        elif cands:
            d.update(status="review", reason="no candidate carries this exact name")
        else:
            d.update(status="unmatched", reason="candidates not fetched" if unfetched else "no candidates")
        s = d["status"] + ("/" + d["confidence"] if "confidence" in d else "")
        tally[s] += 1; rec[s] += r["records"]; out.append(d)
    with open(HERE / "grounding/places_tier2.jsonl", "w") as fh:
        for d in out: fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    for s in sorted(tally): print(f"  {s:16} names={tally[s]:5}  records={rec[s]:7}  ({rec[s]/total:.1%})")

if __name__ == "__main__":
    main()
