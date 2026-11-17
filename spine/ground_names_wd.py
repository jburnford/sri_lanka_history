"""Wikidata grounding for frequent TAXON (vernacular), COMMODITY and ORG names.

Candidates come only from cached WikidataMCP vector searches (cache/wd_search.jsonl) and are verified against
details read back by QID (gazetteer/name_candidates_wikidata.jsonl). A decision is per NAME.

A candidate qualifies when its label or an alias (or, for a taxon, a recorded common name) equals the journal
name and its type fits:
  TAXON      a taxon item (has a taxon name, P225); or a product/disease item, kept as a concept, with the
             taxon it comes from (P1582) carried along as a second, separate link
  COMMODITY  not a place, person, work, organisation or name item; a taxon item is allowed (crop named by genus)
  ORG        description or class reads as an organisation; generic names ("department of agriculture") are
             skipped because their meaning changes with every article
Rules: one qualifying candidate -> matched; several, one dominant by sitelinks (3x) -> matched/medium;
otherwise review with the candidates kept. Taxon names already matched by the Catalogue of Life are left alone.
Output grounding/<type>_wd.jsonl. Usage: ground_names_wd.py TYPE [min_articles=15]
"""
import collections, json, sys
from common import *
import search_names_wd as sn

BAD = re.compile(r"\b(disambiguation|wikimedia|family name|surname|given name|film|album|song|single by|painting|novel|"
                 r"television|video game|band|rockband|musical group|episode|scientific article|scholarly article|human|character|ship|"
                 r"taxonomic rank|magazine|journal|newspaper|book|poem|play by|opera|company|brand|village|town|city|"
                 r"commune|municipality|river|crater|asteroid|racehorse|race horse|operon|gene|soft drink|rose cultivar|restaurant|software|website|game|library|dictionary|musician|singer|story|framework|programming|operating system|protocol|locomotive|aircraft|automobile|car model|typeface|color|colour|mascot|deity|goddess|mythology|surname|name)\b", re.I)
ORG_OK = re.compile(r"\b(organi[sz]ation|society|association|institut|department|ministry|agency|company|firm|bank|"
                    r"university|college|school|garden|museum|board|commission|committee|council|chamber|government|"
                    r"railway|union|club|corporation|service|station|laboratory|office|business|publisher|trust|"
                    r"herbarium|parliament|academy|army|navy|church|mission|bureau|federation|league)", re.I)
ORG_BAD = re.compile(r"\b(disambiguation|wikimedia|family name|film|album|song|novel|television|video game|episode|"
                     r"scientific article|scholarly article|positions?|building|listed|street|human settlement|district|of various types|type of|administrative division)\b", re.I)
GENERIC_ORG = re.compile(r"^((the|a|his|her|local|home|royal|"
                         r"general|central|agricultural|botanical|botanic|planters|chamber|experiment|experimental|"
                         r"board|committee|commission|company|council|department|government|society|association|"
                         r"station|stations|gardens|garden|office|institute|museum|college|school|university|"
                         r"legislature|parliament|bank|firm|club|press|court|customs|police|railway|post|forest|"
                         r"agriculture|commerce|trade|education|works|public|survey|medical|science|sciences|"
                         r"service|bureau|ministry|laboratory|treasury|imperial|municipality|municipal|syndicate|exchange|stock|"
                         r"secretary|state|of|for|and|in|s|co|ltd|limited|messrs)( |$))+$")
PLANT = re.compile(r"\b(plant|tree|crop|palm|grass|fibre|fiber|fruit|shrub|weed|timber|rubber|vegetable|cereal|grain|flower|herb|vine|creeper|legume|fodder|shade|variety|seed|bark|nut|spice|drug|dye|bean|root|tuber|bamboo|cultivar|orchid|fern)")
ANIMAL = re.compile(r"\b(insect|pest|beetle|moth|bug|scale|worm|caterpillar|borer|fly|flies|ant|animal|bird|fish|mammal|cattle|mite|weevil|aphis|aphid|locust|snail|annelid|arachnid|gastropod|arthropod|nematode|protist|butterfl|reptile|snake|crustacean|spider|mollus|amphibian|rodent|lizard)")
FUNGUS = re.compile(r"\b(fung|blight|rust|mildew|mould|mold|canker|rot|parasite|pathogen|bacteri|virus|lichen|oomycete|alga)")
def kinds(txt):
    return {n for n, rx in (("plant", PLANT), ("animal", ANIMAL), ("microbe", FUNGUS), ("disease", DISEASE)) if rx.search(txt)}
def journal_kind(roles):
    w = collections.Counter()
    for part in roles.split(" | "):
        m = re.match(r"(.*) \((\d+)\)$", part)
        if m:
            for k in kinds(m.group(1)): w[k] += int(m.group(2))
    return w
def kind_conflict(roles, desc):
    """True when the journal clearly uses the name for one kind of organism and the item is clearly another."""
    w = journal_kind(roles); dk = kinds(desc.lower())
    if not w or not dk: return False
    top, n = w.most_common(1)[0]
    if top in dk or (top in ("disease", "microbe") and dk & {"disease", "microbe"}): return False
    return n >= 2 * max((w[k] for k in dk), default=0)
DISEASE = re.compile(r"\b(disease|infection|fever|plague|syndrome|disorder|illness)\b", re.I)

def load():
    ent = {}
    for f in ("col_places_wikidata", "place_candidates_wikidata", "sri_lanka_wikidata", "name_candidates_wikidata"):
        p = HERE / f"gazetteer/{f}.jsonl"
        if not p.exists(): continue
        for r in read_jsonl(p):
            if r.get("missing"): continue
            ent[r["requested"]] = r; ent[r["qid"]] = r
    return ent

def names_of(w):
    n = wd_names(w)
    n |= {key(x) for x in w.get("taxon_common_name", [])}
    n |= {key(x) for x in w.get("taxon_name", [])}
    return n - {""}

def plural_keys(k):
    """The name and simple singular/plural variants ("cocoanuts" is not "coconut"; "plantains" is "plantain")."""
    ks = {k}
    if k.endswith("s") and len(k) > 4: ks.add(k[:-1])
    if k.endswith("es") and len(k) > 5: ks.add(k[:-2])
    return ks

THING = re.compile(r"\b(plant|tree|shrub|grass|palm|crop|fruit|vegetable|spice|condiment|fib(re|er)|starch|grain|cereal|wood|timber|"
                   r"oil|fat|wax|drug|medic|food|foodstuff|seed|nut|bean|legume|species|genus|cultivar|variety|breed|animal|"
                   r"insect|bird|fish|mammal|livestock|compound|chemical|alkaloid|stereoisomer|mineral|ore|metal|element|"
                   r"beverage|drink|material|resin|gum|latex|polymer|dye|pigment|fertili[sz]er|manure|sugar|sweetener|flour|"
                   r"meal|product|commodity|substance|tuber|root|leaf|leaves|bark|flower|herb|berry|fodder|forage|textile|"
                   r"fabric|rock|salt|acid|protein|extract|carbohydrate|tea\b|coffee|cocoa|rubber|essential|tobacco|ingredient|staple|pest|parasite|fung|bacteri|"
                   r"virus|disease|infection)", re.I)
MINERAL = re.compile(r"\b(mineral|ore|graphite|metal|gem|stone|mining|mine)\b")

def fits(t, w, desc, roles=""):
    is_taxon = "taxon_name" in w
    is_place = "lat" in w
    product = bool(w.get("natural_product_of_taxon"))
    if t in ("TAXON", "COMMODITY"):
        if is_place or (BAD.search(desc) and not is_taxon): return None
        if is_taxon:
            if kind_conflict(roles, desc): return None
            if t == "COMMODITY" and MINERAL.search(roles) and not PLANT.search(roles.split(" | ")[0]): return None
            return "taxon"
        if not (product or THING.search(desc)) or w.get("sitelinks", 0) < 3: return None
        if DISEASE.search(desc): return "disease" if t == "TAXON" else None
        return "product" if product else "concept"
    if t == "ORG":
        if is_taxon or ORG_BAD.search(desc) or w.get("sitelinks", 0) < 2: return None
        if any(y.isdigit() and int(y) > 1945 for y in w.get("inception", [])): return None
        if not (w.get("inception") or w.get("country") or w.get("headquarters")): return None   # a class of thing, not one body
        return "organisation" if ORG_OK.search(desc) else None

def main():
    t = sys.argv[1]; min_articles = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    ent = load()
    search = {d["query"]: d["results"] for d in read_jsonl(HERE / "cache/wd_search.jsonl")}
    done = set()
    if t == "TAXON":
        done = {d["key"] for d in read_jsonl(HERE / "grounding/taxa_col.jsonl") if d["status"] == "matched"}
    rj = HERE / "grounding/name_rejections.jsonl"          # matches a person has thrown out; never offered again
    rejected = {(d["key"], d["qid"]) for d in read_jsonl(rj) if d["type"] == t} if rj.exists() else set()
    dj = HERE / "grounding/name_decisions.jsonl"
    decided = {d["key"]: d for d in read_jsonl(dj) if d["type"] == t} if dj.exists() else {}
    out, tally, rec = [], collections.Counter(), collections.Counter()
    total = sum(r["records"] for r in read_names(t))
    for r in read_names(t):
        if r["articles"] < min_articles or r["key"] in done: continue
        qs = sn.queries(r, t)
        rank, unfetched = {}, 0
        for qi, q in enumerate(qs):
            for i, (qid, lab, desc) in enumerate(search.get(q, [])[:8]):
                if qid not in ent: unfetched += 1; continue
                rank.setdefault(ent[qid]["qid"], (qi, i))
        ks = plural_keys(r["key"])
        cands = []
        for qid, (qi, i) in rank.items():
            w = ent[qid]; desc = w.get("description") or ""
            nm = names_of(w)
            exact = r["key"] in nm
            lab_exact = r["key"] in {key(v) for v in w.get("labels", {}).values()} | {key(x) for x in w.get("taxon_name", [])}
            near = exact or bool(ks & nm)
            kind = fits(t, w, desc, r["roles"])
            if (r["key"], qid) in rejected: kind = None
            c = {"qid": qid, "label": w.get("labels", {}).get("en") or w.get("labels", {}).get("mul"), "description": desc,
                 "exact": exact, "label_exact": lab_exact, "near": near, "kind": kind, "sitelinks": w.get("sitelinks", 0),
                 "hinted_rank": i + 1 if qi == 0 else None}
            for f in ("taxon_name", "natural_product_of_taxon", "inception", "dissolved", "headquarters", "country"):
                if w.get(f): c[f] = w[f][:3]
            cands.append(c)
        good = sorted([c for c in cands if c["near"] and c["kind"]], key=lambda c: (not c["exact"], -c["sitelinks"]))
        if any(c["exact"] for c in good): good = [c for c in good if c["exact"]]
        if t == "TAXON" and any(c["kind"] == "taxon" for c in good): good = [c for c in good if c["kind"] == "taxon"]   # an organism name wants an organism
        if any(c["label_exact"] for c in good): good = [c for c in good if c["label_exact"]]   # the item's own name beats an alias
        d = {"type": t, "key": r["key"], "records": r["records"], "articles": r["articles"], "first": r["first"],
             "last": r["last"], "surfaces": r["surfaces"], "roles": r["roles"], "source": "wikidata_mcp_search",
             "queries": qs, "candidates": sorted(cands, key=lambda c: (not c["near"], not c["kind"], -c["sitelinks"]))[:6]}
        def choose(c, conf, rule):
            d.update(status="matched", qid=c["qid"], label=c["label"], description=c["description"], kind=c["kind"],
                     confidence=conf if c["label_exact"] or not c["exact"] else "medium", rule=rule + ("" if c["exact"] else "+plural") + ("" if c["label_exact"] or not c["exact"] else "+alias"))
            if c.get("taxon_name"): d["taxon_name"] = c["taxon_name"][0]
            if c.get("natural_product_of_taxon"):
                d["source_taxa"] = [{"qid": q, "taxon_name": (ent.get(q, {}).get("taxon_name") or [None])[0],
                                     "label": ent.get(q, {}).get("labels", {}).get("en")} for q in c["natural_product_of_taxon"]]
        if t == "ORG" and (GENERIC_ORG.match(r["key"]) or len(r["key"].replace(" ", "")) < 5):
            d.update(status="skip", reason="generic organisation name; meaning depends on the article")
        elif not good:
            d.update(status="unmatched", reason="no candidate with this name and a fitting type" +
                     (f" ({unfetched} candidates not read back yet)" if unfetched else ""))
        elif len(good) == 1:
            choose(good[0], "medium" if t == "ORG" and good[0]["sitelinks"] < 10 else "high" if good[0]["exact"] and (good[0]["hinted_rank"] or 9) <= 3 or good[0]["sitelinks"] >= 20 else "medium", "single")
        else:
            # a taxon reading and a product reading of the same word are both right: keep the kind the type asks for first
            pref = [c for c in good if (c["kind"] == "taxon") == (t == "TAXON")] or good
            a, b = pref[0], (pref[1] if len(pref) > 1 else None)
            if b is None: choose(a, "medium", "single_of_kind")
            elif a["sitelinks"] >= 3 * max(b["sitelinks"], 1) and a["sitelinks"] >= 10: choose(a, "medium", "dominant")
            else: d.update(status="review", reason="several items share this name")
            if d["status"] == "matched":
                d["other_senses"] = [{"qid": c["qid"], "label": c["label"], "kind": c["kind"]} for c in good if c["qid"] != a["qid"]][:4]
        # a reviewed decision for a name the rules left open (grounding/name_decisions.jsonl): the chosen item must be
        # one of the candidates read back for this name, and must not have been rejected
        dec = decided.get(r["key"])
        if dec and d["status"] != "matched":
            c = next((c for c in cands if c["qid"] == dec["qid"]), None)
            if c and (r["key"], c["qid"]) not in rejected:
                was = d.get("reason", "")
                choose(c, "medium", "reviewed_proposal")
                d["confidence"] = "medium"
                if not d.get("kind"): d["kind"] = "taxon" if c.get("taxon_name") else "product"
                d.pop("reason", None)
                d.update(decided_by=dec["by"], decision_reason=dec["reason"], rule_outcome_before=was)
        s = d["status"] + (":" + d.get("confidence", "") if d["status"] == "matched" else "")
        tally[s] += 1; rec[s] += r["records"]; out.append(d)
    with open(HERE / f"grounding/{t.lower()}_wd.jsonl", "w") as fh:
        for d in out: fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"{t} records in journal: {total}")
    for s in sorted(tally): print(f"  {s:18} names={tally[s]:5}  records={rec[s]:7}  ({rec[s]/total:.1%})")

if __name__ == "__main__":
    main()
