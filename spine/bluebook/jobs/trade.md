# Job: tidy the import and export ledgers of the Ceylon Blue Books, 1924–1934

You are working in `/home/jic823/Documents/ceylon/spine/bluebook`. Keep to this folder. Create files only under
`extracted/` and `jobs/trade_work/`. Do not edit or delete anything else (another job is writing
`extracted/agriculture*` and `jobs/agriculture_work/`; leave those alone). No network access is needed.
Aim to finish within about 40 minutes. Do 1925 first and get it right; then run the same reader on 1924,
1926 and 1928; then 1930, 1933, 1934 if time allows. Say plainly which volumes you finished.

## What you have

`tables/<year>.jsonl.gz` — one printed table per line, parsed from OCR. Fields: `id` (e.g. `bb1925:p175:t1`),
`year`, `pdf_page`, `printed_page`, `section` (running head such as "Imports", "Exports", "Domestic Exports"),
`headings`, `header_rows`, `rows` (list of rows of cell strings; row/column spans already expanded, so a
spanned heading repeats across the cells of its row).

Use `/home/jic823/miniforge3/bin/python` (standard library only).

## The printed layout

The ledgers run over many pages. Each is a hierarchy printed in the first column:

    CLASS I.—FOOD, DRINK, AND TOBACCO.          class heading
    GROUP A.—GRAIN AND FLOUR.                   group heading
    Grain, barley—                              article (ends with a dash)
    United Kingdom .. cwt.   2622  2622  102157 country row; the unit follows the dot leaders (cwt., lb., ,, or " = same as above)
    British Possessions—                        country-group heading
    British India .. ,,      2693  2693  18853
    Total British Possessions ..                printed subtotal
    Foreign Countries—
    Belgium .. cwt.          13    13    460
    Total ..                 5315  5315  121010 printed article total

- Import pages are printed in two halves side by side: look at `bb1925:p175:t1` (8 columns = two blocks of
  ARTICLES / total quantities imported / quantities entered for home consumption / value of total imports).
  Read the left block top to bottom, then the right block; an article can continue from the left block into
  the right block and from one page to the next ("Brought forward", "Carried forward" rows are running
  totals, not data: skip them but note them).
- Export pages look like `bb1925:p232:t1` and `bb1925:p249:t1`: ARTICLES, then QUANTITY (Produce and
  Manufactures of Ceylon / British, Foreign and other Colonial produce / TOTAL), then VALUE (same three).
- State (class, group, article, country group, unit) carries across rows, blocks and pages until replaced.

## What to produce

`extracted/trade.tsv`, tab-separated, one row per printed country row, with this header:

`table_id  year_volume  pdf_page  printed_page  flow  class_as_printed  group_as_printed  article_as_printed  country_group_as_printed  country_as_printed  unit_as_printed  measure  value_as_printed  value  row_kind  note`

- `flow` is `import` or `export`.
- One output row per printed number, with `measure` one of: `quantity_total`, `quantity_home_consumption`,
  `value_total_rs` (imports); `quantity_ceylon_produce`, `quantity_other_produce`, `quantity_total`,
  `value_ceylon_produce_rs`, `value_other_produce_rs`, `value_total_rs` (exports).
- `row_kind` is `country`, `subtotal` (e.g. "Total British Possessions") or `article_total` ("Total").
- Everything `_as_printed` is exactly what is printed, minus dot leaders. Do not modernise or merge names
  ("Maldivé Islands" and "Maldiv Islands" stay different). Resolve a ditto mark (,, or ") in the unit to the
  unit it repeats, and say `unit from ditto` in `note`.
- `value` is the number with separators removed; a dash, "..", or blank means no figure: leave `value` empty.
- Never invent a number. If a row cannot be read with confidence, write it to `extracted/trade_skipped.tsv`
  (table_id, row index, cells, reason) instead.

## Checks to run before you finish

- For every article with a printed "Total" row, compare it with the sum of its country rows, per measure.
  Write mismatches to `extracted/trade_checks.tsv` and report the share of articles whose totals agree, per
  volume and flow. A low share means the reader is losing or mis-assigning rows: investigate before moving on.
- Write `extracted/trade_README.md`: volumes done, row counts per volume and flow, the agreement shares, known
  problems, and the ten articles with the largest unexplained differences.

Keep your scripts in `jobs/trade_work/` so the result can be rebuilt. End with a short plain summary of what
was produced and what was not.
