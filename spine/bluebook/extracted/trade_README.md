# Ceylon Blue Books trade ledgers

Built from the supplied OCR table JSONL files with standard-library Python. Printed spellings and numerical cells are preserved. No source images or outside sources were used.

The first pass read 1925, 1924, 1926 and 1928 (111 article-ledger tables each). On 17 November 2026 the same reader was extended to every volume from 1907 to 1928 that prints the ledgers in this layout (two blocks of article and country rows for imports; one block with produce, other and total columns for exports). Three things differ before 1923 and are handled in the reader: an article's total is a row of figures with no label (read as the total, with a note); the country group is headed British Colonies up to 1916; and the states of Australia and provinces of South Africa sit under a regional sub-heading, kept in note. Up to 1916 the classes are headed in capitals without the word CLASS. Rows already extracted for the first four volumes are unchanged.

Volumes from 1929 on print trade summaries by class and country but no article-by-country ledgers. Volumes before 1907 print the ledgers in an older single-block layout that this reader does not read (1880-1906), or in sterling with quantities in hundredweights, quarters and pounds (1863-1877); they are not extracted.

## Coverage

| Volume | Flow | Output measure rows | Country measure rows | Articles with Total | All measures agree | Agreement |
|---|---|---:|---:|---:|---:|---:|
| 1907 | import | 9,930 | 8,736 | 392 | 298 | 76.0% |
| 1907 | export | 10,158 | 9,054 | 182 | 151 | 83.0% |
| 1908 | import | 7,236 | 6,228 | 306 | 270 | 88.2% |
| 1908 | export | 11,058 | 9,930 | 187 | 164 | 87.7% |
| 1909 | import | 5,922 | 5,046 | 252 | 202 | 80.2% |
| 1909 | export | 10,340 | 9,235 | 182 | 152 | 83.5% |
| 1910 | import | 18,438 | 15,999 | 749 | 628 | 83.8% |
| 1910 | export | 20,238 | 18,072 | 358 | 308 | 86.0% |
| 1911 | import | 5,886 | 5,172 | 237 | 212 | 89.5% |
| 1911 | export | 9,828 | 8,790 | 169 | 144 | 85.2% |
| 1912 | import | 10,269 | 9,108 | 376 | 315 | 83.8% |
| 1912 | export | 10,056 | 8,988 | 178 | 144 | 80.9% |
| 1913 | import | 9,489 | 8,292 | 364 | 292 | 80.2% |
| 1913 | export | 10,092 | 8,994 | 182 | 159 | 87.4% |
| 1914 | import | 10,644 | 9,405 | 401 | 354 | 88.3% |
| 1914 | export | 10,176 | 9,096 | 178 | 154 | 86.5% |
| 1915 | import | 10,914 | 9,624 | 414 | 357 | 86.2% |
| 1915 | export | 9,924 | 8,838 | 180 | 151 | 83.9% |
| 1916 | import | 10,553 | 9,240 | 410 | 328 | 80.0% |
| 1916 | export | 9,858 | 8,784 | 178 | 150 | 84.3% |
| 1917 | import | 6,693 | 5,694 | 330 | 312 | 94.5% |
| 1917 | export | 5,820 | 4,962 | 140 | 118 | 84.3% |
| 1918 | import | 5,862 | 4,881 | 320 | 286 | 89.4% |
| 1918 | export | 5,214 | 4,422 | 131 | 112 | 85.5% |
| 1919 | import | 6,726 | 5,691 | 338 | 295 | 87.3% |
| 1919 | export | 6,588 | 5,814 | 127 | 108 | 85.0% |
| 1920 | import | 7,779 | 6,459 | 337 | 259 | 76.9% |
| 1920 | export | 7,224 | 6,264 | 128 | 109 | 85.2% |
| 1921 | import | 14,545 | 11,744 | 709 | 561 | 79.1% |
| 1921 | export | 12,351 | 10,515 | 259 | 216 | 83.4% |
| 1922 | import | 9,958 | 8,614 | 422 | 356 | 84.4% |
| 1922 | export | 8,277 | 7,257 | 158 | 147 | 93.0% |
| 1923 | import | 11,283 | 9,212 | 473 | 388 | 82.0% |
| 1923 | export | 9,393 | 7,701 | 167 | 145 | 86.8% |
| 1924 | import | 11,460 | 9,479 | 453 | 369 | 81.5% |
| 1924 | export | 9,783 | 8,112 | 161 | 136 | 84.5% |
| 1925 | import | 12,250 | 10,079 | 487 | 407 | 83.6% |
| 1925 | export | 9,525 | 7,872 | 161 | 137 | 85.1% |
| 1926 | import | 12,464 | 10,255 | 511 | 402 | 78.7% |
| 1926 | export | 9,459 | 7,839 | 164 | 140 | 85.4% |
| 1927 | import | 12,924 | 10,738 | 507 | 416 | 82.1% |
| 1927 | export | 9,534 | 7,869 | 174 | 142 | 81.6% |
| 1928 | import | 13,066 | 10,835 | 523 | 437 | 83.6% |
| 1928 | export | 10,038 | 8,352 | 167 | 130 | 77.8% |

## Check against the page images, 17 November 2026

A reader who had not seen the program compared 312 rows on 39 pages of 13 volumes (1907-1923 and 1927) with the scans: 297 were right in article, country, measure and value (95%), and no figure was misread. The 15 errors were structural and fell into six patterns; five are now handled in the reader (printed "Total for Australia" and "Grand Total" rows read as countries; "Br. Col." and "For. Coun." read as article headings; a running head in capitals read as an article where an article continues; coir fibre printed in Bristle and Mattress columns; a page on which the OCR lost a figure column, now skipped whole). The sixth is not repaired: after a country label printed on two lines the OCR table carries each figure one row low, so countries later in that article get the figures of the country above. Where the article ends in two unlabelled rows and the arithmetic proves the first is not a total, that row is `unassigned` and the country rows of the article carry a note; elsewhere such an article shows only as a total that does not agree. A figure in an article whose total does not agree should be checked on the page before it is quoted. The sample has not been read again since these fixes.

## Method and limitations

- Tea exports up to 1918 are printed with two quantity columns of Ceylon produce, Black and Green. Both are read as quantity_ceylon_produce, with the component (black or green) in note, as cinnamon quills and chips are. The OCR keeps six of the seven printed figures and varies in which it drops, so each row is assigned by its own arithmetic (black + green [+ other] = total); a row that fits no reading is skipped. The 1907 volume lost the United Kingdom figures for tea in the OCR, and one 1917 page is merged with its neighbour, so tea is incomplete for those two years; the totals checks show it.
- Printed period: `trade_periods.tsv` (from `trade_periods.py`) gives the period each ledger table covers. The 1910 volume has two sets (six months ended June 1910; twelve months ended June 1911) and the 1921 volume one for each half-year. `year_volume` is not the period.
- Import blocks are read down the left side, then down the right side. Class, group, article, country group and unit state carry across blocks and pages. Government Stores imports restart state and carry a scope note.
- Source row indexes in the ledger notes, skipped file and checks file are zero-based. Import block locations are recorded in notes and skip reasons. The audit of running totals, reconstructed rows and continuation headings is in `jobs/trade_work/running_totals_and_continuations.tsv`. Article-level check results are in `jobs/trade_work/article_audit.tsv`.
- Every supported printed measure cell is emitted, including blank and dash cells with an empty normalized value. Ditto units are resolved and noted. Omitted units inherit the previous unit and carry a note.
- Article checks sum country rows only. Subtotals and running totals are excluded. A Total is checked against the cumulative country rows above it in its article. Thus an intermediate bare Total uses the countries preceding that row. Later Totals use the larger cumulative sum. Empty country figures contribute zero to arithmetic and retain empty normalized values in the ledger. Empty total cells have no numerical assertion to compare.
- An article agrees only when every readable Total figure agrees exactly and every Total row is interpretable. Unreadable Total rows and Total rows with no figures count as failures in the agreement denominator. The checks file contains numerical mismatches and explicit uncheckable-total entries.
- Explicit paired units become separate quantity rows with their respective units. Unit punctuation is ignored for arithmetic grouping while the ledger retains each printed spelling. Cinnamon quills and chips both use the Ceylon-produce measures, with a component note and separate component checks.
- Repeated continuation headings retain the initial printed article label. The continuation label is retained in notes and the audit. A missing leaf article heading leaves the article field empty and records the printed group. Footnote symbols next to a country are retained in the country field.
- A complete row collapsed into its label cell, a shifted figure duplicated in that label, or stacked country rows are reconstructed only when literal tokens identify the figures. A full-width repeated leaf heading in a continuing right-hand import article is treated as an expanded OCR span and logged in the audit.
- Ambiguous figures, shifted figures without an attributable country, unresolved two-unit rows, and unsupported layouts go to the skipped file. The 1925 machinery table bb1925:p200:t1 has a truncated right block. Its readable total quantities are retained with an omitted-column note. The 1924 machinery table bb1924:p288:t1 similarly retains the two explicit quantity columns. Column meanings in bb1926:p212:t1 remain ambiguous and its data are skipped.
- Figures such as the 1925 cacao Total of 77704253 and the 1926 rubber United Kingdom Ceylon-produce quantity of 4080664 are retained literally. They cause large arithmetic discrepancies in the supplied OCR. These discrepancies remain unresolved. Other failures reflect skipped rows, misplaced headings or figures, intermediate Totals, or source arithmetic. No numerical OCR corrections are made.

## Skipped rows and uncheckable articles

| Volume | Skipped source block rows | Import articles with uncheckable Totals | Export articles with uncheckable Totals |
|---|---:|---:|---:|
| 1907 | 1172 | 5 | 8 |
| 1908 | 2374 | 8 | 7 |
| 1909 | 3310 | 10 | 11 |
| 1910 | 2787 | 33 | 24 |
| 1911 | 3432 | 4 | 4 |
| 1912 | 579 | 4 | 19 |
| 1913 | 334 | 5 | 7 |
| 1914 | 274 | 6 | 15 |
| 1915 | 197 | 9 | 15 |
| 1916 | 438 | 8 | 13 |
| 1917 | 243 | 0 | 4 |
| 1918 | 183 | 1 | 0 |
| 1919 | 219 | 0 | 0 |
| 1920 | 448 | 0 | 0 |
| 1921 | 745 | 3 | 0 |
| 1922 | 193 | 0 | 1 |
| 1923 | 276 | 32 | 4 |
| 1924 | 293 | 21 | 4 |
| 1925 | 212 | 17 | 4 |
| 1926 | 237 | 23 | 1 |
| 1927 | 271 | 24 | 3 |
| 1928 | 306 | 21 | 2 |

## Ten largest unexplained article differences

Articles are ranked by their largest absolute measure discrepancy. Quantities and rupees have different units, so this ranking is a numerical diagnostic.

| Volume | Flow | Article | Total table | Measure | Unit | Printed total | Country sum | Difference |
|---|---|---|---|---|---|---:|---:|---:|
| 1928 | export | Tea— | bb1928:p263:t1, row 60 | quantity_ceylon_produce | lb. | 234890761 | 40227487 | -194663274 |
| 1913 | export | Tea— | bb1913:p889:t1, row 63 | quantity_total | lb. | 8896386 | 182614244 | 173717858 |
| 1923 | export | Tea— | bb1923:p305:t1, row 69 | quantity_ceylon_produce | lb. | 79630540 | 179630540 | 100000000 |
| 1916 | export | Tea— | bb1916:p899:t1, row 61 | value_total_rs |  | 105266462 | 34858645 | -70407817 |
| 1925 | export | Cacao (raw)— | bb1925:p232:t1, row 47 | quantity_total | lb. | 77704253 | 7704253 | -70000000 |
| 1910 | export | Tea— | bb1910:p842:t1, row 63 | value_total_rs |  | 84136607 | 30432917 | -53703690 |
| 1913 | import | Grain, rice— | bb1913:p846:t1, row 15 | value_total_rs |  | 9882 | 50274441 | 50264559 |
| 1926 | export | Rubber— | bb1926:p260:t1, row 53 | quantity_ceylon_produce | lb. | 131840505 | 95114525 | -36725980 |
| 1910 | export | Tea— | bb1910:p744:t1, row 64 | value_total_rs |  | 40451467 | 13418301 | -27033166 |
| 1918 | import | 8 | bb1918:p225:t1, row 19 | value_total_rs |  | 12363837 | 0 | -12363837 |

## Rebuild and verify

```sh
/home/jic823/miniforge3/bin/python jobs/trade_work/read_trade.py 1907 1908 1909 1910 1911 1912 1913 1914 1915 1916 1917 1918 1919 1920 1921 1922 1923 1924 1925 1926 1927 1928
/home/jic823/miniforge3/bin/python jobs/trade_work/verify_trade.py
```

Verification checks the requested header, literal source-number provenance for every normalized figure, country labels, resolved units, block continuity and selected 1925 regressions. Arithmetic verification remains limited to the supplied OCR.