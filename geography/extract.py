"""Extract a Wikidata geography edge list from QLever."""
import csv
import io
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ENDPOINT = "https://qlever.dev/api/wikidata"
ENTITY = "http://www.wikidata.org/entity/"
DIRECT = "http://www.wikidata.org/prop/direct/"
PROPERTIES = (
    "P17", "P47", "P131", "P150", "P177", "P206", "P276", "P361", "P403",
    "P527", "P706", "P885", "P974", "P1365", "P1366", "P3018", "P4552",
)
LOCAL_ONLY = {"P361", "P527", "P1365", "P1366"}


def query(sparql):
    request = Request(
        ENDPOINT,
        data=urlencode({"query": sparql}).encode(),
        headers={
            "Accept": "text/csv",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "CeylonHistoryGeography/1.0",
        },
    )
    with urlopen(request, timeout=90) as response:
        return list(csv.reader(io.StringIO(response.read().decode("utf-8"))))


def fetch_edges(subjects):
    values = " ".join(f"wd:{qid}" for qid in subjects)
    properties = ", ".join(f"wdt:{pid}" for pid in PROPERTIES)
    header, *rows = query(f"""
PREFIX wd: <{ENTITY}>
PREFIX wdt: <{DIRECT}>
SELECT ?subject ?property ?object WHERE {{
  VALUES ?subject {{ {values} }}
  ?subject ?property ?object .
  FILTER(?property IN ({properties}))
}}
""")
    if header != ["subject", "property", "object"]:
        raise ValueError(f"Unexpected edge response header {header}")
    return [
        (subject.removeprefix(ENTITY), prop.removeprefix(DIRECT), obj.removeprefix(ENTITY))
        for subject, prop, obj in rows
        if obj.startswith(ENTITY) and re.fullmatch(r"Q[1-9][0-9]*", obj.removeprefix(ENTITY))
    ]


def main():
    header, *rows = query((HERE / "wikidata-places.rq").read_text())
    if header != ["subject"]:
        raise ValueError(f"Unexpected place response header {header}")
    places = sorted({
        uri.removeprefix(ENTITY) for uri, in rows
        if uri.startswith(ENTITY) and re.fullmatch(r"Q[1-9][0-9]*", uri.removeprefix(ENTITY))
    })
    if not places:
        raise ValueError("QLever returned no places")
    print(f"Found {len(places)} scoped items", flush=True)
    place_set = set(places)
    batches = [places[i:i + 1000] for i in range(0, len(places), 1000)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        edges = {
            (subject, pid, obj)
            for batch in pool.map(fetch_edges, batches)
            for subject, pid, obj in batch
            if pid not in LOCAL_ONLY or obj in place_set
        }
    with (HERE / "wikidata-edges.csv").open("w", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["subject_qid", "pid", "object_qid"])
        writer.writerows(sorted(edges))
    print(f"Wrote {len(edges)} edges", flush=True)


if __name__ == "__main__":
    main()
