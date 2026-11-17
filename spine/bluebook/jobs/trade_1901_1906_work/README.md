# Repair of the 1901–1906 trade reader

The repaired reader writes the original three filenames and original columns. The default run still reads 1901–1906; the original `Reader` remains for earlier layouts. Only `read_trade_old.py`, this work directory, and the three authorized generated outputs were written. No network or page images were used. All programs use the standard library and `/home/jic823/miniforge3/bin/python`.

The output has **79,371 measure rows before and 78,964 after**. Removal is not counted as a successful transcription. Query counts below overlap and are not estimates of all errors in the corpus.

## Reproducing the audit

```sh
/home/jic823/miniforge3/bin/python read_trade_old.py
PYTHONDONTWRITEBYTECODE=1 /home/jic823/miniforge3/bin/python jobs/trade_1901_1906_work/audit.py
```

`before_read_trade_old.py`, `before_trade_1880_1906.tsv.gz`, and the two baseline diagnostic TSVs preserve the baseline. `audit.py` contains the actual before/after query predicates and the explicit expected labels transcribed from the reviewer’s reports. Its results are in `audit_summary.json`. `before_summary.txt` and `after_summary.txt` preserve the reader’s printed tables. `ocr_cases.txt` records the sampled tables with zero-based source row numbers.

Each recheck matches **table_id, source row, measure**, never an article name or a value. Tea can produce two matches because Black and Green share a measure; `matches` records this, and the match retaining the sampled printed figure is selected. `recheck.tsv` retains every original sample column, the old verdict, page evidence, new labels, expected labels, and an explanation of the judgement. Comparison ignores continuation furniture, whitespace, case, and surrounding full stops. It preserves spelling, commas, and the presence of a heading dash. A changed label is not called fixed merely because it looks better.

## The nine defects and their counts

Counts are emitted **measure rows**, except those explicitly called source rows. The named functions below are executable queries in `audit.py`; the supplementary counters are also in that file.

| Defect / query | Before | After |
|---|---:|---:|
| 1. Example stale prefixes or bare Other/Tinned/Free/Bone/Gingelly (`heading_examples`) | 4,572 | 1,437 |
| 2. Article begins with a class/group fragment (`fused`) | 7,242 | 0 |
| 3. Article Cotton under group (b) Cotton (`cotton`) | 213 | 0 |
| 4. Quantity unit contains country-list leaders/quotes/group text (`collapsed`) | 990 | 0 |
| 5. Brace in quantity country/unit label (`brace`) | 227 | 0 |
| 6. Country ends Pos- or begins sessions (`wrapped_fragment`) | 48 | 0 |
| 7. Country contains contd/carried/brought-forward text (`furniture`) | 375 | 0 |
| 8. Government Stores measure rows identified by ledger/page ranges (`gov`) | 1,803 | 1,788 |
| 8. Rows carrying the Government Stores note | 0 | 1,788 |
| 9. Tea rows explicitly labelled Black or Green (`tea_components`) | 0 | 434 |

1. **Sub-entry headings.** `HeadingEvidence` reads the six volumes’ OCR before extraction. A literal inline heading/leaf pair, or the first leaf following a dashed heading, anchors membership. Other leaves must recur in at least two flow/volume runs, remain alphabetically ordered, and lack independent top-level evidence in the same major class. “Other” and similar descriptive words are strong continuation evidence. A descent by a non-generic leaf ends a candidate run; an implicit leaf that crosses past the parent with the same initial is not learned from order alone, since this readily swallows the next alphabetical article. Food/narcotics/live-animal contexts are separated from raw materials, so the two meanings of Tea do not teach each other.

   At extraction time, known membership, descriptive leaves, or an ordered leaf before the parent retain the heading. An unknown name that advances the top-level order drops it. Conflicting or otherwise undecidable evidence leaves the literal name bare and appends `heading uncertain: may belong under "<heading>"`. The emitted spelling always comes from the current OCR; a final-h spelling variant can inform membership but does not replace the name. Headings sharing a country-group cell now work. Continuation article names such as Tea and Dyed do not establish new parents. **24,711 retained output rows have changed article labels**, including the other article repairs below; **2,107 rows explicitly retain heading uncertainty**. The broad example query still matches 1,437 rows: these are not all established errors, and not all bare descriptive names were resolved. The sampled stale Rifles/Shells/Stones/Railway labels and Seeds/Manure/Machinery/Coir/Unenumerated examples were repaired, apart from cases withheld as collapsed blocks.

2. **Class/group text.** A structural lexer consumes class numerals and named group prefixes independently of article labels. It handles merged continuation headings, class tails in the country cell, and literal OCR numerals `1`/`11` without changing them to Roman numerals. Repeated continuation headings retain the parent; a changed class or group resets it. **37,749 retained rows changed class text and 17,178 changed group text**; these overlapping totals include punctuation and context repairs. The 7,242-row fused-heading query falls to zero. Numbered Rails/Sleepers entries are article enumerations and are excluded from this query. `(6) Miscellaneous` remains literal where OCR has `(6)` and the reviewer says `(b)`; it is not silently corrected.

3. **Group named as article.** A group heading is pending until the next useful row. A literal article-only row, including a label duplicated across every OCR column, supplies the article and clears that pending fallback. Apparel can still be named from its group when there is no separate article label. All **213 measure rows** called Cotton under `(b) Cotton` cease matching that error query; sampled Lace and Net rows now say Lace and Net.

4. **Collapsed blocks.** Article data are buffered. A unit must be a recognized literal unit; country-list leaders, quotes, fragments, combined ambiguous units, or unreadable braces invalidate the block. Both malformed country rows and their apparently readable totals are withheld, so garbage never propagates as the total’s unit. The country-list-unit query drops **990 → 0**. **526 source-row skip records** have the collapsed/ambiguous-unit reason; other malformed rows in those blocks also have plain-number/layout skip reasons. The collapsed articles were not reconstructed from a guessed list alignment.

5. **Units and braces.** A suffix parser recognizes units even when leaders are absent (`United Kingdom No.` or `Asia pkgs.`). In a clear braced pair, a unit-only second line inherits the preceding country and country group; `{` is removed from the unit, and each figure remains on its own source row. Article totals and country sums are compared separately by quantity unit, while values remain shared. There are **240 emitted measure rows with a braced-unit-line note**, and **227 → 0** brace-corrupted quantity labels. No article was rejected specifically for an unassignable brace-country pair in this corpus; combined or otherwise unrecognized units are covered by the unsafe-block rule. The sampled Austria/doz., Germany/yds., Switzerland/yds., and Rifles/No. cases agree with the reviewer.

6. **Wrapped countries.** Hyphenated words and parenthesized country names are joined. If both halves contain figures, the remainder of that country group is examined as separate ordered label and figure sequences. Reassociation requires matching sequence lengths and a trailing country label with no figures; discarded suffix vectors contain no digits. Otherwise the ambiguous extra vector is skipped. Source provenance follows the figures. Totals are checked after buffering the article; a mismatch or missing total adds `possible row shift after a wrapped country name` to its country rows. **48 → 0** exposed Pos-/sessions fragments; **735 emitted rows** carry join/reassociation notes, and **687 carry the possible-shift warning**. The reviewed 1905 Tea figure 26566 now belongs to Tasmania, while 126879 belongs to Straits Settlements. Many wrapped articles still do not balance, so this is not a claim of universal shift recovery.

7. **Non-data rows and totals attached to the next article.** Continuation text, including fragments preceding a genuine country, is removed before parsing countries. Carried-over/brought-forward rows are skipped. Blank figures on a country-group marker are skipped as a lost country, rather than invented as an article total. **43 source rows** have that lost-country reason. An exception for a new article label sharing the previous total’s row is accepted on a country-group line only when its figures equal the previous countries’ sums. This puts 7334 on Bricks and Tiles, not Cable/Cordage/Twine. The furniture-country query drops **375 → 0**, including both sampled not-on-page rows.

8. **Government Stores.** `pages/<year>.jsonl.gz` confirms the General Imports of Government Stores headings at 1904 page 711, 1905 page 730, and 1906 page 733. Their text identifies the second ledger; the reader resets article/class/group state on entry. All **1,788 retained measure rows** on the specified ledger pages carry `government stores imports`, compared with zero before. The 15-row decrease from the old ledger output reflects the general parsing/skipping repairs, not a suppression of this ledger.

9. **Tea exports.** Tea outside an article heading such as Seeds or Machinery is read with separate Black and Green components. Six-figure rows represent Black, Green, quantity total, and the three values; seven-figure rows include other-produce quantity. A merged first cell can be split into its two literal figures. The quantity identity and value identity must both fit; the code never repairs a digit to make them fit. Both colour figures use `quantity_ceylon_produce`, distinguished by `component black` / `component green`. Their totals are combined only for checking, never to replace the printed output figures. **434 component rows** are emitted (217 Black, 217 Green); **69 source rows** fit no supported reading and are skipped. Seeds— Tea retains its cwt. seed meaning. No claim is made to recover absent or malformed Tea figures.

## The 240-row recheck

| Old verdict | Yes | No | Removed | Cannot tell |
|---|---:|---:|---:|---:|
| cannot_tell | 0 | 0 | 0 | 1 |
| not_on_page | 0 | 0 | 2 | 0 |
| ok | 137 | 4 | 9 | 0 |
| wrong_article | 57 | 6 | 1 | 0 |
| wrong_country | 4 | 0 | 1 | 0 |
| wrong_unit | 3 | 0 | 11 | 0 |
| wrong_value | 0 | 2 | 2 | 0 |
| **Total** | **201** | **12** | **26** | **1** |

Of the 85 originally marked wrong_article/wrong_unit/wrong_country/not_on_page, **64 now agree, 15 were removed, and 6 remain disagreements**. The four “ok” cases still judged no have explicit reviewer caveats: nested Wines/Burgundy, Arms/Revolvers, and two Durable/Dutiable cases. They are not newly discovered page evidence.

## What remains unrepaired

- Sample 50 still lacks the outer Wines, still heading above Burgundy— In bottle. General nested parent hierarchies are not fully reconstructed.
- Sample 162 remains bare Revolvers rather than Arms— Revolvers.
- Samples 187–190 retain the OCR spelling Carriages and Car- riages. “Carriages and Carts” is not supplied by that OCR article cell, so it was not substituted from another year.
- Samples 198–199 retain Durable rather than the reviewer’s Dutiable.
- Samples 226–227 have the correct article Fibre— Coir and refreshed class, but their literal OCR group `(6) Miscellaneous` disagrees with the reviewer’s `(b) Miscellaneous`; the preceding `(3) Other` is also not reconstructed into that malformed group.
- The four reported OCR figure errors were not corrected. Two collapsed Fish totals were withheld with their blocks; the Machinery total 43799 and Military/Naval quantity 9 remain unchanged. The damaged Brass total remains “cannot tell.”
- Collapsed country lists, unsupported Tea readings, lost country labels, other layout failures, and unresolved heading relationships remain in skipped output or carry uncertainty notes. These counts and the total checks show that the whole corpus is not certified error-free.

## Validation

`audit.py` checks all 78,964 emitted rows: every nonblank printed figure occurs in its own OCR source row (or is one of the literal components of a merged Tea cell), and every numeric `value` equals that raw figure with thousands commas removed. **Zero numeric-provenance errors.** It also asserts 240 recheck records, no blank article names, no brace-corrupted quantity labels, and no country-list units. Reader execution and the audit pass with the specified interpreter. The row schema and diagnostic schemas are unchanged. Lower article counts in some flows reflect structural headings ceasing to be spurious articles; skipped blocks are excluded from the new article denominator. Arithmetic agreement is diagnostic, not label verification, and several flow totals still have substantial disagreement.

## Reader’s printed table before

```text
volume flow   figures  articles  with_total  all_agree
1901   import    6,855       343        285       226  79.3%   skipped rows 171
1901   export    6,786       220        131       103  78.6%   skipped rows 171
1902   import    6,291       332        269       145  53.9%   skipped rows 220
1902   export    6,756       212        126        89  70.6%   skipped rows 220
1903   import    5,931       292        247       192  77.7%   skipped rows 217
1903   export    6,336       169        127       110  86.6%   skipped rows 217
1904   import    6,579       440        298       238  79.9%   skipped rows 255
1904   export    6,126       161         99        77  77.8%   skipped rows 255
1905   import    6,963       470        297       264  88.9%   skipped rows 211
1905   export    7,218       170        123        92  74.8%   skipped rows 211
1906   import    7,266       485        330       287  87.0%   skipped rows 222
1906   export    6,264       170        124       103  83.1%   skipped rows 222
```

## Reader’s printed table after

```text
volume flow   figures  articles  with_total  all_agree
1901   import    6,645       330        279       224  80.3%   skipped rows 278
1901   export    6,588       182        128       103  80.5%   skipped rows 278
1902   import    6,396       319        268       147  54.9%   skipped rows 166
1902   export    6,852       183        134        89  66.4%   skipped rows 166
1903   import    5,865       289        242       200  82.6%   skipped rows 203
1903   export    6,655       170        134       113  84.3%   skipped rows 203
1904   import    6,270       427        282       236  83.7%   skipped rows 346
1904   export    6,216       158        111        91  82.0%   skipped rows 346
1905   import    6,753       463        301       265  88.0%   skipped rows 303
1905   export    7,032       164        130       104  80.0%   skipped rows 303
1906   import    7,272       484        334       290  86.8%   skipped rows 203
1906   export    6,420       168        126       109  86.5%   skipped rows 203
```

“Skipped rows” is the reader’s per-volume count, repeated on both flow lines. These are source-row skip records, not emitted measure counts.
