# Third repair of the 1901–1906 trade reader

The same three output files and schemas now contain **78,575 measure rows**, down from **79,072**. The audit checked every emitted figure against its own OCR source row and found **zero numeric provenance errors**. All extraction and checks used the standard library and local OCR. The supplied scan verdicts provided the page evidence.

| Item | Whole-output query | Before → after |
|---|---|---:|
| A | Measure rows on source rows quarantined for suspected country displacement | 573 → 0 |
| A | Measure rows from the three realigned Yellow Metal source rows | 6 → 9 |
| B | Cinnamon Plantation/Quills and Chips component measures | 0 → 278 |
| B | Cinnamon Plantation other-produce quantities, including genuine ones | 110 → 56 |
| B | Black/Green component measures on export Tea | 434 → 627 |
| B | Black/Green component measures on plain Tea at bb1903:p687 | 12 → 0 |
| B | Port— In bottle, China, quantity cells at bb1903:p635 | 2 → 0 |
| C | Bare Guns, double / Grapes / Mutton and Poultry and Game in the reviewed groups | 348 / 144 / 159 → 0 / 0 / 0 |
| C | Measures headed Printing Materials | 0 → 102 |
| D | Quantity records with a blank unit | 802 → 430 |
| E | Measures in source rows withheld for reviewed group conflicts | 1,626 → 0 |
| E | Retained measures with a literal numeric subgroup nested under (3) Other | 0 → 306 |
| E | Pearls and Precious Stones measures carrying a group | 84 → 0 |
| F | Gibraltar Green dash flagged by the scan | 1 → 0 |
| G | 1902 Tea export measures | 0 → 371 |

Counts refer to emitted measures unless otherwise specified. Queries overlap. The before files are snapshots of the second repair's output and rechecks.

## A. Country and figure alignment

At bb1902:p607, the OCR put the first colony's figures on the group marker, the next vector beside British India, and the total beside Mauritius. Source row 17 now carries British India and 900, row 18 carries Mauritius and 87, and row 19 is the total. Yellow Metal is its own heading. The United Kingdom value was withheld because OCR has 1380 where the scan reads 1330. Its quantities remain.

At bb1902:p613, the OCR spread the country names over the brace lines. It put 68688 / 58688 on the Straits Settlements label even though that line belongs to British India. The neighbouring brace lines and later repeated country names leave the wider alignment ambiguous. The reader withholds 21 source rows in that span, including sample 54 and its erroneous home-consumption figure.

The reader checks figures attached to bare country-group markers or markers sharing a unit line throughout all six volumes. It accepts a previous article total when its figures agree with the buffered country sums. A braced second line can be assigned to its preceding country when explicit leaders separate the marker from the unit and the preceding country has a braced line. The marker still takes effect on the next named country. With ambiguous markers, the reader withholds the ensuing run until an independent article label. It also withholds earlier export rows in the same buffered run whose value columns fail their own sum when the marker signals a possible displaced column.

The corpus scan found **52 marker rows in 27 tables**. One was realigned from the page check, five were verified totals, two were usable second unit lines, and **44 other marker rows were withheld**. In total, **177 source rows** in affected spans were withheld for alignment, including the 21 braced rows. The 573 previously emitted measures on those sources are gone. The marker inventory records every disposition. [round3_country_markers.tsv](round3_country_markers.tsv)

## B. Quantity columns

Cinnamon uses the literal Plantation/Chips or Quills/Chips header. Both component cells use `quantity_ceylon_produce` with a component note. The reader also recognizes the wrapped 1901 header and its continuation. An ordinary other-produce quantity is emitted when the OCR contains that separate cell. In the 1905 Cinnamon block the OCR crops the rightmost value for 25 source rows. Two 1902 Cinnamon rows failed the component quantity identity and were withheld.

Tea requires Black/Green header evidence on the page or on the adjacent page of the same Tea run, corroborated by the row layout and component sums. The 11-column OCR continuation at bb1903:p683 uses the header from bb1903:p682. Plain raw-material Tea at bb1903:p687 uses the ordinary columns. British India's 42 and the United Kingdom's 9 are both ordinary Ceylon-produce quantities. For China at bb1903:p635, both quantity cells are withheld because OCR reads `1` in cells that the scan shows as dashes. The literal value of Rs. 1 remains.

## C. Article headings

The membership heuristic rejected valid siblings after a descending name such as Guns, single → Guns, double, or because a leaf also occurs at the top level elsewhere. The reviewed ordered families establish membership where the current OCR contains the heading and its leaf. Across the reviewed groups, **651 bare measures** in the table above disappear. Full family labels rise **225 → 573** for Arms, **408 → 552** for Fruit, fresh, and **111 → 306** for Meat, frozen, including other supported siblings.

A separate fused-label heuristic split the literal Printing Materials into Printing and Materials. Keeping the complete OCR name yields 102 measures, including 93 on the same source and measure as a formerly split label.

## D. Units

A heading carrying an explicit unit on its first data line can share the following leaf label when membership is supported. This recovers cwt. for Unenumerated— Dutiable and Coffee— Arabian— Native. Explicit ditto marks can inherit a unit across neighbouring leaves under the same parent, including Bars from Silver— Bullion to Silver— Coin. The reader also separates a literal unit from the figure in the first quantity cell on six source rows, including reams and cases at bb1903:p668.

**359 retained quantity measures** acquire a unit, 239 on rows with recognized ditto markers. The broad blank-unit count still includes rows with no usable unit evidence. On bb1903:p668's Photographic Materials total, the 266 total gets cases. Its companion home-consumption cell is withheld because the scan shows an illegible trailing digit that the OCR omits.

## E. Classes and groups

A numeric OCR token on a Miscellaneous or Timber subgroup stays literal and occupies the subgroup level under its recorded numbered parent. Repeated numbered headers preserve their recorded subgroup. The six reviewed conflicting headings are withheld across their affected spans, **275 source rows** in all. The skipped file records the literal tokens, including `(3) Other (4) Miscellaneous` at bb1902:p656 and `(3) Other (6) Miscellaneous` at bb1906:p716. It also records the reviewed `(8) Other` and `(2) Other` conflicts. The reader does not replace those numerals with the scan's letters or numbers.

The wrapped `IV.—Bullion and` / `Coin.` title at bb1903:p702 is joined from the OCR. Entering the new class clears the previous group's state. The missing 1902 export class at the beginning of the ledger remains a limitation of the OCR.

## F. Blank and dash

Gibraltar's Green cell at bb1903:p682 is blank in the scan but contains a dash in the OCR. That component is withheld with a specific reason. The surviving Black, other-produce and total figures stay on source row 37.

## G. 1902 Tea

The 12-column OCR continuation at bb1902:p651 was excluded by the 8/9-column table selector. Its explicit Black/Green and produce headers now identify the seven data columns, recovering **161 measures on 23 source rows**. On bb1902:p650 the six OCR cells cover four quantities and two values. The rightmost total value is absent. With the continuation header and a unique valid interpretation of each retained row, that page yields **210 measures on 35 source rows**. The 35 missing total values have explicit skip records.

Two p650 rows remain withheld. The United Kingdom OCR gives 103182944 and 411514 against total 103593858. Malta gives 351665 against total 351565 with both other quantities shown as dashes. The OCR cannot establish which figure in either vector is wrong.

## Rechecks and reproduction

[recheck3.tsv](recheck3.tsv) includes all **279** samples with the original verdict, the expected and new fields, and a judgement. **267 agree, 11 were withheld, and one is still ambiguous**. Of the 28 originally marked wrong, 21 now agree and seven were withheld. Four other rows had a verdict of “ok” but the scan notes explicitly identify a contradictory group numeral. Sample 82's damaged glyph remains ambiguous. Matching uses table ID, source row and measure. Component notes distinguish parallel measures, and sample 72 records the corrected measure on the same source row.

The first earlier recheck moved from 197 to 184 agreements. Previously agreeing samples **137–144** (bb1904:p697) and **228–232** (bb1906:p716) are now withheld because of the reviewed group conflicts. Its previously disagreeing samples **226–227** also became withheld. The second earlier recheck still has **224 agreements and 14 disagreements**, with no row worse under its original expectations. The row-by-row comparison is in [recheck_round3_earlier_regressions.tsv](recheck_round3_earlier_regressions.tsv).

From the repository root, run:

```sh
export PYTHONDONTWRITEBYTECODE=1
/home/jic823/miniforge3/bin/python read_trade_old.py
/home/jic823/miniforge3/bin/python jobs/trade_1901_1906_work/audit_round2_first.py
/home/jic823/miniforge3/bin/python jobs/trade_1901_1906_work/audit_round2.py --round3
/home/jic823/miniforge3/bin/python jobs/trade_1901_1906_work/audit_round3.py
```

The `--round3` switch bypasses the older claim that only Perfumery may lose a figure/country pair. The original scan expectations and provenance checks still run. Executable before/after queries and results are in [audit_round3.py](audit_round3.py) and [round3_audit_summary.json](round3_audit_summary.json).
