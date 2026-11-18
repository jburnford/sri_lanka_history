# Ceylon directory section survey

The inventory covers 37 OCR folders and 27,921 PDF pages from the 1871–72
through 1969–70 editions. The 1,198 section rows follow PDF order, including
repeated and displaced leaves. Each held PDF page is assigned once. The two
1883–84 Part 2 scans are counted separately. The input is the local layout OCR
and the source registry at `../../sources/ocr_registry.tsv`. The survey
excludes estate-only extracts and directories whose scope extends beyond Ceylon.
The tables record
section headings, dates, layout and page ranges. They contain no directory entries.

## Rebuild and read the tables

Run the rebuild from `spine/directories/`.

```sh
/home/jic823/miniforge3/bin/python -B survey/survey.py
```

Set `CEYLON_OCR_ROOT` to choose an OCR root. The script checks the local and
office paths in that order when the variable is unset. It reads the original
`pdf_page` values and matches batch folders to their unsuffixed registry rows.
It surveys 1922 first, then archive.org 1920–21, then the other folders by
starting year. The build writes `volumes.tsv`, `sections.tsv`, `coverage.tsv`
and `validation.json`. The manual audit is recorded in `audit.tsv`.

The section map uses contents references, running heads, section titles, OCR
block types and table widths. The reviewed ranges and reasons are in
`boundaries_overrides.tsv`. On pages with two sections, the running heading,
the dominant material and the surrounding sequence determine the page
assignment. Estate-name indexes count as `estates_directory` because they
look up estates by English or vernacular name. Other indexes and contents
pages appear in the volume inventory. Publisher catalogue contents are included
where identifiable. Classified trade lists are `trade_lists` when the
organising unit is the trade, including trade lists grouped by town.

The additional class `reference_material` covers standalone terminology
tables, such as the tables of local titles and English equivalents.
`unclassified` covers seven pages where the section type remains unclear or
the material is too fragmentary to place. Printed numbering is the reading
from the page header where legible. A slash separates multiple readings on a
scan, including two-page spreads. Empty printed numbers indicate no usable
header number. Correction dates are transcribed as read, with anomalies noted.

`ocr_condition` measures the share of pages where the expected table, list
or prose structure is recoverable from OCR blocks. Good is at least 85%,
mixed is 50% to under 85%, and poor is below 50%. It measures structure at the
section level. `confidence` records confidence in the class and its boundaries.

## Coverage and extraction candidates

Coverage cells count held PDF pages. A zero means the held material supplies
no pages in the class and there is no specific reason to expect a missing
section in the supplied scan. A question mark means the available pages
cannot establish absence. When a section is partly held, its cell gives the
pages present. Year labels use the first year of the edition. Where the year
repeats, the part, alternate scan or repository distinguishes the columns.
Counts include advertising and repeated scans where held.

| Section type | Folders | PDF pages | Comparable layout |
| --- | ---: | ---: | --- |
| General alphabetical addresses | 34 | 6,835 | 5,772 pages of alphabetised names with occupations and addresses in 32 folders |
| Estates | 30 | 5,948 | 3,874 pages of estate, owner, agent, acreage and crop tables in 26 folders |
| Associations and institutions | 21 | 1,065 | 521 pages of institutional rosters in 13 folders |
| Trade lists | 21 | 739 | 339 pages of names grouped under trade headings in 16 folders |
| Registered companies | 14 | 659 | 281 pages of capital and director profiles with property tables in seven folders |
| Colombo merchants | 13 | 894 | 143 pages with an agencies column and 751 with business and agencies |
| Outstation merchants | 12 | 254 | 99 pages of firm, staff and address tables alongside trade lists in 12 folders |

Government material totals 3,213 pages across 23 folders. It ranges from
department rosters to tax law and fee schedules. Professional material recurs
in 27 folders, with 551 pages. The main runs cover different professions,
including lawyers, surveyors, hospital staff and visiting agents.

The 1922 pilot aligns with PDF 462–465 for associations, 466–467 for banks,
468–500 for Colombo firms and 548–555 for the Kandy merchants and trade
directory. The Chamber material starts in progress at PDF 462. The printed
sequence jumps from 418 to 424. In the archive.org 1920–21 copy, PDF 258–265
contains associations, 266–267 banks, 268–306 Colombo merchants and 363–367
the Kandy directory.

## Missing PDF pages

Twenty-one folders are missing their first OCR batch or batches. Every range
below starts at PDF 1 in the registry. The held ranges and totals are in
`volumes.tsv`.

| Missing PDF pages | Editions or copies |
| --- | --- |
| 1–1000 | 1902 archive.org, both 1904 and both 1905 copies, 1907 archive.org, 1909, 1925, 1943, 1949, 1950, 1956, 1967–68 |
| 1–2000 | 1937, 1940, 1941, 1942, 1960–61, 1963, 1964, 1969–70 |

The eight folders missing PDF 1–2000 are too partial for whole-volume
comparison. They hold 114–517 pages each. The 1940, 1963 and 1964 batches
are principally address pages. Several batches starting at PDF 1001 also
begin mid-directory, so they can support targeted work on the sections
they hold. The other 16 folders cover every registry PDF page.

Completeness here refers to the source PDF. The archive.org 1906 copy carries
a registry warning about more than 100 missing source pages. The 1951 PDF
starts mid-reference and ends among the hill estates. The 1955 PDF starts
mid-calendar after advertisements and ends in the industrial tables. The
1959 PDF jumps from local government to the middle of the trade lists and
from the opening estate index to partway through men's addresses. The
1956, 1960–61, 1964 and 1967–68 scans end within a named section. Missing
printed leaves have no assigned PDF ranges.

## Changes visible across the run

- An early directory is also an almanac. The 1871–72 volume places a long
  reference section, a coffee manual and commercial conversion tables before
  the staff and business directories. In 1920–21 the dated chronology fills
  nine PDF pages.
- The Colombo merchant table is recognisable over many editions. The 1871–72
  copy holds three pages of it, 1922 holds 33 and 1946 holds 121. In the 1940s
  the third column describes the nature of the business and its agencies.
- Estate lookup changes direction. The 1880s and 1900s include separate
  English-to-vernacular and vernacular-to-English indexes. The held 1969–70
  index shows vernacular names beside the estate and a page reference.
- Address organisation varies even in adjacent decades. The 1925 copy
  has one alphabet, and 1937 has separate men's, ladies' and overseas
  series. The supplied 1943 and 1944 volumes use a combined alphabet.
  The later address sections again frequently distinguish those series.

## Audit and weak spots

The first pass used `random.Random(19221920)` and drew eight sections per
folder or all sections when fewer than eight were available. For each row,
the first page, last page and next held PDF page were read from the OCR.
The preceding page was also checked where held. At the end of a batch or
PDF, the missing successor was recorded as outside the held OCR.

On the first pass, 227 of 282 sampled rows agreed on all three checks.
Class agreed on 268, start on 262 and end on 253. The 55 rows with a
disagreement were revised. Splits and merges yielded 62 distinct corrected
rows to recheck. All 62 agreed on recheck. The two passes and original ends
are in `audit.tsv`. To inspect the current deterministic sample, use
`survey.py --review-audit`. Use the displayed volume number with
`--volume-from`, `--volume-to` and `--review-starts` for specific revised rows.

Generic `DIRECTORIES` heads, mixed-content spreads and advertising banners
are the most difficult boundaries. Institutions can contain schools and
religious bodies under the same printed section. The 1883 alternate scan,
the two overlapping 1951 mercantile runs and other repeated leaves affect
historical page-count comparisons. Some printed numbers and correction
years are visibly inconsistent in OCR. See the volume and section notes
before using those numbers as extraction identifiers.
