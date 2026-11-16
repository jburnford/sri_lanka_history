# Status, 16 November 2026 (evening, all Blue Book volumes in)

Written for a check-in after working alone. Detail is in `README.md` (how it works) and `UPSTREAM_ERRORS.md`
(what is wrong upstream).

## What exists now

A rebuilt graph in a separate Neo4j database (`neo4j-ceylon-spine`, Browser http://localhost:7478, Bolt 7691),
loaded from decision files in under a minute. The old database and Codex's GIS folders are untouched.

| In the graph | Count |
|---|---:|
| Articles (canonical copies) | 53,501 |
| Printed names, all types | 169,425 |
| Article-to-name links | 845,450 |
| Places with a QID | 2,407 |
| Taxon name records (Catalogue of Life) | 3,611, of which 932 are synonyms linked to an accepted name |
| Wikidata concepts (taxa, products, diseases, organisations) | 859 |
| Blue Book tables and officials (person-years) | 46,999 and 146,383 |
| Person profiles | 38,579; 680 linked to Wikidata and/or a Colonial Office List person |
| Colonial Office List officials and postings | 1,212 and 12,492 |
| Empire Evolution territories | 739 |

## Coverage of the journal's records

| Type | Matched | In review | Unmatched or skipped | Not attempted |
|---|---:|---:|---:|---:|
| Places (374,553 records) | 73.4% | 13.3% | 0.5% | 12.7% |
| Taxa (164,859 records) | 52.0% | 3.7% | 18.7% | 25.5% |
| Commodities (134,358 records) | 66.8% | 1.5% | 16.7% | 15.0% |
| Organisations (88,690 records) | 6.0% | 0.4% | 36.8% | 56.8% |

"Not attempted" is the long tail: place names in fewer than 5 articles, other names in fewer than 15 (taxa matched by the Catalogue of Life go
down to 3). All Wikidata candidates have now been read back. A second search adds the journal's own description
to the query ("mace spice", "Liberian coffee variety"), which found items filed under a modern name: sugar,
mace, Liberian coffee, black tea. Still unmatched and frequent: cocoa, pepper (several senses), plumbago
(graphite), Indian tea, Ceylon tea, chillies, dadap, lucerne. These need either a person's decision or the
local Wikidata dump, where an old name can be looked up directly among aliases.

**Common names now reach the same taxon as scientific names.** A Wikidata item matched to a printed name is a
`Concept` node. A taxon item is tied to its Catalogue of Life record by its scientific name (`SAME_TAXON`), and
a product is tied to the taxon it comes from (`PRODUCT_OF`, Wikidata's "natural product of taxon"). So
*Cocos nucifera* is reached from "Cocos nucifera", "coconut", "coconut palm", and, as products, "copra",
"coconut oil", "coir" and "coconuts".

**Organisations are mostly not in Wikidata.** Names such as "Department of Agriculture" or "Planters'
Association" mean a different body in each article and are skipped on purpose (9.7% of records). Bodies
specific to Ceylon mostly have no Wikidata item. The 56 matched names are well-known bodies (Kew, Peradeniya,
Colonial Office, Indian Tea Association). Local identifiers for the Ceylon bodies are a decision for you.

## Ceylon Blue Books

62 volumes are in, 1863 to 1938 (`bluebook/README.md` has the detail):

- **46,999 printed tables** kept as printed, each with its page and headings (`bluebook/tables/`).
- **Confidence level on every table** (`bluebook/table_confidence.tsv.gz`): 3,774 have every checkable printed
  total agreeing with its parts; 15,216 have at least 90% of their numbers confirmed by a second OCR reading
  (the scan's Tesseract text); 5,976 are partly confirmed; 21,904 have nothing to confirm them; 129 are
  flagged as invented. The OCR model writes plausible tables on blank pages (a 1905 blank verso became
  "quarterly statements, Q1-Q4"). On printed pages its misread rate for numbers is about 2% in the 1925-1938
  volumes, by comparison with the second reading.
- **300,107 links from table labels to names the spine had already resolved**: 21,492 tables name a known
  place, commodity or taxon. Trade partners get the polity for the volume's year.
- **People**: 146,383 person-years of officials across all volumes. 5,121 match a Colonial Office List person
  (1,083 with a matching appointment year) and 11,496 have a journal profile as a candidate. The extractor was
  written on four volumes and has not been checked on the others.
- **Figures**: two Codex Sol jobs, run from written briefs (`bluebook/jobs/*.md`), produced 4,918 agricultural
  figures (acreage by crop and province, district returns, live stock; seven volumes) and 88,045 trade figures
  (imports and exports by article and country; 1924, 1925, 1926, 1928). These two jobs covered the first
  thirteen volumes only and have not been rerun on the rest. I checked samples against the parsed
  tables and loaded them: 77,741 `Observation` nodes, 92% tied to a place name and 31% to a crop or article name.
  Printed totals agree with the sum of parts for 92% of acreage checks and 78–85% of trade articles; the rest
  are listed, not repaired. Example from the graph: coffee falls from 207,066 acres in 1868 to 1,389 in 1912
  while rubber rises from 4,100 in 1902 to 184,551 in 1911 (sums over the provinces that report).
  The `codex` on the PATH (0.166.0) cannot run commands because its helper binary is missing; I used the
  complete install at `~/.codex/plugins/.plugin-appserver/codex`.

## The 1834 Ceylon Gazetteer (Casie Chitty)

Parsed from the Internet Archive text you sent into 386 entries (`gazetteer/casie_chitty_1834.jsonl`): headword,
bracketed alternative spellings, kind of place, "N miles <direction> of <place>" statements (122 entries), and
the entry text. `analysis/casie_chitty_matches.tsv` lines the headwords up with the journal and with Wikidata's
Sri Lanka items: 82 headwords occur in the journal as printed and 93 more under a nearby spelling; 28 match a
Wikidata item exactly and 57 by a spelling-tolerant comparison (Bentotte / Bentota). Those are candidates, not
decisions. Known gaps: the entries for Ceylon, Kandy, Trincomalee and a few other long articles open in a way
the parser does not recognise, so their text is attached to the entry before them (flagged with a note).
Worth redoing on the fresh OCR.

## What to trust, and how far

- **Place matches from the Colonial Office List gazetteer** (49% of records): QIDs come from that project.
  2,378 of its 3,207 rows are still marked unverified there.
- **Place matches from Wikidata search** (about 14% of records): rule-checked, not human-checked. My first
  version matched Travancore to a Melbourne suburb and Acheen to a shipwreck; the checks were tightened and a
  random sample of 45 then looked right in 43 cases, by my reading. Treat the medium-confidence ones as needing
  a look.
- **Taxa**: scientific names matched against Catalogue of Life release COL26.11. A guard sends a match to
  review when the journal's usage points to another kingdom (anthrax the disease, not Anthrax the fly;
  castor the plant, not Castor the beaver). 105 names were caught that way.
- **Commodities and common-name taxa** (Wikidata search): a candidate must carry the printed name as its
  label, an alias or a recorded common name, and its description must read as a plant, animal, product,
  material or disease. Early versions matched "cocoa" to a software framework and "potatoes" to a short story;
  those are now refused. A match on an item's own name outranks a match on an alias; I read all 320 alias-only
  matches and rejected ten ("pepper" to bell pepper, "coke" to Coca-Cola, "lac" to the lac operon). Alias
  matches are marked medium confidence.
- **Organisations**: I read the first 57 matches; one was wrong (an East Timor ministry) and is
  recorded in `grounding/name_rejections.jsonl`, which the matcher obeys.
- **People**: links are from the journal's own person pipeline. The research assistant's review covers 22 profiles: all 13
  asserted QIDs she checked were right; she found 3 the pipeline missed and 3 mixed profiles.

## Changes made outside this folder

- `col_matching`, branch `ceylon-data`, commit `0b7f01c`, pushed: three reviewed person links (Hart, Small,
  Fawcett). `master` is unchanged.
- `col_matching/data/kg/person_grounding_merge_dropped.jsonl` (git-ignored log) was overwritten when I ran the
  merge script once; I could not restore it.
- `/mnt/data/jic823/wikidata/20261109/`: Wikidata dump downloading; checksum and slim extract queued.
- `empire-evolution`: cloned, not edited.

## Queries worth running (`queries.cypher`)

1. Trimen across three projects: journal profile, Wikidata item, Colonial Office List career.
2. The taxa in articles that mention him, with authorship and accepted names.
3. People in rubber articles who held posts in Malaya, with the year of their first posting there.
4. Places named in cinchona articles by decade, with the polity at that date.
5. Postings whose polity was found by following Empire Evolution successions.
6. The review queue: frequent place names without a decision.

## Open decisions for you

- Whether to merge `ceylon-data` into `master` in `col_matching`.
- `spine/` is now in a local clone of `jburnford/sri_lanka_history` rooted at the project folder; pushing waits for your word.
- Which upstream fixes in `UPSTREAM_ERRORS.md` to apply first. I have applied none beyond the three person links.
