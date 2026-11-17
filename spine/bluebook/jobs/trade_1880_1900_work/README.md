# Ceylon Blue Books trade ledgers, 1880–1900

Completed the reader pass for all 18 requested volumes, in the requested order: 1896, 1880, 1881, 1882, 1883, 1885, 1886, 1887, 1889b, 1890, 1891, 1892, 1893, 1894, 1897, 1898, 1899, 1900. 1896 was implemented, inspected, and independently value-verified first. No requested volume was omitted. Extraction is partial in every volume: unreadable or ambiguous rows remain in the skipped file; no volume is claimed to be completely deciphered.

Final output: **95,312 printed figures**, **18,639 skipped source rows**, and **4,552 article/measure discrepancies**. The reader recognized all 997 ledger tables identifiable by their import/export country headers. Shipping tables and non-ledger recapitulations are excluded.

## Files and reproduction

- `extracted/trade_1880_1900.tsv.gz`: requested figure schema, deterministic gzip.
- `extracted/trade_1880_1900_skipped.tsv`: original, unmodified cell arrays with zero-based row indexes and reasons.
- `extracted/trade_1880_1900_checks.tsv`: exact discrepancies; the sign is printed total minus readable country sum.
- `jobs/trade_1880_1900_work/read_trade.py`: independent reader; does not import or modify `read_trade_old.py`.
- `verify_values.py`, `verification.json`: independent value re-parser and results.
- `verify_structure.py`, `structure_verification.json`: headers, provenance, disjoint emitted/skipped rows, summary counts, ledger-header coverage, and exact difference arithmetic.
- `manual_audit.md`, `manual_audit_cases.json`, `manual_audit_display.txt`: the 30-row review with source cells and emitted observations.
- `layouts_<volume>.json`: detected schemas, errors, and in-page schema changes. `skipped_<volume>.tsv` and `ledger_<volume>.txt` make local review easier.

Run from the repository root using only the standard library:

```sh
/home/jic823/miniforge3/bin/python jobs/trade_1880_1900_work/read_trade.py
/home/jic823/miniforge3/bin/python jobs/trade_1880_1900_work/verify_values.py
/home/jic823/miniforge3/bin/python jobs/trade_1880_1900_work/verify_structure.py
```

The reader accepts optional volume keys, e.g. `1896`; that rewrites the three combined output files with only those volumes. The final files contain all 18 volumes. No network was used. All files created or changed by this job are inside the work directory or the three authorized output paths.

## Layout variants and handling

1. **Import ledgers with 8 or 9 columns:** read quantity total, home consumption, rupees/cents value, and gross duty; ignore the rate and average price. Example: `bb1896:p529:t1`.
2. **Split or merged money:** join a rupee cell and a one- or two-digit cent cell, or parse an explicit merged rupee/cent figure. A cent digit `4` stays four cents, never forty. Explicit currency labels and clearly delimited dates are removed from the numeric text with a note when needed. Incomplete money is skipped.
3. **Separate average-price columns:** respect the header positions, e.g. `bb1896:p560:t1`. A changed quantity layout that would make the average/duty boundary uncertain is skipped. Average prices and export duties/royalties/Tea Fund figures are excluded.
4. **Split cwt/qr/lb:** join a cwt cell and its `qr lb` cell when the quantity header establishes their common measure; preserve fractions in pounds. Example: Butter at `bb1896:p528:t1`. Convert to decimal cwt with four places; note `cwt qr lb`.
5. **Several units for one measure:** output a separate figure for each explicitly established unit, such as packages plus cwt or gallons plus gills. A merged multi-unit cell is accepted only if its unit order gives one unique partition. Example: Marine Stores at `bb1896:p548:t1`, and the three explicit quantity units at `bb1880:p528:t1` row 24. Different units are never added.
6. **Expanded repeated spans:** collapse identical complete repeated quantity cells to one figure. Equal isolated component digits are not sufficient evidence of a repeated span.
7. **Unit-only rows and ditto:** carry explicit article/header units into subsequent rows and record the carry in the note. Prefixes and suffixes, Unicode fractions, and OCR LaTeX fractions are supported. Finite decimal quantities are exact; a recurring fraction is rounded to 12 places with an explicit note while checks retain the exact rational number.
8. **Article on a row of its own:** keep it for the following countries. A prefix such as `Articles of food and drink : Tea ...` is split into the printed heading and article, including when that row only contains units. Repeated article cells do not start new articles.
9. **Literal classes and groups:** retain the nearest recognized printed headings; split explicit colon prefixes and numbered class/group prefixes. Leading-dash subarticle labels remain literal. No missing parent article name is reconstructed by alphabetical inference.
10. **Country label shifts:** repair only a country explicitly anchored in column 0 or 2, or an explicit country/article exchange. Restoring a missing first cell requires an empty trailing cell. Every repair is noted. Group labels, including OCR spelling variants, remain as printed; the United Kingdom has an empty group.
11. **Country-group rows with figures or several countries in one cell:** skip them, because a country versus group total or shifted country cannot be assigned safely. No country is inferred from an amount or a balancing sum.
12. **Export Value/Total header drift:** use explicit produce/other/total labels and currency cells. A Total header outside the top-level Value span is included only if its own figure or rupee/cent grouping can be read. For example, many `bb1896:p575:t1` rows merge money into a purported cent column with no reliable other-produce/total distinction; these rows are skipped, while its first United Kingdom Coffee, Liberian row is readable.
13. **Header spelling/punctuation variants:** accept `Article`, `Articles`, colons, periods, leading bullets, and `home-consumption`, while still requiring the import/export country heading. Actual ledger widths range from 8 to 21 columns.
14. **Unsupported or malformed compounds:** skip tons with unidentified component columns, multiple unlabelled numbers, repeated/missing unit structures, invalid cwt components, invalid cents, and supplementary `&` rows whose relationship to a preceding row is uncertain. Digits are never corrected and amounts are never used to choose a layout.

No explicit subtotal-labelled rows were found in the ledger label columns; accepted observations are `country` or `article_total`. Missing/dash cells produce no figure observation. Numeric zero figures are retained.

## Exact checks and count definitions

Checks re-sum the readable country rows for each individual article instance. Cwt components are compared in pounds; money is compared in cents. Fractions use `Fraction` throughout, so the four-place cwt output never enters reconciliation. Other quantities stay in their printed units. An absent figure contributes zero to the check, without creating an output observation.

For a single unit, `printed_total`, `country_sum`, and `difference` are normalized scalar values (pounds, cents, or the original quantity unit). When a measure has several units, those fields are JSON objects mapping each unit to its exact amount; cwt keys are labelled `lb`. This preserves one check row per article and measure without combining incompatible units. Nonterminating exact sums are written as rational strings.

A discrepancy can reflect missing skipped country rows, OCR mistakes, or a source inconsistency; it does not by itself establish a printing error. `articles_with_total` counts article instances with a readable total row. `articles_all_measures_agree` requires agreement across every unit/measure and no skipped rows within that article. `rows_skipped` also includes ambiguous label/context rows; it is a count of source rows, not figures.

## Verification and manual review

The independent verifier re-parsed all **95,312 values** with **zero errors**: 43,381 money values, 15,115 cwt/qr/lb values, and 36,816 other quantities. It also checked that the numeric tokens in every `value_as_printed` occur unchanged in the cited original source row. All three output headers are exact, emitted and skipped rows do not overlap, no identifiable ledger header was missed, and all 4,552 check differences satisfy exact arithmetic.

The final eye review covers **30 source rows, 10 each from 1880, 1896, and 1900**, five imports and five exports per volume, spanning their ledgers. All **128 figures** in that sample match the source cells, headers, and label context. See `manual_audit.md` for every table and row. The earlier Tea article-carry error was corrected and unresolved export Total groupings now cause a skip. The review also retained visible source inconsistencies, such as the 1880 Provisions components and total, without alteration.

The 1896 Confectionery example (`bb1896:p529:t1`, rows 3–11) reconciles exactly in both quantities, value, and duty. The first United Kingdom Coffee, Liberian row (`bb1896:p575:t1` row 3) joins `419 | 1 11` to 419.3482 cwt and reads value 5032.18 rupees.

## What could not be read

All requested volumes have partial omissions. The skipped file preserves all **18,639 omitted rows** and their specific reasons. Common reason families are shown below; money failures often include the offending cells in the reason, so they are divided among many distinct reason strings.

| Rows | Reason |
|---:|---|
| 3,423 | figures on a country-group heading; specific country/total cannot be assigned |
| 1,796 | cwt quantity does not have cwt, qr and lb |
| 1,483 | figures after the article total without a new article label |
| 1,298 | quantity unit not explicitly established |
| 914 | country unreadable, multiple country rows merged, or shifted numeric label |
| 764 | merged multiple-unit quantity cannot be partitioned uniquely |
| 292 | unlabelled figures without preceding readable country figures; country versus total ambiguous |
| 251 | multiple country/group labels in the two label columns |
| 246 | supplementary quantity beginning with &: association with preceding printed row is ambiguous |
| 210 | incomplete or ambiguous rupees/cents: ['0'] |
| 146 | not an unambiguous number: '1 —' |
| 141 | changed quantity layout across separate average-price columns cannot be assigned safely |
| 123 | export header quantity/value boundary is ambiguous |
| 112 | incomplete or ambiguous rupees/cents: ['0', ''] |

## Ledger inventory

| Volume | Import tables | Export tables | Column widths | Tables with output |
|---|---:|---:|---|---:|
| 1896 | 43 | 28 | 8, 9, 10, 11, 12, 13, 14, 15, 16 | 60 |
| 1880 | 22 | 15 | 8, 9, 10, 11, 12, 13, 14, 15 | 35 |
| 1881 | 21 | 17 | 8, 9, 10, 11, 12, 13, 15, 16 | 36 |
| 1882 | 20 | 16 | 8, 9, 10, 11, 12, 13, 14, 15 | 32 |
| 1883 | 23 | 19 | 8, 9, 10, 11, 12, 13, 14, 16, 19 | 34 |
| 1885 | 23 | 20 | 8, 9, 10, 11, 12, 13, 15, 17, 19 | 37 |
| 1886 | 26 | 21 | 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | 40 |
| 1887 | 29 | 21 | 8, 9, 10, 11, 12, 13, 14, 16, 17, 18 | 47 |
| 1889b | 30 | 23 | 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20 | 50 |
| 1890 | 29 | 23 | 8, 9, 10, 11, 12, 13, 14, 15, 16, 19 | 48 |
| 1891 | 26 | 22 | 8, 9, 10, 11, 12, 13, 14, 15, 16 | 44 |
| 1892 | 30 | 24 | 8, 9, 10, 11, 12, 13, 14, 15, 16, 21 | 48 |
| 1893 | 42 | 27 | 8, 9, 10, 11, 12, 13, 15 | 67 |
| 1894 | 40 | 26 | 8, 9, 10, 11, 12, 13, 14, 16 | 59 |
| 1897 | 41 | 26 | 8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20 | 59 |
| 1898 | 42 | 27 | 8, 9, 10, 11, 12, 13, 14, 15, 16, 18 | 64 |
| 1899 | 44 | 29 | 8, 9, 10, 11, 12, 13, 14, 15, 17, 21 | 65 |
| 1900 | 53 | 29 | 8, 9, 10, 11, 12, 16 | 65 |

## Requested per-volume and flow counts

| Volume | Flow | Figures written | Articles with total | Every measure agrees | Rows skipped |
|---|---|---:|---:|---:|---:|
| 1896 | import | 4,173 | 131 | 62 | 719 |
| 1896 | export | 1,634 | 40 | 25 | 683 |
| 1880 | import | 2,004 | 75 | 11 | 462 |
| 1880 | export | 1,093 | 18 | 11 | 383 |
| 1881 | import | 2,058 | 70 | 22 | 372 |
| 1881 | export | 1,475 | 34 | 13 | 358 |
| 1882 | import | 2,570 | 84 | 24 | 312 |
| 1882 | export | 1,243 | 33 | 17 | 422 |
| 1883 | import | 2,194 | 59 | 17 | 437 |
| 1883 | export | 1,172 | 25 | 14 | 495 |
| 1885 | import | 2,309 | 69 | 25 | 438 |
| 1885 | export | 1,695 | 51 | 27 | 493 |
| 1886 | import | 2,557 | 74 | 27 | 591 |
| 1886 | export | 2,082 | 62 | 32 | 419 |
| 1887 | import | 2,982 | 73 | 18 | 561 |
| 1887 | export | 2,289 | 66 | 38 | 415 |
| 1889b | import | 3,076 | 77 | 26 | 631 |
| 1889b | export | 2,530 | 76 | 41 | 424 |
| 1890 | import | 2,482 | 64 | 19 | 539 |
| 1890 | export | 2,294 | 56 | 31 | 384 |
| 1891 | import | 2,608 | 83 | 15 | 484 |
| 1891 | export | 1,736 | 46 | 26 | 510 |
| 1892 | import | 3,296 | 91 | 20 | 536 |
| 1892 | export | 1,809 | 55 | 28 | 591 |
| 1893 | import | 4,743 | 173 | 94 | 382 |
| 1893 | export | 3,621 | 118 | 78 | 255 |
| 1894 | import | 4,040 | 132 | 69 | 614 |
| 1894 | export | 2,276 | 79 | 37 | 448 |
| 1897 | import | 3,117 | 97 | 46 | 801 |
| 1897 | export | 2,270 | 72 | 37 | 540 |
| 1898 | import | 3,448 | 101 | 35 | 815 |
| 1898 | export | 2,332 | 65 | 30 | 534 |
| 1899 | import | 3,844 | 111 | 66 | 794 |
| 1899 | export | 2,702 | 78 | 37 | 558 |
| 1900 | import | 6,709 | 193 | 109 | 681 |
| 1900 | export | 2,849 | 77 | 42 | 558 |
