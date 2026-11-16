"""Compare every number in the parsed tables with an independent second reading of the same page.

The second reading is conventional OCR (Tesseract-style): the text layer inside the scanned PDF, joined with
the Internet Archive's own OCR text for the item where it has one. It is noisy and has no table structure,
but it does not invent content. A number that both readings give for the same page is
very unlikely to be wrong; a table on a page where the text layer is empty is probably invented.

Input : /mnt/data/jic823/ceylon_blue_books/<dir>/<stem>.pdf   (stem = inner folder name of the OCR output)
Output: bluebook/second_reading_pages.tsv.gz    per page: characters and number count in the text layer
        bluebook/second_reading_tables.tsv.gz   per table: numbers of 3+ digits, how many the text layer also has
Only numbers of three or more digits are compared: shorter ones match by chance.
"""
import collections, csv, glob, gzip, json, re, subprocess, sys
from pathlib import Path

BB = Path(__file__).parent
PDFS = Path("/mnt/data/jic823/ceylon_blue_books")
OCR = Path("/mnt/data/jic823/ocr_chandra/out_chandra2")
IA = BB.parent / "sources/bluebook_ia_text"
TOK = re.compile(r"\d[\d,.]*\d")
BOILER = re.compile(r"This content downloaded from|All use subject to|\d+\.\d+\.\d+\.\d+ on \w+, \d+ \w+ \d{4}.*")


def digits(s): return re.sub(r"\D", "", s)


def page_tokens(pdf):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, errors="replace").stdout
    out = []
    for p in txt.split("\f"):
        p = "\n".join(l for l in p.splitlines() if not BOILER.search(l))
        toks = {digits(m) for m in TOK.findall(p)}
        out.append((len(re.sub(r"\s", "", p)), {t for t in toks if len(t) >= 3}))
    return out


def ia_tokens(key):
    """The Internet Archive's own OCR text, cut into pages by its page index (fetch_ia_text.py)."""
    st, pi = IA / f"{key}_searchtext.txt.gz", IA / f"{key}_pageindex.json.gz"
    if not st.exists() or not pi.exists(): return []
    text = gzip.open(st, "rt", errors="replace").read()
    out = []
    for a, b, *_ in json.load(gzip.open(pi, "rt")):
        p = "\n".join(l for l in text[a:b].splitlines() if not BOILER.search(l))
        out.append((len(re.sub(r"\s", "", p)), {t for t in (digits(m) for m in TOK.findall(p)) if len(t) >= 3}))
    return out


def main():
    pdf_by_stem = {p.stem: p for p in PDFS.glob("*/*.pdf")}
    pages_out, tables_out = [], []
    for v in csv.DictReader(open(BB / "volumes.tsv"), delimiter="\t"):
        if v.get("key") == "skip": continue
        key = v.get("key") or v["year"]
        inner = [p.name for p in (OCR / v["folder"]).iterdir() if p.is_dir()]
        pdf = pdf_by_stem.get(inner[0]) if inner else None
        if not pdf: print(key, "no pdf found for", v["folder"]); continue
        pt, ia = page_tokens(pdf), ia_tokens(key)
        if ia and abs(len(ia) - len(pt)) <= 1:      # same page count: a number counts if either text has it
            pt = [(max(a[0], b[0]), a[1] | b[1]) for a, b in zip(pt, ia)] + pt[len(ia):]
        elif ia: print(key, "page counts differ: pdf", len(pt), "archive text", len(ia), "- archive text not used")
        for i, (chars, toks) in enumerate(pt, 1): pages_out.append((key, i, chars, len(toks)))
        n_all = n_ok = 0
        for l in gzip.open(BB / f"tables/{key}.jsonl.gz", "rt"):
            t = json.loads(l)
            chars, toks = pt[t["pdf_page"] - 1] if t["pdf_page"] <= len(pt) else (0, set())
            nums = [digits(m) for r in t["rows"] for c in dict.fromkeys(r) for m in TOK.findall(c)]
            nums = [x for x in nums if len(x) >= 3]
            ok = sum(x in toks for x in nums)
            tables_out.append((t["id"], t["pdf_page"], chars, len(nums), ok))
            n_all += len(nums); n_ok += ok
        print(key, "pages", len(pt), "numbers", n_all, f"also in text layer {n_ok / max(n_all, 1):.1%}", flush=True)
    for name, head, rows in (("second_reading_pages", ["key", "pdf_page", "text_layer_chars", "text_layer_numbers"], pages_out),
                             ("second_reading_tables", ["table_id", "pdf_page", "text_layer_chars", "numbers", "numbers_in_text_layer"], tables_out)):
        with gzip.open(BB / f"{name}.tsv.gz", "wt", newline="") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n"); w.writerow(head); w.writerows(rows)


if __name__ == "__main__":
    main()
