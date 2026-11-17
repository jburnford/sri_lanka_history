# Ceylon entity spine

Started 16 November 2026 after a review of the first Ceylon graph (`../kg`, Neo4j `neo4j-ceylon`). That graph
is left untouched. This folder rebuilds the entity layer so that it stands on three existing projects:

- the Colonial Office List graph (`../col_matching`) for places, officials and careers;
- the Empire Evolution graph (`../empire-evolution`) for dated polities and their successions;
- Wikidata, and the Catalogue of Life for taxa, for shared identifiers.

## Principles

1. **Files are the source of truth.** Every decision is a row in `grounding/*.jsonl`. Neo4j is a projection
   that `load_graph.py` wipes and rebuilds in about a minute.
2. **Keep what was printed, what was decided, and the entity apart.** A `Name` is what the journal printed.
   A `RESOLVES_TO` link is a decision with a status, a confidence, a source and a rule. The entity is a third
   thing. None overwrites another, and a decision can be reversed without touching the mentions.
3. **Hold both readings where there are two.** A name used for a town and its district keeps both senses.
   A place keeps its lasting geographic item and, separately, the polity that held it in the year in question,
   found by following Empire Evolution successions (`empire.py`).
4. **No identifier from memory.** QIDs come from the Colonial Office List files, from WikidataMCP vector search,
   or from a reviewer, and are read back by identifier before use. Taxon records come from a pinned Catalogue
   of Life release.
5. **Errors in upstream projects are logged, then fixed at the source.** See `UPSTREAM_ERRORS.md`.

## Pipeline

| Step | Script | Output |
|---|---|---|
| Name frequency per entity type | `build_names.py` | `names/<TYPE>.tsv` |
| Places, tier 1: Colonial Office List gazetteer | `ground_places_col.py` | `grounding/places_tier1.jsonl` |
| Places, review pass (two senses, place + polity) | `resolve_place_reviews.py` | `grounding/places_tier1b.jsonl` |
| Places, tier 2: Wikidata vector search, verified | `search_places_wd.py`, `ground_places_wd.py` | `grounding/places_tier2.jsonl` |
| Taxa: Catalogue of Life name matching | `ground_taxa_col.py` | `grounding/taxa_col.jsonl` |
| Common-name taxa, commodities, organisations: Wikidata search, verified | `search_names_wd.py`, `ground_names_wd.py` | `grounding/{taxon,commodity,org}_wd.jsonl` |
| Wikidata taxon items joined to the Catalogue of Life | `join_wd_taxa_col.py` | `grounding/wd_taxon_col.jsonl` |
| 1834 Ceylon Gazetteer entries and matches | `parse_casie_chitty.py`, `match_casie_chitty.py` | `gazetteer/casie_chitty_1834.jsonl`, `analysis/casie_chitty_matches.tsv` |
| People: existing journal links + careers | `people_careers.py` | `grounding/people.jsonl` |
| People: research assistant's review overlay | `apply_people_review.py` | `grounding/people_review.jsonl` |
| Cross-check of the two base graphs | `check_col_vs_empire.py` | `grounding/col_polity_check.tsv` |
| Load tables | `build_graph_tables.py` | `graph/*.tsv.gz` |
| Neo4j projection | `load_graph.py` | database on `bolt://127.0.0.1:7691` |
| Demo queries | `queries.cypher`, `run_queries.py` | — |

Gazetteers read back from Wikidata by identifier are in `gazetteer/`; caches of searches and matches are in
`cache/`. Corrections made by a person live in `grounding/people_corrections.jsonl`.

## Graph model

```
(Article)-[:MENTIONS {records, surfaces, roles, polity_at_date}]->(Name {type, key, label})
(Name)-[:RESOLVES_TO {status, confidence, source, rule}]->(Place | Taxon | Concept)
(Concept)-[:SAME_TAXON]->(Taxon)                     Wikidata taxon item = Catalogue of Life record, by scientific name
(Concept)-[:PRODUCT_OF]->(Concept)                   product -> the taxon it comes from (Wikidata P1582)
(Taxon)-[:SYNONYM_OF]->(Taxon)                       Catalogue of Life: name as printed -> accepted name
(Article)-[:MENTIONS_PERSON {records, methods, roles}]->(Profile)
(Profile)-[:IDENTIFIED_AS {authority, source, review_status}]->(WikidataPerson | ColPerson)
(ColPerson)-[:HELD]->(Posting)-[:AT]->(Place)
(Posting)-[:IN_COLONY]->(Place)                      the colony as the Colonial Office List grounded it
(Posting)-[:IN_POLITY]->(Territory)                  the polity for the posting's years
(Place)-[:IS_TERRITORY]->(Territory)-[:LINEAGE {type}]->(Territory)
```

A `Profile` is a proposed grouping of journal mentions, not a verified person. `mixed_profile = 1` marks
profiles a reviewer found to contain more than one person; do not apply a profile-level identity to every
mention of such a profile.

## Running it

```bash
cd /home/jic823/Documents/ceylon/spine
/home/jic823/miniforge3/bin/python build_graph_tables.py
/home/jic823/miniforge3/bin/python load_graph.py
/home/jic823/miniforge3/bin/python run_queries.py 1 3
```

The Neo4j container is `neo4j-ceylon-spine` (Browser at http://localhost:7478, Bolt 7691). Its login is in
`../neo4j-local/auth-spine.env`.

## Known limits

- Decisions are per name, not per mention. "Victoria" or "Kingston" gets one reading or goes to review.
- Mention counts are one record per entity per roughly 2,500-word chunk, not every printed occurrence.
- People links come from the journal's person pipeline and are model- or rule-decided unless the row says a
  reviewer confirmed them. The gold sample has 22 of 100 profiles answered.
- Publications, estates and most organisations are loaded as names only. Generic organisation names are
  skipped on purpose; a match a person rejects goes in `grounding/name_rejections.jsonl`.
- The research assistant's review files (`gold/`, `grounding/people_review.jsonl`) are not in the repository; see
  `../SOURCES.md`. The load tables (`graph/`, rebuilt by `build_graph_tables.py`) are included as a snapshot of
  17 Nov 2026, so `load_graph.py` can fill a Neo4j database on a machine that has only this repository.
