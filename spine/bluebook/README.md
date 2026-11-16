# Ceylon Blue Books in the spine

Started 16 November 2026 from the Chandra OCR in `/mnt/data/jic823/ocr_chandra/out_chandra2` (read only).
Volumes present: 1869, 1889 (part 1), 1890 (40-page sample), 1902, 1904, 1912 (supplementary), 1924, 1925,
1926, 1928, 1930, 1933, 1934. `volumes.tsv` maps folder to year; add a line when a new volume arrives and rerun.

## Layers

| Layer | Script | Output | What it is |
|---|---|---|---|
| Tables as printed | `build_tables.py` | `tables/<year>.jsonl.gz`, `pages/<year>.jsonl.gz`, `inventory.tsv` | One record per printed table: page, running section, headings above it, cells. Nothing interpreted. 7,354 tables. |
| Labels linked to the spine | `link_cells.py` | `cell_links.tsv.gz`, `table_name_links.tsv.gz`, `unlinked_labels.tsv` | A row or column label links when the spine has already matched that name to an entity. Places also get the polity for the volume's year. |
| People in the Civil Establishment | `extract_officers.py` | `extracted/officers_index.tsv`, `extracted/civil_establishment.tsv` | 1869, 1889, 1902, 1904: the alphabetical list of officers and the returns (office, name, date of appointment, salary, department). |
| People matched | `match_officers.py` | `extracted/officer_matches.tsv` | Blue Book person-years matched to Colonial Office List persons (surname, initials, a Ceylon posting in time); journal profiles offered as candidates only. |
| Agriculture (Codex Sol job) | `jobs/agriculture.md` | `extracted/agriculture*.tsv` | Acreage by crop, land/produce/stock by district, live stock. Brief and Codex's scripts are in `jobs/`. |
| Trade (Codex Sol job) | `jobs/trade.md` | `extracted/trade*.tsv` | Imports and exports by article and country, 1924–1934. |

Table id: `bb<year>:p<pdf page>:t<n on page>`. Every extracted row carries it, so any number can be traced to
its page.

## In the graph

```
(BlueBookTable {id, year, pdf_page, printed_page, section, headings})-[:HAS_LABEL {cells, labels, polity_at_date}]->(Name)
(BlueBookOfficer {id, year, name, offices, appointment_years})-[:LISTED_IN]->(BlueBookTable)
(BlueBookOfficer)-[:IDENTIFIED_AS {authority, confidence, review_status}]->(ColPerson)
(BlueBookOfficer)-[:CANDIDATE_FOR]->(Profile)
```

A `BlueBookOfficer` is one name in one volume. The same person in two volumes is two nodes until they are
identified with the same Colonial Office List person; most of the 14,491 (clerks, teachers, headmen,
postmasters) are in no other source and are not merged across volumes yet.

## Known limits

- Running sections are only detected from 1924 on (bracketed running heads). Earlier volumes rely on headings.
- `header_rows` from the OCR is sometimes wrong; readers should not trust it blindly.
- Label linking is by exact name. "Kegalla", "Maldive Islands", "Foreign Countries" and other frequent labels
  with no resolved name are listed in `unlinked_labels.tsv`.
- Officer matching has not been checked by a person. "High" means the printed appointment year equals the
  start year of one of the Colonial Office List postings; "medium" rests on surname, initials and dates.
- The numbers in tables are OCR output and have not been checked against the scans, except by the total checks
  the extraction jobs run.
