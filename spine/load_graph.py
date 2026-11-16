"""Load graph/*.tsv.gz into the spine Neo4j (bolt://127.0.0.1:7691). The database is a projection: this
script wipes it and rebuilds it from the tables, so nothing of value lives only in Neo4j.
Usage: load_graph.py          (credentials read from ../neo4j-local/auth-spine.env)
"""
import csv, gzip, json, sys, time
from pathlib import Path
from neo4j import GraphDatabase
csv.field_size_limit(sys.maxsize)
HERE = Path(__file__).parent
G = HERE / "graph"
URI = "bolt://127.0.0.1:7691"

def rows(name):
    path = HERE / name if name.endswith((".tsv.gz", ".tsv")) else G / f"{name}.tsv.gz"   # a full relative path, or a graph table
    with (gzip.open if str(path).endswith(".gz") else open)(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            yield {k: (v if v != "" else None) for k, v in r.items()}

def run(s, name, cypher, batch=5000, conv=None):
    buf, n, t0 = [], 0, time.time()
    for r in rows(name):
        if conv: conv(r)
        buf.append(r)
        if len(buf) >= batch:
            s.run(cypher, rows=buf).consume(); n += len(buf); buf = []
    if buf: s.run(cypher, rows=buf).consume(); n += len(buf)
    print(f"  {name:18} {n:>8,}  {time.time()-t0:5.1f}s", flush=True)

def ints(*keys):
    def f(r):
        for k in keys:
            if r.get(k) is not None:
                try: r[k] = int(float(r[k]))
                except ValueError: r[k] = None
    return f
def floats(*keys):
    def f(r):
        for k in keys:
            if r.get(k) is not None: r[k] = float(r[k])
    return f

CONSTRAINTS = [("Article", "id"), ("Name", "id"), ("Place", "id"), ("Taxon", "id"), ("Concept", "id"), ("BlueBookTable", "id"), ("BlueBookOfficer", "id"), ("Observation", "id"), ("Profile", "id"), ("WikidataPerson", "id"),
               ("ColPerson", "id"), ("Posting", "id"), ("Territory", "id")]

def main():
    auth = tuple((HERE.parent / "neo4j-local/auth-spine.env").read_text().strip().removeprefix("NEO4J_AUTH=").split("/", 1))
    with GraphDatabase.driver(URI, auth=auth) as db, db.session(database="neo4j") as s:
        while True:
            n = s.run("MATCH (n) WITH n LIMIT 50000 DETACH DELETE n RETURN count(*) AS c").single()["c"]
            if not n: break
        for label, prop in CONSTRAINTS:
            s.run(f"CREATE CONSTRAINT {label.lower()}_{prop} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE").consume()
        s.run("CREATE INDEX name_type_key IF NOT EXISTS FOR (n:Name) ON (n.type, n.key)").consume()
        s.run("CREATE INDEX article_year IF NOT EXISTS FOR (n:Article) ON (n.year)").consume()
        s.run("CREATE INDEX place_qid IF NOT EXISTS FOR (n:Place) ON (n.qid)").consume()
        s.run("DROP INDEX name_search IF EXISTS").consume()
        s.run("CREATE FULLTEXT INDEX name_search IF NOT EXISTS FOR (n:Name|Profile|Place|Taxon|Concept|BlueBookOfficer) ON EACH [n.label, n.name, n.key]").consume()
        s.run("CALL db.awaitIndexes(300)").consume()
        run(s, "articles", "UNWIND $rows AS r CREATE (a:Article) SET a = r", conv=ints("year", "words", "first_scan_page", "n_pages"))
        run(s, "territories", "UNWIND $rows AS r CREATE (t:Territory) SET t = r", conv=ints("start", "end"))
        run(s, "territory_edges", "UNWIND $rows AS r MATCH (a:Territory {id:r.from}), (b:Territory {id:r.to}) CREATE (a)-[:LINEAGE {type:r.type}]->(b)")
        run(s, "places", "UNWIND $rows AS r MERGE (p:Place {id:r.id}) SET p += r, p.name = r.label", conv=lambda r: (floats("lat", "lon")(r), ints("is_empire_territory")(r)))
        run(s, "col_places", "UNWIND $rows AS r MERGE (p:Place {id:r.id}) ON CREATE SET p.qid = r.qid, p.label = r.label, p.name = r.label SET p.col_label = r.label")
        s.run("MATCH (p:Place), (t:Territory) WHERE t.qid = p.qid MERGE (p)-[:IS_TERRITORY]->(t)").consume()
        run(s, "taxa", "UNWIND $rows AS r CREATE (t:Taxon) SET t = r")
        s.run("MATCH (t:Taxon) WHERE t.accepted_id IS NOT NULL MATCH (a:Taxon {id:t.accepted_id}) MERGE (t)-[:SYNONYM_OF]->(a)").consume()
        run(s, "concepts", "UNWIND $rows AS r CREATE (c:Concept) SET c = r, c.name = r.label")
        run(s, "concept_links", "UNWIND $rows AS r WITH r WHERE r.type = 'PRODUCT_OF' MATCH (a:Concept {id:r.from}), (b:Concept {id:r.to}) CREATE (a)-[:PRODUCT_OF]->(b)")
        run(s, "concept_links", "UNWIND $rows AS r WITH r WHERE r.type = 'SAME_TAXON' MATCH (a:Concept {id:r.from}), (b:Taxon {id:r.to}) CREATE (a)-[:SAME_TAXON]->(b)")
        run(s, "names", "UNWIND $rows AS r CREATE (n:Name) SET n = r, n.id = r.type + ':' + r.key", conv=ints("records", "articles"))
        run(s, "resolutions", """UNWIND $rows AS r MATCH (n:Name {id: r.type + ':' + r.key})
              SET n.resolution_status = r.status
              WITH n, r WHERE r.entity_id IS NOT NULL
              MATCH (e {id: r.entity_id}) WHERE e:Place OR e:Taxon OR e:Concept
              CREATE (n)-[:RESOLVES_TO {status:r.status, confidence:r.confidence, source:r.source, rule:r.rule}]->(e)""", batch=1000)
        run(s, "mentions", """UNWIND $rows AS r MATCH (a:Article {id:r.article}), (n:Name {id: r.type + ':' + r.key})
              CREATE (a)-[:MENTIONS {records:r.records, surfaces:r.surfaces, roles:r.roles, polity_at_date:r.polity_at_date}]->(n)""", batch=10000, conv=ints("records"))
        run(s, "profiles", "UNWIND $rows AS r CREATE (p:Profile) SET p = r", conv=ints("records", "articles", "first", "last", "mixed_profile"))
        run(s, "profile_mentions", """UNWIND $rows AS r MATCH (a:Article {id:r.article}), (p:Profile {id:r.profile})
              CREATE (a)-[:MENTIONS_PERSON {records:r.records, methods:r.methods, roles:r.roles}]->(p)""", batch=10000, conv=ints("records"))
        run(s, "wikidata_persons", "UNWIND $rows AS r CREATE (w:WikidataPerson) SET w = r")
        run(s, "col_persons", "UNWIND $rows AS r CREATE (c:ColPerson) SET c = r, c.name = coalesce(r.given_names + ' ', '') + coalesce(r.surname, '')", conv=ints("birth_year", "first_edition", "last_edition"))
        run(s, "identities", """UNWIND $rows AS r MATCH (p:Profile {id:r.profile}) MATCH (t {id:r.target}) WHERE t:WikidataPerson OR t:ColPerson
              CREATE (p)-[:IDENTIFIED_AS {authority:r.authority, source:r.source, confidence:r.confidence, review_status:r.review_status}]->(t)""")
        run(s, "postings", """UNWIND $rows AS r MATCH (c:ColPerson {id:r.person})
              CREATE (c)-[:HELD]->(po:Posting {id:r.id, position:r.position, position_norm:r.position_norm, start:r.start, end:r.end, acting:r.acting,
                     place_as_recorded:r.place_as_recorded, colony_label:r.colony_label, polity_by_lineage:r.polity_by_lineage})
              WITH po, r
              CALL (po, r) { WITH po, r WHERE r.place IS NOT NULL MATCH (pl:Place {id:r.place}) CREATE (po)-[:AT]->(pl) }
              CALL (po, r) { WITH po, r WHERE r.colony IS NOT NULL MATCH (co:Place {id:r.colony}) CREATE (po)-[:IN_COLONY]->(co) }
              CALL (po, r) { WITH po, r WHERE r.polity_at_date IS NOT NULL MATCH (t:Territory {id:r.polity_at_date}) CREATE (po)-[:IN_POLITY]->(t) }""",
            batch=2000, conv=ints("start", "end", "acting", "polity_by_lineage"))
        s.run("MATCH (c:ColPerson) WHERE c.wikidata_qid IS NOT NULL MERGE (w:WikidataPerson {id:'wd:' + c.wikidata_qid}) ON CREATE SET w.qid = c.wikidata_qid MERGE (c)-[:SAME_AS {source:'col_matching person_grounding.final'}]->(w)").consume()
        if (HERE / "bluebook/tables_index.tsv.gz").exists():       # Ceylon Blue Book tables and their labels
            run(s, "bluebook/tables_index.tsv.gz", "UNWIND $rows AS r CREATE (t:BlueBookTable) SET t = r", conv=ints("year", "pdf_page", "n_rows", "n_cols", "n_links"))
            if (HERE / "bluebook/table_confidence.tsv.gz").exists():   # evidence that the table was read correctly (bluebook/confidence.py)
                run(s, "bluebook/table_confidence.tsv.gz", """UNWIND $rows AS r MATCH (t:BlueBookTable {id:r.table_id})
                      SET t.confidence = r.level, t.totals_checked = r.totals_checked, t.totals_agree = r.totals_agree,
                          t.share_in_second_reading = toFloat(r.share_in_second_reading), t.confidence_flags = r.flags""",
                    conv=ints("totals_checked", "totals_agree"))
            run(s, "bluebook/table_name_links.tsv.gz", """UNWIND $rows AS r MATCH (t:BlueBookTable {id:r.table}), (n:Name {id: r.type + ':' + r.key})
                  CREATE (t)-[:HAS_LABEL {cells:r.cells, labels:r.labels, polity_at_date:r.polity_at_date}]->(n)""", batch=5000, conv=ints("cells"))
        ob = "bluebook/observations.tsv.gz"                       # printed figures extracted from Blue Book tables
        if (HERE / ob).exists():
            def conv(r):
                r["value"] = float(r["value"]) if r.get("value") not in (None, "") else None
                for k in ("year_volume", "year_data"): r[k] = int(r[k]) if r.get(k) else None
            run(s, ob, """UNWIND $rows AS r MATCH (t:BlueBookTable {id:r.table})
                  CREATE (o:Observation {id:r.id, kind:r.kind, year_volume:r.year_volume, year_data:r.year_data, area_as_printed:r.area_as_printed,
                          parent_as_printed:r.parent_as_printed, measure_as_printed:r.measure_as_printed, unit_as_printed:r.unit_as_printed,
                          value_as_printed:r.value_as_printed, value:r.value, note:r.note})-[:PRINTED_IN]->(t)
                  WITH o, r
                  CALL (o, r) { WITH o, r WHERE r.area_key IS NOT NULL MATCH (n:Name {id:'PLACE:' + r.area_key}) CREATE (o)-[:ABOUT_PLACE]->(n) }
                  CALL (o, r) { WITH o, r WHERE r.measure_key IS NOT NULL MATCH (n:Name {id:r.measure_type + ':' + r.measure_key}) CREATE (o)-[:MEASURES]->(n) }""", batch=5000, conv=conv)
        om = "bluebook/extracted/officer_matches.tsv"            # people named in the Civil Establishment, per volume
        if (HERE / om).exists():
            run(s, om, """UNWIND $rows AS r CREATE (o:BlueBookOfficer {id:r.bb_person, year:r.year_volume, surname:r.surname, initials:r.initials,
                  name:r.names_as_printed, offices:r.offices_as_printed, appointment_years:r.appointment_years})
                  WITH o, r UNWIND split(coalesce(r.tables, ''), ' ') AS tid MATCH (t:BlueBookTable {id:tid}) CREATE (o)-[:LISTED_IN]->(t)""", batch=2000, conv=ints("year_volume"))
            run(s, om, """UNWIND $rows AS r WITH r WHERE r.col_status = 'matched' MATCH (o:BlueBookOfficer {id:r.bb_person}), (c:ColPerson {id:r.col_person})
                  CREATE (o)-[:IDENTIFIED_AS {authority:'colonial_office_list', source:'bluebook/match_officers.py', confidence:r.col_confidence, review_status:'unreviewed'}]->(c)""")
            run(s, om, """UNWIND $rows AS r WITH r WHERE r.journal_profile_candidate IS NOT NULL MATCH (o:BlueBookOfficer {id:r.bb_person}), (p:Profile {id:r.journal_profile_candidate})
                  CREATE (o)-[:CANDIDATE_FOR {source:'bluebook/match_officers.py', basis:'same surname and initials, active within 20 years'}]->(p)""")
        print("nodes:", {r["l"]: r["n"] for r in s.run("MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS n ORDER BY n DESC")})
        print("rels:", {r["t"]: r["n"] for r in s.run("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS n ORDER BY n DESC")})

if __name__ == "__main__":
    main()
