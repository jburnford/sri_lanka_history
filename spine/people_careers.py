"""Join journal person profiles to their Colonial Office List careers, with the polity resolved per year.

Reads the Tropical Agriculturist person links as they stand (ner/persons/out/persons.tsv: model- and
rule-decided, not yet human-checked) and the CO List career events. For each linked person, lists every
posting with the place as grounded, the colony as recorded, and the Empire Evolution polity for those years.
Outputs grounding/people.jsonl (one row per linked profile) and analysis/careers_outside_ceylon.tsv.
"""
import collections, csv, json, sys
from common import *
from empire import Empire
csv.field_size_limit(sys.maxsize)
PERSONS = DATA / "tropical-agriculturist/ner/persons/out/persons.tsv"
CEYLON = {"Q918153", "Q854"}

def main():
    E = Empire()
    events = collections.defaultdict(list)
    for e in read_jsonl(COL / "career_events.jsonl"): events[e["person_id"]].append(e)
    colp = {p["person_id"]: p for p in read_jsonl(COL / "persons.jsonl")}
    out, elsewhere, n_wd, n_col, n_both = [], collections.Counter(), 0, 0, 0
    before_after = collections.Counter()
    (HERE / "analysis").mkdir(exist_ok=True)
    fixes = {c["profile_id"]: c for c in read_jsonl(HERE / "grounding/people_corrections.jsonl")} if (HERE / "grounding/people_corrections.jsonl").exists() else {}
    for r in csv.DictReader(open(PERSONS), delimiter="\t"):
        fix = fixes.get(r["id"])
        if fix: r.update(fix["set"])          # reviewed corrections applied on top of the pipeline's links
        qid, cid = r["wikidata_qid"].strip(), r["colist_person_id"].strip()
        if not qid and not cid: continue
        n_wd += bool(qid); n_col += bool(cid); n_both += bool(qid and cid)
        d = {"type": "PERSON", "profile_id": r["id"], "name": r["display"], "records": int(r["mentions"]),
             "articles": int(r["articles"]), "first": r["first"], "last": r["last"], "journal_roles": r["roles"],
             "wikidata_qid": qid or None, "qid_source": r["qid_source"] or None, "qid_confidence": r["qid_confidence"] or None,
             "colist_person_id": cid or None, "colist_decision": r["colist_decision"] or None,
             "review_status": "unreviewed", "source": "tropical-agriculturist ner/persons v2"}
        if fix: d["correction"] = fix["why"]
        if cid and cid in events:
            car, ceylon_years = [], []
            for e in sorted(events[cid], key=lambda e: (e.get("year_start") or 0, e.get("seq") or 0)):
                ys = e.get("year_start"); ye = e.get("year_end") or ys
                pol = None
                q = e.get("colony_qid") or e.get("place_qid")
                if ys and q:
                    t, path, hops = E.polity_at(q, ys, ye)
                    if t: pol = {"territory": t["id"], "name": t["name"], "qid": t["qid"], "resolved_by_lineage": bool(hops)}
                car.append({"position": e.get("position"), "start": ys, "end": e.get("year_end"), "acting": e.get("is_acting"),
                            "place_as_recorded": e.get("place_raw"), "place_qid": e.get("place_qid"), "place_label": e.get("place_label"),
                            "colony_qid": e.get("colony_qid"), "colony_label": e.get("colony_label"), "polity_at_date": pol})
                if e.get("colony_qid") in CEYLON and ys: ceylon_years.append(ys)
            d["career"] = car
            d["colist_name"] = " ".join(x for x in [colp.get(cid, {}).get("given_names") or colp.get(cid, {}).get("given"), colp.get(cid, {}).get("surname")] if x) or None
            cols = {}
            for c in car:
                if c["colony_qid"] and c["colony_qid"] not in CEYLON and c["start"]:
                    cols.setdefault((c["colony_qid"], c["colony_label"]), c["start"])
            for (cq, cl), y in cols.items():
                elsewhere[(cq, cl)] += 1
                if ceylon_years: before_after["before Ceylon" if y < min(ceylon_years) else "after first Ceylon posting"] += 1
        out.append(d)
    with open(HERE / "grounding/people.jsonl", "w") as fh:
        for d in out: fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    with open(HERE / "analysis/careers_outside_ceylon.tsv", "w") as fh:
        fh.write("colony_qid\tcolony\tjournal_people_who_served_there\n")
        for (cq, cl), n in elsewhere.most_common(): fh.write(f"{cq}\t{cl}\t{n}\n")
    with_car = [d for d in out if d.get("career")]
    print(f"linked profiles: {len(out)} (Wikidata {n_wd}, CO List {n_col}, both {n_both}); with career events: {len(with_car)}")
    print("journal records carried by linked profiles:", sum(d["records"] for d in out))
    print("served outside Ceylon:", sum(1 for d in with_car if any(c['colony_qid'] and c['colony_qid'] not in CEYLON for c in d['career'])), dict(before_after))
    for (cq, cl), n in elsewhere.most_common(15): print(f"  {n:3}  {cl} ({cq})")

if __name__ == "__main__":
    main()
