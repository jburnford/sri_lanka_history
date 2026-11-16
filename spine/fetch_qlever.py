"""Read labels, aliases, description, types, country, coordinates and sitelink count for known QIDs from the
QLever Wikidata index, into the same JSONL shape as fetch_wikidata_entities.py. Lookup by identifier only.
Usage: fetch_qlever.py OUT.jsonl < qids.txt     (resumable)
"""
import json, re, sys, time, urllib.parse, urllib.request
API = "https://qlever.dev/api/wikidata"
UA = "historical-gazetteer-builder/0.1 (research script)"
Q = """PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX schema: <http://schema.org/> PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT ?q ?p ?v WHERE { VALUES ?q { %s } {
  { ?q rdfs:label ?v . FILTER(LANG(?v) IN ("en","si","ta")) BIND(CONCAT("label@", LANG(?v)) AS ?p) }
  UNION { ?q skos:altLabel ?v . FILTER(LANG(?v) = "en") BIND("alias" AS ?p) }
  UNION { ?q schema:description ?v . FILTER(LANG(?v) = "en") BIND("desc" AS ?p) }
  UNION { ?q wdt:P31 ?v . BIND("instance_of" AS ?p) } UNION { ?q wdt:P17 ?v . BIND("country" AS ?p) }
  UNION { ?q wdt:P131 ?v . BIND("admin_parent" AS ?p) } UNION { ?q wdt:P625 ?v . BIND("coord" AS ?p) }
  UNION { ?q wdt:P225 ?v . BIND("taxon_name" AS ?p) } UNION { ?q wdt:P105 ?v . BIND("taxon_rank" AS ?p) }
  UNION { ?q wdt:P1566 ?v . BIND("geonames" AS ?p) }
  UNION { ?q wikibase:sitelinks ?v . BIND("sitelinks" AS ?p) } } }"""

def run(batch):
    body = urllib.parse.urlencode({"query": Q % " ".join("wd:" + q for q in batch)}).encode()
    for k in range(6):
        try:
            req = urllib.request.Request(API, data=body, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())["results"]["bindings"]
        except Exception as ex:
            print("retry", k, repr(ex)[:150], file=sys.stderr); time.sleep(4 * 2 ** k)
    raise SystemExit("gave up; rerun to resume")

def main():
    out = sys.argv[1]
    want = [l.strip() for l in sys.stdin if re.fullmatch(r"Q\d+", l.strip())]
    have = set()
    try:
        for l in open(out): have.add(json.loads(l)["requested"])
    except FileNotFoundError: pass
    todo = [q for q in dict.fromkeys(want) if q not in have]
    print(f"want {len(want)} have {len(have)} todo {len(todo)}", file=sys.stderr)
    with open(out, "a") as fh:
        for i in range(0, len(todo), 200):
            batch = todo[i:i + 200]
            recs = {q: {"qid": q, "labels": {}, "aliases": {}, "description": None, "sitelinks": 0} for q in batch}
            for b in run(batch):
                q = b["q"]["value"].rsplit("/", 1)[-1]; p = b["p"]["value"]; v = b["v"]["value"]
                r = recs.get(q)
                if r is None: continue
                if p.startswith("label@"): r["labels"][p[6:]] = v
                elif p == "alias": r["aliases"].setdefault("en", []).append(v)
                elif p == "desc": r["description"] = v
                elif p == "sitelinks": r["sitelinks"] = int(v)
                elif p == "coord":
                    m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", v, re.I)
                    if m and "lat" not in r: r["lon"], r["lat"] = round(float(m.group(1)), 5), round(float(m.group(2)), 5)
                elif p in ("taxon_name", "geonames"): r.setdefault(p, []).append(v)
                else: r.setdefault(p, []).append(v.rsplit("/", 1)[-1])
            for q in batch:
                r = recs[q]
                if not r["labels"] and not r["description"] and len(r) == 5: r["missing"] = True
                r["requested"] = q; r["via"] = "qlever"
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush(); time.sleep(0.5)
            print(f"{i + len(batch)}/{len(todo)}", file=sys.stderr)

if __name__ == "__main__":
    main()
