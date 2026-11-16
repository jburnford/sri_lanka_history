# Agriculture extract

4,918 observation rows from 53 tables; 3,379 numeric values. Missing-value cells are retained as rows. 24 candidate tables were skipped. All 13 supplied volumes were searched. This is a selective extraction, not complete coverage of every volume.

Rebuild from this folder using the standard library only:

```sh
/home/jic823/miniforge3/bin/python jobs/agriculture_work/extract_agriculture.py
/home/jic823/miniforge3/bin/python jobs/agriculture_work/validate_agriculture.py
```

## Coverage

| Volume | Kind | Tables used (observation rows) |
| --- | --- | --- |
| 1869 | acreage_by_crop | bb1869:p11:t2 (49), bb1869:p11:t3 (49) |
| 1869 | land_produce_stock | bb1869:p530:t1 (150), bb1869:p535:t1 (68) |
| 1869 | live_stock | bb1869:p11:t4 (10) |
| 1889 | — | No tables extracted |
| 1890 | — | No tables extracted |
| 1902 | acreage_by_crop | bb1902:p16:t1 (110), bb1902:p16:t2 (110) |
| 1902 | land_produce_stock | bb1902:p680:t1 (86), bb1902:p681:t1 (90), bb1902:p682:t1 (84), bb1902:p683:t1 (104), bb1902:p684:t1 (100), bb1902:p685:t1 (102), bb1902:p686:t1 (102), bb1902:p687:t1 (42), bb1902:p688:t1 (55), bb1902:p689:t1 (25), bb1902:p690:t1 (112) |
| 1902 | live_stock | bb1902:p16:t3 (10) |
| 1904 | acreage_by_crop | bb1904:p18:t1 (110), bb1904:p18:t2 (110) |
| 1904 | land_produce_stock | bb1904:p726:t1 (88), bb1904:p727:t1 (92), bb1904:p728:t1 (84), bb1904:p729:t1 (104), bb1904:p730:t1 (102), bb1904:p731:t1 (102), bb1904:p732:t1 (106), bb1904:p733:t1 (48), bb1904:p734:t1 (50), bb1904:p735:t1 (25), bb1904:p736:t1 (112) |
| 1904 | live_stock | bb1904:p18:t3 (10) |
| 1912 | acreage_by_crop | bb1912:p16:t4 (110), bb1912:p17:t1 (110) |
| 1912 | land_produce_stock | bb1912:p253:t1 (78), bb1912:p254:t1 (98), bb1912:p255:t1 (88), bb1912:p256:t1 (110), bb1912:p257:t1 (92), bb1912:p258:t1 (82), bb1912:p259:t1 (72), bb1912:p260:t1 (74), bb1912:p261:t1 (41), bb1912:p262:t1 (32), bb1912:p263:t1 (44), bb1912:p264:t1 (112) |
| 1912 | live_stock | bb1912:p17:t2 (10) |
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

## Reading the fields

- The source is OCR, not page images. “As printed” means the supplied OCR string, with whitespace at the edges and trailing dot leaders removed from labels. Single punctuation dots, accents, hyphenation, spelling and OCR errors are retained. Missing-value strings such as `...` are preserved unchanged in value_as_printed.
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

254 acreage total comparisons were attempted: 200 agree, 17 differ, 37 cannot be checked. Agreement is 200/217 (92.2%) of computable comparisons, or 200/254 (78.7%) of all attempted comparisons.

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
- OCR-looking geographic names and crop spellings remain literal. Dates not explicitly established are deliberately blank. A few Gross Produce cells report money rather than a physical quantity; these are retained in that statistic with their explicit currency text, without conversion. The 1904 Kandy tobacco return reports 10,168,000 cwt.; the suspect magnitude/unit is flagged without changing the source number. No network, external references or page images were used.
