# Statistical View of the Progress of Ceylon: extraction and audit

All 63 supplied volumes were searched locally, across every table, with `1896`, `1871`, and `1911` processed first in that order. No network requests or digit corrections were made. Only this work directory and the three requested output paths were written.

Final extract: **45,118 figure cells**, including 44,828 numeric values and 290 non-numeric literals, from **77 tables in 49 volumes**. There are 50 series and 2,461 observed (series, year) cells. 1,593/2,461 (64.7%) agree across every available printing. Restricting to cells printed in at least two volumes: **1,404/2,272 (61.8%)** agree.

## Files and reproduction

- `../../extracted/statistical_view.tsv.gz`: requested nine columns; one retained source cell per row. `year_volume` preserves the input key, including `1889b`, so the two 1889 parts remain distinct.
- `../../extracted/statistical_view_compare.tsv`: one row per observed series/year. Distinct values and their volume keys are represented as a JSON array, most common first. Numeric values compare by their exact parsed number; non-numeric cells compare by their exact literal text, with `kind: literal` distinguishing them.
- `../../extracted/statistical_view_skipped.tsv`: table, row, column, or section excluded and the reason. A `:no_table` identifier is a diagnostic placeholder, not an invented source table.
- `series_map.tsv`: every distinct full header mapped to each series, units/currencies, and first/last retained volume. The header list is JSON inside TSV to preserve slashes and punctuation.
- `volume_checks.tsv`, `series_checks.tsv`, `most_disagreement.tsv`, `eye_review.tsv`: machine-readable versions of the checks below. `series_checks.tsv` enumerates every covered year, including gaps and fiscal labels.
- `page_context.json`: local page headings and notes, including publisher currency conversions, approximation/coverage qualifications, and expenditure exclusions. These notes are source context; footnote financial schedules are not treated as independent columns of the annual table.
- `validation.json` and `validate.py`: independent source/cross-file checks, including 31 explicit sterling expressions. Run validation with the same Python interpreter after finalization.
- `alignment_audit.tsv`: evidence for every entire physical column withheld because of sustained vertical displacement.
- `extract.py`, `finalize.py`, `report.py`: standard-library-only reproducible pipeline. Run from this repository with `/home/jic823/miniforge3/bin/python jobs/statistical_view_work/extract.py`, then `finalize.py`, then `report.py` using the same interpreter. `extract.py --pilot` limits extraction to the three initial volumes. Finalization requires the full run.

## Reading rules and layout variants

1. **Full annual view, split over two pages.** The first block has the year at left, demographic/land/finance columns; the continuation has shipping and trade, with the year at right. Multi-row column headers are joined top to bottom with ` / `. Repeated span-expanded header cells are retained exactly, so `Population. / Population.` is intentional. Unit rows accidentally embedded beside the first data year are treated as units rather than figures. The header string remains the original top header, even when a later printed currency marker changes the unit; the series and note specify that change.
2. **Wide/overlapping tables.** 1866 merges both pages into a damaged 32-column grid. Other years have extra empty columns, repeated text spans, trailing fragments of the facing-page expenditure column, or shifted financial headers. Unsafe parts are withheld; separately aligned earlier row segments are retained. The 1885 financial columns can be read separately from its shifted demographic block. The 1871 demographic/financial table cannot be assigned safely and is withheld; its shipping/trade continuation is retained. 1894 continuation year labels run impossibly into the future and are withheld; no year labels are repaired.
3. **Missing or corrupted headings.** Some later pages omit parent shipping/import/export headings in the parsed table, even though subheadings survive. Those columns cannot supply a full safe header and are skipped. Blank, duplicate, or non-plain year labels are not inferred. A corrupted label such as `Bick.` is not silently mapped to births.
4. **Currency changes.** The local notes say the publisher converted historical money figures to pounds sterling, including amounts originally in rupees. Later reprints generally show sterling through data year 1888 and rupees from 1889. This is later than the currency change in the underlying accounts. We perform **no currency conversion**. `_gbp` and `_rupees` are separate series. A currency is assigned only from that volume’s printed column/marker or money-figures note. The 1891 note conflicts with its later figures, so the affected money cells are withheld. Where a later row has only a stale sterling header and no local change marker/note, it is withheld.
5. **Fiscal labels.** `1910-11` and `1911-12` remain strings, separate from calendar-year `1910` and `1911`. The printed 1910-11 financial period spans 18 months. Abridged tables can use a single year label for a period represented differently in the full table; they are not silently relabelled.
6. **Abridged view, 1924–1938.** Local page notes explicitly call this an abridgment of the earlier annual view. Measures run down rows and years across columns. In this orientation `column_as_printed` carries the printed measure hierarchy; the note identifies the transposed year header. Only directly labelled year columns with safe measure alignment are used. Continuations without year headers are withheld because their parsed column positions and sometimes their numbers of year columns change. 1925/1926 have displaced measure labels and 1935 merges several measures in each cell; those first tables are withheld. Some money rows in 1927/1932/1934 have lost their printed unit in the parsed data and are withheld, rather than assumed to be rupees. No figures are reconstructed from missing tables.
7. **Missing inputs.** The annual view is announced but has no parsed data table in several early volumes. 1889 part I has no matching series; part II is `1889b`. 1924 and 1931 announce the abridged first page but provide no parsed table there. These are input/OCR availability gaps, not evidence that the original printed books contained no series.
8. **Numbers and literals.** Properly grouped commas are removed for numeric parsing; decimal points and explicit currency prefixes are accepted. A clearly written £/s./d. expression becomes decimal pounds (up to 12 decimal places for recurring fractions), preserving the entire original expression. Footnote-marked numbers, malformed digit groupings, fractions and repeated-figure instructions are retained with empty `value`. Nothing is filled forward, stripped of footnote markers, corrected to a majority, or expanded from “figures repeated.” Blank cells, ellipses and dash-only absence markers are not figure observations. The mapping units `count implied` identify measures without an explicit printed unit.

## Alignment audit

A second pass withheld **151 physical columns** with strong evidence of vertical row displacement. For each series/year, a candidate reference number must occur in at least four distinct volumes. A column is withheld only when at least five of its values exactly match reference numbers at the same nonzero year offset, including at least three consecutive year labels, while disagreeing at their own labels. Offsets inspected: ±1, ±2 and ±10. The whole physical column is withheld, including apparently aligned portions; the reference is used only to identify unsafe alignment, never to replace or move a figure. Counts and literal examples are in `alignment_audit.tsv`. This conservative rule sacrifices some recoverable cells and cannot prove whether an isolated differing number is OCR or print.

Additional source-row inspection found horizontal shifts in the 1899 demographic rows for 1882–1888, the 1910 early land columns, and the 1929 abridged revenue group. Those segments are withheld. Systematically truncated UK-tonnage columns in 1915/1918 and incomplete facing-page expenditure fragments are also withheld. Isolated plain-number disagreements remain as printed in the supplied OCR.

## 1. Per-volume counts

“Figures skipped” counts identifiable source figure cells withheld by the rules, not absent blank/ellipsis cells. Whole unreadable tables count numeric-bearing cells rather than estimating the number of figures inside merged strings. Counts are therefore observed-cell counts: **unknown figures on pages with no parsed table are additional and cannot be counted**. A zero in a missing volume means zero identifiable cells, not zero lost printed figures. Non-numeric figure-cell entries retained in the extract count as figures written.

| Volume | Tables used | Figures written | Figure cells skipped |
|---|---:|---:|---:|
| 1863 | 0 | 0 | 0 |
| 1866 | 0 | 0 | 842 |
| 1868 | 2 | 887 | 12 |
| 1869 | 2 | 463 | 452 |
| 1871 | 1 | 462 | 530 |
| 1877 | 2 | 1,162 | 112 |
| 1880 | 0 | 0 | 0 |
| 1881 | 0 | 0 | 0 |
| 1882 | 0 | 0 | 0 |
| 1883 | 0 | 0 | 0 |
| 1885 | 2 | 751 | 565 |
| 1886 | 1 | 642 | 575 |
| 1887 | 2 | 1,115 | 203 |
| 1889 | 0 | 0 | 0 |
| 1889b | 2 | 1,245 | 153 |
| 1890 | 0 | 0 | 1,422 |
| 1891 | 1 | 583 | 167 |
| 1892 | 0 | 0 | 1,461 |
| 1893 | 1 | 552 | 920 |
| 1894 | 1 | 607 | 898 |
| 1896 | 2 | 1,184 | 408 |
| 1897 | 2 | 834 | 725 |
| 1898 | 2 | 553 | 1,100 |
| 1899 | 2 | 1,305 | 300 |
| 1900 | 2 | 811 | 825 |
| 1901 | 2 | 1,651 | 14 |
| 1902 | 1 | 834 | 823 |
| 1903 | 1 | 849 | 880 |
| 1904 | 2 | 1,026 | 693 |
| 1905 | 2 | 1,744 | 14 |
| 1906 | 2 | 1,768 | 0 |
| 1907 | 2 | 1,711 | 85 |
| 1908 | 2 | 1,641 | 258 |
| 1909 | 1 | 829 | 1,057 |
| 1910 | 2 | 1,846 | 11 |
| 1911 | 2 | 1,880 | 0 |
| 1912 | 2 | 1,645 | 249 |
| 1913 | 2 | 1,178 | 616 |
| 1914 | 1 | 437 | 1,447 |
| 1915 | 2 | 1,579 | 333 |
| 1916 | 2 | 1,682 | 250 |
| 1917 | 1 | 476 | 1,420 |
| 1918 | 2 | 1,409 | 516 |
| 1919 | 2 | 1,510 | 461 |
| 1920 | 1 | 717 | 1,252 |
| 1921 | 2 | 1,564 | 438 |
| 1922 | 2 | 1,352 | 598 |
| 1923 | 2 | 1,695 | 271 |
| 1924 | 0 | 0 | 189 |
| 1925 | 0 | 0 | 184 |
| 1926 | 0 | 0 | 390 |
| 1927 | 1 | 37 | 290 |
| 1928 | 1 | 145 | 90 |
| 1929 | 1 | 93 | 125 |
| 1930 | 1 | 100 | 125 |
| 1931 | 0 | 0 | 98 |
| 1932 | 1 | 19 | 172 |
| 1933 | 1 | 153 | 112 |
| 1934 | 1 | 34 | 230 |
| 1935 | 0 | 0 | 139 |
| 1936 | 1 | 94 | 136 |
| 1937 | 1 | 135 | 96 |
| 1938 | 1 | 129 | 119 |

Total: **77 distinct tables; 45,118 figures written; 25,851 identifiable figure cells skipped**, plus uncountable figures on missing parsed pages.

## 2. Per-series coverage and agreement

Agreement includes exact literal comparison when `value` is empty. “2+” removes single-printing cells, which otherwise count as vacuously agreeing. Shares are over observed series/year cells, not all theoretical years. Exact year lists and numerator/denominator counts are in `series_checks.tsv`.

| Series | Years covered | Cells | All agree | All agree, 2+ volumes |
|---|---|---:|---:|---:|
| area_square_miles | 1844, 1851, 1881, 1891, 1901, 1911, 1921, 1931–1933 | 10 | 40.0% | 14.3% |
| births | 1824–1923, 1910-11, 1911-12 | 102 | 66.7% | 66.0% |
| cultivated_area_acres | 1828–1842, 1845–1876, 1879–1923, 1910-11, 1911-12 | 94 | 66.0% | 65.2% |
| deaths | 1828–1923, 1910-11, 1911-12 | 98 | 59.2% | 58.3% |
| expenditure_gbp | 1821–1888 | 68 | 2.9% | 2.9% |
| expenditure_rupees | 1881, 1889–1912, 1914–1917, 1921, 1927–1933, 1937–1938, 1910-11, 1911-12 | 41 | 46.3% | 21.4% |
| exports_domestic_value_rupees | 1881, 1891, 1901, 1911, 1921, 1927–1933, 1937–1938 | 14 | 92.9% | 87.5% |
| exports_foreign_countries_value_rupees | 1881, 1891, 1901, 1911, 1921, 1927–1933, 1937–1938 | 14 | 92.9% | 87.5% |
| exports_foreign_produce_excluding_specie_value_rupees | 1881, 1891, 1901, 1911, 1921, 1927–1933, 1937–1938 | 14 | 100.0% | 100.0% |
| exports_other_british_possessions_value_rupees | 1881, 1891, 1901, 1911, 1921, 1927–1933, 1937–1938 | 14 | 100.0% | 100.0% |
| exports_other_countries_value_gbp | 1825–1842, 1845–1888 | 62 | 54.8% | 54.8% |
| exports_other_countries_value_rupees | 1889–1921, 1910-11, 1911-12 | 35 | 77.1% | 75.8% |
| exports_specie_value_rupees | 1881, 1891, 1901, 1911, 1927–1933, 1937–1938 | 13 | 92.3% | 85.7% |
| exports_uk_value_gbp | 1825–1842, 1845–1888 | 62 | 48.4% | 48.4% |
| exports_uk_value_rupees | 1881, 1889–1921, 1927–1933, 1937–1938, 1910-11, 1911-12 | 45 | 84.4% | 81.6% |
| exports_value_gbp | 1825–1888 | 64 | 64.1% | 64.1% |
| exports_value_rupees | 1881, 1889–1921, 1927–1933, 1937–1938, 1910-11, 1911-12 | 45 | 77.8% | 73.7% |
| imports_foreign_countries_value_rupees | 1881, 1891, 1901, 1911, 1921, 1927–1933, 1937–1938 | 14 | 92.9% | 87.5% |
| imports_other_british_possessions_value_rupees | 1881, 1891, 1901, 1911, 1921, 1927–1933, 1937–1938 | 14 | 85.7% | 75.0% |
| imports_other_countries_value_gbp | 1825–1842, 1845–1888 | 62 | 50.0% | 50.0% |
| imports_other_countries_value_rupees | 1889–1921, 1910-11, 1911-12 | 35 | 80.0% | 78.8% |
| imports_uk_value_gbp | 1825–1842, 1845–1888 | 62 | 46.8% | 46.8% |
| imports_uk_value_rupees | 1881, 1889–1921, 1927–1933, 1937–1938, 1910-11, 1911-12 | 45 | 73.3% | 68.4% |
| imports_value_gbp | 1825–1888 | 64 | 51.6% | 51.6% |
| imports_value_rupees | 1881, 1889–1921, 1927–1933, 1937–1938, 1910-11, 1911-12 | 45 | 68.9% | 63.2% |
| land_leased_acres | 1927–1928 | 2 | 50.0% | 0.0% |
| land_leasing_premia_rupees | 1927–1928 | 2 | 100.0% | — |
| land_sales_acres | 1828–1832, 1838–1839, 1843–1923, 1926–1928, 1910-11, 1911-12 | 93 | 74.2% | 72.4% |
| land_sales_amount_gbp | 1838–1839, 1843–1888 | 48 | 75.0% | 74.5% |
| land_sales_amount_rupees | 1881, 1889–1917, 1921, 1927–1928, 1910-11, 1911-12 | 35 | 91.4% | 87.0% |
| marriages | 1824–1923, 1910-11, 1911-12 | 102 | 76.5% | 76.0% |
| military | 1823–1827, 1835–1907, 1913–1914, 1921 | 81 | 75.3% | 74.7% |
| military_and_shipping | 1835–1843, 1847–1871, 1881, 1891, 1901, 1911, 1921, 1931 | 40 | 100.0% | 100.0% |
| population | 1823–1881, 1889–1891, 1900–1901, 1910–1911, 1921, 1910-11 | 68 | 55.9% | 53.8% |
| population_excluding_military_shipping | 1881, 1891, 1901, 1911, 1921, 1931 | 6 | 83.3% | 83.3% |
| public_debt_gbp | 1881, 1891, 1901, 1911, 1921, 1926–1928, 1931–1934, 1937–1938 | 14 | 64.3% | 37.5% |
| public_debt_rupees | 1881, 1891, 1901, 1911, 1921, 1926–1934, 1937–1938 | 16 | 75.0% | 42.9% |
| revenue_gbp | 1821–1888 | 68 | 76.5% | 76.5% |
| revenue_non_taxation_rupees | 1881, 1891, 1901, 1911, 1921, 1927–1928, 1931–1933, 1937–1938 | 12 | 100.0% | 100.0% |
| revenue_rupees | 1881, 1889–1912, 1914–1917, 1921, 1927–1928, 1931–1933, 1937–1938, 1910-11, 1911-12 | 39 | 87.2% | 80.8% |
| revenue_taxation_rupees | 1881, 1891, 1901, 1911, 1921, 1927–1928, 1931–1933, 1937–1938 | 12 | 91.7% | 83.3% |
| scholars | 1834–1842, 1845–1923, 1926–1927, 1910-11, 1911-12 | 92 | 65.2% | 62.8% |
| schools | 1834–1842, 1844–1923, 1926–1927, 1910-11, 1911-12 | 93 | 78.5% | 77.5% |
| shipping_british_colonies_tonnage | 1855–1921, 1910-11, 1911-12 | 69 | 56.5% | 55.2% |
| shipping_british_uk_tonnage | 1855–1921, 1910-11, 1911-12 | 69 | 58.0% | 56.7% |
| shipping_foreign_tonnage | 1855–1921, 1910-11, 1911-12 | 69 | 50.7% | 49.3% |
| shipping_other_countries_tonnage | 1825–1842, 1845–1921, 1910-11, 1911-12 | 97 | 52.6% | 51.6% |
| shipping_total_tonnage | 1825–1921, 1910-11, 1911-12 | 99 | 73.7% | 73.2% |
| shipping_uk_tonnage | 1825–1842, 1845–1921, 1910-11, 1911-12 | 97 | 35.1% | 33.7% |
| teachers | 1926–1927 | 2 | 100.0% | — |

## 3. Review by eye against source table rows

I read 30 retained source figures against their full supplied JSON table rows and headers: 10 each from 1896, 1871 and 1911, spread across years and measures. **All 30 match the original cell strings and their retained header assignments.** Twenty-nine have numeric values; the 1871 exports total for 1853 is `3,261,565*`, correctly retained literally with an empty numeric value. This is a review against the supplied OCR rows, not a new reading of page images.

The initial pilot additionally exposed the shifted 1896 shipping block: for example the row labelled 1855 contains total tonnage `681,071`, while the 1871 and 1911 rows place that sequence at 1856. The affected physical tonnage columns were withheld, not repaired, and the retained 30-figure sample uses an 1896 import figure instead. The 1871 demographic table was excluded before sampling because its columns and financial rows are displaced. The full original rows are preserved beside the checked figures in `eye_review.tsv`.

| Volume/table | Data year | Series | Source row, column | Literal → numeric value |
|---|---|---|---|---|
| bb1896:p7:t1 | 1823 | population | 3, 3 | `751,210` → `751210` |
| bb1896:p7:t1 | 1847 | births | 27, 5 | `38,861` → `38861` |
| bb1896:p7:t1 | 1896 | deaths | 76, 7 | `81,898` → `81898` |
| bb1896:p7:t1 | 1882 | scholars | 62, 9 | `92,791` → `92791` |
| bb1896:p7:t1 | 1896 | land_sales_amount_rupees | 76, 12 | `413,042` → `413042` |
| bb1896:p7:t1 | 1874 | revenue_gbp | 54, 13 | `1,241,558` → `1241558` |
| bb1896:p7:t1 | 1890 | expenditure_rupees | 70, 14 | `15,316,224` → `15316224` |
| bb1896:p8:t1 | 1896 | imports_uk_value_rupees | 78, 8 | `21,277,620` → `21277620` |
| bb1896:p8:t1 | 1853 | imports_value_gbp | 35, 10 | `3,527,182` → `3527182` |
| bb1896:p8:t1 | 1896 | exports_value_rupees | 78, 13 | `68,464,574` → `68464574` |
| bb1871:p6:t1 | 1825 | shipping_uk_tonnage | 8, 1 | `5,363` → `5363` |
| bb1871:p6:t1 | 1838 | shipping_other_countries_tonnage | 21, 2 | `180,225` → `180225` |
| bb1871:p6:t1 | 1844 | shipping_total_tonnage | 27, 3 | `332,081` → `332081` |
| bb1871:p6:t1 | 1855 | shipping_british_uk_tonnage | 38, 4 | `261,590` → `261590` |
| bb1871:p6:t1 | 1871 | shipping_british_colonies_tonnage | 54, 5 | `671,800` → `671800` |
| bb1871:p6:t1 | 1863 | shipping_foreign_tonnage | 46, 6 | `148,117` → `148117` |
| bb1871:p6:t1 | 1830 | imports_uk_value_gbp | 13, 7 | `40,777` → `40777` |
| bb1871:p6:t1 | 1860 | imports_value_gbp | 43, 9 | `3,551,239` → `3551239` |
| bb1871:p6:t1 | 1868 | exports_other_countries_value_gbp | 51, 11 | `993,409` → `993409` |
| bb1871:p6:t1 | 1853 | exports_value_gbp | 36, 12 | `3,261,565*` → `(empty)` |
| bb1911:p7:t1 | 1901 | population | 82, 3 | `3,565,954` → `3565954` |
| bb1911:p7:t1 | 1823 | military | 4, 4 | `5,852` → `5852` |
| bb1911:p7:t1 | 1910-11 | births | 91, 5 | `241,488` → `241488` |
| bb1911:p7:t1 | 1911-12 | marriages | 92, 6 | `21,386` → `21386` |
| bb1911:p7:t1 | 1885 | schools | 66, 8 | `3,421` → `3421` |
| bb1911:p7:t1 | 1858 | cultivated_area_acres | 39, 10 | `736,026` → `736026` |
| bb1911:p7:t1 | 1911-12 | revenue_rupees | 92, 13 | `47,246,222` → `47246222` |
| bb1911:p8:t1 | 1911-12 | shipping_total_tonnage | 93, 3 | `14,926,764` → `14926764` |
| bb1911:p8:t1 | 1889 | imports_value_rupees | 71, 9 | `60,695,136` → `60695136` |
| bb1911:p8:t1 | 1873 | exports_uk_value_gbp | 54, 10 | `4,056,138` → `4056138` |

## 4. Twenty cells with the most disagreement

Rank: number of distinct volumes outside the most common value, then number of distinct values, then total volumes. Ties use series/year order. Every value and volume is listed below; `literal` marks unparsed text. Differences involving footnote-marked literals need not imply different underlying numeric figures.

Statuses: `all agree`; `one volume differs` when exactly two values occur and one has only one volume while the other has at least two; otherwise `two values` for exactly two, and `many values` for three or more. Two-value chronological changes name the first new volume when the printings form two contiguous runs. Interleaving printings are explicitly marked as having no single change volume. These classifications describe printings; they do not establish a revision or justify correction.

1. **imports_value_gbp, 1863** — 29 volumes; 15 outside the modal value; many values.
   - `5433806`: 1868, 1869, 1871, 1877, 1885, 1886, 1887, 1889b, 1893, 1896, 1897, 1899, 1901, 1905.
   - `5433608`: 1906, 1907, 1908, 1910, 1911, 1913, 1915, 1916, 1918, 1919, 1921, 1922, 1923.
   - `5433607`: 1912.
   - `5433846`: 1902.

2. **imports_other_countries_value_gbp, 1855** — 29 volumes; 15 outside the modal value; many values.
   - `1939696`: 1868, 1869, 1871, 1877, 1885, 1886, 1887, 1889b, 1893, 1896, 1897, 1899, 1901, 1905.
   - `1939966`: 1906, 1907, 1908, 1910, 1911, 1912, 1913, 1915, 1916, 1918, 1919, 1921, 1922, 1923.
   - `1939698`: 1902.

3. **imports_value_gbp, 1831** — 29 volumes; 15 outside the modal value; many values.
   - `282988`: 1906, 1907, 1908, 1910, 1911, 1912, 1913, 1915, 1916, 1918, 1919, 1921, 1922, 1923.
   - `282989`: 1868, 1869, 1871, 1877, 1885, 1886, 1887, 1889b, 1893, 1896, 1897, 1899, 1901, 1902.
   - `282981`: 1905.

4. **scholars, 1877** — 27 volumes; 15 outside the modal value; many values.
   - `69463`: 1877, 1887, 1889b, 1891, 1894, 1896, 1899, 1900, 1901, 1903, 1904, 1905.
   - `69436`: 1906, 1907, 1908, 1910, 1911, 1912, 1919, 1922, 1923.
   - `69,436†` (literal): 1909, 1915, 1916, 1917, 1918, 1920.

5. **exports_uk_value_rupees, 1891** — 23 volumes; 14 outside the modal value; many values.
   - `41483842`: 1906, 1907, 1908, 1910, 1911, 1912, 1915, 1921, 1923.
   - `41483824`: 1896, 1897, 1898, 1899, 1901, 1902, 1905.
   - `41483825`: 1928, 1929, 1930, 1933, 1936, 1937, 1938.

6. **exports_other_countries_value_gbp, 1847** — 30 volumes; 14 outside the modal value; two values.
   - `397757`: 1868, 1869, 1871, 1877, 1885, 1886, 1887, 1889b, 1893, 1896, 1897, 1898, 1899, 1901, 1902, 1905.
   - `397957`: 1906, 1907, 1908, 1910, 1911, 1912, 1913, 1915, 1916, 1918, 1919, 1921, 1922, 1923.

7. **imports_value_gbp, 1841** — 29 volumes; 12 outside the modal value; two values.
   - `679670`: 1868, 1869, 1871, 1877, 1885, 1886, 1887, 1889b, 1893, 1896, 1897, 1899, 1901, 1902, 1905, 1908, 1922.
   - `976670`: 1906, 1907, 1910, 1911, 1912, 1913, 1915, 1916, 1918, 1919, 1921, 1923.

8. **cultivated_area_acres, 1874** — 27 volumes; 10 outside the modal value; many values.
   - `1550901`: 1877, 1889b, 1891, 1894, 1896, 1899, 1900, 1901, 1903, 1905, 1906, 1907, 1908, 1911, 1919, 1922, 1923.
   - `1,550,901*` (literal): 1915, 1916, 1917, 1918, 1920, 1921.
   - `1,550,901†` (literal): 1909, 1910.
   - `1570901`: 1912.
   - `1650901`: 1904.

9. **imports_uk_value_gbp, 1837** — 29 volumes; 9 outside the modal value; many values.
   - `168585`: 1868, 1869, 1871, 1877, 1886, 1887, 1889b, 1893, 1896, 1897, 1899, 1901, 1902, 1905, 1906, 1912, 1915, 1916, 1918, 1921.
   - `158585`: 1907, 1908, 1910, 1911, 1913, 1919.
   - `108585`: 1885.
   - `138585`: 1923.
   - `168555`: 1922.

10. **exports_value_gbp, 1853** — 30 volumes; 9 outside the modal value; many values.
   - `3261565`: 1886, 1887, 1889b, 1893, 1896, 1899, 1901, 1902, 1905, 1906, 1907, 1908, 1910, 1912, 1913, 1915, 1916, 1918, 1919, 1922, 1923.
   - `3,261,565*` (literal): 1868, 1869, 1871, 1877, 1897, 1898, 1911.
   - `3261563`: 1885.
   - `3281565`: 1921.

11. **cultivated_area_acres, 1873** — 27 volumes; 9 outside the modal value; many values.
   - `1253702`: 1889b, 1891, 1894, 1896, 1899, 1900, 1901, 1903, 1904, 1905, 1906, 1907, 1908, 1911, 1912, 1919, 1922, 1923.
   - `1,253,702*` (literal): 1915, 1916, 1917, 1918, 1920, 1921.
   - `1,253,702†` (literal): 1909, 1910.
   - `66424`: 1877.

12. **marriages, 1877** — 29 volumes; 9 outside the modal value; many values.
   - `17798`: 1877, 1887, 1889b, 1891, 1894, 1896, 1898, 1899, 1900, 1901, 1903, 1904, 1905, 1906, 1907, 1908, 1911, 1919, 1922, 1923.
   - `17,798†` (literal): 1909, 1910, 1913, 1915, 1916, 1918, 1920, 1921.
   - `17793`: 1912.

13. **exports_uk_value_rupees, 1896** — 16 volumes; 8 outside the modal value; many values.
   - `55455785`: 1906, 1907, 1908, 1910, 1911, 1915, 1921, 1923.
   - `55455585`: 1897, 1898, 1899, 1901, 1902, 1905.
   - `47221052`: 1896.
   - `55455795`: 1912.

14. **expenditure_rupees, 1901** — 15 volumes; 8 outside the modal value; many values.
   - `29216747`: 1928, 1929, 1930, 1933, 1936, 1937, 1938.
   - `25896594`: 1901, 1905, 1906, 1910, 1911, 1917.
   - `25856594`: 1903.
   - `25896591`: 1909.

15. **expenditure_rupees, 1891** — 16 volumes; 8 outside the modal value; many values.
   - `16435079`: 1896, 1901, 1903, 1905, 1906, 1910, 1911, 1917.
   - `16772393`: 1928, 1929, 1930, 1933, 1936, 1937, 1938.
   - `16435071`: 1909.

16. **births, 1877** — 29 volumes; 8 outside the modal value; two values.
   - `49779`: 1877, 1887, 1889b, 1891, 1894, 1896, 1898, 1899, 1900, 1901, 1903, 1904, 1905, 1906, 1907, 1908, 1911, 1912, 1919, 1922, 1923.
   - `49,779†` (literal): 1909, 1910, 1913, 1915, 1916, 1918, 1920, 1921.

17. **deaths, 1877** — 29 volumes; 8 outside the modal value; two values.
   - `62124`: 1877, 1887, 1889b, 1891, 1894, 1896, 1898, 1899, 1900, 1901, 1903, 1904, 1905, 1906, 1907, 1908, 1911, 1912, 1919, 1922, 1923.
   - `62,124†` (literal): 1909, 1910, 1913, 1915, 1916, 1918, 1920, 1921.

18. **imports_uk_value_rupees, 1891** — 22 volumes; 7 outside the modal value; two values.
   - `19340559`: 1896, 1897, 1899, 1901, 1902, 1905, 1906, 1907, 1908, 1910, 1911, 1912, 1915, 1921, 1923.
   - `19340560`: 1928, 1929, 1930, 1933, 1936, 1937, 1938.

19. **imports_value_rupees, 1891** — 22 volumes; 7 outside the modal value; two values.
   - `66635392`: 1896, 1897, 1899, 1901, 1902, 1905, 1906, 1907, 1908, 1910, 1911, 1912, 1915, 1921, 1923.
   - `66635382`: 1928, 1929, 1930, 1933, 1936, 1937, 1938.

20. **deaths, 1882** — 27 volumes; 6 outside the modal value; many values.
   - `54688`: 1894, 1896, 1898, 1900, 1903, 1905, 1906, 1907, 1908, 1909, 1910, 1911, 1913, 1915, 1916, 1918, 1919, 1920, 1921, 1922, 1923.
   - `54683`: 1887, 1891, 1901, 1904.
   - `54658`: 1912.
   - `54689`: 1889b.

## Verification completed

- All 45,118 source coordinates were re-opened from `tables/*.jsonl.gz` and checked: `value_as_printed` is exactly the original cell; table/volume IDs and row/column notes agree; no source cell is duplicated.
- Every numeric result was re-parsed with the same documented conservative grammar; the gzip TSV and both plain TSVs were read to completion, and their record counts checked.
- Comparison and mapping files are derived only from retained observations. Each comparison group counts distinct volume keys, and each JSON values list is sorted by volume frequency.
- Only the approved work directory and the three named output files were used for writes. The scripts use the requested Python interpreter and standard library.
