# Main exports in the Ceylon Blue Books, 1880–1900

Read all 18 requested export ledgers in the order 1896, 1891, 1893, then the remaining volumes chronologically. The tables below cover 145 blocks and all 108 commodity-volume pairs. Source rows are zero-based and page numbers in these notes are PDF pages.

## Block status

R = read. P = partly read. Multiple letters follow the order of blocks in the ledger. All six commodities were located in every volume, with two doubtful article identifications noted below.

| Volume | Tea | Coffee | Cinchona | Cinnamon | Coconut oil | Plumbago |
|---|---|---|---|---|---|---|
| 1880 | R | R/R | R | R | P | P |
| 1881 | R | R/R/R | R | R | P | R |
| 1882 | R | R/R/R | P | P | R | R |
| 1883 | P | R/R/R | R | R | R | R |
| 1885 | R | R/P/R | R | P | R | P |
| 1886 | R | P/R/R | R | R | R | R |
| 1887 | R | R/R/R | R | R | R | R |
| 1889b | R | R/R/R | R | R | R | R |
| 1890 | R | R/P/R | R | P | P | R |
| 1891 | R | P/R/R | P | P | R | P |
| 1892 | P | R/R/R | P | P | R | R |
| 1893 | R | R/R/R | R | R | R | R |
| 1894 | R | R/R/P | R | R | R | P |
| 1896 | R | R/R/R | R | R | R | R |
| 1897 | R | R/R/R | R | P | R | R |
| 1898 | R | R/R/R | P | R | P | R |
| 1899 | P | R/R/R | R | R/R | P | R |
| 1900 | R | R/R/R | R | P/R | R | P |

## Figures and rule reader

`main_exports.tsv` contains **8,721 records**. There are 8,367 clear, 147 doubtful, and 207 unreadable. The rule reader agrees on 4,807 and differs on 322. It supplied no matching reading for 3,592, including 3,291 clear figures. Comparison uses the same source row, destination or total, measure and figure, with dot leaders ignored. A move between produce categories also counts as a difference.

- **1897 Plumbago, PDF 574 row 15.** The rule reader carried forward Tea Lead. The cwt. and royalty labels start the plumbago block one row above its article label. The UK line gives `170180 1 12` and `1646494 95`.
- **1885 Cinnamon, PDF 527 row 34.** The rule reader took repeated `28` quantity cells as Rs. 28.28 of colony produce and put `14 0` under other produce. The currency cells give Rs. 14.00 in the colony and total columns.
- **1887 Cinchona, PDF 478 rows 32–40.** The first line labels the second weight column `Br. and Twig. lb.`. The rule reader treated that component as other produce. The US row has 84,737 lb. and Rs. 1,694.74 in the branch and twig columns.

## Headings and pages to check first

- **1896 PDFs 575, 579 and 593.** The Coffee parent is on 575 row 3, and the Native and Plantation figures change position within the page. Tea is in the source header at 579 row 2. Cocoanut on 593 row 39 belongs to Oil, printed with Cinnamon at row 2. The same Oil sequence establishes the coconut sub-lines in other volumes. Each recovered parent has its source in `blocks.tsv`.
- **1896 PDF 597 rows 5–6 and 1886 PDF 486 rows 14–15.** The country list and figures are packed into single cells. The printed order and the counts of destination names and figure groups anchor the individual entries.
- **1892 PDF 564 rows 23–60 and 1880 PDF 534 rows 29–43.** Overlapping or displaced destination labels leave 132 Tea records and 40 coconut oil records unreadable. Their source digits are retained with the visible labels in the notes.
- **1891 PDF 525 rows 4–13.** The two Plumbago weight columns can be read. A single currency pair survives before royalty, with uncertain placement in the value columns.
- **1882 PDF 495 rows 4–13 and 1892 PDF 546 rows 54–61.** The source says `Peppermint` in the usual cinnamon position between Chanks and Clocks, and `Cinnamon Bark` in a separate branch-and-trunk bark block in the usual cinchona position. Both article identifications remain doubtful.
- **1890 PDF 517 rows 37–38, 1894 PDF 550 rows 19–20 and 1898 PDF 591 rows 34–35.** The UK lines for cinnamon, plumbago and cinchona retain unit labels where quantity digits are missing. Other unreadable cells include incomplete or out-of-range cwt. components and merged cinnamon weights with a missing component boundary.
- **1899 PDFs 588–589.** Tea crosses the page break under `Tea—contd.`. PDF 604 row 15 adds three drums after the China quantity. The drum assignment is doubtful.
- **1893 PDF 577 rows 3 and 18, and PDF 581 row 17.** Native coffee has different colony and total currency figures. The Tea value for Australia is `9374122 95` in both cells. The digits are retained in each case.

Coffee seed lines belong to the Seeds heading, visible at 1896 PDF 595 row 38 and 1897 PDF 586 row 30. The coffee blocks cover the bean grades. Cinnamon totals retain chips when the ledger includes them, along with the separately printed component where legible.

## Sum checks

`blocks.tsv` lists the cited ranges, distinct destinations with at least one reading, country sums, and printed article totals. The checks use exact arithmetic from the printed strings, including doubtful readings. They use country total cells when present and available components when a row has no total cell. When the ledger prints multiple units or named quantity components in the total columns, the result is keyed by unit. Cwt. is displayed to four decimal places. Split source cells are joined by ` | ` in `value_as_printed`.

A `no_total` result means the article total is absent or unreadable. The sum checks were made after transcription. The checker validates source cells, table and row references, numbers, block arithmetic and commodity-volume coverage.

```sh
python jobs/main_exports_1880_1900_work/check.py
```
