"""Index of the History of Ceylon Tea estate and planter registries, for linking only.

historyofceylontea.com has already compiled registers of estates and of planters from the Ferguson directories
and other sources. This project does not rebuild that work: it links to it. This script reads the registry pages
saved locally (by the harvest in /mnt/data/jic823/historyofceylontea_wayback, which this script does not touch)
and writes a small index: for each page its name, the fields needed to tell namesakes apart, and its URL.

The index (links/hoct/) is local and is not published. Only matches, each a link from one of our names to
their page, are published (see match_hoct.py).

Output: links/hoct/estates.tsv    site_id, name, post_town, district, url
        links/hoct/planters.tsv   site_id, name, first_year, last_year, estates (as listed on the page), url
Run with the harvest's Python:  /mnt/data/jic823/historyofceylontea_wayback/_scripts/venv/bin/python build_hoct_index.py
"""
import csv, glob, os, re, sys
from pathlib import Path

BASE = "/mnt/data/jic823/historyofceylontea_wayback"
sys.path.insert(0, BASE + "/_scripts")
import parse_registries as P            # the harvest's own parser: read only
from bs4 import BeautifulSoup

OUT = Path(__file__).parent / "hoct"
SITE = "https://www.historyofceylontea.com"


def years(rows):
    ys = [int(y) for r in rows for y in re.findall(r"\b(1[89]\d\d|20[0-2]\d)\b", " ".join(str(v) for v in r.values()))]
    return (min(ys), max(ys)) if ys else ("", "")


def main():
    man = {}
    for kind, pat, fn, name in (("estate", "raw/tea-estates/estates-registry/*.html", P.parse_estate, "estates.tsv"),
                                ("planter", "raw/tea-planters/planters-registry/*.html", P.parse_planter, "planters.tsv")):
        rows, bad = [], 0
        for path in sorted(glob.glob(os.path.join(BASE, pat))):
            rel = os.path.relpath(path, BASE)
            sid = re.search(r"--(\d+)\.html$", path)
            try:
                rec = fn(BeautifulSoup(open(path, "rb").read(), "lxml"))
            except Exception:
                bad += 1; continue
            if not rec or not rec.get("name"): bad += 1; continue
            url = f"{SITE}/{rel[len('raw/'):]}"
            if kind == "estate":
                rows.append((sid[1] if sid else "", rec["name"], rec.get("Post Town", ""), rec.get("District", ""), url))
            else:
                hist = [r for sec in (rec.get("sections") or {}).values() if isinstance(sec, list) for r in sec if isinstance(r, dict)]
                y0, y1 = years(hist)
                est = sorted({str(r.get("Estate") or r.get("Estate Name") or "").strip() for r in hist} - {""})
                rows.append((sid[1] if sid else "", rec["name"], y0, y1, " | ".join(est)[:300], url))
        OUT.mkdir(exist_ok=True)
        with open(OUT / name, "w", newline="") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(["site_id", "name", "post_town", "district", "url"] if kind == "estate" else ["site_id", "name", "first_year", "last_year", "estates", "url"])
            w.writerows(rows)
        print(kind, len(rows), "pages indexed;", bad, "not parsed")


if __name__ == "__main__":
    main()
