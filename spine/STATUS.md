# Status, 16 November 2026 (evening, all Blue Book volumes in)

Written for a check-in after working alone. Detail is in `README.md` (how it works) and `UPSTREAM_ERRORS.md`
(what is wrong upstream).

## Review fixes (branch `review-fixes`, 16 November 2026, late)

An independent review checked this work against the code and data. Changes made on this branch:

- **Officer index, 1907–1917.** From 1907 the index is printed as "Name and Office | Page", in one or two
  columns. The extractor read the page number as the office, dropped the second printed column, and skipped
  single-column pages. `bluebook/extract_officers.py` now reads every layout; `officers_index.tsv` grows from
  102,808 to 135,406 rows (pre-1907 rows unchanged, with a new `column` field).
- **Officer matching.** "high" now needs the appointment year to equal the start of a *Ceylon* posting and at
  least two initials (`bluebook/match_officers.py`). **Not rerun here**: needs `graph/`.
- **Table confidence.** Unlabelled running subtotals were only kept when they agreed, so they could never fail;
  they no longer count towards a level. "summed" needs a non-trivial total (not zeros, not one part), and
  "two_readings" needs at least 10 distinct numbers. No table moved up a level. See the Blue Books section.
- **Places.** `common.in_sri_lanka()` replaces "is in `sri_lanka_wikidata.jsonl`", which also held ~213 items
  outside Sri Lanka (that is how `ireland` became the Republic of Ireland). A match is refused when the
  journal places the name in Ceylon and the candidate is elsewhere. Three proper names of British Indian
  provinces are no longer skipped as generic. Rerun on 16 November (late) with `col_matching` and
  `empire-evolution` cloned beside the repository; the pre-review code reproduced the committed files exactly
  first. Changed decisions: the 15 rejected places go to review, Ireland is the island (Q22890), and "north west
  provinces" is the North-Western Provinces (Q138521).
- **Rejections.** 27 wrong matches with evidence in the journal's own role text were added to
  `grounding/name_rejections.jsonl` (madura → Madura Island, summerville → Georgia, united provinces → Dutch
  Republic, board of revenue → a Chinese ministry, cacao → a drink, lime → Tilia, citronella → a tree genus,
  ...). `ground_taxa_col.py` now honours rejections too. Taxa, commodities and organisations were rerun here.

- **Polities.** `empire.polity_at` follows succession in one direction of time and no longer jumps sideways
  or borrows a container from the wrong period (details in `UPSTREAM_ERRORS.md`). On the Colonial Office List
  career events, about 220 wrong answers were withdrawn or corrected (Newfoundland -> Canada, Penang after 1946
  -> Singapore, Nyasaland -> Southern Rhodesia, Tanganyika -> Zanzibar), and about 70 probably-right ones are now
  unresolved (mostly Lagos, blocked by a false upstream edge). `grounding/col_polity_check.tsv` is rerun.
- **Paths.** Scripts read `CEYLON_PROJECT` (where `col_matching` and `empire-evolution` are; default: the
  repository root) and `CEYLON_DATA` (default `/mnt/data/jic823`) instead of hard-coded workstation paths.

To finish on the workstation, where the Tropical Agriculturist corpus and `graph/` are: `build_graph_tables.py`,
`bluebook/link_cells.py`, `bluebook/match_officers.py`, `bluebook/link_observations.py`, `load_graph.py`.
`people_careers.py` would refresh the career polities, but it rewrites `grounding/people.jsonl` from scratch and
drops the research assistant's review overlay, so run `apply_people_review.py` straight after it. The graph counts
below are from the load before the review.

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
| Places (374,553 records) | 73.3% | 13.5% | 0.4% | 12.7% |
| Taxa (164,859 records) | 51.9% | 3.8% | 18.7% | 25.5% |
| Commodities (134,358 records) | 65.3% | 3.0% | 16.7% | 15.0% |
| Organisations (88,690 records) | 5.8% | 0.4% | 37.0% | 56.8% |

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
specific to Ceylon mostly have no Wikidata item. 72 names are matched (77 before the review removed six wrong
ones and corrected Cambridge University); most are well-known bodies (Kew, Peradeniya, Colonial Office, Indian
Tea Association). Local identifiers for the Ceylon bodies are a decision for you.

## Ceylon Blue Books

62 volumes are in, 1863 to 1938 (`bluebook/README.md` has the detail):

- **46,999 printed tables** kept as printed, each with its page and headings (`bluebook/tables/`).
- **Confidence level on every table** (`bluebook/table_confidence.tsv.gz`, revised in the review): 1,833 have
  every checkable printed total agreeing with its parts, at least one of them non-trivial; 13,046 have at least
  90% of 10+ distinct numbers also in a second OCR reading of the page (the Internet Archive's OCR and/or the
  PDF text layer; for 1863 and 1880–1894 only the Internet Archive's); 8,248 are partly confirmed; 23,743 have
  nothing to confirm them; 129 are flagged as invented. 64,203 of 168,652 total checks agree (38%). The second
  reading only says the digits are printed on that page, not that they are in the right row or column. The OCR
  model writes plausible tables on blank pages (a 1905 blank verso became "quarterly statements, Q1-Q4").
- **300,107 links from table labels to names the spine had already resolved**: 21,492 tables name a known
  place, commodity or taxon. Trade partners get the polity for the volume's year.
- **People**: 146,383 person-years of officials in the 39 volumes that print the lists (1863–1917), before the
  review's officer-index fix added about 32,600 index names for 1907–1917. 5,121 match a Colonial Office List
  person (1,083 "high") and 11,496 have a journal profile as a candidate; these numbers will change when
  `match_officers.py` is rerun. In a sample of 20 matches about 5 were uncertain (common surnames such as de
  Saram, Dias, Koch with one initial).
- **Figures**: two Codex Sol jobs, run from written briefs (`bluebook/jobs/*.md`), produced 4,918 agricultural
  figures (acreage by crop and province, district returns, live stock; seven volumes) and 88,045 trade figures
  (imports and exports by article and country; 1924, 1925, 1926, 1928). The briefs supplied a sample of
  thirteen volumes; agriculture used seven of them and trade four. Acreage and trade-ledger tables are present
  in about 45 volumes each and have not been extracted. A trade article whose total agrees can still have
  figures under the wrong country (coir mats, 1928). I checked samples against the parsed
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
Wikidata item exactly and 56 by a spelling-tolerant comparison (Bentotte / Bentota). Those are candidates, not
decisions. Known gaps: the entries for Ceylon, Kandy, Trincomalee and a few other long articles open in a way
the parser does not recognise, so their text is attached to the entry before them (flagged with a note).
The review found a larger case: about 16 entries from Pichampitty to Quiparawa sit inside "Resale"
(`cc1834:0315`), plus Budumalwal, Wedamaha Nuwera and Wallametty torre inside their neighbours; none of them
is indexed. Worth redoing on the fresh OCR.

## What to trust, and how far

- **Place matches from the Colonial Office List gazetteer** (49% of records): QIDs come from that project.
  2,378 of its 3,207 rows are still marked unverified there.
- **Place matches from Wikidata search** (about 14% of records): rule-checked, not human-checked. My first
  version matched Travancore to a Melbourne suburb and Acheen to a shipwreck; the checks were tightened and a
  random sample of 45 then looked right in 43 cases, by my reading. The independent review found about 7.5%
  clearly wrong in a sample of 40 (15% counting wrong sense or period), including high-confidence ones
  (madura, summerville); those found are now rejected. Treat all tier-2 matches as needing a look.
- **Taxa**: scientific names matched against Catalogue of Life release COL26.11. A guard sends a match to
  review when the journal's usage points to another kingdom (anthrax the disease, not Anthrax the fly;
  castor the plant, not Castor the beaver). 105 names were caught that way.
- **Commodities and common-name taxa** (Wikidata search): a candidate must carry the printed name as its
  label, an alias or a recorded common name, and its description must read as a plant, animal, product,
  material or disease. Early versions matched "cocoa" to a software framework and "potatoes" to a short story;
  those are now refused. A match on an item's own name outranks a match on an alias; I read all 320 alias-only
  matches and rejected ten ("pepper" to bell pepper, "coke" to Coca-Cola, "lac" to the lac operon). Alias
  matches are marked medium confidence.
- **Organisations**: I read the first 57 matches; one was wrong (an East Timor ministry). The review found six
  more among all 77. All are recorded in `grounding/name_rejections.jsonl`, which the matcher obeys.
- **People**: links are from the journal's own person pipeline. The research assistant's review covers 22 profiles: all 13
  asserted QIDs they checked were right; they found 3 the pipeline missed and 3 mixed profiles.
- **Polities**: found by following Empire Evolution succession for the year (`empire.py`). Since the review, a
  place that the graph cannot place unambiguously gets no polity rather than a neighbour's. Known gaps: Lagos and
  Southern Nigeria after 1914 (a false upstream edge), Zambia and Malawi missing as successors, and the Raj after
  1947 resolving to Pakistan (4 events).

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
