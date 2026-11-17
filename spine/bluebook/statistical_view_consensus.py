"""One value per series and year from the "Statistical View of the Progress of Ceylon", by agreement of printings.

Every Blue Book reprints the whole annual series, so a figure for (say) the population in 1851 is printed in
some thirty volumes, each set in type and read by OCR separately. extracted/statistical_view_compare.tsv (from the
Codex job in jobs/statistical_view_work/) lists the distinct values per series and year with the volumes that
print each. This script takes the value most volumes print and says how strong the agreement is. Nothing is
corrected: a minority value is an OCR slip in that volume or a revision, and stays in statistical_view.tsv.gz.

Output: extracted/statistical_view_series.tsv
  series, data_year, value, volumes_agreeing, volumes_printing, other_values, support
  support: strong   at least 5 volumes print the value and at least 80% of the printings agree
           fair     at least 2 volumes print it and it has a clear majority (at least twice the next value)
           weak     anything else, including a single printing
"""
import csv, json
from pathlib import Path

BB = Path(__file__).parent


def main():
    out, tally = [], {}
    for r in csv.DictReader(open(BB / "extracted/statistical_view_compare.tsv"), delimiter="\t"):
        vals = [v for v in json.loads(r["distinct_values_with_volumes_json"]) if v.get("kind") == "number"]
        if not vals: continue
        vals.sort(key=lambda v: -len(v["volumes"]))
        n, tot = len(vals[0]["volumes"]), sum(len(v["volumes"]) for v in vals)
        nxt = len(vals[1]["volumes"]) if len(vals) > 1 else 0
        support = "strong" if n >= 5 and n / tot >= 0.8 else "fair" if n >= 2 and n >= 2 * max(nxt, 1) else "weak"
        if len(vals) > 1 and n == nxt: support = "weak"
        out.append((r["series"], r["data_year"], vals[0]["value"], n, tot,
                    "; ".join(f"{v['value']} ({len(v['volumes'])})" for v in vals[1:4]), support))
        tally[support] = tally.get(support, 0) + 1
    with open(BB / "extracted/statistical_view_series.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["series", "data_year", "value", "volumes_agreeing", "volumes_printing", "other_values", "support"]); w.writerows(out)
    print(len(out), tally)


if __name__ == "__main__":
    main()
