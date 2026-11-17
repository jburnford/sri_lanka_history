"""Measure how much printed ink lies inside the outline of every parsed table.

The OCR model sometimes writes a plausible table for a blank page that has show-through from the other side.
Show-through is light grey, not black, so the share of dark pixels inside the table's outline on the scan
separates a printed table from an invented one. Sideways and faint pages still have ink; blank ones have none.

Usage: page_ink.py [volume key ...]   with keys, only those volumes are measured and the rest kept.
Output: bluebook/ink.tsv.gz   table_id, dark_share (inside the table outline), page_dark_share
"""
import csv, gzip, json, sys
from pathlib import Path
import fitz
import numpy as np

BB = Path(__file__).parent
PDFS = Path("/mnt/data/jic823/ceylon_blue_books")
OCR = Path("/mnt/data/jic823/ocr_chandra/out_chandra2")


def pix(page):
    pm = page.get_pixmap(dpi=36, colorspace=fitz.csGRAY)
    return np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.stride)[:, :pm.width] < 100


def share(dark, box):
    h, w = dark.shape
    x0, y0, x1, y1 = (max(0, min(int(v), lim)) for v, lim in zip(box, (w, h, w, h)))
    a = dark[y0:y1, x0:x1]
    return float(a.mean()) if a.size else 0.0


def main():
    pdf_by_stem = {p.stem: p for p in PDFS.glob("*/*.pdf")}
    only = set(sys.argv[1:])        # volume keys to (re)measure; the others are kept from the existing file
    keep = []
    if only and (BB / "ink.tsv.gz").exists():
        keep = [r for r in csv.reader(gzip.open(BB / "ink.tsv.gz", "rt"), delimiter="\t")][1:]
        keep = [r for r in keep if r[0].split(":")[0][2:] not in only]
    with gzip.open(BB / "ink.tsv.gz", "wt", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n"); w.writerow(["table_id", "dark_share", "page_dark_share"]); w.writerows(keep)
        for v in csv.DictReader(open(BB / "volumes.tsv"), delimiter="\t"):
            if v.get("key") == "skip": continue
            key = v.get("key") or v["year"]
            if only and key not in only: continue
            inner = [p.name for p in (OCR / v["folder"]).iterdir() if p.is_dir()][0]
            boxes = {}
            for l in open(OCR / v["folder"] / inner / f"{inner}_layout.jsonl"):
                d = json.loads(l); boxes[d["pdf_page"]] = d["page_box"]
            doc = fitz.open(pdf_by_stem[inner]); cur = None
            for l in gzip.open(BB / f"tables/{key}.jsonl.gz", "rt"):
                t = json.loads(l); p = t["pdf_page"]
                if p > len(doc) or p not in boxes: continue
                if cur != p: px = pix(doc[p - 1]); cur = p; W, H = px.shape[1], px.shape[0]; whole = share(px, (W * .1, H * .1, W * .9, H * .9))
                pb = boxes[p]; fx, fy = W / pb[2], H / pb[3]; bx = t["bbox"]
                w.writerow([t["id"], f"{share(px, (bx[0] * fx, bx[1] * fy, bx[2] * fx, bx[3] * fy)):.5f}", f"{whole:.5f}"])
            print(key, flush=True)


if __name__ == "__main__":
    main()
