"""Ceylon Blue Books: the article-by-country trade ledgers in the single-block layout of 1880-1906.

From 1907 the ledgers are read by jobs/trade_work/read_trade.py. Before that each page is one block:

    article | country | figures ...

with the article named once, countries below it under "Br. Col.—" and "For. Coun.—", and the article's total as a
row of figures with no label. Classes and groups are headings that span the table.

  1901-1906  quantities are single numbers; values are whole rupees
             imports: total quantity, quantity entered for home consumption, value
             exports: quantity and value, each as Ceylon produce / other produce / total
  1880-1900  quantities of weight are printed as hundredweights, quarters and pounds ("837 0 7"); values as
             rupees and cents in two columns; further columns give average price and duty. See LAYOUT below.

Everything is kept as printed; `value` is the number where the cell is one, and for cwt-qr-lb the weight in cwt.
Each article is checked: its country rows should add to its total row. Rows that cannot be read safely go to the
skipped file with a reason, and are never guessed.

Output (same columns as trade.tsv.gz):
  extracted/trade_1880_1906.tsv.gz
  extracted/trade_1880_1906_checks.tsv     articles whose total does not equal the sum of their countries
  extracted/trade_1880_1906_skipped.tsv
Usage: read_trade_old.py [volume key ...]
"""
import collections, csv, gzip, io, json, re, sys
from decimal import Decimal
from pathlib import Path

BB = Path(__file__).parent
FIELDS = ("table_id year_volume pdf_page printed_page flow class_as_printed group_as_printed article_as_printed "
          "country_group_as_printed country_as_printed unit_as_printed measure value_as_printed value row_kind note").split()
IMPORT = ["quantity_total", "quantity_home_consumption", "value_total_rs"]
EXPORT = ["quantity_ceylon_produce", "quantity_other_produce", "quantity_total",
          "value_ceylon_produce_rs", "value_other_produce_rs", "value_total_rs"]
EMPTY = {"", ".", "..", "...", "—", "–", "-", "--", "―", "…", "— —", "Nil", "nil"}
DITTO = {'"', "''", ",,", "„", "”", "“", "〃", "»", "do.", "Do.", "do", "Do"}
GROUP = re.compile(r"^(Br(?:it(?:ish)?)?\.? ?Col(?:onies|\.)?|For(?:eign)?\.? ?Coun(?:tries|\.)?)\s*[—–\-.:]*\s*", re.I)
LEADERS = re.compile(r"\s*(?:\.{2,}|…+)[\s.…]*")
YEARS_NEW = [str(y) for y in range(1901, 1907)]


def clean(s): return LEADERS.sub(" ", s).strip(" .")


def num(c):
    """(value, ok). A dash or blank is ('', True); a number is (digits, True); anything else is ('', False)."""
    c = re.sub(r"^Rs\.?\s*", "", c.strip())
    if c in EMPTY: return "", True
    c2 = c.replace(",", "")          # a cell with a space holds two figures (two printed rows merged): not a number
    if re.fullmatch(r"\d+", c2): return c2, True
    return "", False


def flow_of(t):
    h = " ".join(t["rows"][0]).lower() if t["rows"] else ""
    first = t["rows"][0][0].strip().lower() if t["rows"] else ""
    if "countr" not in h: return None
    if first.startswith("imports") and t["n_cols"] == 5: return "import"
    if first.startswith("exports") and t["n_cols"] in (8, 9): return "export"
    return None


class Reader:
    def __init__(self, year):
        self.year = year
        self.rows, self.skipped, self.articles = [], [], []
        self.flow = None
        self.reset()

    def reset(self):
        self.cl = self.gr = self.parent = self.article = self.cg = self.unit = ""
        self.cur = None
        self.leaf = None            # the article cell last seen (the OCR repeats it on every row of the article)
        self.last_sub = None
        self.pending = ""           # a group heading that may itself be the article ("(a) Apparel, made up")

    def skip(self, t, i, r, why): self.skipped.append((t["id"], i, json.dumps(r, ensure_ascii=False), why))

    def start(self, name, t, i, continued=False):
        # Sub-entries sit under a heading ending in a dash ("Coffee—": Mixed, Unmixed). Nothing in the table marks
        # where they end. Articles and sub-entries are each in alphabetical order, so the heading is dropped when a
        # name sorts before the previous sub-entry but after the heading itself ("Confectionery" after "Unmixed").
        if self.parent and name and not continued:
            k, pk, prev = name.lower(), self.parent.rstrip("—–- ").lower(), (self.last_sub or "").lower()
            if prev and k < prev and k > pk: self.parent = ""
            self.last_sub = name if self.parent else None
        full = (self.parent + " " + name).strip() if self.parent and name else (name or self.parent)
        if continued and self.cur and self.cur["article"] == full: return
        self.pending = ""
        self.article, self.cg, self.unit = full, "", ""
        self.cur = {"article": full, "flow": self.flow, "start": t["id"], "row": i, "sum": collections.defaultdict(Decimal),
                    "totals": [], "countries": 0, "skips": 0, "continued": continued}
        self.articles.append(self.cur)

    def heading(self, s, t, i):
        s = s.strip()
        parts = [x for x in re.split(r"(?<=contd\.)\s+|\s+(?=\(\d+\)\s|\([a-z]\)\s)", s) if x]      # "II.—Raw Materials—contd. (2) Metal—contd. Copper, sheathing"
        if len(parts) > 1:
            for x in parts[:-1]: self.heading(x, t, i)
            last = parts[-1]
            if re.match(r"^(?:[IVX]+\.\s*[—–-]|\(\w+\))", last) or last.rstrip().endswith(("—", "–")) or re.search(r"contd\.?$", last): self.heading(last, t, i)
            else: self.start(clean(last), t, i)           # the article's own name, merged into the heading cell
            return
        g = GROUP.match(s)
        if g and g.end() == len(s):
            self.cg = "British Colonies" if g[1].lower().startswith("br") else "Foreign Countries"; return
        contd = bool(re.search(r"cont(?:inue)?d\.?\s*$", s, re.I))
        base = re.sub(r"\s*[—–-]?\s*cont(?:inue)?d\.?\s*$", "", s, flags=re.I).strip()
        if re.match(r"^[IVXL]+\.\s*[—–-]", base): self.cl, self.gr, self.parent = base, "", ""
        elif re.match(r"^\(\d+\)", base): self.gr, self.parent, self.pending = base, "", base
        elif re.match(r"^\([a-z]\)", base): self.gr = re.sub(r"\s*\([a-z]\).*$", "", self.gr).strip() + " " + base; self.parent = ""; self.pending = base
        else:
            p = base.rstrip("—–- ").strip() + "—"
            if not (contd and self.parent == p): self.parent = p; self.last_sub = None
            return
        # a class or group heading does not end the article in hand: its total row does (see read)

    def read(self, tables):
        for t in tables:
            flow = flow_of(t)
            if not flow: continue
            if flow != self.flow: self.flow = flow; self.reset()
            measures = IMPORT if flow == "import" else EXPORT
            for i, r in enumerate(t["rows"]):
                r = [c.strip() for c in r]
                if r[0].lower().rstrip(".,:") in ("imports", "exports"): continue
                body = [c for c in r if c and c not in ("Rs.", "Rs")]
                if not body: continue
                if len(set(body)) == 1 and (len(body) >= 3 or not any(re.search(r"\d", c) for c in r[2:])) and not re.search(r"\d{2,}", body[0]):
                    self.heading(body[0], t, i); continue
                # two ways the OCR misplaces the label cells of a country row:
                #   the country in the article column, its leaders and unit in the country column
                #   the whole row one column to the left (country in the article column, figures from the second)
                def unitish(x):
                    x = LEADERS.sub("", x).strip(" .")
                    return x == "" or x in DITTO or re.fullmatch(r"[A-Za-z]{1,6}\.?", x) is not None
                if r[0] and r[1] and re.match(r"^(?:\.{2,}|…)", r[1]) and unitish(r[1]) and any(re.search(r"\d", x) or x in ("—", "–", "-") for x in r[2:]):
                    r = ["", r[0] + " " + r[1]] + r[2:]
                elif r[0] and LEADERS.search(r[0]) and not r[-1] and (num(r[1])[1] and (re.search(r"\d", r[1]) or r[1] in EMPTY - {""})):
                    r = [""] + r[:-1]
                r[1] = re.sub(r"^(?:\.{2,}|…)[\s.…]*", "", r[1])
                a, c, figs = r[0], r[1], r[2:2 + len(measures)]
                if any(x.strip() and x.strip() not in ("Rs.", "Rs") for x in r[2 + len(measures):]):
                    self.skip(t, i, r, "figures in a column beyond the layout"); continue
                hasfig = any(re.search(r"\d", x) for x in figs)
                contd = False
                if re.fullmatch(r"[—–-]?\s*cont(?:inue)?d\.?", c, re.I): contd, c = True, ""
                if a and re.match(r"^(?:[IVXL]+\.\s*[—–-]|\((?:\d+|[a-z])\)\s)", a) and (t["id"], a) != self.leaf:
                    # class and group headings merged into the article cell: peel them off, keep the article's own name
                    self.leaf = (t["id"], a)
                    rest = a
                    while True:
                        m = re.match(r"^((?:[IVXL]+\.\s*[—–-]\s*)?(?:\((?:\d+|[a-z])\)\s*)?[^—–:(]*[—–:]+(?:\s*contd\.)?)\s*(.*)$", rest)
                        if not m or not re.match(r"^(?:[IVXL]+\.\s*[—–-]|\((?:\d+|[a-z])\))", rest): break
                        self.heading(m[1].rstrip("—–: ") if not re.search(r"contd\.$", m[1]) else m[1], t, i); rest = m[2].strip()
                    if re.match(r"^\((?:\d+|[a-z])\)\s", rest):                 # "(a) Apparel, made up": the group is the article
                        self.heading(rest, t, i); rest = re.sub(r"^\(\w+\)\s*", "", rest)
                    rest = re.sub(r"^[IVXL]+\.\s*[—–-]\s*", "", rest)       # a class numeral left without its text
                    a = rest
                if a and (t["id"], a) == self.leaf and not contd: a = ""          # the same article cell, repeated
                elif a: self.leaf = (t["id"], a)
                if a:
                    if re.search(r"cont(?:inue)?d\.?\s*$", a, re.I): contd = True; a = re.sub(r"\s*[—–-]?\s*cont(?:inue)?d\.?\s*$", "", a, flags=re.I)
                    if a.rstrip().endswith(("—", "–")) and not c and not hasfig:
                        self.heading(a + ("—contd." if contd else ""), t, i); continue
                    self.start(clean(a), t, i, continued=contd)
                if not c and not hasfig: continue
                if (self.cur is None or self.cur.get("closed")) and not a and self.pending and (c or hasfig):
                    name = re.sub(r"^\(\w+\)\s*", "", self.pending).rstrip("—–- ")
                    self.parent = ""; self.start(clean(name), t, i); self.cur["named_by_heading"] = True
                if self.cur is None or (self.cur.get("closed") and not a):
                    self.skip(t, i, r, "figures with no article heading above them (after an article's total, or at the start of a run of pages)"); continue
                m = GROUP.match(c)
                if m and (m.end() == len(c) or c[m.end():].strip()):
                    self.cg = "British Colonies" if m[1].lower().startswith("br") else "Foreign Countries"
                    c = c[m.end():].strip()
                    if not c and not hasfig: continue
                note = [f"source row {i}"] + (["article named by its group heading"] if self.cur.get("named_by_heading") else [])
                if not c:
                    kind, country, unit = "article_total", "", self.unit
                    note.append("unlabelled row of figures read as the article total")
                elif re.match(r"^total\b", c, re.I):
                    kind, country, unit = "article_total", clean(c), self.unit
                else:
                    kind = "country"
                    parts = LEADERS.split(c, maxsplit=1)
                    country, tail = parts[0].strip(" ."), (parts[1].strip() if len(parts) > 1 else "")
                    if tail in DITTO or not tail: unit = self.unit; note += ["unit from ditto"] if tail in DITTO and self.unit else []
                    else: unit = tail; self.unit = unit
                    if not country or re.search(r"\d", country):
                        self.cur["skips"] += 1; self.skip(t, i, r, "country label not readable"); continue
                vals = [num(x) for x in figs]
                if not all(ok for _, ok in vals):
                    self.cur["skips"] += 1; self.skip(t, i, r, "a figure cell is not a plain number"); continue
                if kind == "country": self.cur["countries"] += 1
                else: self.cur["closed"] = True
                for mname, raw, (v, _) in zip(measures, figs, vals):
                    self.rows.append([t["id"], self.year, t["pdf_page"], t.get("printed_page") or "", flow, self.cl, self.gr, self.article,
                                      self.cg if kind == "country" else "", country, unit if mname.startswith("quantity") else "", mname,
                                      re.sub(r"^Rs\.?\s*", "", raw), v, kind, "; ".join(note)])
                    if kind == "country" and v: self.cur["sum"][mname] += Decimal(v)
                    elif kind == "article_total" and v: self.cur["totals"].append((mname, Decimal(v), t["id"], i, self.cur["sum"][mname]))
        return self


def write(path, fields, rows):
    if path.suffix == ".gz":
        with gzip.GzipFile(filename="", mode="wb", fileobj=path.open("wb"), mtime=0) as g, io.TextIOWrapper(g, encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(fields); w.writerows(rows)
    else:
        with path.open("w", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(fields); w.writerows(rows)


def main():
    years = sys.argv[1:] or YEARS_NEW
    readers = []
    for y in years:
        tables = [json.loads(l) for l in gzip.open(BB / f"tables/{y}.jsonl.gz", "rt")]
        readers.append(Reader(y).read(tables))
    out = BB / "extracted"
    write(out / "trade_1880_1906.tsv.gz", FIELDS, (r for rd in readers for r in rd.rows))
    write(out / "trade_1880_1906_skipped.tsv", ["table_id", "row_index", "cells", "reason"], (r for rd in readers for r in rd.skipped))
    checks = []
    print("volume flow   figures  articles  with_total  all_agree")
    for rd in readers:
        for flow in ("import", "export"):
            arts = [a for a in rd.articles if a["flow"] == flow and a["countries"]]
            wt = [a for a in arts if a["totals"]]
            good = 0
            for a in wt:
                last = {}
                for mname, v, tid, i, s in a["totals"]: last[mname] = (v, tid, i, s)      # the last total row of the article
                bad = [(mname, v, tid, i, s) for mname, (v, tid, i, s) in last.items() if v != s]
                good += not bad
                for mname, v, tid, i, s in bad:
                    checks.append((rd.year, flow, a["article"], a["start"], tid, i, mname, v, s, s - v, a["skips"], "continued from an earlier page" if a["continued"] else ""))
            n = sum(1 for r in rd.rows if r[4] == flow)
            if n: print(f"{rd.year:6} {flow:6} {n:8,} {len(arts):9,} {len(wt):10,} {good:9,}  {good / max(len(wt), 1):.1%}   skipped rows {sum(1 for s in rd.skipped)}")
    write(out / "trade_1880_1906_checks.tsv", ["year_volume", "flow", "article_as_printed", "article_start_table", "total_table_id", "total_row_index",
                                               "measure", "printed_total", "country_sum", "difference", "skipped_rows_in_article", "note"], checks)


if __name__ == "__main__":
    main()
