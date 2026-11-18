# Job: read the main export lines of the Ceylon Blue Books, 1880–1900, entry by entry

Work in `spine/bluebook`. Create files only under `jobs/main_exports_1880_1900_work/`. Do not edit anything
else. No network. `/home/jic823/miniforge3/bin/python`, standard library only.

## Why
A rule-based reader (`jobs/trade_1880_1900_work/read_trade.py`, read its README first for the layouts) produced
`extracted/trade_1880_1900.tsv.gz`, but for the colony's main exports it missed the main line in most years: it
skips any row it cannot place by rule. For six commodities we need every year read by a reader who looks at each
table: **tea; coffee (every kind printed: plantation, native, Liberian, and any unqualified line); cinchona bark;
cinnamon (bark: plantation, wild, or unqualified; not the oils or leaves); coconut oil; plumbago.**

## Input
`tables/<key>.jsonl.gz` for the 18 volumes 1880, 1881, 1882, 1883, 1885, 1886, 1887, 1889b, 1890, 1891, 1892,
1893, 1894, 1896, 1897, 1898, 1899, 1900. One printed table per line: `id`, `pdf_page`, `printed_page`,
`headings`, `header_rows`, `n_cols`, `rows` (cell strings; spans already expanded). The export ledgers have a
header starting `Articles.` | `Countries to which exported`. Also useful: `extracted/trade_1880_1900_skipped.tsv`
(rows the rule reader would not place, with reasons) and the `ledger_<volume>.txt` files in the old work folder.

## The job
For each volume and each commodity, find its block in the export ledger (it may run over a page break, and an
article printed as a sub-line, such as "— Cocoanut" under an "Oil" heading, belongs to that heading: look up the
page to find the heading, and say where you found it). Read **every country row and the total row** of the block
yourself, cell by cell, and write the figures down. Do not write a new general parser; a helper that prints the
rows of a table for you to read is fine. Where the rule reader already has the row, compare and keep whichever
you can justify from the cells, noting any difference.

Rules:
- Never correct a digit and never choose a reading because it makes a sum work or looks plausible for the trade.
  If cells are shifted or merged and the row cannot be read with confidence, record the row with
  `reading = unreadable` and say what is there.
- You are not given any outside figures for these trades, and must not use remembered ones. The result will be
  tested afterwards against an independent source; a reading tuned to expectation would spoil that test.
- Keep printed spellings of articles and countries. Keep quantities in the printed unit (cwt qr lb as decimal
  cwt to four places, as the old reader does, with the printed form kept).
- If a volume does not print a commodity, or its pages are not among the tables, say so: `not_found` with where
  you looked.

## Output
`jobs/main_exports_1880_1900_work/main_exports.tsv`, one row per figure:
`commodity` (tea, coffee, cinchona, cinnamon, coconut_oil, plumbago), `year_volume`, `table_id`, `source_row`
(zero-based row index in the table), `pdf_page`, `article_as_printed`, `heading_above_as_printed` (when the
article is a sub-line), `country_as_printed` (blank on a total row), `row_kind` (country, article_total),
`measure` (quantity_ceylon_produce, quantity_other_produce, quantity_total, value_ceylon_produce_rs,
value_other_produce_rs, value_total_rs), `unit_as_printed`, `value_as_printed`, `value`, `reading` (clear,
doubtful, unreadable), `agrees_with_rule_reader` (yes, no, not_read_by_it), `note`.

`blocks.tsv`, one row per commodity, kind and volume: `commodity`, `article_as_printed`, `year_volume`, tables and
rows of the block, `status` (read, partly_read, unreadable, not_found), `countries_read`, `country_sum_quantity`,
`printed_total_quantity`, `sum_agrees` (yes, no, no_total), the same three for value, and `note`. The sum check is
reported, never used to alter a reading.

`check.py`: every figure's `value_as_printed` occurs in the cited source row's cells; ids and rows exist; the
block sums in `blocks.tsv` are recomputed from `main_exports.tsv`; no commodity-volume pair is missing from
`blocks.tsv`. Must pass.

`README.md` (under 80 lines): a grid of commodity by volume with the block status; counts of figures by `reading`;
how often you differed from the rule reader and the three most instructive differences; where headings were lost
and how you recovered them; what remains unreadable and why; and the pages a person should look at first.

Do 1896 first (the old README describes its layout), then 1891 and 1893, then the rest in order. Stop when all
18 volumes are done.
