# Ceylon Blue Books trade ledgers

Built from the supplied OCR table JSONL files with standard-library Python. Printed spellings and numerical cells are preserved. No source images or outside sources were used.

Completed the extraction and checks for 1925 first, followed by 1924, 1926 and 1928. Each of these four volumes has 111 article-ledger tables. These are completed reader passes with the unresolved rows and discrepancies listed below.

1930, 1933 and 1934 were inspected. Their supplied tables contain trade summaries, but searches across every cell found neither the import quantity/home-consumption headers nor the export produce/manufactures headers. Article-country extraction for those volumes could not be completed from these inputs.

## Coverage

| Volume | Flow | Output measure rows | Country measure rows | Articles with Total | All measures agree | Agreement |
|---|---|---:|---:|---:|---:|---:|
| 1925 | import | 12,250 | 10,079 | 487 | 407 | 83.6% |
| 1925 | export | 9,525 | 7,872 | 161 | 137 | 85.1% |
| 1924 | import | 11,460 | 9,479 | 453 | 369 | 81.5% |
| 1924 | export | 9,783 | 8,112 | 161 | 136 | 84.5% |
| 1926 | import | 12,464 | 10,255 | 511 | 402 | 78.7% |
| 1926 | export | 9,459 | 7,839 | 164 | 140 | 85.4% |
| 1928 | import | 13,066 | 10,835 | 523 | 437 | 83.6% |
| 1928 | export | 10,038 | 8,352 | 167 | 130 | 77.8% |
| 1930 | No article/country ledgers present in supplied tables | 0 | 0 | 0 | 0 | n/a |
| 1933 | No article/country ledgers present in supplied tables | 0 | 0 | 0 | 0 | n/a |
| 1934 | No article/country ledgers present in supplied tables | 0 | 0 | 0 | 0 | n/a |

## Method and limitations

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
| 1925 | 212 | 17 | 4 |
| 1924 | 293 | 21 | 4 |
| 1926 | 237 | 23 | 1 |
| 1928 | 306 | 21 | 2 |

## Ten largest unexplained article differences

Articles are ranked by their largest absolute measure discrepancy. Quantities and rupees have different units, so this ranking is a numerical diagnostic.

| Volume | Flow | Article | Total table | Measure | Unit | Printed total | Country sum | Difference |
|---|---|---|---|---|---|---:|---:|---:|
| 1925 | export | Cacao (raw)— | bb1925:p232:t1, row 47 | quantity_total | lb. | 77704253 | 7704253 | -70000000 |
| 1926 | export | Rubber— | bb1926:p260:t1, row 53 | quantity_ceylon_produce | lb. | 131840505 | 95114525 | -36725980 |
| 1924 | export | Coconuts, fresh— | bb1924:p321:t1, row 22 | quantity_ceylon_produce | No. | 20121041 | 29121041 | 9000000 |
| 1928 | import | Grain (rice, not in the husk)— | bb1928:p197:t1, row 25 | value_total_rs |  | 108150832 | 103150432 | -5000400 |
| 1924 | export | Textile manufactures not elsewhere specified— | bb1924:p352:t1, row 22 | quantity_total | No. | 4000504 | 0 | -4000504 |
| 1926 | import | Coal— | bb1926:p290:t1, row 8 | value_total_rs |  | 2657072 | 0 | -2657072 |
| 1926 | import | Salt, other— | bb1926:p191:t1, row 37 | value_total_rs |  | 1758422 | 3517149 | 1758727 |
| 1926 | import | Cinematograph films— | bb1926:p230:t1, row 21 | quantity_total | lin.ft. | 317462 | 2060062 | 1742600 |
| 1924 | import | Vegetables, raw, potatoes— | bb1924:p271:t1, row 21 | value_total_rs |  | 1731741 | 581741 | -1150000 |
| 1928 | import | Earthenware and stoneware— | bb1928:p214:t1, row 66 | value_total_rs |  | 162095 | 1218719 | 1056624 |

## Rebuild and verify

```sh
/home/jic823/miniforge3/bin/python jobs/trade_work/read_trade.py 1925 1924 1926 1928 1930 1933 1934
/home/jic823/miniforge3/bin/python jobs/trade_work/verify_trade.py
```

Verification checks the requested header, literal source-number provenance for every normalized figure, country labels, resolved units, block continuity and selected 1925 regressions. Arithmetic verification remains limited to the supplied OCR.