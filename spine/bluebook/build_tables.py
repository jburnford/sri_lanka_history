"""Ceylon Blue Books: turn the page-layout OCR into one record per printed table, with its page, the running
section, the headings above it and its cells. Nothing is interpreted here; this is the lossless table layer
that later, section-specific readers work from.

Input : /mnt/data/jic823/ocr_chandra/out_chandra2/<folder>/<name>/<name>_layout.jsonl  (volumes.tsv lists them)
Output: bluebook/tables/<year>.jsonl.gz   one table per line
        bluebook/pages/<year>.jsonl.gz    one page per line: printed page, running section, headings, text blocks
        bluebook/inventory.tsv            tables and pages per volume and section
Table id: bb<year>:p<pdf page>:t<n on page>. Row/col spans are expanded so every row has the same width.
"""
import csv, glob, gzip, html, json, os, re, sys, collections
from html.parser import HTMLParser
from pathlib import Path
HERE = Path(__file__).parent
ROOT = Path(os.environ.get("CEYLON_DATA", "/mnt/data/jic823")) / "ocr_chandra/out_chandra2"

def text(s):
    s = re.sub(r"<br\s*/?>", " ", s); s = re.sub(r"<math[^>]*>(.*?)</math>", r"\1", s, flags=re.S)
    s = re.sub(r"\\frac\{(\d+)\}\{(\d+)\}", r"\1/\2", s)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

class T(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.cur = None; self.cell = None; self.in_head = False
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "thead": self.in_head = True
        elif tag == "tr": self.cur = {"cells": [], "head": self.in_head}
        elif tag in ("td", "th") and self.cur is not None:
            def n(v):
                try: return max(1, min(int(v), 60))
                except Exception: return 1
            self.cell = {"t": [], "cs": n(a.get("colspan", 1)), "rs": n(a.get("rowspan", 1)), "th": tag == "th"}
        elif tag == "br" and self.cell is not None: self.cell["t"].append(" ")
    def handle_endtag(self, tag):
        if tag == "thead": self.in_head = False
        elif tag in ("td", "th") and self.cell is not None and self.cur is not None:
            self.cell["t"] = re.sub(r"\s+", " ", "".join(self.cell["t"])).strip(); self.cur["cells"].append(self.cell); self.cell = None
        elif tag == "tr" and self.cur is not None:
            self.rows.append(self.cur); self.cur = None
    def handle_data(self, d):
        if self.cell is not None: self.cell["t"].append(d)

def grid(rows):
    """Expand colspan/rowspan into a rectangle; spanned cells repeat their text."""
    out, carry = [], {}
    for r in rows:
        line, c = [], 0
        cells = list(r["cells"])
        while cells or c in carry:
            if c in carry:
                t, left = carry[c]; line.append(t)
                if left > 1: carry[c] = (t, left - 1)
                else: del carry[c]
                c += 1; continue
            cell = cells.pop(0)
            for k in range(cell["cs"]):
                line.append(cell["t"])
                if cell["rs"] > 1: carry[c] = (cell["t"], cell["rs"] - 1)
                c += 1
        out.append(line)
    w = max((len(l) for l in out), default=0)
    return [l + [""] * (w - len(l)) for l in out], w

PRINTED = re.compile(r"^\(?\s*([A-Z]{1,2} ?\d{1,3}[A-Z]?|[ivxlc]+|\d{1,4})\s*\)?\.?$")
RUNNING = re.compile(r"^\[?\s*([A-Z][A-Za-z,&;.' \-]{2,60}?)\.?\s*\]?$")

def main():
    (HERE / "tables").mkdir(exist_ok=True); (HERE / "pages").mkdir(exist_ok=True)
    inv = []
    for v in csv.DictReader(open(HERE / "volumes.tsv"), delimiter="\t"):
        if v.get("key") == "skip": continue
        fs = glob.glob(str(ROOT / v["folder"] / "*" / "*_layout.jsonl"))
        if not fs: print("missing", v["folder"]); continue
        year = v["year"]; key = v.get("key") or year; nt = 0; section = None; secs = collections.Counter(); np_ = 0
        with gzip.open(HERE / f"tables/{key}.jsonl.gz", "wt") as ft, gzip.open(HERE / f"pages/{key}.jsonl.gz", "wt") as fp:
            for line in open(fs[0]):
                d = json.loads(line); np_ += 1
                blocks = sorted(d["blocks"], key=lambda b: (b["bbox"][1], b["bbox"][0]))
                printed, running = None, None
                for b in blocks:
                    if b["label"] in ("Page-Header", "Page-Footer"):
                        t = text(b["content"])
                        m = PRINTED.match(t)
                        if m and printed is None: printed = m.group(1)
                        elif "BLUE BOOK" not in t.upper() and RUNNING.match(t) and ("[" in t or "]" in t): running = RUNNING.match(t).group(1).strip()
                if running: section = running
                heads, k, texts = [], 0, []
                for b in blocks:
                    t = text(b["content"])
                    if b["label"] in ("Section-Header", "Caption"):
                        heads.append({"y": b["bbox"][1], "text": t[:300]})
                    elif b["label"] in ("Text", "Footnote", "List-Group"): texts.append(t)
                    elif b["label"] == "Table":
                        p = T(); p.feed(b["content"]); rows, w = grid(p.rows)
                        if not rows: continue
                        k += 1; nt += 1
                        nh = sum(1 for r in p.rows if r["head"] or all(c["th"] for c in r["cells"]))
                        above = [h["text"] for h in heads if h["y"] <= b["bbox"][1]][-3:]
                        ft.write(json.dumps({"id": f"bb{key}:p{d['pdf_page']}:t{k}", "year": int(year), "volume": v["folder"], "pdf_page": d["pdf_page"],
                            "printed_page": printed, "section": section, "headings": above, "bbox": b["bbox"], "n_rows": len(rows), "n_cols": w,
                            "header_rows": nh, "rows": rows}, ensure_ascii=False) + "\n")
                        secs[section or ""] += 1
                fp.write(json.dumps({"year": int(year), "volume": v["folder"], "pdf_page": d["pdf_page"], "printed_page": printed, "section": section,
                                     "headings": [h["text"] for h in heads], "n_tables": k, "text": texts}, ensure_ascii=False) + "\n")
        inv.append((year, v["folder"], np_, nt, " | ".join(f"{s or '?'} ({n})" for s, n in secs.most_common(40))))
        print(year, "pages", np_, "tables", nt)
    with open(HERE / "inventory.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["year", "folder", "pages", "tables", "tables_by_running_section"]); w.writerows(inv)

if __name__ == "__main__":
    main()
