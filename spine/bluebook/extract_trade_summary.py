"""Ceylon Blue Books, 1922-1938: value of trade with each country, by class.

Each volume prints four "Summary Statements of the Value of ..." by country and class: (1) imports, (2) domestic
exports, (3) re-exports, (4) total exports. These exist for the years after 1928 too, when the article-by-country
ledgers are no longer printed, so they are the only source here for trade partners in 1929-1938.

Everything is kept as printed. Each row carries its own check: the classes add to "Total Merchandise", and
merchandise plus bullion and specie adds to the row total. A row that passes both was read correctly in every
cell (barring errors that cancel); a row that fails is flagged, never corrected.

Output: bluebook/extracted/trade_by_country_class.tsv
        bluebook/extracted/trade_by_country_class_checks.tsv   rows whose printed totals do not add up, or cannot be checked
"""
import collections, csv, glob, gzip, json, re
from pathlib import Path

BB = Path(__file__).parent
STATEMENT = [(r"value of imports", "imports"), (r"domestic exports", "domestic_exports"), (r"re-?exports", "re_exports"),
             (r"total exports", "total_exports")]
EMPTY = re.compile(r"^(|[—–\-.… ]+|nil)$", re.I)
FIELDS = ["table_id", "year_volume", "year_data", "pdf_page", "statement", "region_as_printed", "country_as_printed", "row_kind",
          "column_as_printed", "measure", "value_as_printed", "value", "row_check", "note"]


def clean(s): return re.sub(r"\s*\.{2,}\s*$", "", re.sub(r"\s+", " ", s)).strip(" .")


def num(c):
    c = c.strip()
    if EMPTY.match(c): return 0
    c = re.sub(r"[*†‡§]", "", c).replace(",", "").replace(" ", "")
    return int(c) if c.isdigit() else None


def measure_of(head):
    h = head.lower().strip()
    if h.startswith("total merchandise"): return "total_merchandise"
    if h.startswith("total"): return "total"                 # "Total Imports (including Bullion and Specie)"
    m = re.search(r"class\s+([ivx]+)", h)
    if m and m[1] == "v" and ("miscellaneous" in h or "animals" in h): return "class_iv"   # the OCR read "Class IV." as "Class V." (1929)
    if "bullion" in h or (m and m[1] == "v"): return "bullion_and_specie"    # headed "Class V." from 1933
    if "postal" in h: return "postal_articles"               # a separate column in the total-exports statement from 1936
    if m: return "class_" + m[1]
    return ""


def main():
    out, checks, stat = [], [], collections.Counter()
    for f in sorted(glob.glob(str(BB / "tables/*.jsonl.gz"))):
        key = Path(f).name.split(".")[0]
        for l in gzip.open(f, "rt"):
            t = json.loads(l)
            if not t["rows"]: continue
            head2 = " ".join(c for r in t["rows"][:2] for c in r).lower()
            title = " ".join(t.get("headings") or [])
            if not ("countries of" in head2 and "class i" in head2 and "summary statement" in title.lower()): continue
            title_l = title.lower()
            st = next((name for pat, name in STATEMENT if re.search(pat, title_l)), "")
            ym = re.search(r"during the year (\d{4})", title_l)
            yd = ym[1] if ym else ""
            nh = next(i for i, r in enumerate(t["rows"]) if any(re.fullmatch(r"[\d,]{2,}", c.strip()) for c in r[1:]))
            heads = [clean(" ".join(dict.fromkeys(r[j] for r in t["rows"][:nh] if j < len(r) and r[j].strip() not in ("Rs.", "Rs")))) for j in range(t["n_cols"])]
            meas = [measure_of(h) for h in heads]
            region = ""
            for i, r in enumerate(t["rows"][nh:], nh):
                label = clean(r[0])
                vals = r[1:]
                if not label and not any(v.strip() for v in vals): continue
                if not any(re.search(r"\d", v) or v.strip() in ("—", "–", "-") for v in vals):
                    if label: region = label                      # "Africa :", "Other Parts of British Empire"
                    continue
                kind = "grand_total" if re.match(r"grand total", label, re.I) else "total" if re.match(r"total\b", label, re.I) else "country"
                nums = {meas[j]: num(r[j]) for j in range(1, len(r)) if meas[j]}
                cls = [v for k, v in nums.items() if k.startswith("class_") or k == "postal_articles"]
                tm, bu, tot = nums.get("total_merchandise"), nums.get("bullion_and_specie"), nums.get("total")
                problems = []
                if any(v is None for v in nums.values()): chk = "unreadable figure"
                else:
                    if tm is not None and cls and sum(cls) != tm: problems.append(f"classes add to {sum(cls)}, total merchandise printed {tm}")
                    if tm is not None and bu is not None and tot is not None and tm + bu != tot: problems.append(f"merchandise and bullion add to {tm + bu}, total printed {tot}")
                    chk = "adds up" if not problems and tm is not None and sum(k.startswith("class_") for k in nums) >= 4 else "; ".join(problems) or "not checkable"
                stat[(key, chk if chk in ("adds up", "not checkable", "unreadable figure") else "does not add up")] += 1
                if chk != "adds up": checks.append((t["id"], key, yd, st, label, i, chk))
                notes = [f"source row {i}"] + ([] if yd else ["year not read from the heading: the volume year is given"]) + ([] if st else ["statement not identified from the heading"])
                for j in range(1, len(r)):
                    if not meas[j]: continue
                    v = num(r[j])
                    out.append((t["id"], t["year"], yd or t["year"], t["pdf_page"], st, region if kind == "country" else "", label, kind, heads[j], meas[j], r[j].strip(),
                                "" if v is None or EMPTY.match(r[j].strip()) else v, chk, "; ".join(notes + [f"column {j}"])))
    with open(BB / "extracted/trade_by_country_class.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n"); w.writerow(FIELDS); w.writerows(out)
    with open(BB / "extracted/trade_by_country_class_checks.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n"); w.writerow(["table_id", "volume", "year_data", "statement", "row_label", "source_row", "check"]); w.writerows(checks)
    vols = sorted({k for k, _ in stat})
    print(len(out), "figures;", len(vols), "volumes")
    for k in vols:
        a, b, c, d = (stat[(k, x)] for x in ("adds up", "does not add up", "not checkable", "unreadable figure"))
        print(f"  {k}: rows {a + b + c + d}, add up {a} ({a / max(a + b + c + d, 1):.0%}), do not {b}, not checkable {c}, unreadable {d}")


if __name__ == "__main__":
    main()
