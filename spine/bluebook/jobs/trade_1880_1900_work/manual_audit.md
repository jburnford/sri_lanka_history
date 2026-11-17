# Manual review of 30 source rows

Compared every emitted figure in each selected row with the supplied OCR table cells, its headers, and preceding article/country-group labels. This is a review of the supplied JSONL table rows, not a comparison against PDF images.

All 128 emitted figures in the final 30-row sample match their source figures and assignments. No source figure was changed.

The first review found a heading-only Tea row being mistaken for a class and therefore carrying the preceding article name. The reader now recognizes the article in the colon prefix even when its first row contains only units. The review also exposed monetary Total headers outside the OCR top-level Value span: these are included only when the currency grouping is established; otherwise the entire row is skipped. Both fixes were applied before the final sample review.

Examples: Butter joins `1092` and `0 17` into `1092 0 17` (1092.1518 cwt); duty `3277 | 4` becomes 3277.04. Umbrellas from French India restore an explicitly anchored country label and preserve `13\frac{9}{12}` as 13.75 dozen. The Provisions row in 1880 prints 160.5 and 25 cwt but total 175.5 cwt: all three printed quantities remain unchanged.

| Case | Volume | Flow | Table | Row | Figures | Result |
|---:|---|---|---|---:|---:|---|
| 1 | 1880 | import | bb1880:p499:t1 | 42 | 4 | matched |
| 2 | 1880 | import | bb1880:p504:t1 | 41 | 4 | matched |
| 3 | 1880 | import | bb1880:p510:t1 | 19 | 4 | matched |
| 4 | 1880 | import | bb1880:p515:t1 | 54 | 2 | matched |
| 5 | 1880 | import | bb1880:p520:t1 | 18 | 4 | matched |
| 6 | 1880 | export | bb1880:p527:t1 | 13 | 4 | matched |
| 7 | 1880 | export | bb1880:p528:t1 | 24 | 10 | matched |
| 8 | 1880 | export | bb1880:p531:t1 | 14 | 4 | matched |
| 9 | 1880 | export | bb1880:p535:t1 | 47 | 9 | matched |
| 10 | 1880 | export | bb1880:p537:t1 | 40 | 4 | matched |
| 11 | 1896 | import | bb1896:p528:t1 | 32 | 4 | matched |
| 12 | 1896 | import | bb1896:p534:t1 | 58 | 4 | matched |
| 13 | 1896 | import | bb1896:p550:t1 | 37 | 1 | matched |
| 14 | 1896 | import | bb1896:p561:t1 | 60 | 4 | matched |
| 15 | 1896 | import | bb1896:p568:t1 | 12 | 4 | matched |
| 16 | 1896 | export | bb1896:p574:t1 | 18 | 6 | matched |
| 17 | 1896 | export | bb1896:p579:t1 | 55 | 4 | matched |
| 18 | 1896 | export | bb1896:p585:t1 | 36 | 4 | matched |
| 19 | 1896 | export | bb1896:p592:t1 | 54 | 4 | matched |
| 20 | 1896 | export | bb1896:p598:t1 | 51 | 2 | matched |
| 21 | 1900 | import | bb1900:p571:t1 | 32 | 6 | matched |
| 22 | 1900 | import | bb1900:p579:t1 | 19 | 4 | matched |
| 23 | 1900 | import | bb1900:p593:t1 | 47 | 3 | matched |
| 24 | 1900 | import | bb1900:p607:t1 | 38 | 3 | matched |
| 25 | 1900 | import | bb1900:p619:t1 | 16 | 4 | matched |
| 26 | 1900 | export | bb1900:p628:t1 | 37 | 6 | matched |
| 27 | 1900 | export | bb1900:p634:t1 | 44 | 4 | matched |
| 28 | 1900 | export | bb1900:p645:t1 | 4 | 4 | matched |
| 29 | 1900 | export | bb1900:p650:t1 | 24 | 4 | matched |
| 30 | 1900 | export | bb1900:p653:t1 | 31 | 4 | matched |
