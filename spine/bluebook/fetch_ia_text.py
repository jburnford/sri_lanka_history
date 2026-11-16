"""Download the Internet Archive's own page-indexed OCR text for each Blue Book volume.

Two small files per item: <stem>_hocr_searchtext.txt.gz (the text) and <stem>_hocr_pageindex.json.gz (where each
page starts and ends in it). Used by second_reading.py as an independent reading of the numbers.
Serial, one second between requests. Saved in spine/sources/bluebook_ia_text/.
"""
import csv, json, time, urllib.request
from pathlib import Path

BB = Path(__file__).parent
OUT = BB.parent / "sources/bluebook_ia_text"
UA = {"User-Agent": "research-script/1.0"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for v in csv.DictReader(open(BB / "volumes.tsv"), delimiter="\t"):
        item = v["archive_org_identifier"]
        if not item or v.get("key") == "skip": continue
        key = v.get("key") or v["year"]
        if (OUT / f"{key}_pageindex.json.gz").exists(): continue
        try:
            files = [f["name"] for f in json.loads(get(f"https://archive.org/metadata/{item}/files"))["result"]]
            st = [f for f in files if f.endswith("_hocr_searchtext.txt.gz")]; pi = [f for f in files if f.endswith("_hocr_pageindex.json.gz")]
            if not st or not pi: print(key, item, "no OCR text files"); continue
            time.sleep(1); a = get(f"https://archive.org/download/{item}/{urllib.request.quote(st[0])}")
            time.sleep(1); b = get(f"https://archive.org/download/{item}/{urllib.request.quote(pi[0])}")
            (OUT / f"{key}_searchtext.txt.gz").write_bytes(a); (OUT / f"{key}_pageindex.json.gz").write_bytes(b)
            print(key, item, len(a), flush=True)
        except Exception as e:
            print(key, item, "failed:", e, flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
