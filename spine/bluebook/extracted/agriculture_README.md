# Agriculture extract

12,686 observation rows from 134 tables; 9,186 numeric values. Missing-value cells are retained as rows. 376 candidate tables were skipped. The first pass searched 13 volumes for all three kinds of table; a second pass (below) took the opening Agricultural Statistics tables from 41 more. This is a selective extraction, not complete coverage of every volume.

Rebuild from this folder using the standard library only:

```sh
/home/jic823/miniforge3/bin/python jobs/agriculture_work/extract_agriculture.py
/home/jic823/miniforge3/bin/python jobs/agriculture_work/validate_agriculture.py
```

## Coverage

| Volume | Kind | Tables used (observation rows) |
| --- | --- | --- |
| 1863 | acreage_by_crop | bb1863:p10:t2 (98) |
| 1866 | acreage_by_crop | bb1866:p11:t2 (49), bb1866:p11:t3 (49) |
| 1868 | acreage_by_crop | bb1868:p11:t2 (49), bb1868:p11:t3 (49) |
| 1869 | acreage_by_crop | bb1869:p11:t2 (49), bb1869:p11:t3 (49) |
| 1869 | land_produce_stock | bb1869:p530:t1 (150), bb1869:p535:t1 (68) |
| 1869 | live_stock | bb1869:p11:t4 (10) |
| 1871 | acreage_by_crop | bb1871:p13:t2 (49), bb1871:p13:t3 (49) |
| 1877 | — | No tables extracted |
| 1880 | acreage_by_crop | bb1880:p8:t4 (56), bb1880:p8:t5 (80) |
| 1881 | acreage_by_crop | bb1881:p10:t5 (80), bb1881:p10:t6 (80) |
| 1882 | acreage_by_crop | bb1882:p10:t6 (80), bb1882:p11:t1 (80) |
| 1883 | acreage_by_crop | bb1883:p10:t4 (80), bb1883:p11:t1 (80) |
| 1885 | acreage_by_crop | bb1885:p13:t1 (80), bb1885:p13:t2 (80) |
| 1886 | acreage_by_crop | bb1886:p13:t1 (80), bb1886:p13:t2 (90) |
| 1887 | acreage_by_crop | bb1887:p14:t2 (90), bb1887:p14:t3 (90) |
| 1889 | — | No tables extracted |
| 1889b | acreage_by_crop | bb1889b:p14:t2 (90), bb1889b:p14:t3 (100) |
| 1890 | acreage_by_crop | bb1890:p295:t1 (100), bb1890:p295:t2 (100) |
| 1891 | acreage_by_crop | bb1891:p297:t1 (100), bb1891:p297:t2 (100) |
| 1892 | acreage_by_crop | bb1892:p310:t1 (100), bb1892:p310:t2 (100) |
| 1893 | acreage_by_crop | bb1893:p18:t1 (100), bb1893:p18:t2 (100) |
| 1894 | acreage_by_crop | bb1894:p14:t1 (100), bb1894:p14:t2 (100) |
| 1896 | acreage_by_crop | bb1896:p15:t1 (100), bb1896:p15:t2 (100) |
| 1897 | acreage_by_crop | bb1897:p17:t1 (100), bb1897:p17:t2 (100) |
| 1898 | acreage_by_crop | bb1898:p15:t1 (100), bb1898:p15:t2 (100) |
| 1899 | acreage_by_crop | bb1899:p15:t1 (100), bb1899:p15:t2 (100) |
| 1900 | acreage_by_crop | bb1900:p18:t1 (100), bb1900:p18:t2 (100) |
| 1901 | acreage_by_crop | bb1901:p16:t1 (100), bb1901:p16:t2 (100) |
| 1902 | acreage_by_crop | bb1902:p16:t1 (110), bb1902:p16:t2 (110) |
| 1902 | land_produce_stock | bb1902:p680:t1 (86), bb1902:p681:t1 (90), bb1902:p682:t1 (84), bb1902:p683:t1 (104), bb1902:p684:t1 (100), bb1902:p685:t1 (102), bb1902:p686:t1 (102), bb1902:p687:t1 (42), bb1902:p688:t1 (55), bb1902:p689:t1 (25), bb1902:p690:t1 (112) |
| 1902 | live_stock | bb1902:p16:t3 (10) |
| 1903 | acreage_by_crop | bb1903:p18:t1 (110), bb1903:p18:t2 (110) |
| 1904 | acreage_by_crop | bb1904:p18:t1 (110), bb1904:p18:t2 (110) |
| 1904 | land_produce_stock | bb1904:p726:t1 (88), bb1904:p727:t1 (92), bb1904:p728:t1 (84), bb1904:p729:t1 (104), bb1904:p730:t1 (102), bb1904:p731:t1 (102), bb1904:p732:t1 (106), bb1904:p733:t1 (48), bb1904:p734:t1 (50), bb1904:p735:t1 (25), bb1904:p736:t1 (112) |
| 1904 | live_stock | bb1904:p18:t3 (10) |
| 1905 | acreage_by_crop | bb1905:p15:t1 (110), bb1905:p15:t2 (120) |
| 1906 | acreage_by_crop | bb1906:p16:t1 (120), bb1906:p16:t2 (110) |
| 1907 | acreage_by_crop | bb1907:p17:t1 (110), bb1907:p17:t2 (110) |
| 1908 | acreage_by_crop | bb1908:p14:t2 (110), bb1908:p14:t3 (110) |
| 1910 | acreage_by_crop | bb1910:p14:t2 (110), bb1910:p14:t3 (110) |
| 1911 | acreage_by_crop | bb1911:p14:t2 (110), bb1911:p14:t3 (110) |
| 1912 | acreage_by_crop | bb1912:p16:t4 (110), bb1912:p17:t1 (110) |
| 1912 | land_produce_stock | bb1912:p253:t1 (78), bb1912:p254:t1 (98), bb1912:p255:t1 (88), bb1912:p256:t1 (110), bb1912:p257:t1 (92), bb1912:p258:t1 (82), bb1912:p259:t1 (72), bb1912:p260:t1 (74), bb1912:p261:t1 (41), bb1912:p262:t1 (32), bb1912:p263:t1 (44), bb1912:p264:t1 (112) |
| 1912 | live_stock | bb1912:p17:t2 (10) |
| 1913 | acreage_by_crop | bb1913:p15:t2 (110), bb1913:p15:t3 (110) |
| 1914 | acreage_by_crop | bb1914:p15:t2 (110), bb1914:p15:t3 (110) |
| 1915 | acreage_by_crop | bb1915:p14:t3 (110), bb1915:p14:t4 (110) |
| 1916 | acreage_by_crop | bb1916:p16:t3 (110), bb1916:p16:t4 (110) |
| 1917 | acreage_by_crop | bb1917:p15:t2 (110), bb1917:p15:t3 (110) |
| 1918 | acreage_by_crop | bb1918:p15:t2 (110), bb1918:p15:t3 (110) |
| 1919 | acreage_by_crop | bb1919:p14:t2 (110), bb1919:p14:t3 (110) |
| 1920 | acreage_by_crop | bb1920:p15:t2 (110), bb1920:p15:t3 (110) |
| 1921 | acreage_by_crop | bb1921:p15:t2 (90), bb1921:p15:t3 (90) |
| 1922 | acreage_by_crop | bb1922:p15:t2 (90), bb1922:p15:t3 (90) |
| 1923 | acreage_by_crop | bb1923:p15:t2 (90), bb1923:p15:t3 (90) |
| 1924 | land_produce_stock | bb1924:p397:t1 (168) |
| 1924 | live_stock | bb1924:p400:t1 (168) |
| 1925 | — | No tables extracted |
| 1926 | live_stock | bb1926:p318:t1 (174) |
| 1928 | acreage_by_crop | bb1928:p327:t1 (480) |
| 1928 | live_stock | bb1928:p330:t1 (174) |
| 1930 | — | No tables extracted |
| 1933 | — | No tables extracted |
| 1934 | — | No tables extracted |

The complete reviewed candidate inventory, including per-table dating decisions and counts, is in `jobs/agriculture_work/candidate_inventory.tsv`. Each excluded candidate has a reason in `agriculture_skipped.tsv`.

## Second pass: opening Agricultural Statistics, 1862–1923

Almost every volume opens with a summary "Agricultural Statistics": acres under each crop by province, printed twice, for the previous year and for the volume year. The first pass took these from 1869, 1902, 1904, 1912 and 1928 only. The second pass (`SECOND_PASS` in the script) adds the pair from every other volume that prints one, read with the same rules as the first pass (`simple_acreage`), so every printed total is checked the same way.

- Years: the year captions printed between the two tables, read from the page text; the order (previous year first) was checked against the page images for 1885, 1910, 1911, 1921 and 1922. Where two volumes print the same year the figures agree, apart from OCR digit slips.
- 1863 prints both years (1862, 1863) as two blocks of one parsed table; checks are labelled with the year in brackets.
- 1877 prints no table: the page says the agricultural returns for 1877 were found so defective that they were not given.
- 1910 and 1911: the Blue Book year changed, and one table covers January 1, 1910, to June 30, 1911. Its figures carry year_data 1910 and a note giving the period. It is printed in both volumes.
- 1921–1923: the 1921 table is from the Census of Production, 1921. In the 1922 and 1923 volumes only paddy, other grains and cotton are for the year printed; the other crops repeat the 1921 census figures (page footnote), so those figures carry year_data 1921 and a note.
- Footnote marks in a figure or heading (for example the tea totals 1901–1911, which a footnote compares with Ferguson's Directory, or rubber 1914–1921, interplanted or excluding small holdings) carry the footnote text in note.
- Crop names are as printed: Cocoanuts, Coconuts, Cocoa-nuts; Cocoa and Cacao; Pasture and Pasturage. Units as printed (Acres, Acre, OCR "Aeres", "Acrea").
- Not taken in this pass: the district returns that follow later in each volume, and livestock.

## Second printings

Each volume reprints the previous year's table, so most acreage figures are printed twice, set in type and read by OCR separately. `agriculture_second_printing.tsv` pairs every figure with its other printings (same data year, area and crop; printed crop spellings such as Cocoanuts/Coconuts joined): 3,959 pairs, 3,889 the same, 65 different, 5 with one side blank or unreadable. Each figure's note names its other printing; where they differ it gives the other figure and which printing the totals checks favour. The 1921 census figures repeated in 1922 and 1923 are paired too.

Where two printings differ, `totals` / `other_totals` say whether the totals each takes part in add up. One adds up and the other does not in 41 pairs: the one that adds up is most likely the right reading. Neither adds up in 14; both add up in 10, which suggests a revision between editions or two errors that cancel. No figure is changed on this evidence.

## Page-image readings, 1879–1891

The OCR of the opening tables for 1879–1891 misreads many figures: it drops or merges digits (the 1881 volume gives coffee as 34,460 and 36,183 acres for 341,460½ and 361,838½) and confuses 3 with 8 and 5 with 6. These 21 tables (the data years 1879–1891, each printed in its own volume and again in the next where that survives) were read by eye from the archive.org page images. `page_readings/acreage/` holds one file per table, the grid in the parsed table's row and column order with notes on single cells. The readings replace the OCR string in value_as_printed for 1,816 cells; 222 of them differ from the OCR, and those quote the OCR string in note. source_cells.tsv keeps the OCR string. Labels (provinces and crops) are still the OCR's.

- A reading is what the page shows, not a corrected figure. Where the print is faint, broken or blotted, or a 3 prints like an 8, the reading takes the digit the totals and the other printing require, and a note says so. Where a figure is clearly printed but does not add up, it is kept and the note gives what the totals imply: for example 1880 Eastern coconuts (57786, the totals imply 37786), the 1880 tobacco total misprinted 99957, the 1883 coffee total (292779; the provinces add to 292679) and the 1891 cinchona total (12127; Central and Uva add to 12172).
- 1888: the Uva figure for coffee and cacao is printed once (56073) across both columns, and the coffee, cacao and tea totals exclude Uva (page footnote). The reading puts 56073 in the Coffee column, with a note, and leaves Cacao blank.
- Cinchona: the summary table has no cinchona column in 1880 or 1882–1885; this is the printed table, not a reading gap. From 1886 to 1891 the provinces reporting cinchona change from year to year (1886 Central only; 1887 Uva only; 1888 Central only; 1890 Sabaragamuwa 27000).

Misprints in the Blue Book itself stay as printed. 49 printed figures that the page images, the totals, the other printing or the neighbouring years show to be wrong (for example 1885 Western cinnamon 112021, 1863 Southern cotton 105806, 1890 Sabaragamuwa cinchona 27000) are listed in `page_readings/acreage_suspect.tsv` and marked in note with "probable misprint" and the reason. The viewer chart draws them as hollow points.

An outlier check of every acreage series (see `page_readings/README.md`) found five more OCR misreadings outside these tables, read from the page images and applied the same way: `page_readings/acreage_cells.tsv` (1921 Eastern paddy 103380 in the 1922 volume, 1904 Sabaragamuwa paddy 89469 in the 1905 volume, 1895 Northern paddy 52887, 1894 Sabaragamuwa cacao 1111 and North-Western coffee 876). Its other findings (`page_readings/acreage_outliers.tsv`) are figures the page prints, including misprints in one volume that the other volume prints correctly; those are left as printed, and their second-printing notes give the other figure.

## Reading the fields

- The source is OCR, except for the page-image readings above. “As printed” means the supplied OCR string, with whitespace at the edges and trailing dot leaders removed from labels. Single punctuation dots, accents, hyphenation, spelling and OCR errors are retained. Missing-value strings such as `...` are preserved unchanged in value_as_printed.
- Each row corresponds to one selected source measurement cell, including blank and no-figure cells. Zero-based source row and column are recorded in note; the unaltered cell is also recorded in `jobs/agriculture_work/source_cells.tsv`. Repeated expanded province/district heading cells produce no observations.
- Crop and animal names are measure_as_printed. For row-oriented district returns, note gives the exact statistic header (acreage, Gross Produce., or Number.) so acreage and produce for the same crop remain distinguishable. For cultivated-land returns, the lower printed header is the measure and the upper header is retained in note. No synthetic combined measure label is introduced.
- Units are copied from explicit headers or the same source cell. An explicit unit immediately above an observation is used for that observation only. Units are not guessed from a neighbouring crop or a previous district. Numeric portions of cells containing explicit units are separated, with the complete source cell preserved in note. Blank unit means no safe explicit unit was available. Acre/Acres retain their printed forms; no unit conversions are performed. A heading saying only Acreage has no separate unit, so unit_as_printed is blank.
- Decimal parsing accepts ordinary decimals, properly grouped thousands separators, Unicode quarter/eighth fractions and terminating fractions encoded with LaTeX or a spaced numerator/denominator. Explicit typographic footnote markers are retained in value_as_printed and noted when ignored for parsing. Letters are never changed into digits. Narrative returns, mixed/ambiguous numbers and letter-marked numbers remain unparsed with a note.
- Province headings set the parent for district rows. Unlabelled provincial subtotal rows retain an empty area label and are marked printed total. Colony totals retain their printed label (or blank if unlabelled). The 1924 stock table has a split “Province of” / “Sabaragamuwa ..” label: area and parent retain the latter cell, and note preserves the prefix. No area spelling is repaired.
- Scope includes primary crop acreage, gross produce quantities, land acreages, estate counts and current livestock counts. Wage rates, prices, production per acre, seed rates, historical increases, manufactures, mines, dairies and multi-year general progress tables are outside this extract. The district livestock returns of 1902/1904/1912 belong to land_produce_stock; the later combined province/district summary tables belong to live_stock. The small opening colony livestock summaries are also included as live_stock.

## Data years

- Opening Agricultural Statistics: 1869 page 11 lists 1868 then 1869; 1902 page 16 lists 1901 then 1902; 1904 page 18 lists 1903 then 1904. The two acreage tables follow that order. In 1912 the acreage tables lie on separate pages: page 16 explicitly says 1911, page 17 says 1912. Opening stock summaries date each numeric column explicitly.
- The 1869 Western Province produce/stock block (page 535) is dated 1869 by its facing continuation heading on page 536. The cultivated-land table on page 530 has no explicit year; its year_data is left empty.
- The 1902, 1904 and 1912 detailed district crop, stock and cultivated-land returns do not establish a reporting year explicitly in their table/page headings or text. year_data is left empty rather than equated automatically with year_volume.
- The 1924 cultivated/pasture/waste return explicitly reports 1923 (page 397 footnote). For the 1924, 1926 and 1928 livestock summary tables no explicit count year appears on the page: year_data remains empty.
- The 1928 acreage note dates rubber to a July 1928 census. Other crops are estimates based on the 1921 and 1924 censuses: there is no single data year, so year_data is empty with a note.

## Totals checks

1153 acreage total comparisons were attempted: 1000 agree, 105 differ, 48 cannot be checked. Agreement is 1000/1105 (90.5%) of computable comparisons, or 1000/1153 (86.7%) of all attempted comparisons.

Every printed TOTAL row/column in the eight opening acreage tables is checked, including the 1869 corner grand totals in both directions. The 1928 CEYLON row is compared with provinces, and each numeric province summary with its districts; districts are never added again to province totals. Row totals and column totals are separate comparisons, so they may overlap in the cells they assess.

Sums use Decimal with no rounding tolerance. A dash, blank, Nil or dots remains missing in the data; for checking, a sum is the sum of available numeric parts, not an assertion that missing parts are zero. An unreadable nonmissing part makes the comparison uncheckable. No numeric total or no numeric parts is also uncheckable. `agriculture_checks.tsv` contains mismatches and uncheckable comparisons (empty computed sum/difference for uncheckable). Difference is printed total minus computed sum. `jobs/agriculture_work/totals_audit.tsv` includes every comparison, status and missing/unreadable-part counts. Mismatching total cells are flagged in agriculture.tsv; figures are never corrected to make a total agree. Additional land and livestock total comparisons are in `jobs/agriculture_work/other_totals_audit.tsv`; these also flag suspect total cells in agriculture.tsv but are excluded from the acreage agreement percentage.

## Validation

The independent validator checks every output observation against a unique source cell, confirms literal label/unit provenance, independently parses each numeric value using rational arithmetic, reconciles the candidate/skip lists, and independently recomputes the opening crop totals from the source. Results are saved in `jobs/agriculture_work/validation_report.json`.

## Gaps and cautions

- 1889 inputs cover pages 1–282 (tables 9–279), and 1890 inputs cover pages 301–340 (tables 301–339). No target table was found in those supplied fragments; this does not establish absence in the complete historical volumes.
- Most 1869 detailed blocks have unlabelled facing-page continuations, shifted crop/stock columns or subdistrict hierarchies requiring more layout evidence. Only the clear Western Province block and the initial cultivated-land return are used. Subdistrict blocks were not reassigned to district aggregates.
- The uncultivated-land continuation pages in 1902, 1904 and 1912 have no area column and their row alignment with the preceding page is not secure; all are skipped.
- The 1924 Nature of Crops tables have misaligned crop headings/data. Page 395 has 18 columns with 16 numbered positions and Cacao headings over empty columns; page 396 loses the tobacco produce slot and subsequent headings shift. They are skipped in full, including their otherwise clear early columns.
- The 1925 acreage and livestock tables and 1926 acreage table show a province aggregate beside the first district label, followed by shifted district data and an unlabelled last row. They are skipped in full. The 1926 acreage headers also misplace Vegetables. No area labels are reassigned from arithmetic alone.
- The 1928 acreage table has a missing Northern Province Coconuts total despite numeric district acreages; retained as printed and marked uncheckable. Other arithmetic discrepancies are reported, not repaired.
- 1930 page 215 has no parsed table (n_tables=0), though page text contains colony crop/stock summaries and says provincial/district figures were omitted as unreliable. It is not reconstructed as a fictitious table. The 1933 and 1934 crop/stock tables collapse the two adjacent layouts: livestock numbers align with crop names and most crop numbers are absent. Both candidate tables are skipped.
- OCR-looking geographic names and crop spellings remain literal. Dates not explicitly established are deliberately blank. A few Gross Produce cells report money rather than a physical quantity; these are retained in that statistic with their explicit currency text, without conversion. The 1904 Kandy tobacco return reports 10,168,000 cwt.; the suspect magnitude/unit is flagged without changing the source number. No network or external references were used; page images were used only for the 1879–1891 readings.
