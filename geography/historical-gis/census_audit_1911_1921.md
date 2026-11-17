# Image audit of 1911 and 1921 comparative census tables

Inputs audited were `geography/historical-gis/census_1911_towns.tsv` and `geography/historical-gis/census_1921.tsv`. Compared the visible census row labels, column headings, values, title pages and applicable footnotes on original scan images. An independent transcription compared against the TSVs found **213 matching populated cells** of **216 possible**, three justified empty cells and zero incorrect transcribed numerals. Geographic keys, generated provenance and note wording are assessed below. No canonical input was edited.

## 1911 town and village statistics

E. B. Denham, *The Census of Ceylon, 1911. Town and Village Statistics*, H. C. Cottle, Government Printer, Colombo, **1912**. The title page (PDF 3) expressly excludes military and shipping. The audited numbers measure occupied houses, persons and literates. English-literates columns follow the general-literates columns and were not transcribed. The figures represent the 1901 and 1911 censuses. The book's publication date is separate. [Title page scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=3)

The row label and applicable enclosing heading are confirmed for each row. Names beginning with a town name in the TSV are normalized display names. The source often uses simply “Local Board” or “Municipality” under the named area.

| Row | Printed page / PDF page | Image |
|---|---|---|
| Negombo Local Board | 30 / 37 | [Scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=37) |
| Kalutara Local Board | 36 / 43 | [Scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=43) |
| Kandy Municipality | 44 / 51 | [Scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=51) |
| Matale Local Board | 70 / 77 | [Scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=77) |
| Galle Municipality | 122 / 130 | [Scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=130) |
| Matara Local Board | 142 / 150 | [Scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=150) |
| Batticaloa Local Board | 166 / 175 | [Scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=175) |

Read each row in this order, following the scan. Houses 1901, 1911. Persons 1901 male, female, total and 1911 male, female, total. Literates 1901 male, female and 1911 male, female.

```
Negombo Local Board     —    2434   5806  5234 11040   6867  6093 12960   2287 1372 3528 1999
Kalutara Local Board  1993   2361   5821  5679 11500   6542  6464 13006      —    — 3601 1523
Kandy Municipality    4755   5239  15049 11337 26386  16688 12763 29451   7192 2559 8349 3176
Matale Local Board     975   1097   2981  1970  4951   3475  2317  5792   1480  327 1723  526
Galle Municipality    6565   7299  18773 18392 37165  20093 19867 39960   8091 2878 8980 3925
Matara Local Board    2009   2366   6021  5859 11880   7010  6841 13851   2762 1209 3476 1611
Batticaloa Local Bd.  1827   1971   5159  4810  9969   5584  5082 10666   2659 1031 3203 1541
```

- **Negombo 1901 occupied houses.** The 4,106 at the 1901 houses column is braced across the Local Board and adjacent Town of Negombo rows through Duwa. No board-only number is visible. The blank is justified. The adjacent starred 1901 person figures for Bolawalana II and Periyamulla II include portions within Local Board limits, per the footnote on p. 30. The board-only population of 11,040 has no star and sums from 5,806 plus 5,234. Exact reason for the difference from 19,819 (10,020 male and 9,799 female) in 1901 Census Table IV remains unverified. Preserve the two source-linked observations and avoid adding starred adjacent values to the Local Board count. [1911 comparative scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=37) · [1901 Table IV scan](https://digitalcollections.crl.edu/record/387349/files/024.pdf)
- **Kalutara 1901 literacy.** The print literally gives 5,821 male and 5,679 female in the general-literates columns, exactly repeating the population sex counts. The true values are unresolved. The two nulls are justified and the transcription note should state both printed figures and that this is a probable source error. [Scan](https://archive.org/download/tdl.45514-the-census-of-ceylon-1911-town-and-village-statistics-the-towns-and-vi/TVA_BOK_0045514_The_Census_of_Ceylon_1911_1912.pdf#page=43)
- **Cross-source count differences.** The Matara 1901 Census Table IV count is 11,848 (6,007 male, 5,841 female) versus the 1911 volume’s 11,880 (6,021 male, 5,859 female). Both sum correctly. The 1901 occupied-house pairs (1911 volume / 1901 volume) are Kandy 4,755 / 4,615, Matale 975 / 966, Galle 6,565 / 6,550 and Matara 2,009 / 2,003. Kalutara and Batticaloa match on occupied houses. Negombo's 3,770 in the original 1901 report has no direct board-only counterpart in the 1911 comparative column. Preserve the separate published observations. [1901 Table IV p. 25](https://digitalcollections.crl.edu/record/387349/files/024.pdf) · [1901 Table IV pp. 26–27](https://digitalcollections.crl.edu/record/387349/files/025.pdf)
- **Observation provenance.** Current source catalogue URL for this volume opens the general item only. Its downloadable original PDF link above is confirmed in the public archive metadata. Using the direct PDF as the source catalogue URL allows the current build to append the verified `#page=` locator to each observation. The 1911 comparison scope could explicitly repeat the military and shipping exclusion from its title page. Source parents written as town or district anchors are normalized rather than guaranteed literal enclosure labels. In particular, the Kalutara row is under Kalutara Totamune (Kalutarabadda) within Kalutara District, and the Matara row under Matara Four Gravets within Matara District.

## 1921 town and village statistics

L. J. B. Turner, *Census Publications, Ceylon, 1921. Volume II. Town and Village Statistics*, H. Ross Cottle, Government Printer, Colombo, **1923**. The title page (PDF 4) expressly excludes military and shipping. The summary table is PDF 13, with no legible folio on that image, headed “Ceylon, &c.” with the column groups “Habitable Buildings”, “Persons” and “Literates” for 1911 and 1921. The columns to the right for English literates, race and religion are outside these inputs. [Title page scan](https://archive.org/download/in.ernet.dli.2015.196126/2015.196126.Census-Publications-Ceylon-1921-Vol-2.pdf#page=4) · [Table scan](https://archive.org/download/in.ernet.dli.2015.196126/2015.196126.Census-Publications-Ceylon-1921-Vol-2.pdf#page=13)

Read each row in this order. Habitable buildings 1911, 1921. Persons 1911 male, female, total and 1921 male, female, total. Literates 1911 male, female and 1921 male, female.

```
Ceylon                691899 825542 2175030 1931320 4106350 2381812 2116793 4498605 878766 204062 1156119 381475
Western               195583 231368  591959  514362 1106321  666928  579919 1246847 289391 108830  376543 183668
Central                74686  89182  358476  313782  672258  379598  338141  717739 116090  15670  151489  32793
Southern              121343 142020  316909  311908  628817  337365  333869  671234 121533  29779  160258  57826
Northern               69974  82673  184438  185528  369966  187221  187608  374829  87378  19638  102777  39573
Eastern                33899  39513   94383   89315  183698   97784   95037  192821  28886   4181   37733   7093
North Western          90580 107020  240372  193744  434116  275874  216307  492181 107777  16503  149592  33955
North Central          20286  25888   47424   38537   85961   54929   41596   96525  19964    774   27156   1604
Uva                    28030  34876  115601  101091  216692  124228  109636  233864  30354   2201   39639   6250
Sabaragamuwa           57518  73002  225468  183053  408521  257224  214590  471814  77393   6486  110331  18668
Colombo Municipality   40009  45934  133736   84790  218526  149595   94568  244163  65187  21484   87657  33339
```

- **Scope.** Starred 1911 provincial figures are adjusted, where necessary, for area changes since the 1911 Census. The independent dagger note applies specifically to ward figures, which were adjusted as far as possible to 1921 areas. The municipality section begins under “Western Province” with ward rows beneath the municipality total. “Colombo District (exclusive of the Municipality)” begins a new block. A `source_parent` of `Colombo` for Colombo Municipality is ambiguous and should be `Western Province` if the field conveys the enclosing heading. The scope could say “Municipal total; 1911 ward figures beneath this row were adjusted as far as possible to 1921 ward areas” if recording the footnote alongside that row. The November 1911 Wellawatta South Ward boundary footnote, associated exclusive-district cross-reference, and estate literacy note apply to lower rows outside this input. “Habitable Buildings” remains a distinct metric from 1911's “Occupied Houses”. [Table and notes scan](https://archive.org/download/in.ernet.dli.2015.196126/2015.196126.Census-Publications-Ceylon-1921-Vol-2.pdf#page=13)
- **National reconciliation.** The nine provinces sum to the 1911 national entries throughout. For 1921 the Ceylon count includes two separately listed enumerations. Train has 653 male, 90 female, 743 total, 594 male literates and 45 female literates. Basses has 8 male, 8 total and 7 male literates, with no female figures printed. This accounts exactly for the national minus provincial differences of 661 male, 90 female, 751 persons, 601 male literates and 45 female literates. The national buildings value matches the province sum. [Table scan](https://archive.org/download/in.ernet.dli.2015.196126/2015.196126.Census-Publications-Ceylon-1921-Vol-2.pdf#page=13)
- **Faint type.** The end digit of 1911 North Central persons is damaged near the column border. It resolves uniquely as **85,961** from 47,424 plus 38,537 and the Ceylon minus other provinces check. Colombo Municipality’s 1911 count **218,526** resolves from 133,736 plus 84,790, consistent with the partly printed final digit. No uncertain published numeral was silently substituted. [Table scan](https://archive.org/download/in.ernet.dli.2015.196126/2015.196126.Census-Publications-Ceylon-1921-Vol-2.pdf#page=13)
- **Observation provenance.** Current source catalogue URL opens the general item even though PDF p. 13 is known. The direct original PDF above is confirmed in public archive metadata and permits the build to append `#page=13` automatically.
