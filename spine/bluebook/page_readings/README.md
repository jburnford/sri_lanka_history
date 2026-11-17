# Page readings

Figures read by eye from the archive.org page images, where the OCR in `tables/` is too poor to use. Each file is one parsed table (`bb1880_p8_t5.tsv` is `bb1880:p8:t5`) and is used by `jobs/agriculture_work/extract_agriculture.py` in place of the OCR strings for that table's figures.

## acreage/

The opening "Agricultural Statistics" (acres by crop and province) for the data years 1879–1891: 21 tables in the volumes for 1880–1892, every printing of those years in the collection. The page images are `https://archive.org/download/<identifier>/page/n<pdf_page - 1>.jpg` (identifiers in `volumes.tsv`).

Format, tab-separated:

- The first line names the columns (crops as printed, after a `#` corner cell). The remaining lines are the province rows and then the printed total row, labelled `TOTAL` whether the page labels it "Total" or leaves it blank. Rows and columns are in the same order as the parsed table, starting below its crop and units rows; the extractor checks that the labels line up.
- Cells are as printed: `½` and `2/9` fractions, `—`, `-`, `...` and `..` for no figure, `*` footnote marks.
- A line starting `!` is a note on one cell: `! <row>	<column>	<note>`. Notes say where a digit is faint, broken, blotted or ambiguous (in several of these volumes a 3 prints like an 8), which reading the totals and the other printing support, and where a clearly printed figure does not add up.

A reading records what the page shows. Where the print is clear but a figure does not add up, it is kept as printed and the note says what the totals imply.

## acreage_outliers.tsv

An outlier check on every acreage series (crop × area) for 1862–1923, outside the 1879–1891 tables already read. A figure is flagged when its ratio to the median of its neighbours (up to two years either side) lies more than two standard deviations from the series' own spread of such ratios, is at least 1.5 times off, and is at least 50 acres: 186 flagged printings, 106 distinct figures.

- 62 are printed the same in two volumes, each read by OCR separately, so they are what the Blue Book printed; they were not looked at further.
- The other 44 (one printing only, or two printings that differ) were checked against the page images, or against the printed totals where the row and column both add up. The file lists the ones looked at on the page, with a verdict: `ocr_error` (the page prints something else), `misprint_in_one_printing` (one volume's printing is wrong, the other's is right) or `as_printed` (the page prints it, often a figure the totals carry but neighbouring years contradict).

The five `ocr_error` cells are applied from `acreage_cells.tsv` (which now also holds the 34 cells found on review, below) (one row per cell: table, zero-based source row and column, the reading, a note), the same way as the table readings. The other findings change nothing: a misprint in one volume is left as printed, and its second-printing note in `extracted/agriculture.tsv` gives the other volume's figure. One `ocr_error` finding is not applied: 1894 Sabaragamuwa paddy, whose last digit is broken (8099?) but whose fourth digit is a clear 9, so the reading the total needs (80977) is not what the page shows.

## acreage_suspect.tsv

Printed figures that are probably wrong at source, or not comparable with other years. Each was checked on the page image, which prints it as given. One row per printed cell, with its zero-based source row and column, its data year, area, crop and printed value, a `kind` and the reason. A total that includes a flagged part is listed too.

`kind` says how strong the case is:

- `misprint` (15): the totals or the other printing show it (1880 Eastern coconuts 57786, where row and column totals both imply 37786; 1885 Central cacao 892 in the 1886 volume, 8929 in the 1885 volume).
- `source_error` (30): the printed totals carry the figure, so it is not a typesetting slip, but the years either side contradict it (1885 Western cinnamon 112021, against 33955 in 1884 and 33420 in 1886, printed so in both volumes). An error in the return or in compiling it.
- `doubtful` (4): only the neighbouring years speak against it, and they are few or far (1871 Western paddy 379731; 1863 Southern other grain 86821), or a part and its total disagree and either could be wrong (1888 Western cotton 302).
- `shared_figure` (1): 1888 Uva, one figure printed across the Coffee and Cacao columns. Not an error.

The figures stay as printed in `extracted/agriculture.tsv`; the extractor starts the note with "probable misprint", "probable error in the return", "outlier, possibly an error" or "one figure for two columns", then the reason. The viewer chart draws them as hollow red points and scales its axis without them.

## Review, 17 November 2026

The readings and flags were checked against the page images by a second reader.

- 1,316 cells in 16 of the 21 reading files were compared with the scans: none differs from a legible figure, and none departs from the page to make a total agree. One reading was changed (`bb1883_p10_t4.tsv`, the 1882 coffee total: a broken 4 first read as 1) and one form corrected (`0½` for `½`).
- Where a glyph is broken or faint the readings take the digit the totals require. Most such cells have a `!` note; about a dozen do not (for example 1881 volume Northern cotton 154, several broken 4s in the 1880 table, 1885 Eastern coffee 53). The figures agree with the totals and the other printing.
- The readings of the second printing of 1880 (in the 1881 volume) and of 1882 (in the 1883 volume) were partly taken from the first printing's reading, so their agreement is weaker evidence than for the other years.
- 34 more OCR misreadings outside 1879–1891, found by comparing whole tables with the page images, were added to `acreage_cells.tsv`. They are concentrated in fractions (¼ and ¾ read as ½) and in the 1902–1905 volumes.
