"""Cross-check: Colonial Office List career events against Empire Evolution polities, resolved by year.

For each event whose place_qid or colony_qid is an Empire Evolution territory:
  in_date     the territory's own dates contain the event years
  resolved    not in date, but a lineage neighbour (successor, predecessor, containing colony) is: the place
              stays as written and the polity for that year is known. No error; the join was too simple.
  unresolved  no territory in the lineage covers the years: an error or gap on one side.
Writes grounding/col_polity_check.tsv (per QID) and grounding/col_polity_unresolved.tsv.
"""
import collections
from common import *
from empire import Empire

def main():
    E = Empire()
    stats = collections.defaultdict(lambda: {"label": "", "in_date": 0, "resolved": 0, "unresolved": 0,
                                             "to": collections.Counter(), "years": []})
    tot = collections.Counter()
    for e in read_jsonl(COL / "career_events.jsonl"):
        ys = e.get("year_start"); ye = e.get("year_end") or ys
        if not ys: continue
        seen = set()
        for f in ("place_qid", "colony_qid"):
            q = e.get(f)
            if not q or q not in E.by_qid or q in seen: continue
            seen.add(q)
            s = stats[q]; s["label"] = (e.get("place_label") if f == "place_qid" else e.get("colony_label")) or s["label"]
            t, path, hops = E.polity_at(q, ys, ye)
            k = "in_date" if hops == 0 else "resolved" if t else "unresolved"
            s[k] += 1; tot[k] += 1
            if k == "resolved": s["to"][f"{t['name']} ({t['start']}-{t['end']})"] += 1
            if k == "unresolved": s["years"].append(ys)
    print("territory links:", dict(tot))
    rows = sorted(stats.items(), key=lambda x: -(x[1]["resolved"] + x[1]["unresolved"]))
    with open(HERE / "grounding/col_polity_check.tsv", "w") as fh, open(HERE / "grounding/col_polity_unresolved.tsv", "w") as fu:
        fh.write("qid\tcol_label\tempire_rows\tin_date\tresolved\tunresolved\tresolved_to\n")
        fu.write("qid\tcol_label\tempire_rows\tunresolved_events\tevent_years\n")
        for q, s in rows:
            own = "; ".join(f"{E.terr[t]['name']} {E.terr[t]['start']}-{E.terr[t]['end']}" for t in E.by_qid[q])
            fh.write("\t".join([q, str(s["label"]), own, str(s["in_date"]), str(s["resolved"]), str(s["unresolved"]),
                                " | ".join(f"{k}: {v}" for k, v in s["to"].most_common(4))]) + "\n")
            if s["unresolved"]:
                fu.write("\t".join([q, str(s["label"]), own, str(s["unresolved"]), f"{min(s['years'])}-{max(s['years'])}"]) + "\n")
    print("\nresolved through the graph (top):")
    for q, s in sorted(stats.items(), key=lambda x: -x[1]["resolved"])[:12]:
        print(f"  {str(s['label'])[:28]:28} {s['resolved']:5} -> " + " | ".join(f"{k}: {v}" for k, v in s["to"].most_common(2)))
    print("\nunresolved (top):")
    for q, s in sorted(stats.items(), key=lambda x: -x[1]["unresolved"])[:18]:
        if s["unresolved"]:
            own = "; ".join(f"{E.terr[t]['start']}-{E.terr[t]['end']}" for t in E.by_qid[q])
            print(f"  {q:10} {str(s['label'])[:28]:28} own dates {own[:24]:24} unresolved={s['unresolved']:4} event years {min(s['years'])}-{max(s['years'])}")
    print("QIDs with unresolved events:", sum(1 for s in stats.values() if s["unresolved"]))

if __name__ == "__main__":
    main()
