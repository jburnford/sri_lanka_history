# Ceylon Blue Books in the spine

Started 16 November 2026 from the Chandra OCR in `/mnt/data/jic823/ocr_chandra/out_chandra2` (read only).
Volumes present: 62, covering 1863 to 1938 with gaps (1889 is in two parts; second copies of 1877 and 1892
are listed but not loaded). `volumes.tsv` maps folder to year and archive.org item; add a line when a new volume arrives and rerun.

## Layers

| Layer | Script | Output | What it is |
|---|---|---|---|
| Tables as printed | `build_tables.py` | `tables/<year>.jsonl.gz`, `pages/<year>.jsonl.gz`, `inventory.tsv` | One record per printed table: page, running section, headings above it, cells. Nothing interpreted. 46,999 tables. |
| Labels linked to the spine | `link_cells.py` | `cell_links.tsv.gz`, `table_name_links.tsv.gz`, `unlinked_labels.tsv` | A row or column label links when the spine has already matched that name to an entity. Places also get the polity for the volume's year. |
| People in the Civil Establishment | `extract_officers.py` | `extracted/officers_index.tsv`, `extracted/civil_establishment.tsv` | 1863–1917 (39 volumes): the alphabetical list of officers and the returns (office, name, date of appointment, salary, department). From 1907 the list is "Name and Office \| Page" in one or two printed columns; `column` says which. |
| People matched | `match_officers.py` | `extracted/officer_matches.tsv` | Blue Book person-years matched to Colonial Office List persons (surname, initials, a Ceylon posting in time); journal profiles offered as candidates only. |
| Agriculture (Codex Sol job) | `jobs/agriculture.md`, `jobs/agriculture_work/` | `extracted/agriculture*.tsv` | 12,686 figures from 134 tables in 48 volumes. The first pass (seven volumes) took acreage by crop, land/produce/stock by district and live stock; 24 tables with misaligned OCR columns were skipped, not guessed. A second pass took the opening Agricultural Statistics (acres by crop and province, previous year and volume year) from every other volume, 1862–1923 (1877 prints none). 935 of 1,096 checkable printed acreage totals agree; the rest are OCR digit slips, flagged in `note`, never corrected. Most years are printed twice (each volume reprints the previous year): `extracted/agriculture_second_printing.tsv` pairs the printings, 3,814 of 3,959 pairs agree, and each figure's note names its other printing. |
| Trade (Codex Sol job) | `jobs/trade.md`, `jobs/trade_work/` | `extracted/trade*.tsv` | 88,045 figures: imports and exports by article and country for 1924, 1925, 1926, 1928. 78–85% of articles have printed totals that equal the sum of their country rows; the rest are OCR digit errors or skipped rows, listed in `trade_checks.tsv`. 1930–34 do not print the country ledgers. |
| Figures linked to the spine | `link_observations.py` | `observations.tsv.gz`, `observation_labels_unlinked.tsv` | Each figure's area or country and its crop or article, where the printed label is a name already resolved. `label_aliases.tsv` holds Blue Book spellings ("U. S., America"). |

The atlas's **Blue Books** view (`docs/bluebook.js`) shows every table beside its archive.org page image (image `n<pdf page - 1>`; each archive.org item has as many page images as the PDF has pages). `export_viewer.py` writes its data to `docs/data/bluebook/`; rerun it after any change to the tables, confidence levels or extracts.

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
identified with the same Colonial Office List person; most of them (clerks, teachers, headmen,
postmasters) are in no other source and are not merged across volumes yet.

## How far to trust the numbers

Every table has a confidence level in `table_confidence.tsv.gz` (and on the `BlueBookTable` node as
`confidence`), from three tests that do not depend on each other. `confidence.py` explains the rules.

| Level | Tables | Meaning |
|---|---:|---|
| `summed` | 1,833 | every printed total that could be checked equals the sum of its parts, and at least one is non-trivial (a non-zero total of two or more non-zero parts) |
| `two_readings` | 13,046 | at least 90% of the numbers are also in a second, conventional OCR reading of the page, and the table has at least 10 distinct numbers of 3+ digits |
| `partly` | 8,248 | at least half the totals agree (one non-trivially), or at least 70% of 5+ distinct numbers are in the second reading |
| `unconfirmed` | 23,743 | nothing confirms it. Not evidence of error: mostly tables of names and words, tables with few numbers, sideways pages and the 1880-1894 volumes, where the second reading is poor |
| `suspect` | 129 | the page is blank or a section title page and the table is invented. Do not use |

What the tests showed:

- **The OCR model invents tables on blank pages.** A blank verso in 1905 came back as "quarterly statements"
  with Q1-Q4 revenue; others as "Bank of America", "churches of Rio de Janeiro", "the Colony of Toronto".
  The rule that finds them (no text in the second reading and no ink inside the table's outline on the scan)
  was right in 8 of 8 cases checked by eye. A table invented over a title page that the rule misses is possible.
- **On printed pages the numbers are mostly right.** In the 1925-1938 volumes 91-94% of numbers of three or
  more digits are also in the second reading. For numbers that a printed total proves correct the second
  reading has 96%, so the model's own misread rate there is about 2% (about 4% in 1897; five volumes tested).
- **A total that does not agree is weak evidence.** 64,203 of 168,652 sum checks agree (unlabelled running subtotals, which were only kept when they agreed, are no longer counted). In the failures read
  by eye the numbers were usually right and the check was wrong: a table continued from another page, a
  running subtotal, or columns of different units under one heading.
- **Sideways tables** are read by the model but not by the second reading, so they stay `unconfirmed`.
- The extracted agriculture and trade figures (`observations.tsv.gz`): 98.6% come from `two_readings`
  tables, 1.4% from `summed` or `partly`, 18 figures from `unconfirmed`, none from `suspect`.
- **What the second reading does not check.** It is a set-membership test: a number counts if the same digits
  appear anywhere in the second reading of that page. It does not check that a number is in the right row or
  column, so a row shift or invented headers can still pass. For 1863 and 1880–1894 the second reading is the
  Internet Archive's OCR alone. Several PDFs (1866–1877, 1896–1899, 1905, 1908, 1910, 1911) are JSTOR / South
  Asia Open Archives downloads, so their text layer is JSTOR's OCR.

Scripts: `second_reading.py` (PDF text layer joined with the Internet Archive's OCR text, fetched by
`fetch_ia_text.py`), `page_ink.py` (dark pixels inside each table outline), `confidence.py` (the levels;
`confidence_by_volume.tsv` is the summary).

## Known limits

- Running sections are only detected from 1921 on (bracketed running heads). Earlier volumes rely on headings. A bracketed footer ("Extracted from the Reports of the several Government Agents") became the running section of about 800 tables in 1880, 1881, 1890 and 1891.
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
