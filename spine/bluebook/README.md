# Ceylon Blue Books in the spine

Started 16 November 2026 from the Chandra OCR in `/mnt/data/jic823/ocr_chandra/out_chandra2` (read only).
Volumes present: 62, covering 1863 to 1938 with gaps (1889 is in two parts; second copies of 1877 and 1892
are listed but not loaded). `volumes.tsv` maps folder to year and archive.org item; add a line when a new volume arrives and rerun.

## Layers

| Layer | Script | Output | What it is |
|---|---|---|---|
| Tables as printed | `build_tables.py` | `tables/<year>.jsonl.gz`, `pages/<year>.jsonl.gz`, `inventory.tsv` | One record per printed table: page, running section, headings above it, cells. Nothing interpreted. 7,354 tables. |
| Labels linked to the spine | `link_cells.py` | `cell_links.tsv.gz`, `table_name_links.tsv.gz`, `unlinked_labels.tsv` | A row or column label links when the spine has already matched that name to an entity. Places also get the polity for the volume's year. |
| People in the Civil Establishment | `extract_officers.py` | `extracted/officers_index.tsv`, `extracted/civil_establishment.tsv` | 1869, 1889, 1902, 1904: the alphabetical list of officers and the returns (office, name, date of appointment, salary, department). |
| People matched | `match_officers.py` | `extracted/officer_matches.tsv` | Blue Book person-years matched to Colonial Office List persons (surname, initials, a Ceylon posting in time); journal profiles offered as candidates only. |
| Agriculture (Codex Sol job) | `jobs/agriculture.md`, `jobs/agriculture_work/` | `extracted/agriculture*.tsv` | 4,918 figures from 53 tables in seven volumes: acreage by crop, land/produce/stock by district, live stock. 24 tables with misaligned OCR columns were skipped, not guessed. 200 of 217 checkable printed totals agree. |
| Trade (Codex Sol job) | `jobs/trade.md`, `jobs/trade_work/` | `extracted/trade*.tsv` | 88,045 figures: imports and exports by article and country for 1924, 1925, 1926, 1928. 78–85% of articles have printed totals that equal the sum of their country rows; the rest are OCR digit errors or skipped rows, listed in `trade_checks.tsv`. 1930–34 do not print the country ledgers. |
| Figures linked to the spine | `link_observations.py` | `observations.tsv.gz`, `observation_labels_unlinked.tsv` | Each figure's area or country and its crop or article, where the printed label is a name already resolved. `label_aliases.tsv` holds Blue Book spellings ("U. S., America"). |

Table id: `bb<year>:p<pdf page>:t<n on page>`. Every extracted row carries it, so any number can be traced to
its page.

## In the graph

```
(BlueBookTable {id, year, pdf_page, printed_page, section, headings})-[:HAS_LABEL {cells, labels, polity_at_date}]->(Name)
(Observation {kind, year_volume, year_data, area_as_printed, measure_as_printed, unit_as_printed, value_as_printed, value})-[:PRINTED_IN]->(BlueBookTable)
(Observation)-[:ABOUT_PLACE]->(Name)      (Observation)-[:MEASURES]->(Name)
(BlueBookOfficer {id, year, name, offices, appointment_years})-[:LISTED_IN]->(BlueBookTable)
(BlueBookOfficer)-[:IDENTIFIED_AS {authority, confidence, review_status}]->(ColPerson)
(BlueBookOfficer)-[:CANDIDATE_FOR]->(Profile)
```

A `BlueBookOfficer` is one name in one volume. The same person in two volumes is two nodes until they are
identified with the same Colonial Office List person; most of the 14,491 (clerks, teachers, headmen,
postmasters) are in no other source and are not merged across volumes yet.

## How far to trust the numbers

Every table has a confidence level in `table_confidence.tsv.gz` (and on the `BlueBookTable` node as
`confidence`), from three tests that do not depend on each other. `confidence.py` explains the rules.

| Level | Tables | Meaning |
|---|---:|---|
| `summed` | 3,774 | every printed total that could be checked equals the sum of its parts |
| `two_readings` | 15,216 | at least 90% of the numbers are also in a second, conventional OCR reading of the page |
| `partly` | 5,976 | at least half the totals agree, or 70-90% of the numbers are in the second reading |
| `unconfirmed` | 21,904 | nothing confirms it. Not evidence of error: mostly tables of names and words, tables with few numbers, sideways pages and the 1880-1894 volumes, where the second reading is poor |
| `suspect` | 129 | the page is blank or a section title page and the table is invented. Do not use |

What the tests showed:

- **The OCR model invents tables on blank pages.** A blank verso in 1905 came back as "quarterly statements"
  with Q1-Q4 revenue; others as "Bank of America", "churches of Rio de Janeiro", "the Colony of Toronto".
  The rule that finds them (no text in the second reading and no ink inside the table's outline on the scan)
  was right in 8 of 8 cases checked by eye. A table invented over a title page that the rule misses is possible.
- **On printed pages the numbers are mostly right.** In the 1925-1938 volumes 91-94% of numbers of three or
  more digits are also in the second reading. For numbers that a printed total proves correct the second
  reading has 96%, so the model's own misread rate there is about 2% (about 4% in 1897; five volumes tested).
- **A total that does not agree is weak evidence.** 77,056 of 181,505 sum checks agree. In the failures read
  by eye the numbers were usually right and the check was wrong: a table continued from another page, a
  running subtotal, or columns of different units under one heading.
- **Sideways tables** are read by the model but not by the second reading, so they stay `unconfirmed`.
- The extracted agriculture and trade figures (`observations.tsv.gz`): 98.7% come from `two_readings`
  tables, 1.3% from `summed` or `partly`, 18 figures from `unconfirmed`, none from `suspect`.

Scripts: `second_reading.py` (PDF text layer joined with the Internet Archive's OCR text, fetched by
`fetch_ia_text.py`), `page_ink.py` (dark pixels inside each table outline), `confidence.py` (the levels;
`confidence_by_volume.tsv` is the summary).

## Known limits

- Running sections are only detected from 1924 on (bracketed running heads). Earlier volumes rely on headings.
- `header_rows` from the OCR is sometimes wrong; readers should not trust it blindly.
- Label linking is by exact name. "Kegalla", "Maldive Islands", "Foreign Countries" and other frequent labels
  with no resolved name are listed in `unlinked_labels.tsv`.
- Officer matching has not been checked by a person. "High" means the printed appointment year equals the
  start year of one of the Colonial Office List postings; "medium" rests on surname, initials and dates.
- The numbers are OCR output and have not been checked against the scans. I compared the two extracts with the
  parsed tables for a handful of rows (1902 acreage, 1925 barley imports and citronella exports) and they agreed;
  the total checks are the only systematic test. A figure whose article total does not agree should not be quoted
  without looking at the page.
- Only 28% of trade articles link to a resolved commodity name ("Curios", "Piece goods", "Manufactures of iron
  and steel" are not journal vocabulary); 93% of country rows link to a place.
