"""Tier 1 place grounding: journal place names -> the Colonial Office List (Imperial Careers) gazetteer.

A decision is per NAME (not per mention). Output grounding/places_tier1.jsonl, one row per journal name that
the CO List gazetteer knows. QIDs come only from the CO List files; Wikidata details were read back by QID.
  matched/high    one CO List QID, the journal name is that item's label or alias, types agree
  matched/medium  one CO List QID, but it is a period polity whose label differs (India -> British Raj)
  review          several CO List QIDs, or the journal uses the name for a different kind of thing
"""
import collections, json
from common import *

def main():
    wd = {r["requested"]: r for r in read_jsonl(HERE / "gazetteer/col_places_wikidata.jsonl")}
    idx = collections.defaultdict(dict)
    for p in read_jsonl(COL / "places.jsonl"):
        for nm in {p["place"], p["label"]}:
            k = key(nm)
            if not k: continue
            e = idx[k].setdefault(p["qid"], {"count": 0, "match_types": set()})
            e["count"] += p.get("count", 1); e["match_types"].add(p["match_type"])
    out, tally, rec = [], collections.Counter(), collections.Counter()
    total = 0
    for r in read_names("PLACE"):
        total += r["records"]
        cands = idx.get(r["key"])
        if not cands: continue
        rc = role_class(r["roles"])
        rows = []
        for q, e in sorted(cands.items(), key=lambda x: -x[1]["count"]):
            w = wd.get(q, {})
            desc = (w.get("description") or "")
            wd_kind = "settlement" if SETTLEMENT.search(desc.split(",")[0]) and not POLITY.search(desc.split(",")[0]) else \
                      "area" if POLITY.search(desc) else "other"
            rows.append({"qid": w.get("qid", q), "label": w.get("labels", {}).get("en"), "description": desc,
                         "name_is_label": r["key"] in wd_names(w), "wd_kind": wd_kind,
                         "col_events": e["count"], "col_match_types": sorted(e["match_types"]),
                         "lat": w.get("lat"), "lon": w.get("lon")})
        d = {"type": "PLACE", "key": r["key"], "records": r["records"], "articles": r["articles"],
             "first": r["first"], "last": r["last"], "journal_use": rc, "surfaces": r["surfaces"],
             "source": "col_gazetteer", "candidates": rows}
        top = rows[0]
        clash = (rc == "settlement" and top["wd_kind"] == "area") or (rc == "area" and top["wd_kind"] == "settlement")
        if len(rows) > 1:
            d.update(status="review", reason="several CO List QIDs for this name")
        elif clash:
            d.update(status="review", reason=f"journal uses it as {rc}, CO List QID is a {top['wd_kind']}")
        elif top["name_is_label"]:
            d.update(status="matched", confidence="high", qid=top["qid"], label=top["label"])
        else:
            d.update(status="matched", confidence="medium", qid=top["qid"], label=top["label"],
                     reason="CO List uses a period polity or variant whose label differs from the printed name")
        s = d["status"] + ("/" + d["confidence"] if "confidence" in d else "")
        tally[s] += 1; rec[s] += r["records"]; out.append(d)
    with open(HERE / "grounding/places_tier1.jsonl", "w") as fh:
        for d in out: fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"place records in journal: {total}")
    for s in sorted(tally): print(f"  {s:16} names={tally[s]:5}  records={rec[s]:7}  ({rec[s]/total:.1%})")

if __name__ == "__main__":
    main()
