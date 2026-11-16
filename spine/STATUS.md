# Status, 16 November 2026 (afternoon, updated after the Blue Books arrived)

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
| Places with a QID | 1,645 |
| Taxon name records (Catalogue of Life) | 3,611, of which 932 are synonyms linked to an accepted name |
| Wikidata concepts (taxa, products, diseases, organisations) | 859 |
| Blue Book tables and officials (person-years) | 7,354 and 14,491 |
| Person profiles | 38,579; 680 linked to Wikidata and/or a Colonial Office List person |
| Colonial Office List officials and postings | 1,212 and 12,492 |
| Empire Evolution territories | 739 |

## Coverage of the journal's records

| Type | Matched | In review | Unmatched or skipped | Not attempted |
|---|---:|---:|---:|---:|
| Places (374,553 records) | 71.6% | 9.9% | 0.4% | 18.1% |
| Taxa (164,859 records) | 52.2% | 3.7% | 18.6% | 25.5% |
| Commodities (134,358 records) | 64.2% | 1.3% | 19.6% | 15.0% |
| Organisations (88,690 records) | 5.9% | 0.4% | 37.0% | 56.8% |

"Not attempted" is the long tail: names in fewer than 15 articles (taxa matched by the Catalogue of Life go
down to 3). The taxon, commodity and organisation figures will rise a little: Wikidata throttled the read-back
of candidates, and about 12,000 lower-ranked candidates were still to be read when this was written
(`cache/fetch_names.log`). Rerun `ground_names_wd.py`, `join_wd_taxa_col.py`, `build_graph_tables.py`,
`load_graph.py` when it finishes.

**Common names now reach the same taxon as scientific names.** A Wikidata item matched to a printed name is a
`Concept` node. A taxon item is tied to its Catalogue of Life record by its scientific name (`SAME_TAXON`), and
a product is tied to the taxon it comes from (`PRODUCT_OF`, Wikidata's "natural product of taxon"). So
*Cocos nucifera* is reached from "Cocos nucifera", "coconut", "coconut palm", and, as products, "copra",
"coconut oil", "coir" and "coconuts".

**Organisations are mostly not in Wikidata.** Names such as "Department of Agriculture" or "Planters'
Association" mean a different body in each article and are skipped on purpose (9.7% of records). Bodies
specific to Ceylon mostly have no Wikidata item. The 56 matched names are well-known bodies (Kew, Peradeniya,
Colonial Office, Indian Tea Association). Local identifiers for the Ceylon bodies are a decision for you.

## Ceylon Blue Books (arrived this afternoon)

Thirteen volumes are in (`bluebook/README.md` has the detail):

- **7,354 printed tables** kept as printed, each with its page and headings (`bluebook/tables/`).
- **32,644 links from table labels to names the spine had already resolved**: 3,493 tables name a known place,
  commodity or taxon. Trade partners get the polity for the volume's year.
- **People**: the 1869, 1889, 1902 and 1904 volumes list the whole Civil Establishment: 12,599 index entries
  and 7,295 named posts with dates of appointment. 599 person-years match a Colonial Office List person
  (95 with a matching appointment year). **97 people are now in all three sources** (Blue Book, Colonial
  Office List, journal): Trimen appears in 1889 as Director at Peradeniya, Willis and Carruthers in 1902 and
  1904. About 13,900 person-years (clerks, teachers, headmen) are in no other source.
- **Figures**: two Codex Sol jobs, run from written briefs (`bluebook/jobs/*.md`), produced 4,918 agricultural
  figures (acreage by crop and province, district returns, live stock; seven volumes) and 88,045 trade figures
  (imports and exports by article and country; 1924, 1925, 1926, 1928). I checked samples against the parsed
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
