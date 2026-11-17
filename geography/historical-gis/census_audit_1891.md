# 1881 and 1891 source image audit

I independently read the original Lionel Lee *Census of Ceylon, 1891*, Volume II images from the local Internet Archive scan, then compared a second numeric entry against both TSVs. No canonical input was edited. [Source scan](https://archive.org/download/wbsl.4536/4536.pdf)

## Coverage and value checks

| Source and scope | Coverage | Result |
| --- | --- | --- |
| Table III, printed p. 12, PDF p. 17 | Ceylon, 9 province rows, 22 district rows, Colombo Municipality. 33 rows × 6 census count cells. | All 198 values and locators match. |
| Table III, printed p. 13, PDF p. 18 | Two Negombo Local Board scopes, Kalutara, Ratnapura, Kurunégala. 5 rows × 6 cells. | All 27 numbers match. Three dashes in the 1881 columns for Negombo's contemporary limits match the TSV blanks. |
| Table III, printed p. 14, PDF p. 19 | Puttalam, Chilaw, Kandy, Mátalé, Nuwara Eliya and Badulla. 6 rows × 6 cells. | All 36 numbers and locators match. |
| Table III, printed p. 15, PDF p. 20 | Batticaloa, Trincomalee, Galle, Mátara and Hambantota. 5 rows × 6 cells. | All 30 numbers and locators match. |
| Table II, printed p. 11, PDF p. 16 | All 33 area and density rows, including Colombo Municipality. | All 32 legible areas and all 33 densities match. One obscured area remains blank. |

The 356 actual observations matched their source images. Within those 356 are 291 count values, 32 area values and 33 density values. The 49 Table III source rows include three explicitly blank comparator cells in addition to the 291 numbers. All 82 row locators match the printed and PDF pagination. Geographic parent and unit labels agree with the relevant row labels and section hierarchy. Appendix Table I, PDF p. 6, supplies the explicit 26 February 1891 date, and 17 February 1881 is confirmed on the 1946 General Report's Table 3, printed p. 57, PDF p. 87. The 1891 volume's title page, PDF p. 2, confirms that it was printed in 1892. [1891 Table I](https://archive.org/download/wbsl.4536/4536.pdf#page=6) · [1946 Table 3](https://noolaham.net/project/1018/101739/101739.pdf#page=87)

Reopened the GeoPackage read-only. It contains all 356 observations under source ID `census-1891`, with 144 represented on 1881-02-17 and 212 on 1891-02-26. All have publication year 1892. Colombo Municipality's area preserves the printed `9 9/20` and parses to 9.45 square miles.

## Scope and proposed metadata corrections

- Table III explicitly excludes military and shipping. The GeoPackage applies that scope to every population observation from this table. Table II's header gives the same exclusion, but its generated density observations do not carry it in `scope` unless row detail says so. In `build.py` at generation of Table II `population_density`, append “Population excludes military and shipping.” to the existing `area_scope`, preserving the Colombo Lake, district grouping, and historical scope statements. Table II, printed p. 11, PDF p. 16.
- In `census_1891_area_density.tsv`, rows `province:sabaragamuwa` and `province:uva` have notes about “1881 comparator” carried over from Table III. Remove those two `note` values in the area/density file. Table II reports 1891 area and density. Keep the comparator notes on Table III population rows. The existing data values and dates are correct.
- The source footnote on Table II applies to the Colombo Municipality area. The count excludes military and shipping, and the area excludes Colombo Lake. The TSV captures the Lake exclusion. Table III distinguishes Colombo Municipality, Colombo District exclusive of the municipality, and Negombo District. Puttalam excludes separately tabulated Chilaw. Mullaitívu and Vavuniya are also separately tabulated.
- Table III printed p. 12 explicitly includes Tamankaduwa in Nuwarakaláwiya District. Table II uses the shorter name and the same enumeration row. The link to Anuradhapura is a successor/place join supplied by the project, and the row retains the historical printed district name.
- Printed p. 13 footnotes support both Negombo scopes, Ratnapura Town in 1881, and the differing 1881 and 1891 Kurunégala Local Board limits. Printed p. 14 supports Chilaw Town and Mátalé Town in 1881. The Nuwara Eliya row explicitly combines the Local Board with areas outside the Local Board limits. Printed p. 15 identifies the 1881 Batticaloa comparator as the town within Police limits and Hambantota as the Four Gravets. The existing scope and note fields preserve these distinctions.

## Source anomaly and limits

- Chilaw District area is ink-obscured in the source at PDF p. 16, including at 300 dpi. The printed density 241 is legible. Subtracting Kurunégala's 1,845 and Puttalam's 890 square miles from the North-Western Province total of 2,997 suggests 262 square miles. The printed population of 63,231 divided by 262 gives 241.34, which rounds to 241. Keep the transcription blank, or label 262 explicitly as a derived figure with the formula and source.
- The three 1881 cells for Negombo's 1891 limits are printed as dashes. Their nulls indicate the table does not report a comparator for that scope.
- Table III also prints other divisions, kórales, pattus, estates, and change columns. Those cells are outside these transcriptions. There are no unaudited nonnull values in the two files. Chilaw's area is the single unreadable source value among the selected rows.

No numeric correction is proposed. [Table II](https://archive.org/download/wbsl.4536/4536.pdf#page=16) · [Table III](https://archive.org/download/wbsl.4536/4536.pdf#page=17)
