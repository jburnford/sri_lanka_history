# Status, 17 November 2026

Written for a check-in after working alone. Detail is in `README.md` (how it works) and `UPSTREAM_ERRORS.md`
(what is wrong upstream).

## Review of the 16 November work, and fixes (17 November 2026)

Everything committed on 16 November after the first review was checked again, the acreage figures against the
page images by readers who had not seen the extraction.

- **No extraction error found.** Every acreage figure checked was in the right row, column, crop, province
  and year (year order confirmed on the page for 24 volumes; the pairing of first and second printings
  recomputed independently).
- **OCR slips outside 1879–1891: about 3% of cells** in the tables compared whole with the page (45 of about
  1,540), mostly fractions (eighths and quarters read as ½; the 1905 table lost its fractions) and broken
  type. A second round read every table with no second printing (1867, 1869, 1871, 1894, 1895) and both pages
  of every pair of printings that disagreed. 74 cells are corrected from the page
  (`bluebook/page_readings/acreage_cells.tsv`); agreeing printed totals rose from 1,000 of 1,105 to 1,083 of
  1,175, and 4,159 of 4,179 pairs of printings now agree. Of the 15 that still differ, 9 are real differences
  in print between two volumes and 3 cannot be settled from the scan. The acreage figures are now either
  read from the page, printed the same way in two volumes, or (1928 only) unchecked.
- **The 1879–1891 page readings hold**: 1,316 cells compared, none differs from a legible figure. One reading
  changed (the 1882 coffee total, a broken 4).
- **"Probable misprint" was too strong for most of the flagged figures.** `acreage_suspect.tsv` now has a
  `kind`: 15 misprints (totals or the other printing show it), 30 probable errors in the return (the printed
  totals carry them), 4 doubtful outliers, 1 figure shared by two columns.
- **The acreage validator is not an independent check of the OCR**: it confirms each output against the OCR
  table or page reading, so it cannot see a misread figure. Its README now says so.
- **Table confidence**: a "total that does not agree" no longer reports a pence or cents amount as if it were
  printed (`converted_cells`), and the list is no longer cut inside an entry. Levels are unchanged.
- **Reruns left by the first review are done**: place grounding (16 names changed), officer matching,
  label links, figure links and the graph load.
- The Blue Book viewer was checked against its sources (identical after a fresh export) and against
  archive.org page counts for 14 volumes; the scan shown beside a table is the right page.
- **The 1909 volume is in** (its OCR arrived on 17 November): 1,092 tables, its two acreage tables, 5,337
  index names. Its even pages show the edge of the facing page, which the OCR read as an extra column; the
  officer index extractor now allows for that (1911 gained 704 names too).
- **Codex Sol jobs, 17 November** (briefs in `bluebook/jobs/*.md` and `grounding/review_jobs*/`; each result
  sampled before use):
  - *Names in review.* It read 681 crop, plant and commodity names with their candidates and proposed 241
    matches; I read 50 and rejected none. They are applied through `grounding/name_decisions.jsonl` (rule
    `reviewed_proposal`, confidence medium). Commodities are now 70.3% matched by record.
  - *Place names in review.* It read the 600 most frequent of 1,077 and proposed 160 matches (48 read, none
    rejected), applied the same way; 440 names it left open carry its note (ambiguous between which items, or
    no fitting candidate) in `grounding/place_review_notes.jsonl`. A second run read the remaining 1,754 names
    and proposed 423 matches (50 read, none rejected), also applied. Places are 77.5% matched by record.
  - *Statistical View series.* The annual series reprinted in every volume (population, births, deaths,
    schools, revenue, expenditure, imports, exports, shipping, land sales): 45,118 figures from 49 volumes.
    `bluebook/statistical_view_consensus.py` takes the value most volumes print: 2,437 series-years, 1,967 with
    strong support (five or more volumes, 80% agreeing). Loaded as `series:` observations.
  - *Trade 1880–1900* and a repair of my 1901–1906 reader are still running. My first 1901–1906 reader put the
    right figures under the wrong article too often (150 of 240 sampled rows right), so nothing before 1907 is
    loaded.
- **Other sources.** `sources/ocr_registry.tsv` lists every OCR'd piece downloaded so far with its collection,
  title and date. The Ferguson directories will not be re-extracted: historyofceylontea.com has already
  compiled estate and planter registers from them, and this project links to those pages
  (`links/build_hoct_index.py`; the index itself stays local).
- Not done: the 1928 acreage table (341 figures, one printing) has not been compared with the page; the
  officials extractor is unchecked outside the volumes sampled; trade before 1907 is not extracted.
- **Trade is extended** (17 November): the article-by-country ledgers for all 22 volumes 1907–1928 (about
  439,200 figures; 76–94% of article totals agree; 297 of 312 sampled rows right against the scans, no misread digits, and five of the six error patterns found are now handled), each table's printed period (the 1910 volume holds two
  periods, 1921 two half-years), and a second source, value of trade by country and class for 1922–1938
  (43,454 figures; 97–100% of rows add up). Tea exports to 1918 are printed in Black and Green columns and
  needed their own reading; tea is still incomplete for 1907 and 1917. The graph holds 432,536 figures.

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
  provinces are no longer skipped as generic. **Not rerun here**: `resolve_place_reviews.py` and
  `ground_places_wd.py` need the Empire Evolution data and `col_matching`.
- **Rejections.** 27 wrong matches with evidence in the journal's own role text were added to
  `grounding/name_rejections.jsonl` (madura → Madura Island, summerville → Georgia, united provinces → Dutch
  Republic, board of revenue → a Chinese ministry, cacao → a drink, lime → Tilia, citronella → a tree genus,
  ...). `ground_taxa_col.py` now honours rejections too. Taxa, commodities and organisations were rerun here.

To finish on the workstation: `resolve_place_reviews.py`, `ground_places_wd.py 5`, `match_casie_chitty.py`,
`build_graph_tables.py`, `bluebook/link_cells.py`, `bluebook/match_officers.py`,
`bluebook/link_observations.py`, `load_graph.py`. The graph counts below are from the load before the review.

## What exists now

A rebuilt graph in a separate Neo4j database (`neo4j-ceylon-spine`, Browser http://localhost:7478, Bolt 7691),
loaded from decision files in under a minute. The old database and Codex's GIS folders are untouched.

| In the graph | Count |
|---|---:|
| Articles (canonical copies) | 53,501 |
| Printed names, all types | 169,425 |
| Article-to-name links | 845,450 |
| Places with a QID | 2,777 |
| Taxon name records (Catalogue of Life) | 3,611, of which 932 are synonyms linked to an accepted name |
| Wikidata concepts (taxa, products, diseases, organisations) | 970 |
| Blue Book tables and officials (person-years) | 48,091 and 167,416 |
| Blue Book figures (acreage, district returns, trade, annual series) | 434,973 |
| Person profiles | 38,579; 680 linked to Wikidata and/or a Colonial Office List person |
| Colonial Office List officials and postings | 1,212 and 12,492 |
| Empire Evolution territories | 739 |

## Coverage of the journal's records

| Type | Matched | In review | Unmatched or skipped | Not attempted |
|---|---:|---:|---:|---:|
| Places (374,553 records; before the review rerun) | 73.4% | 13.3% | 0.5% | 12.7% |
| Taxa (164,859 records) | 56.5% | 3.3% | 14.7% | 25.5% |
| Commodities (134,358 records) | 70.2% | 2.7% | 12.1% | 15.0% |
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

63 volumes are in, 1863 to 1938 (`bluebook/README.md` has the detail):

- **48,091 printed tables** kept as printed, each with its page and headings (`bluebook/tables/`).
- **Confidence level on every table** (`bluebook/table_confidence.tsv.gz`, revised in the review): 1,903 have
  every checkable printed total agreeing with its parts, at least one of them non-trivial; 13,545 have at least
  90% of 10+ distinct numbers also in a second OCR reading of the page (the Internet Archive's OCR and/or the
  PDF text layer; for 1863 and 1880–1894 only the Internet Archive's); 8,429 are partly confirmed; 24,083 have
  nothing to confirm them; 131 are flagged as invented. 65,391 of 172,546 total checks agree (38%). The second
  reading only says the digits are printed on that page, not that they are in the right row or column. The OCR
  model writes plausible tables on blank pages (a 1905 blank verso became "quarterly statements, Q1-Q4").
- **300,107 links from table labels to names the spine had already resolved**: 21,492 tables name a known
  place, commodity or taxon. Trade partners get the polity for the volume's year.
- **People**: 167,416 person-years of officials in the 40 volumes that print the lists (1863–1917). 6,100
  match a Colonial Office List person (562 "high": a Ceylon posting's start year and two initials agree;
  5,439 medium; 99 low) and 13,108 have a journal profile as a candidate. In a sample of 20 earlier matches
  about 5 were uncertain (common surnames such as de Saram, Dias, Koch with one initial).
- **Figures**: two Codex Sol jobs, run from written briefs (`bluebook/jobs/*.md`), produced 4,918 agricultural
  figures (acreage by crop and province, district returns, live stock; seven volumes) and 88,045 trade figures
  (imports and exports by article and country; 1924, 1925, 1926, 1928). The briefs supplied a sample of
  thirteen volumes; agriculture used seven of them and trade four. The trade ledgers were later extended to 1907–1928 (see the top of this file). A trade article whose total agrees can still have
  figures under the wrong country (coir mats, 1928). I checked samples against the parsed
  tables and loaded them. A second pass on 16 November took the opening acreage tables from every volume that
  prints one (1862–1923): 12,906 agricultural figures from 136 tables, with the 1879–1891 tables read from the
  page images (`bluebook/extracted/agriculture_README.md`). The graph holds 85,729 `Observation` nodes.
  Printed totals agree with the sum of parts for 92% of acreage checks and 78–85% of trade articles; the rest
  are listed, not repaired. Example from the graph: coffee falls from 207,066 acres in 1868 to 1,389 in 1912
  while rubber rises from 4,100 in 1902 to 184,551 in 1911 (sums over the provinces that report).
  The `codex` on the PATH (0.166.0) cannot run commands because its helper binary is missing; I used the
  complete install at `~/.codex/plugins/.plugin-appserver/codex`.

## The 1834 Ceylon Gazetteer (Casie Chitty)

Parsed from the Internet Archive text you sent into 439 entries (`gazetteer/casie_chitty_1834.jsonl`): headword,
bracketed alternative spellings, kind of place, "N miles <direction> of <place>" statements (137 entries), and
the entry text. `analysis/casie_chitty_matches.tsv` lines the headwords up with the journal and with Wikidata's
Sri Lanka items: 96 headwords occur in the journal as printed and 108 more under a nearby spelling; 32 match a
Wikidata item exactly and 65 by a spelling-tolerant comparison (Bentotte / Bentota). Those are candidates, not
decisions.

Re-parsed on 17 November 2026 (the first parse had 386 entries). The review's finding was right: one misread
headword, "Resale" for Pesale, moved the parser's place in the alphabet from P to R, and the 22 entries from
Pichampitty to Quiparawa were attached to it. The parser now takes alphabetical order from the longest
consistent run of entries, so one misread letter is an outlier. It also reads entries that open "Kandy. The
name ...", "CEYLON. The island ...", "Calpentyn (Gulf of). This ...", "Maderegamuwe. a village" (a stop for the
comma) and headwords the OCR garbled ("Ga//e", "Ha/pe", "llpekadawe"). 53 entries are new; none was dropped,
and 26 earlier entries lost text that belonged to a neighbour. Ids stay with their entry
(`gazetteer/casie_chitty_ids.tsv`, keyed on the source line); new entries are numbered from 0387, and six take
the ids the atlas had already given them by hand (`cc1834:kandy`, `cc1834:galle-town`, ...).

Three headwords are out of alphabetical order where they stand and are probably misread first letters:
Resale (Pesale), Wedamaha Nuwera (among the Med- entries) and Budumalwal (among the E- entries). They carry a
note; I have not checked them on the 1834 page images. The Internet Archive text of the 1834 original was read
as Tamil script and is unusable, so this is still the 1989 Navrang reprint's text; a fresh OCR of the 1834
scan would settle the misreadings.

The atlas index (`analysis/hgis_chitty_1834_index.tsv`, 393 entries) does not yet list the 46 new entries that
it did not already hold.

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
- **Polities**: `empire.polity_at` follows lineage edges in both directions with no geographic check, so some
  postings get a neighbour's polity (Newfoundland → Dominion of Canada 1867–1931, Penang and Malacca →
  Singapore Crown Colony, Northern Rhodesia → Southern Rhodesia). Not fixed yet.

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
