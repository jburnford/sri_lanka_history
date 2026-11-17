# Job: the "Statistical View of the Progress of Ceylon" series, from every Blue Book volume

You are working in `/home/jic823/Documents/ceylon/spine/bluebook`. Create files only under
`jobs/statistical_view_work/` and the three output files named below in `extracted/`. Do not edit or delete
anything else. No network access is needed. Use `/home/jic823/miniforge3/bin/python` (standard library only).
Aim to finish within about 45 minutes. Do the 1896 volume first, then 1871 and 1911, then all the others.

## Input

`tables/<key>.jsonl.gz` — one printed table per line, parsed from OCR (63 volumes, 1863–1938; file keys are
years, plus `1889b`). Fields: `id` (e.g. `bb1896:p7:t1`), `year`, `pdf_page`, `headings`, `header_rows`,
`n_cols`, `rows` (rows of cell strings; spans already expanded, so a spanned header cell repeats).

Near the front of most volumes is a long table headed "Statistical View of the Progress of Ceylon from the
year 1821 ..." (see `bb1896:p7:t1`, `bb1871:p5:t1`, `bb1911:p7:t1`). It has one row per year and columns such
as area, population, military, births, marriages, deaths, schools and scholars, land sales, revenue,
expenditure, imports, exports, shipping, and others; it continues over several pages and tables, each with
its own columns. Because every volume reprints the whole series, most figures are printed many times, set in
type and read by OCR separately. That makes it possible to tell an OCR slip from a real revision.

The OCR is good but not perfect. Never correct a figure. If a row or column cannot be read safely, skip it
and say why.

## Output

`extracted/statistical_view.tsv.gz` (gzip, tab-separated), one row per printed figure:

    table_id year_volume pdf_page data_year column_as_printed series value_as_printed value note

- `column_as_printed`: the full header of the column, top header row to bottom, joined with " / ".
- `series`: a short stable name you assign so the same column lines up across volumes
  (`population`, `births`, `deaths`, `revenue`, `expenditure`, `imports_value`, `exports_value`, ...). Keep a
  table of your mapping in `jobs/statistical_view_work/series_map.tsv` (series, the distinct printed headers
  mapped to it, the unit or currency as printed, first and last volume). Money changes from sterling
  (£ s. d.) to rupees in the 1870s: keep separate series for different currencies or units, never convert.
- `value`: the number, or empty where the cell is not a plain number; £ s. d. as decimal pounds with the
  triple kept in `value_as_printed`. `note`: `source row N, column M` and anything a reader must know.

`extracted/statistical_view_compare.tsv`: one row per (series, data_year): number of volumes printing it, the
distinct values with the volumes that print each (most common first), and a status: `all agree`,
`one volume differs` (probably an OCR slip in that volume), `two values` (possibly a revision: say from which
volume the value changes), `many values`.

`extracted/statistical_view_skipped.tsv`: table_id, what was skipped, why.

## Checks you must run and report

1. Per volume: tables used, figures written, figures skipped. Save in
   `jobs/statistical_view_work/README.md` with the layout variants you met.
2. Per series: years covered, share of (series, year) cells where all volumes agree.
3. Look by eye at 30 figures spread over three volumes against the table rows and report what you found.
4. List the 20 (series, year) cells with the most disagreement, with the values and volumes.
