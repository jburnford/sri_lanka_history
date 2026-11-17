// Spine graph demo queries. Run each in Neo4j Browser (http://localhost:7478) or with run_queries.py.

// 1. One person across three projects: journal profile, Wikidata, Colonial Office List career.
MATCH (p:Profile {name:'Henry Trimen'})
OPTIONAL MATCH (p)-[i:IDENTIFIED_AS]->(w:WikidataPerson)
OPTIONAL MATCH (p)-[:IDENTIFIED_AS]->(c:ColPerson)-[:HELD]->(po:Posting)
OPTIONAL MATCH (po)-[:IN_POLITY]->(t:Territory)
RETURN p.name AS person, p.records AS journalRecords, p.review_status AS review, w.qid AS wikidata,
       c.person_id AS coListId, po.start AS year, po.position AS position, po.place_as_recorded AS place, t.name AS polity
ORDER BY year;

// 2. What the journal connects him to: the taxa named in the articles that mention him.
MATCH (p:Profile {name:'Henry Trimen'})<-[:MENTIONS_PERSON]-(a:Article)-[:MENTIONS]->(n:Name {type:'TAXON'})-[:RESOLVES_TO]->(t:Taxon)
OPTIONAL MATCH (t)-[:SYNONYM_OF]->(acc:Taxon)
RETURN t.name AS nameAsPrinted, t.authorship AS authorship, t.status AS status, acc.name AS acceptedName,
       count(DISTINCT a) AS articles, min(a.year) AS first, max(a.year) AS last
ORDER BY articles DESC LIMIT 15;

// 3. Knowledge carried by careers: people who appear in rubber articles and served in Malaya, with dates.
MATCH (a:Article)-[:MENTIONS]->(:Name {type:'COMMODITY', key:'rubber'})
MATCH (a)-[:MENTIONS_PERSON]->(p:Profile)-[:IDENTIFIED_AS]->(c:ColPerson)-[:HELD]->(po:Posting)-[:IN_POLITY]->(t:Territory)
WHERE t.name IN ['Federated Malay States', 'Straits Settlements'] OR t.name STARTS WITH 'Malay'
WITH p, c, t, min(po.start) AS firstMalaya, count(DISTINCT a) AS rubberArticles, min(a.year) AS firstArticle, max(a.year) AS lastArticle
RETURN p.name AS person, c.name AS coListName, t.name AS polity, firstMalaya, rubberArticles, firstArticle, lastArticle
ORDER BY rubberArticles DESC LIMIT 20;

// 4. Where a crop was discussed from: places named in cinchona articles, by decade, with the polity then.
MATCH (a:Article)-[:MENTIONS]->(:Name {type:'TAXON', key:'cinchona'})
MATCH (a)-[m:MENTIONS]->(n:Name {type:'PLACE'})-[:RESOLVES_TO]->(pl:Place)
WHERE NOT pl.qid IN ['Q918153', 'Q854']
OPTIONAL MATCH (t:Territory {id:m.polity_at_date})
RETURN (a.year / 10) * 10 AS decade, pl.label AS place, t.name AS polityAtDate, count(DISTINCT a) AS articles
ORDER BY decade, articles DESC;

// 5. Postings whose polity was found by following Empire Evolution successions, not by the recorded QID.
MATCH (c:ColPerson)-[:HELD]->(po:Posting {polity_by_lineage:1})-[:IN_POLITY]->(t:Territory)
RETURN po.colony_label AS colonyAsRecorded, t.name AS polityAtDate, count(*) AS postings, min(po.start) AS from, max(po.start) AS to
ORDER BY postings DESC LIMIT 15;

// 6. Review queue: the most frequent place names still without a decision.
MATCH (n:Name {type:'PLACE'}) WHERE NOT (n)-[:RESOLVES_TO]->()
RETURN n.label AS name, n.records AS records, n.articles AS articles, n.resolution_status AS status
ORDER BY n.articles DESC LIMIT 25;

// 7. One plant, every name: printed names that reach Cocos nucifera directly, through a common name, or as a product.
MATCH (t:Taxon {name:'Cocos nucifera'})
CALL (t) {
  MATCH (n:Name)-[:RESOLVES_TO]->(t) RETURN n, 'scientific name' AS how
  UNION MATCH (n:Name)-[:RESOLVES_TO]->(:Concept)-[:SAME_TAXON]->(t) RETURN n, 'common name' AS how
  UNION MATCH (n:Name)-[:RESOLVES_TO]->(:Concept)-[:PRODUCT_OF]->(:Concept)-[:SAME_TAXON]->(t) RETURN n, 'product' AS how
}
RETURN how, n.type AS type, n.label AS printedName, n.articles AS articles ORDER BY how, articles DESC;

// 8. People in all three sources: Blue Book establishment, Colonial Office List career, journal.
MATCH (o:BlueBookOfficer)-[:IDENTIFIED_AS]->(c:ColPerson)<-[:IDENTIFIED_AS]-(p:Profile)
WITH c, p, o ORDER BY o.year
RETURN c.surname AS surname, c.given_names AS given, collect(DISTINCT o.year) AS blueBookYears, head(collect(o.offices)) AS officeInBlueBook, p.name AS journalProfile, p.articles AS journalArticles
ORDER BY journalArticles DESC LIMIT 20;

// 9. A commodity in both sources by year: Blue Book tables that label it, and journal articles that mention it.
MATCH (n:Name {type:'COMMODITY', key:'cinnamon'})
MATCH (t:BlueBookTable)-[:HAS_LABEL]->(n)
WITH n, t.year AS year, count(DISTINCT t) AS blueBookTables
OPTIONAL MATCH (a:Article {year: year})-[:MENTIONS]->(n)
RETURN year, blueBookTables, count(DISTINCT a) AS journalArticles ORDER BY year;

// 10. Trade partners as the polity they were in the volume's year (Empire Evolution), counted by tables.
MATCH (t:BlueBookTable)-[h:HAS_LABEL]->(n:Name {type:'PLACE'}) WHERE h.polity_at_date IS NOT NULL
MATCH (x:Territory {id:h.polity_at_date})
WHERE t.section IN ['Imports', 'Exports', 'Domestic Exports']
RETURN x.name AS polity, min(t.year) AS firstVolume, max(t.year) AS lastVolume, count(DISTINCT t) AS tables
ORDER BY tables DESC LIMIT 20;

// 11. A traded article by destination and year, from the Blue Book ledgers: citronella oil exports (Ceylon produce, lb.).
//     Only links marked exact are used: a heading such as "China, exc. Hong Kong" is linked to China as excludes_part and
//     is shown under its printed label instead. year_data is the year the period ends; period_as_printed has the period.
MATCH (o:Observation)-[m:MEASURES]->(:Name {key:'citronella oil'})
WHERE o.kind = 'trade:export:quantity_ceylon_produce' AND o.value IS NOT NULL AND m.relation = 'exact'
OPTIONAL MATCH (o)-[a:ABOUT_PLACE]->(n:Name)-[:RESOLVES_TO]->(p:Place) WHERE a.relation = 'exact'
WITH coalesce(p.label, o.area_as_printed) AS destination, o.year_data AS year, sum(o.value) AS lb
RETURN destination, collect(toString(year) + ': ' + toString(toInteger(lb))) AS byYear, sum(lb) AS total ORDER BY total DESC LIMIT 12;

// 12. Acreage under a crop by province across volumes (Blue Book "Agricultural Statistics").
//     A year's return is often printed again in the next volume. Each (crop, year, province) is counted once, from the
//     earliest volume that prints it; printings lists the volumes, and differing lists the figures when they disagree.
MATCH (o:Observation {kind:'agriculture:acreage_by_crop'})-[:MEASURES]->(m:Name) WHERE m.key IN ['tea', 'coffee', 'cinchona', 'rubber', 'cacao']
  AND o.value IS NOT NULL AND o.year_data IS NOT NULL AND NOT toLower(o.area_as_printed) CONTAINS 'total'
WITH m.key AS crop, o.year_data AS year, toLower(trim(o.area_as_printed)) AS province, o ORDER BY o.year_volume
WITH crop, year, province, collect(o) AS os
WITH crop, year, province, head(os).value AS acres, size(os) AS printings,
     [x IN os WHERE x.value <> head(os).value | province + ' ' + toString(x.year_volume) + ': ' + toString(toInteger(x.value))] AS diff
RETURN crop, year, toInteger(sum(acres)) AS acresSummedOverProvinces, count(*) AS provinces, max(printings) AS timesPrinted,
       reduce(l = [], d IN collect(diff) | l + d) AS differingLaterPrintings ORDER BY crop, year;
