"""Second pass over tier-1 place names left in review. Keeps both readings where the name has two senses.

  dominant      several CO List QIDs, one carries the printed name and >=10x the events of the next -> that one
  place+polity  the CO List has a geographic item and an Empire Evolution polity for the same name
                -> the geographic item is the place; the polity is recorded beside it (polity_qid)
  sri_lanka     several CO List QIDs, exactly one of them in the Sri Lanka gazetteer -> that one
  well_known    one CO List QID carrying the printed name, >=100 sitelinks, not a polity (Berlin, Vienna)
  town+district journal uses a Sri Lankan name mostly as an area, CO List has the town, and the Sri Lanka
                gazetteer has "<Name> District" -> both senses kept; primary follows the journal's usage
Anything else stays in review. Output grounding/places_tier1b.jsonl (rows override tier 1 for the same name).
"""
import collections, json
from common import *
from empire import Empire

def main():
    E = Empire()
    sl = {}
    for r in read_jsonl(HERE / "gazetteer/sri_lanka_wikidata.jsonl"):
        lab = r.get("labels", {}).get("en")
        if lab: sl.setdefault(key(lab), []).append(r)
    slq = {r["qid"] for rs in sl.values() for r in rs}
    sitelinks = {r["qid"]: r.get("sitelinks", 0) for r in read_jsonl(HERE / "gazetteer/col_places_wikidata.jsonl")}
    out, tally, rec = [], collections.Counter(), collections.Counter()
    for d in read_jsonl(HERE / "grounding/places_tier1.jsonl"):
        if d["status"] != "review": continue
        c = d["candidates"]; rule = None
        if len(c) > 1:
            terr = [x for x in c if x["qid"] in E.by_qid]; geo = [x for x in c if x["qid"] not in E.by_qid]
            exact = [x for x in c if x["name_is_label"]]
            if len(terr) == 1 and len(geo) == 1:
                d.update(status="matched", confidence="medium", qid=geo[0]["qid"], label=geo[0]["label"], polity_qid=terr[0]["qid"],
                         polity_label=terr[0]["label"], rule="place+polity"); rule = "place+polity"
            elif len([x for x in c if x["qid"] in slq]) == 1:
                x = next(x for x in c if x["qid"] in slq)
                d.update(status="matched", confidence="medium", qid=x["qid"], label=x["label"], rule="sri_lanka_preferred"); rule = "sri_lanka_preferred"
            elif exact and exact[0] is c[0] and c[0]["col_events"] >= 10 * c[1]["col_events"]:
                d.update(status="matched", confidence="medium", qid=c[0]["qid"], label=c[0]["label"], rule="dominant"); rule = "dominant"
        elif c[0]["name_is_label"] and sitelinks.get(c[0]["qid"], 0) >= 100 and c[0]["qid"] not in E.by_qid:
            d.update(status="matched", confidence="medium", qid=c[0]["qid"], label=c[0]["label"], rule="well_known"); rule = "well_known"
        elif d["journal_use"] == "area" and c[0]["wd_kind"] == "settlement":
            dist = [r for r in sl.get(d["key"] + " district", []) if "Q854" in r.get("country", []) or True]
            if len(dist) == 1:
                t = c[0]; di = dist[0]
                d.update(status="matched", confidence="medium", qid=di["qid"], label=di["labels"]["en"], rule="town+district",
                         senses=[{"sense": "district", "qid": di["qid"], "label": di["labels"]["en"], "primary": True, "lat": di.get("lat"), "lon": di.get("lon"), "description": di.get("description")},
                                 {"sense": "town", "qid": t["qid"], "label": t["label"], "primary": False, "lat": t.get("lat"), "lon": t.get("lon"), "description": t.get("description")}])
                d["candidates"].append({"qid": di["qid"], "label": di["labels"]["en"], "description": di.get("description"), "lat": di.get("lat"), "lon": di.get("lon")})
                rule = "town+district"
        if rule: d.pop("reason", None); d["source"] = "col_gazetteer+review_pass"
        tally[rule or "still review"] += 1; rec[rule or "still review"] += d["records"]
        out.append(d)
    with open(HERE / "grounding/places_tier1b.jsonl", "w") as fh:
        for d in out: fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    for k in tally: print(f"  {k:14} names={tally[k]:4} records={rec[k]:6}")
    print("still in review:", [(d["key"], d["records"]) for d in out if d["status"] == "review"][:25])

if __name__ == "__main__":
    main()
