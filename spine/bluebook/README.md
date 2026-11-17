# Ceylon Blue Books in the spine

Started 16 November 2026 from the Chandra OCR in `/mnt/data/jic823/ocr_chandra/out_chandra2` (read only).
Volumes present: 63, covering 1863 to 1938 with gaps (1889 is in two parts; second copies of 1877 and 1892
are listed but not loaded). `volumes.tsv` maps folder to year and archive.org item; add a line when a new volume arrives and rerun.

## Layers

| Layer | Script | Output | What it is |
|---|---|---|---|
| Tables as printed | `build_tables.py` | `tables/<year>.jsonl.gz`, `pages/<year>.jsonl.gz`, `inventory.tsv` | One record per printed table: page, running section, headings above it, cells. Nothing interpreted. 48,091 tables. |
| Labels linked to the spine | `link_cells.py` | `cell_links.tsv.gz`, `table_name_links.tsv.gz`, `unlinked_labels.tsv` | A row or column label links when the spine has already matched that name to an entity. Places also get the polity for the volume's year. |
| People in the Civil Establishment | `extract_officers.py` | `extracted/officers_index.tsv`, `extracted/civil_establishment.tsv` | 1863–1917 (39 volumes): the alphabetical list of officers and the returns (office, name, date of appointment, salary, department). From 1907 the list is "Name and Office \| Page" in one or two printed columns; `column` says which. |
| People matched | `match_officers.py` | `extracted/officer_matches.tsv` | Blue Book person-years matched to Colonial Office List persons (surname, initials, a Ceylon posting in time); journal profiles offered as candidates only. |
| Agriculture (Codex Sol job) | `jobs/agriculture.md`, `jobs/agriculture_work/` | `extracted/agriculture*.tsv` | 12,906 figures from 136 tables in 49 volumes. The first pass (seven volumes) took acreage by crop, land/produce/stock by district and live stock; 24 tables with misaligned OCR columns were skipped, not guessed. A second pass took the opening Agricultural Statistics (acres by crop and province, previous year and volume year) from every other volume, 1862–1923 (1877 prints none). The 1879–1891 tables (21, where the OCR is worst) were read by eye from the page images instead: `page_readings/acreage/`, 1,816 cells; 222 differ from the OCR string (the note quotes it). An outlier check, a cell-by-cell comparison of fifteen volumes' tables with the page images, and a reading of both pages wherever two printings disagreed found 79 more OCR misreadings, applied from `page_readings/acreage_cells.tsv`. About 3% of cells were misread in the tables compared whole; elsewhere a figure is protected by its second printing. 50 printed figures that are probably wrong at source or not comparable stay as printed, marked in note by kind: misprint, error in the return, doubtful outlier, shared figure (`page_readings/acreage_suspect.tsv`). 1,083 of 1,175 printed acreage totals agree (50 do not, 42 cannot be checked); the rest are OCR digit slips or errors at source, flagged in `note`, never corrected. Most years are printed twice (each volume reprints the previous year): `extracted/agriculture_second_printing.tsv` pairs the printings, 4,159 of 4,179 pairs agree (9 of the rest differ in print), and each figure's note names its other printing. |
| Trade ledgers (Codex Sol job, extended) | `jobs/trade.md`, `jobs/trade_work/`, `trade_periods.py` | `extracted/trade.tsv.gz`, `trade_checks.tsv`, `trade_skipped.tsv`, `trade_periods.tsv` | About 439,200 figures: imports and exports by article and country for the 22 volumes 1907–1928. The reader written for 1924–1928 was extended on 17 November 2026 to the earlier layout (unlabelled total rows, "British Colonies", regional sub-headings, capitalised class headings, tea in Black and Green columns); the 88,045 rows of the first pass are unchanged. 76–94% of an article's printed totals equal the sum of its country rows, by volume and flow; the rest are listed in `trade_checks.tsv`, not repaired. A check of 312 sampled rows against the page images found 95% right in article, country, measure and value, with no misread digit; the structural errors it found are described in `extracted/trade_README.md`, and most are now handled. Each table's printed period is in `trade_periods.tsv`: the 1910 volume holds six months to June 1910 and twelve months to June 1911, and 1921 is printed in two half-years. Not read: 1880–1906 (an older single-block layout) and 1863–1877 (sterling; hundredweights, quarters and pounds). See `extracted/trade_README.md`. |
| Trade by country and class | `extract_trade_summary.py` | `extracted/trade_by_country_class.tsv`, `trade_by_country_class_checks.tsv` | 43,454 figures from the "Summary Statements of the Value of ..." in the 17 volumes 1922–1938: imports, domestic exports, re-exports and total exports by country and class (I–IV, bullion and specie, totals). The only source here for trade partners after 1928. Every row checks itself (classes add to total merchandise; merchandise plus bullion adds to the total): 97–100% of rows add up in each volume except 1927 (86%, one page lost its last column); `row_check` marks the rest. |
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
| `summed` | 1,903 | every printed total that could be checked equals the sum of its parts, and at least one is non-trivial (a non-zero total of two or more non-zero parts) |
| `two_readings` | 13,545 | at least 90% of the numbers are also in a second, conventional OCR reading of the page, and the table has at least 10 distinct numbers of 3+ digits |
| `partly` | 8,429 | at least half the totals agree (one non-trivially), or at least 70% of 5+ distinct numbers are in the second reading |
| `unconfirmed` | 24,083 | nothing confirms it. Not evidence of error: mostly tables of names and words, tables with few numbers, sideways pages and the 1880-1894 volumes, where the second reading is poor |
| `suspect` | 131 | the page is blank or a section title page and the table is invented. Do not use |

What the tests showed:

- **The OCR model invents tables on blank pages.** A blank verso in 1905 came back as "quarterly statements"
  with Q1-Q4 revenue; others as "Bank of America", "churches of Rio de Janeiro", "the Colony of Toronto".
  The rule that finds them (no text in the second reading and no ink inside the table's outline on the scan)
  was right in 8 of 8 cases checked by eye. A table invented over a title page that the rule misses is possible.
- **On printed pages the numbers are mostly right.** In the 1925-1938 volumes 91-94% of numbers of three or
  more digits are also in the second reading. For numbers that a printed total proves correct the second
  reading has 96%, so the model's own misread rate there is about 2% (about 4% in 1897; five volumes tested).
- **A total that does not agree is weak evidence.** 65,391 of 172,546 sum checks agree (unlabelled running subtotals, which were only kept when they agreed, are no longer counted). In the failures read
  by eye the numbers were usually right and the check was wrong: a table continued from another page, a
  running subtotal, or columns of different units under one heading.
- **Sideways tables** are read by the model but not by the second reading, so they stay `unconfirmed`.
- The extracted agriculture and trade figures (`observations.tsv.gz`, about 432,500): 67.6% come from `two_readings`
  tables, 26.6% from `summed`, 4.1% from `partly`, 1.6% (7,034 figures) from `unconfirmed`, none from `suspect`.
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
- Only 36% of trade ledger figures link to a resolved commodity name ("Curios", "Piece goods", "Manufactures of iron
  and steel" are not journal vocabulary); 93% of country rows link to a place.
