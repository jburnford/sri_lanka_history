"""Frequency table of extracted entity names, per type, from the Tropical Agriculturist mention files.

Source of truth is the extraction output (ner/mentions/part_*.jsonl.gz), keyed by stable article id.
A "record" is one entity per ~2,500-word chunk, so counts are chunk-level presence, not printed occurrences.
Output: names/<TYPE>.tsv  (key, records, articles, first_year, last_year, top surface forms, top roles)
"""
import collections, glob, gzip, json, re, sys, unicodedata
from pathlib import Path

SRC = Path("/mnt/data/jic823/tropical-agriculturist/ner/mentions")
OUT = Path(__file__).parent / "names"

def key(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"^the ", "", s)

def year(aid):
    m = re.search(r"#(\d{4})-", aid)
    return int(m.group(1)) if m else None

def main():
    stats = collections.defaultdict(lambda: {"n": 0, "arts": set(), "y0": 9999, "y1": 0,
                                             "surf": collections.Counter(), "roles": collections.Counter()})
    for f in sorted(glob.glob(str(SRC / "part_*.jsonl.gz"))):
        for line in gzip.open(f, "rt"):
            a = json.loads(line)
            y = year(a["id"])
            for m in a.get("mentions", []):
                k = key(m.get("norm") or m.get("text") or "")
                if not k: continue
                s = stats[(m.get("type"), k)]
                s["n"] += 1; s["arts"].add(a["id"])
                if y: s["y0"] = min(s["y0"], y); s["y1"] = max(s["y1"], y)
                s["surf"][m.get("text", "")] += 1
                if m.get("role"): s["roles"][m["role"].lower()] += 1
    by_type = collections.defaultdict(list)
    for (t, k), s in stats.items(): by_type[t].append((k, s))
    OUT.mkdir(exist_ok=True)
    for t, rows in by_type.items():
        rows.sort(key=lambda r: -len(r[1]["arts"]))
        tot = sum(s["n"] for _, s in rows)
        with open(OUT / f"{t}.tsv", "w") as fh:
            fh.write("key\trecords\tarticles\tfirst\tlast\tsurfaces\troles\n")
            for k, s in rows:
                fh.write("\t".join([k, str(s["n"]), str(len(s["arts"])), str(s["y0"]), str(s["y1"]),
                    " | ".join(f"{a} ({b})" for a, b in s["surf"].most_common(4)),
                    " | ".join(f"{a} ({b})" for a, b in s["roles"].most_common(4))]) + "\n")
        cum, marks = 0, {}
        for i, (_, s) in enumerate(rows, 1):
            cum += s["n"]
            for p in (50, 80, 90):
                if p not in marks and cum >= tot * p / 100: marks[p] = i
        print(f"{t}\tnames={len(rows)}\trecords={tot}\tnames covering 50/80/90% of records: {marks.get(50)}/{marks.get(80)}/{marks.get(90)}")

if __name__ == "__main__":
    main()
