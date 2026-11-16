# Job: tidy the agricultural tables of the Ceylon Blue Books

You are working in `/home/jic823/Documents/ceylon/spine/bluebook`. Keep to this folder. Create files only under
`extracted/` and `jobs/agriculture_work/`. Do not edit or delete anything else. No network access is needed.
Aim to finish within about 40 minutes; if you run short, deliver fewer volumes done well and say which.

## What you have

`tables/<year>.jsonl.gz` — one printed table per line, parsed from OCR of the Ceylon Blue Books
(years 1869, 1889, 1890, 1902, 1904, 1912, 1924, 1925, 1926, 1928, 1930, 1933, 1934). Fields:

- `id` (for example `bb1902:p16:t1`), `year` (the volume's year), `pdf_page`, `printed_page`
- `section` (running head, often null before 1924), `headings` (up to three headings printed above the table)
- `header_rows` (how many leading rows are header rows; sometimes wrong), `rows` (list of rows; each row a list
  of cell strings; row and column spans already expanded, so a spanned heading repeats across cells)

`pages/<year>.jsonl.gz` has the page text if you need context (for example which year a table refers to).

Use `/home/jic823/miniforge3/bin/python` (standard library only).

## What to produce

`extracted/agriculture.tsv`, tab-separated, one row per printed number, with this header:

`table_id  year_volume  year_data  pdf_page  printed_page  table_kind  area_level  area_as_printed  parent_area_as_printed  measure_as_printed  unit_as_printed  value_as_printed  value  note`

Cover these three kinds of table (`table_kind`):

1. `acreage_by_crop` — "Agricultural Statistics": acres under each crop by province (and by district where
   printed). Example: `bb1902:p16:t1`, `bb1869:p11:t2`. Each volume usually prints two such tables side by
   side, one for the previous year and one for the volume's year; work out `year_data` from the headings or
   page text, and leave it empty with a `note` if you cannot tell.
2. `land_produce_stock` — the district returns headed like "Cultivated and Uncultivated Lands, Wages, Produce,
   Stock, &c." (example `bb1869:p530:t1`) and their later equivalents: acreage, produce quantities, numbers of
   live stock, by district within province.
3. `live_stock` — "Number of Live Stock" summary tables by province.

Rules:

- `area_as_printed`, `measure_as_printed`, `unit_as_printed` and `value_as_printed` are exactly what is printed
  (trim trailing dot leaders such as " ....."). Do not modernise spellings, do not merge "Cocoanuts" with
  "Coconuts", do not translate units.
- `value` is the number as a decimal: remove thousands separators; turn printed fractions into decimals
  (`21978¾` -> `21978.75`); a dash, "..", "Nil" or blank means no figure: leave `value` empty and keep
  `value_as_printed`.
- `area_level` is `province`, `district`, `colony_total` or `other`. A province heading row inside a table
  (for example a row where every cell reads "WESTERN PROVINCE") sets `parent_area_as_printed` for the district
  rows below it and produces no data rows itself. Keep printed total rows, with `area_level` `colony_total`
  or with `note` = `printed total`.
- Skip a table rather than guess when its layout is unclear; list every skipped candidate in
  `extracted/agriculture_skipped.tsv` with `table_id` and a short reason.
- Never invent a number. If OCR looks wrong (a letter inside a number, a total that does not add up), keep the
  printed string, leave `value` empty if it cannot be read as a number, and say so in `note`.

## Checks to run before you finish

- For every `acreage_by_crop` table with a printed TOTAL column or row, compare the printed total with the sum
  of the parts and report mismatches in `extracted/agriculture_checks.tsv` (table_id, area or measure, printed
  total, computed sum, difference).
- Write `extracted/agriculture_README.md`: which tables were used per volume and kind, row counts, how
  `year_data` was decided, the share of totals that agree, and anything you were unsure about.

Keep your scripts in `jobs/agriculture_work/` so the result can be rebuilt. End with a short plain summary of
what was produced and what was not.
