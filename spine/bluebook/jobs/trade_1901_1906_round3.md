# Third repair of the 1901–1906 trade reader

You are repairing `read_trade_old.py` in this folder (`spine/bluebook`). It reads the import and export ledgers of the
Ceylon Blue Books 1901–1906 from OCR tables (`tables/<year>.jsonl.gz`, pages in `pages/<year>.jsonl.gz`) and writes
`extracted/trade_1880_1906.tsv.gz`, `extracted/trade_1880_1906_checks.tsv`, `extracted/trade_1880_1906_skipped.tsv`.
Two earlier repair rounds are documented in `jobs/trade_1901_1906_work/README.md` and `README_round2.md`. Read both first.

A third independent check of 279 output rows against the page images is in
`jobs/trade_1901_1906_work/scan_check3_sample.tsv` (the rows, with `sample_number`) and
`scan_check3_results_a.tsv` (1901–1903: 109 of 132 right) and `scan_check3_results_b.tsv` (1904–1906: 141 of 147 right).
The `what_the_page_shows` column says what is printed. These verdicts are your test cases. The checker read the
page images; where the OCR disagrees with the checker, the page image is right, but you may not invent text the OCR
does not contain: withhold the row (write it to the skipped file with a reason) instead.

## Rules (unchanged)
- Write only: `read_trade_old.py`, the three output files, and files inside `jobs/trade_1901_1906_work/`.
- Python: `/home/jic823/miniforge3/bin/python`, standard library only. No network.
- Never correct a figure or a spelling. Same output columns. Every emitted figure must come from its source row.
- Prefer withholding a row to emitting it with a wrong country, column or label.

## Defects to fix, in order of importance
A. **Figure on the wrong country** (samples 51, 54; bb1902). These are the worst kind of error. Find how the country
   and figure became misaligned (51: value 87 belongs to Mauritius, British India is 900, and "Yellow Metal" is not
   under "Tin—"; 54: the figure belongs to British India, Straits Settlements has only a yds. line). Find every other
   place in all six volumes where the same mechanism applies; fix or withhold. Report the count.
B. **Wrong column** (72, 90, 124, 125). Cinnamon exports print Ceylon produce in Plantation / Chips sub-columns: treat
   them as components of quantity_ceylon_produce (as you did for Black/Green tea), never as other produce. Tea
   Black/Green components must be assigned only where the table header prints Black and Green (bb1903:p687 does
   not). 90: a value was emitted as a quantity where both quantities are dashes.
C. **Missing heading level** (13, 14, 37 "Arms— Guns, double"; 45, 84 "Fruit, fresh— Grapes"; 46, 184 "Meat,
   frozen— …") and a truncated label (22 "Printing Materials"). Find the general cause; count affected rows.
D. **Units blank** where the page prints a unit or a ditto mark under one (10, 11, 100–103, 148, 151). Carry a unit
   down through ditto marks and from the article heading where the OCR supports it.
E. **Class/group** (76, 131, 132, 167, 168, 274; also 80, 81, 165, 166 "(8) Other" for "(3) Other"): lettered
   subgroups "(b)", "(c)" read as "(6)" or lost, and the "(3) Other" level missing; Pearls under "IV.—Bullion and
   Coin" given a "(3) Other" group that class does not have. Keep literal OCR numerals; fix the structure.
F. **Blank cell emitted as a dash** (121).
G. **1902 tea exports are missing from the output entirely** (the rows are in the skipped file). Find why and
   recover them if the OCR supports it; otherwise explain exactly what blocks it.

## Required evidence
- `jobs/trade_1901_1906_work/recheck3.tsv`: every one of the 279 sample rows, relocated by table_id + source row +
  measure, with the new values and a judgement against the checker's verdict.
- Rerun the two earlier rechecks (`audit_round2_first.py`, `audit_round2.py`) and list any row that got worse.
- `jobs/trade_1901_1906_work/README_round3.md`: for each of A–G what you changed, counts before → after across the
  whole output, what remains unfixed and why. Keep it under 150 lines.
- Stop when A–G are done or shown to be blocked. Do not start other improvements.
