# Original image audit of five census inputs

I compared all 171 extant data rows with the original page images, including all 577 quantitative/date cells or explicit missing markers, the corresponding source labels and table scope, and every printed page or PDF locator used by these inputs. Source-defined headings and report notes were checked where needed. The parent labels for municipalities and the normalized identifiers in the TSV are project joins rather than literal table cells. No canonical changes were made during this review.

| Input | Data rows and fields checked | Original image locators |
| --- | --- | --- |
| `census_gazette.tsv` | 71 rows; all 142 counts, place labels, headings and the seven populated note entries | Gazette No. 9,533, 23 March 1946, printed pp. 489–490, PDF pp. 1–2, rendered to `/tmp/census-audit-late-scans/gazette-{1,2}.jpg` and crops `g1-left.jpg`, `g1-right.jpg`, `g2-l.jpg`, `g2-r.jpg` |
| `census_1946_final.tsv` | 51 rows; nine provinces with two populations, two densities and area, and 42 towns with 1946 population, density and area (171 values total). The 1931 fields are correctly blank for towns in this table. | Table 10, print p. 72 / PDF p. 104; Table 14, print pp. 75–77 / PDF pp. 109–111, local `/tmp/ceylon-history-research/final-{104,109,110,111}.jpg` |
| `census_1946_districts.tsv` | 20 revenue districts; all 80 male/female cells in the two census columns, spot note below about the parent metadata | Table 97, print p. 147 / PDF p. 195, local `/tmp/ceylon-history-research/districts-195.jpg` |
| `census_dcs.tsv` | 21 retained rows; 166 numeric entries and the two Chilaw missing markers. The omitted Gampaha, Mullaitivu, Kilinochchi, Ampara, Polonnaruwa and Moneragala rows contain only missing markers for 1871–1946. | Statistical Abstract 2023 Table 2.1, Both sexes, PDF p. 1, rendered `/tmp/census-audit-late-scans/dcs-1.jpg` |
| `census_dates.tsv` | Eight census dates and eight nationwide count cells, excluding shipping/services scope | Table 3, print p. 57 / PDF p. 87, local `/tmp/ceylon-history-research/final-087.jpg` |

## Corrections in Gazette

- Kurunegala district 1946, TSV line 25 at time of review, `485866` → `485366`. In the scan the clogged first digit of the final three reads as a 3 when compared against similarly inked 3s. The two printed child counts 485,366 and 184,789 equal the printed North-Western 670,155. The North Western province note claiming a 500 discrepancy should be deleted or replaced with a reading note. The associated printed 22.2% rate is consistent with 485,366 / 397,239. See `/tmp/census-audit-late-scans/kurunegala.png` and `g1-right.jpg`.
- Kegalla district footnote B, printed p. 490, TSV line 30. The high-resolution crop `/tmp/census-audit-late-scans/kegalla-fn.png` reads as 3 estates, followed by a bracket-like mark. The current note says 2. Distinguish from footnote B on the preceding page, which applies to Puttalam and Chilaw and prints 2. The digit is moderately obscured and can be noted as a reading if desired. Kegalla counts 314,567 and 401,370 agree.
- Gazette 1931 Ceylon printed total, p. 489: the heavy ink on the glyph read as 3 obscures its left-hand opening and the OCR reads 5,806,871. No numeric correction proposed to 5,306,871. The p. 489 percentages place it near 5.3 million (6,650,825 at +25.3%), and final Table 3 clearly prints 5,306,871. The nine Gazette province rows total 5,306,863 (8 below the reported national figure), an exact source inconsistency also present when final Table 10's 1931 rows are summed and compared with final Table 3. Preserve the published province rows. Magnified scan `/tmp/census-audit-late-scans/ceylon.png`.
- Minuwangoda p. 490 counts 1,054 and 1,199 agree with TSV. Printed increase 12.0% is a source arithmetic anomaly, implied increase about 13.8%. Preserve existing note.

The Gazette introduction says the 1946 figures were correctable and in some cases used preliminary counts. It also says pre-existing 1931 administrative units were aggregated for urban councils constituted after the 1931 census. Preserve Gazette values separately from the final report. All other Gazette counts, pages and available notes checked.

## Other source-specific readings and scope

- DCS 1931 Mannar visibly reads `W25.1`; the normalized numeric 25.1 agrees with the scale and with the 1931 Gazette count 25,137. The DCS print does not key that W on page 1. Preserve 25.1 and optionally note the source marker. The DCS 1921 country value 4,497.9 thousand and final Table 3's 4,498,605 are both as printed in their respective sources. They should remain distinct. DCS prints Hambantota 1946 `150` and Chilaw 1871/1881 `..`, exactly as retained.
- Final Table 10 Western 1946 density 1,310 is printed even though dividing the two printed population and area values gives about 1,310.69. It is the published density field. The area of 1,432 is the explicitly rounded Table 10 value (see final report prose on PDF p. 111, which gives 1,431¾).
- Final Table 14 p. 75 prints `Dehiwela-Mount Lavinia`; p. 77 prose uses `Dehiwala-Mount Lavinia`. The project comparator name is a normalized linkage. The fraction `2 1/64` for Weligama and similar unusual fractions are confirmed against the type.
- Districts Table 97 prints the six sex-count/ratio columns, and the TSV intentionally takes the count columns only. Table 97 lists districts in province blocks without repeated province headings. The province assignments are consistent with the Gazette's district headings and final Table 14; distinct Puttalam/Chilaw are an attended final report presentation difference from the combined Gazette count. The 1946 male/female totals also reconcile to final Table 10 by province.
- The unnamed date rows draw from a table that explicitly lists the dates rather than assuming enumeration on publication dates. The national figures are non-resident exclusions as recorded by the report.

## Source URL references

- Gazette No. 9,533, PDF pp. 1–2: https://diglib.natlib.lk/bitstream/handle/123456789/30704/037_1946-JANUARY-JUNE_9533_I_E.pdf?isAllowed=y&sequence=1
- Census of Ceylon 1946 Volume I Part I General Report, PDF pp. 87, 104, 109–111, 195: https://noolaham.net/project/1018/101739/101739.pdf
- Statistical Abstract 2023 Table 2.1, PDF p. 1: https://www.statistics.gov.lk/abstract2023/CHAP2/2.1.pdf

No unaudited quantitative cells among the five assigned inputs. The audit does not encompass untranscribed percentage/ratio columns, the project gazetteer/QID joins, or census inputs assigned to other reviewers.
