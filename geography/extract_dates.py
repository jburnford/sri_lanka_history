"""Fetch Wikidata time statements and geographic edge date qualifiers."""
import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from time import sleep
from urllib.error import HTTPError

from extract import ENTITY, HERE, LOCAL_ONLY, PROPERTIES, query

PROP = "http://www.wikidata.org/prop/"
STATEMENT = ENTITY + "statement/"
VALUE = "http://www.wikidata.org/value/"
WB = "http://wikiba.se/ontology#"


def local_id(uri):
    return uri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def triples(subjects, restriction):
    subject_terms = " ".join(f"<{uri}>" for uri in subjects)
    sparql = f"""
SELECT ?subject ?predicate ?object WHERE {{
  VALUES ?subject {{ {subject_terms} }}
  ?subject ?predicate ?object .
  {restriction}
}}
"""
    for delay in (5, 15, 30, None):
        try:
            header, *rows = query(sparql)
            break
        except HTTPError as exc:
            if exc.code != 429 or delay is None:
                raise
            sleep(delay)
    if header != ["subject", "predicate", "object"]:
        raise ValueError(f"Unexpected triple response header {header}")
    return rows


def batch_triples(subjects, restriction, batch_size):
    subjects = sorted(subjects)
    batches = [subjects[i:i + batch_size] for i in range(0, len(subjects), batch_size)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        return [
            row for batch in pool.map(partial(triples, restriction=restriction), batches)
            for row in batch
        ]


def time_properties():
    header, *rows = query(f"""
PREFIX wikibase: <{WB}>
SELECT ?property WHERE {{
  ?property wikibase:propertyType wikibase:Time .
}}
""")
    if header != ["property"]:
        raise ValueError(f"Unexpected time property response header {header}")
    return {local_id(uri) for uri, in rows}


def collect_dates(edges):
    time_pids = time_properties()
    subjects = {ENTITY + s for s, _, _ in edges}
    claim_properties = {PROP + pid for pid in time_pids | set(PROPERTIES)}
    claims = batch_triples(subjects, f'FILTER(STRSTARTS(STR(?object), "{STATEMENT}"))', 1400)
    statements = {
        statement: (local_id(s), local_id(p))
        for s, p, statement in claims if p in claim_properties
    }
    print(f"Found {len(statements)} candidate statements", flush=True)

    details = defaultdict(lambda: defaultdict(list))
    for statement, predicate, obj in batch_triples(statements, "", 1600):
        details[statement][predicate].append(obj)

    pending = set()
    for statement, (subject, pid) in statements.items():
        detail = details[statement]
        rank = local_id(detail[WB + "rank"][0])
        suffix = (local_id(statement), rank)
        if pid in time_pids:
            for node in detail[PROP + "statement/value/" + pid]:
                pending.add((subject, pid, "", "", node, *suffix, ""))
        if pid in PROPERTIES:
            for obj in detail[PROP + "statement/" + pid]:
                if not obj.startswith(ENTITY + "Q"):
                    continue
                edge = (subject, pid, local_id(obj))
                if pid in LOCAL_ONLY and edge not in edges:
                    continue
                for predicate, nodes in detail.items():
                    if predicate.startswith(PROP + "qualifier/value/") and local_id(predicate) in time_pids:
                        for node in nodes:
                            pending.add((*edge, local_id(predicate), node, *suffix,
                                         "yes" if edge in edges else "no"))

    nodes = {row[4] for row in pending if row[4].startswith(VALUE)}
    time_data = defaultdict(dict)
    fields = ("timeValue", "timePrecision", "timeCalendarModel")
    predicates = ", ".join(f"<{WB}{field}>" for field in fields)
    for node, predicate, obj in batch_triples(nodes, f"FILTER(?predicate IN ({predicates}))", 1400):
        time_data[node][local_id(predicate)] = obj
    return {
        (subject, pid, obj, qualifier, time_data[node]["timeValue"],
         time_data[node]["timePrecision"], local_id(time_data[node]["timeCalendarModel"]),
         statement, rank, in_csv)
        for subject, pid, obj, qualifier, node, statement, rank, in_csv in pending
        if node in nodes
    }


def main():
    with (HERE / "wikidata-edges.csv").open(newline="") as source:
        edges = {
            (row["subject_qid"], row["pid"], row["object_qid"])
            for row in csv.DictReader(source)
        }
    dates = collect_dates(edges)
    with (HERE / "wikidata-dates.csv").open("w", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow([
            "subject_qid", "pid", "object_qid", "qualifier_pid", "date", "precision",
            "calendar_qid", "statement_id", "rank", "in_edge_csv",
        ])
        writer.writerows(sorted(dates))
    print(f"Wrote {len(dates)} date rows", flush=True)


if __name__ == "__main__":
    main()
