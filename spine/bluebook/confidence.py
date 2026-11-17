"""Confidence level for every parsed Blue Book table, from evidence inside the table and its page.

Two independent tests.

1. Printed totals. For each row whose label starts with "Total" (or "Grand total"), each column of whole
   numbers is summed over the rows since the previous total row and compared with the printed total.
   A check that agrees means every number in it was read correctly and the rows and columns are in the
   right place (barring errors that cancel). Shillings and pence columns are left out (they carry).

2. Invented pages. The OCR model sometimes writes a plausible table for a page that is blank, or that carries
   only a section title, with show-through from the other side. Two signs together mark it: the second reading
   finds no text (or only a title and none of the table's numbers), and page_ink.py finds no dark pixels inside
   the table's outline on the scan. In a sample of 8 such tables all 8 were invented. An empty second reading
   alone is not a sign of invention: it usually means the table is printed sideways.

3. Second reading (second_reading.py). The share of a table's numbers of three or more digits that the
   scan's text layer also gives for the same page. Used only for volumes that have a text layer.

Output: bluebook/table_confidence.tsv.gz   one row per table
        bluebook/confidence_by_volume.tsv  summary
Levels: summed        every printed total that could be checked agrees with the sum of its parts, and at least one
                      of them is non-trivial (a non-zero total of at least two non-zero parts)
        two_readings  at least 90% of the numbers are also in the second reading, and the table has at least
                      MIN_DISTINCT (10) distinct numbers of 3+ digits
        partly        at least half the totals agree (one non-trivially), or at least 70% of the numbers are in the
                      second reading (at least 5 distinct numbers)
        unconfirmed   nothing confirms it: no usable total and no usable second reading. Not evidence of error.
        suspect       the page is probably blank or invented; do not use without looking at the scan
A total that does not agree is weak evidence: in a sample, most such cases were tables continued from another
page or columns the checker grouped wrongly, with the numbers themselves read correctly.

Unlabelled rows of figures are tried as running subtotals, but only an agreeing one is kept (a failing one is
usually not a subtotal at all). Because they can never fail they are reported separately
(running_subtotals_agree) and do not count towards any level. The second reading is a set-membership test (same
digits anywhere on the page): it says the numbers were printed on that page, not that they sit in the right row
or column, so a row shift can still reach two_readings.
"""
import collections, csv, glob, gzip, json, re
from pathlib import Path

BB = Path(__file__).parent
NUM = re.compile(r"^\(?-?[\d,. ]*\d\)?$")
EMPTY = re.compile(r"^(|[-—–.…· ]+|nil|none|do\.?|\"|,,|”|\*+)$", re.I)
TOTAL = re.compile(r"^\W*(grand\s+)?totals?\b", re.I)
MODERN = re.compile(r"\b(Q[1-4]|revenue growth|net income|cost of goods|gross profit|stakeholders?|current liabilities|"
                    r"operating expenses|total liabilities and equity|cash flow|quarterly statements?|GDP|USD|website|email)\b")


def num(c):
    c = c.strip()
    if EMPTY.match(c): return 0
    if not NUM.match(c): return None
    c = c.strip("()").replace(",", "").replace(" ", "")
    if c.count(".") == 1 and len(c.split(".")[1]) == 3 and len(c.split(".")[0]) <= 3: c = c.replace(".", "")  # 12.345 printed for 12,345
    if "." in c: return None  # decimals: not summed
    try: return int(c)
    except ValueError: return None


HALF = str.maketrans({"½": "", "¼": "", "¾": ""})
TOK = re.compile(r"\d[\d,.]*\d")          # as in second_reading.py
MIN_DISTINCT = 10                          # distinct numbers of 3+ digits a table needs to be confirmed by the second reading alone


def roles(rows, ncols):
    """Money columns: a cents column belongs to the rupee column on its left; s. and d. to the pounds column."""
    role = [""] * ncols
    for r in rows[:6]:
        for j, c in enumerate(r[:ncols]):
            h = c.strip().lower().replace(" ", "").rstrip(".")
            if h in ("c", "cts", "cents"): role[j] = "c"
            elif h == "s": role[j] = "s"
            elif h == "d": role[j] = "d"
            elif re.fullmatch(r"rs\.?c", h): role[j] = "rsc"
            elif re.fullmatch(r"£\.?s\.?d", h): role[j] = "lsd"
    return role


def value(r, j, role):
    """Value of column j in the smallest unit, 0 for a printed blank, None when it cannot be read as a number."""
    def cell(k): return r[k].strip().translate(HALF).strip() if k < len(r) else ""
    c = cell(j)
    if role[j] in ("rsc", "lsd"):
        if EMPTY.match(c): return 0
        p = c.replace(",", "").split()
        if not all(x.isdigit() for x in p): return None
        if role[j] == "rsc" and len(p) == 2: return int(p[0]) * 100 + int(p[1])
        if role[j] == "lsd" and len(p) == 3: return int(p[0]) * 240 + int(p[1]) * 12 + int(p[2])
        return None
    v = num(c)
    if v is None: return None
    if j + 1 < len(role) and role[j + 1] == "c":
        w = num(cell(j + 1)); return None if w is None else v * 100 + w
    if j + 2 < len(role) and role[j + 1] == "s" and role[j + 2] == "d":
        s_, d_ = num(cell(j + 1)), num(cell(j + 2)); return None if s_ is None or d_ is None else v * 240 + s_ * 12 + d_
    return v


def blank(r, j): return EMPTY.match(r[j].strip() if j < len(r) else "") is not None


def check_table(t):
    rows, n = t["rows"], t["n_cols"]
    role = roles(rows, n)
    checks = []
    # column totals: a row labelled Total, or an unlabelled row of figures (a running subtotal), against the rows above it
    for j in range(1, n):
        if role[j] in ("c", "s", "d"): continue
        block, seen = [], False
        for i, r in enumerate(rows):
            if len(r) <= j: continue
            if len(set(r)) == 1 and len(r) > 1: continue                      # a spanning section label
            v = value(r, j, role)
            label = r[0].strip()
            is_total = bool(TOTAL.match(label)) or any(TOTAL.match(c) for c in r[1:j])
            sub = label == "" and v is not None and not blank(r, j) and not is_total
            if v is None:
                if seen and not is_total: block = None                       # words among the figures: stop trusting this run
                elif is_total: block = []
                continue
            if is_total or sub:
                if block and sum(1 for b in block if b[1]) >= 2 and not blank(r, j):
                    diff = sum(b[0] for b in block) - v
                    kind = "agree" if diff == 0 else ("one_digit" if len(str(abs(diff)).strip("0")) == 1 else "differ")
                    nontrivial = v != 0 and sum(1 for b in block if b[0]) >= 2
                    # an unlabelled row is only kept when it agrees, so it can never fail: it is recorded as "sub"
                    # and does not count towards the level (see main)
                    if not (sub and kind != "agree"): checks.append((i, j, len(block), v, diff, kind, "sub" if sub else "total", nontrivial))
                block = [(v, True)] if sub and not blank(r, j) else []
                continue
            if block is None: block = []
            seen = seen or not blank(r, j)
            block.append((v, not blank(r, j)))
    # row totals: a column headed Total against the columns before it that carry the same unit heading
    nh = next((i for i, r in enumerate(rows) if any(re.fullmatch(r"[\d,]{2,}", c.strip()) for c in r)), min(4, len(rows)))
    hrows = rows[:max(nh, 1)]
    head = [" ".join(r[j] for r in hrows if j < len(r)) for j in range(n)]
    unit = [hrows[-1][j].strip().lower() if j < len(hrows[-1]) else "" for j in range(n)]
    tcols = [j for j in range(2, n) if re.search(r"\btotal\b", head[j], re.I) and role[j] == ""]
    prev = 1
    for j in tcols:
        if j - 1 in tcols: span_start = next(k for k in range(j, 0, -1) if k - 1 not in tcols)
        else: span_start = j
        cand = [k for k in range(prev, span_start) if role[k] == ""]
        grouped = any(k != j and k in tcols for k in range(span_start, n) if abs(k - j) == 1)
        parts = [k for k in cand if unit[k] == unit[j]] if grouped else cand
        if j + 1 not in tcols: prev = j + 1
        if len(parts) < 2 or (not grouped and len({unit[k] for k in parts}) > 1 and len(hrows) > 1 and any(re.search("total", unit[k]) is None and unit[k] != unit[parts[0]] for k in parts)): continue
        for i, r in enumerate(rows[len(hrows):], len(hrows)):
            if len(r) <= j or blank(r, j) or (len(set(r)) == 1): continue
            v = value(r, j, role); vals = [value(r, k, role) for k in parts]
            if v is None or any(x is None for x in vals) or sum(1 for k in parts if not blank(r, k)) < 2: continue
            diff = sum(vals) - v
            kind = "agree" if diff == 0 else ("one_digit" if len(str(abs(diff)).strip("0")) == 1 else "differ")
            checks.append((i, j, len(parts), v, diff, kind, "row", v != 0 and sum(1 for x in vals if x) >= 2))
    return checks


def repeats(t):
    """A column in which one non-trivial number fills most of the cells is a sign of invented content."""
    hr = t.get("header_rows") or 1
    for j in range(1, t["n_cols"]):
        col = [r[j].strip() for r in t["rows"][hr:] if j < len(r) and re.search(r"\d{3}", r[j])]
        if len(col) >= 5 and collections.Counter(col).most_common(1)[0][1] >= 0.7 * len(col): return True
    return False


def main():
    second, layer = {}, collections.defaultdict(list)
    if (BB / "second_reading_tables.tsv.gz").exists():
        for r in csv.DictReader(gzip.open(BB / "second_reading_tables.tsv.gz", "rt"), delimiter="\t"):
            second[r["table_id"]] = (int(r["text_layer_chars"]), int(r["numbers"]), int(r["numbers_in_text_layer"]))
        for r in csv.DictReader(gzip.open(BB / "second_reading_pages.tsv.gz", "rt"), delimiter="\t"):
            layer[r["key"]].append(int(r["text_layer_chars"]))
    # a volume "has a text layer" when its typical page carries text; only then does an empty page mean something
    has_layer = {k: sorted(v)[len(v) // 2] >= 200 for k, v in layer.items()}
    ink = {}
    if (BB / "ink.tsv.gz").exists():
        for r in csv.DictReader(gzip.open(BB / "ink.tsv.gz", "rt"), delimiter="\t"): ink[r["table_id"]] = float(r["dark_share"])
    out, summ = [], collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(str(BB / "tables/*.jsonl.gz"))):
        key = Path(f).name.split(".")[0]
        pages = {}
        for l in gzip.open(str(f).replace("/tables/", "/pages/"), "rt"):
            p = json.loads(l); pages[p["pdf_page"]] = p
        for l in gzip.open(f, "rt"):
            t = json.loads(l); p = pages.get(t["pdf_page"], {})
            text = " ".join(p.get("text") or []) + " " + " ".join(t["headings"] or []) + " " + " ".join(" ".join(r) for r in t["rows"])
            flags = []
            if not p.get("printed_page") and not p.get("section"): flags.append("no_page_number")
            if MODERN.search(text): flags.append("modern_words")
            if repeats(t): flags.append("repeated_number")
            chars, nn, nin = second.get(t["id"], (None, 0, 0))
            if chars is not None and chars < 40: flags.append("no_second_reading")   # blank page, or a table printed sideways
            share = nin / nn if nn >= 5 and has_layer.get(key) and chars >= 40 else None
            dk = ink.get(t["id"])
            if dk == 0: flags.append("no_ink_in_outline")
            # invented content: the second reading finds a blank page, or only a title, and the scan agrees
            blank_page = chars is not None and chars < 40 and dk == 0
            title_page = chars is not None and chars < 150 and nn >= 10 and nin / nn < 0.1 and (dk == 0 or chars >= 40)
            if blank_page: flags.append("blank_page")
            elif title_page: flags.append("title_page_only")
            suspect = blank_page or title_page or ("no_page_number" in flags and ("modern_words" in flags or "repeated_number" in flags) and not share)
            allchecks = check_table(t)
            checks = [c for c in allchecks if c[6] != "sub"]          # labelled totals and row totals: these can fail
            subs = len(allchecks) - len(checks)                        # unlabelled running subtotals: only kept when they agree
            n = len(checks); ok = sum(c[5] == "agree" for c in checks); one = sum(c[5] == "one_digit" for c in checks)
            ok_real = sum(c[5] == "agree" and c[7] for c in checks)   # agreeing totals that are not zeros or a single part
            cells = sum(c[2] + 1 for c in checks if c[5] == "agree")
            # set membership on a page is easy to satisfy by chance with few numbers (against a random page about 9% of
            # tables with <5 distinct numbers reach 90%, about 3% with 5-9), so few-number tables cannot reach two_readings
            distinct = len({x for r in t["rows"] for c in r for x in (re.sub(r"\D", "", m) for m in TOK.findall(c)) if len(x) >= 3})
            level = ("suspect" if suspect else "summed" if n and ok == n and ok_real else
                     "two_readings" if share is not None and share >= 0.9 and distinct >= MIN_DISTINCT else
                     "partly" if (n and ok * 2 >= n and ok_real) or (share is not None and share >= 0.7 and distinct >= 5) else "unconfirmed")
            if n and ok == n and not ok_real: flags.append("only_trivial_totals")
            if subs: flags.append(f"subtotals_agree:{subs}")
            out.append((t["id"], t["year"], t["pdf_page"], t.get("printed_page") or "", level, n, ok, one, n - ok - one, cells, nn, nin, "" if share is None else f"{share:.2f}", ";".join(flags),
                        "; ".join(f"r{c[0]}c{c[1]} printed {c[3]} sum off by {c[4]:+d}" for c in checks if c[5] != "agree")[:300],
                        ok_real, subs, distinct))
            s = summ[key]; s["tables"] += 1; s[level] += 1; s["checks"] += n; s["agree"] += ok; s["one_digit"] += one
    with gzip.open(BB / "table_confidence.tsv.gz", "wt", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["table_id", "year", "pdf_page", "printed_page", "level", "totals_checked", "totals_agree", "off_by_one_digit", "differ",
                    "numbers_confirmed_by_totals", "numbers_3plus_digits", "also_in_second_reading", "share_in_second_reading", "flags", "disagreements",
                    "nontrivial_totals_agree", "running_subtotals_agree", "distinct_numbers_3plus"]); w.writerows(out)
    with open(BB / "confidence_by_volume.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        cols = ["tables", "summed", "two_readings", "partly", "unconfirmed", "suspect", "checks", "agree", "one_digit"]
        w.writerow(["volume"] + cols + ["share_of_totals_agreeing"])
        tot = collections.Counter()
        for k in sorted(summ):
            s = summ[k]; tot.update(s); w.writerow([k] + [s[c] for c in cols] + [f"{s['agree'] / s['checks']:.3f}" if s["checks"] else ""])
        w.writerow(["all"] + [tot[c] for c in cols] + [f"{tot['agree'] / tot['checks']:.3f}"])
    print({c: tot[c] for c in cols}, f"agree {tot['agree'] / tot['checks']:.1%}")


if __name__ == "__main__":
    main()
