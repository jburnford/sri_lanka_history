# Independent image review of the 1901 census comparison

All 49 rows of `census_1901_comparison.tsv` were read against the original Table IV page images. I independently keyed the printed numbers in the table's order, by occupied houses, persons, males and females, then compared the transcription with the TSV by row identifier. I used the native PDF scan raster to resolve uncertain type. This review covers the extracted national, province, district and town rows. The original table also contains subdivisions outside the extraction.

| Printed page | CRL scan | Rows checked | Values | Unassigned cells |
| --- | --- | ---: | ---: | ---: |
| 24 | 024 | 20 | 320 | 0 |
| 25 | 024 | 14 | 212 | 12 |
| 26 | 025 | 3 | 44 | 4 |
| 27 | 025 | 4 | 56 | 8 |
| 28 | 026 | 5 | 64 | 16 |
| 29 | 026 | 3 | 28 | 20 |
| **Total** | | **49** | **724** | **60** |

All 724 numbers match. All 60 unassigned cells belong to 15 town-year groups, each covering all four measures. I also checked row labels, section hierarchy, population exclusions, publication year, and each row's page link. Table IV identifies one national row, nine province rows, 21 district rows and 18 named urban rows in the extraction. The standardized GIS unit identifiers and aliases are project metadata. [Table IV pp. 24–25](https://digitalcollections.crl.edu/record/387349/files/024.pdf) · [pp. 26–27](https://digitalcollections.crl.edu/record/387349/files/025.pdf) · [pp. 28–29](https://digitalcollections.crl.edu/record/387349/files/026.pdf)

## Dates and population scope

The title page identifies P. Arunachalam, Volume II, H. C. Cottle as Acting Government Printer in Colombo, and publication in 1902. The Table IV title page specifies the four census years and says that earlier figures were adjusted as far as possible to the divisions constituted on 1 March 1901. The printed p. 24 header excludes military, shipping and prisoners of war. Actual census days for all four years were cross-checked against the enumerated dates in Table 3 of the 1946 General Report. Its list agrees with all 196 repeated date fields in the TSV: 27 March 1871, 17 February 1881, 26 February 1891 and 1 March 1901. [1901 title page](https://digitalcollections.crl.edu/record/387349/files/002.pdf) · [Table IV title and scope note](https://digitalcollections.crl.edu/record/387349/files/023.pdf) · [1946 General Report, Table 3, printed p. 57](https://noolaham.net/project/1018/101739/101739.pdf#page=87)

## Confirmed readings and scope notes

- Chilaw Local Board has **694 occupied houses in 1891**. The native p. 28 crop shows the tails of 6 and 9 and the crossbar of 4 clearly. On the same row the 1881 and 1901 entries are 696 and 750. The district row is separate.
- Matara Local Board has **10,180 persons and 5,100 males in 1891**, confirmed from the native p. 27 raster. The thin right stroke of the last zero in the male count makes it resemble 9 in a reduced rendering. The 1901 population is **11,848** in this source. The figure of 11,880 in the 1911 town comparison belongs to that publication.
- Negombo p. 25 and Anuradhapura p. 28 show a visible brace over the combined 1871 entries. In 1881 each metric is printed once across the group without a brace. The current blank town-only cells correctly preserve the reporting scope. For a literal source note, replace “in braces” with “reported jointly” when referring to the 1881 figures. The 1891 braces enclose two separately printed values for each metric, so each receives its own assignment.
- The other combined town groups are Kalutara with Kalutara Totamune, Nuwara Eliya with Kotmale, Galle Municipality with Galle Four Gravets beyond its limits and Akmimana, Matara Local Board with Matara Four Gravets beyond its limits, Puttalam with Puttalam Division, Chilaw with Pitigal Korale North, Badulla with Yatikinda Division, and Ratnapura with Kuruwiti Korale, all for 1871. The p. 29 footnote explicitly dates Kegalla Local Board after 1891 and says separate earlier figures are unavailable. Its 1901 line gives 405 occupied houses and 2,340 persons, 1,312 male and 1,028 female.
- The footnote attached to Jaffna, Mannar and Mullaittivu attributes territory changes to the abolition of Vavuniya District. The report places Vavuniya North and South under Mullaittivu. Colombo Municipality and Colombo District exclusive of the municipality appear as separate rows, and Negombo is a separate district here.

No further numeric corrections emerged. No canonical input was edited during this review.
