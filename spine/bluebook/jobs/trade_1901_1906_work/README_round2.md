# Second repair of the 1901–1906 trade reader

The repaired `read_trade_old.py` writes the same three output files with the same columns. The round-two baseline is the reader/output present at the start of this job, **not** the pre-first-repair output. Output measure rows: **78,964 → 79,072**. Only the authorized reader, work directory and three generated outputs were written. No network, external libraries, or page images were used; the supplied page-image reviews were compared with the OCR and the rebuilt output.

No figure was corrected. All retained baseline figure/country/source-row combinations remain, except **six Perfumery measure rows deliberately withheld**. The additional rows comprise readable article segments previously suppressed after a collapsed block, country rows previously fused into headings, and the first re-headed Cotton row. All emitted figures pass source-row provenance checks, including literal numeric components inside merged cells. Numeric provenance errors: **0**.

## Reproduce

From the repository root, using only the specified interpreter and standard library:

```sh
PYTHONDONTWRITEBYTECODE=1 /home/jic823/miniforge3/bin/python read_trade_old.py
PYTHONDONTWRITEBYTECODE=1 /home/jic823/miniforge3/bin/python jobs/trade_1901_1906_work/audit_round2_first.py
PYTHONDONTWRITEBYTECODE=1 /home/jic823/miniforge3/bin/python jobs/trade_1901_1906_work/audit_round2.py
/home/jic823/miniforge3/bin/python jobs/trade_1901_1906_work/write_report_round2.py
```

`round2_before_read_trade_old.py`, `round2_before_trade_1880_1906*`, `round2_before_summary.txt`, and `round2_before_recheck.tsv` preserve the starting state. The first audit's original helper/results remain; `audit_round2_first.py` reruns its unchanged expectations into `recheck.tsv` and writes separate round-two summary files. `audit_round2.py` defines every query below and generates `recheck2.tsv`, `recheck_round2_regressions.tsv`, and `round2_audit_summary.json`. `round2_table_headers.tsv` records the printed header and interpreted measure order for all **474** selected tables, with zero unrecognized headers. `round2_missing_class_evidence.tsv` records the missing 1902 class evidence.

## A–J changes and executable query counts

Counts are emitted **measure rows**, except where explicitly called source rows. Predicates are named in `audit_round2.py`; overlapping counts are not estimates of all errors.

| Item | Query | Before → after |
|---|---|---:|
| A | `A_orphan_Other_or_Arabian` | 1,449 → 0 |
| A | `A_at_least_three_levels` | 90 → 3,453 |
| B | `B_bare_named_food_subentries` | 669 → 0 |
| C | `C_bare_Liquid_Fuel` | 18 → 0 |
| C | `C_Oil_Liquid_Fuel` | 12 → 30 |
| D | `D_Silver_Pearls` | 249 → 0 |
| D | `D_Desiccated_Fresh` | 372 → 0 |
| E | `E_Arippe_Cinchona_Bark` | 36 → 0 |
| F | `F_Durable_literal` | 15 → 15 |
| G | `G_wrong_cells_on_unequal_reversed_quantities` | 78 → 0 |
| G | `G_reversed_page_quantity_rows` | 454 → 450 |
| H | `H_missing_Cotton_on_two_reviewed_continuations` | 105 → 0 |
| H | `H_1902_export_empty_class` | 1,710 → 1,710 |
| H | `H_literal_1_or_L_class` | 5,721 → 5,721 |
| H | `H_1906_p733_wrong_class` | 0 → 0 |
| H | `H_1906_p721_short_printed_class` | 246 → 246 |
| I | `I_1904_Perfumery_emitted` | 6 → 0 |
| I | `I_Cotton_quantity_other_produce` | 9 → 0 |
| I | `I_Cotton_named_components` | 0 → 20 |
| J | `J_Arrack_British_India_missing_country_group` | 6 → 0 |
| J | `J_country_rows_with_empty_group` (includes valid ungrouped countries) | 10,380 → 9,849 |

**A — Heading stack.** `ModernReader` now keeps the full stack; explicit inline chains and adjacent dashed headings teach each parent/child edge. A repeated heading trims back to its existing level, a nested heading pushes a level, and a known sibling returns to the appropriate ancestor. Families with matching repeated two-leaf structures establish the other Wines sub-headings. This retains Paper— Other— Dutiable, Wines, still— Other— In wood, Coffee— Arabian— Plantation, Machinery— Other— Free, and the other literal three-level chains. Double hyphens are heading separators, not word-wrap hyphens. The starting 795 Other-prefix and 654 Arabian-prefix rows total the 1,449-row orphan query; none remain. A higher three-level count is a structural description, not independent proof that every hierarchy is correct.

**B — Continuation membership.** The evidence pass pools all six volumes and both flows, including nested ordered runs and parenthetical-name variants. Independent homonyms in another class no longer veto the Spices/Coffee/Cocoanut/Oil families. The reader retains heading context separately from a temporarily lost active parent, so readable sub-entries following malformed rows can recover it. An explicit new class or group clears that context. The bare-name query is limited to Food and Drink and the supplied names Wild, Cloves and Mace, Nutmegs, Pepper, Pepper (long), Vanilla, Ginger, Liberian, and Plantation. All 669 formerly bare measure rows acquire their learned heading. Cinnamon, Wild is attested literally in the other volumes; a comma-prefix expansion requires the current preceding article to contain that same prefix. No OCR spelling is replaced by another year's spelling.

**C — Headings in skipped blocks.** Labels and their structural edges are processed before numeric/layout rejection. A collapsed Oil— Castor block therefore still establishes Oil for Liquid Fuel. A legible continuation after an unsafe earlier page starts a fresh buffered segment instead of inheriting the earlier page's rejection. Across the corpus, bare Liquid Fuel falls 18 → 0, and Oil— Liquid Fuel rises 12 → 30. The six reviewed rows on bb1906:p696 all equal Oil— Liquid Fuel.

**D — Branch versus continued leaf.** A continuation suffix does not itself establish a heading. Known leaves such as Desiccated remain under Cocoanut; Fresh returns to that parent. Data-bearing dashed leaves also remain leaves, including when the continuation suffix is on the following OCR row. Pearls and Precious Stones explicitly ends the Silver heading. Two structural relationships supplied in the job are explicit exceptions: top-level Pearls, and Seeds, excluding Food Stuffs— Unenumerated in the reviewed government-store layout. These choose among literal OCR labels; they do not supply corrected spellings. All 249 stale Silver prefixes and 372 Desiccated— Fresh labels disappear.

**E — Consecutive article names.** Wrapping now requires a true word-break hyphen or an attested complete wrapped name. It no longer joins an arbitrary article-only line to the next label. A fused cell containing two independently attested names can be separated when the following country runs have an explicit unit change. Thus bb1906:p714's 36 Arippe Cinchona Bark rows become six Arippe rows with cwt. and 30 Cinchona Bark rows with lb., keeping each figure/country/source row. Related accidental fusions are also removed. Headings/continued leaves displaced onto adjacent data rows are joined as labels without moving their figures.

**F — OCR letters and digits.** No OCR-letter correction was added. All 15 Durable rows stay Durable, including the three newly reviewed disagreements. Duitable is likewise retained in the repaired Seeds chain. Membership may recognize literal singular/plural or final-h variants, but the emitted leaf spelling stays the current OCR spelling. The two new sampled digit errors remain unchanged: 61406 at bb1902:p635 and 205601 at bb1903:p648. Neither spelling changes nor arithmetic balancing are used to repair figures.

**G — Measure headers.** `table_measures` reads each import table's column titles and each export table's Quantity/Value and produce/total header rows. Unsupported titles cause explicit skips rather than positional fallback. The five reversed Paper import tables are bb1902:p636, bb1903:p668, bb1904:p676, bb1905:p695, and bb1906:p698. There are 78 demonstrably wrong quantity assignments where the two cells differ before repair, zero afterward. Equal figures cannot diagnose a swap, so that query excludes them. The total number of quantity records on those pages falls 454 → 450 solely because four Perfumery quantities are withheld under I. All 474 recognized table headers were checked, including exports.

**H — Classes and groups.** Repeating a numbered group now keeps its lettered subgroup, while an explicitly changed class/group resets it. The two reviewed Textile continuations lose 105 missing-Cotton records. Literal class numerals 1 and L are carried through pages without a new printed class and remain literal, never normalized to I; their measure-row count stays 5,721. The lexer also recognizes literal 111. The merged I.—Live Animals—Cattle case already parsed correctly in the starting reader: the class is I.—Live Animals, article Cattle, no subgroup, and the wrong-class query remains zero.

The **1,710 empty 1902 export classes are unrepaired**. The export run opens at p645 with `(1) Animals, Living: Cattle`, without a class numeral. Tables p645–651 contain no class prefix; their page JSON contains no missing class text either. The class state is reset correctly at the change of flow, and cannot inherit a class from the import ledger. The next explicit class is II.—Raw Materials. Filling I would invent an unattested class in that export run. The evidence TSV records the actual headings/text. Also retained is p721's explicit abbreviated `III.—Manufactured`: the page/table OCR supplies no Articles tail. Its 246 rows keep that literal shorter title; the Cotton subgroup is fixed. The single sampled abbreviated-title disagreement remains no.

**I — Quantity sub-columns.** On bb1904:p676, Perfumery's gal./cases headers and vectors do not preserve a reliable row alignment. The entire block is withheld; all **16 source rows** have the explicit reason `quantity sub-columns gal. / cases: OCR row alignment ambiguous`. This removes six formerly emitted measure records, including two value-only/blank-quantity rows which must not survive as apparently safe data. No figures are reconstructed.

On bb1906:p714, the two literal component headers and numeric rows are unambiguous: Kapok or Tree Cotton and Cotton for Spinning are both Ceylon-produce quantities. Both now use quantity_ceylon_produce with their respective `component ...` notes, never quantity_other_produce. The quantity total and the three value columns retain their ordinary meanings. Twenty component records are emitted; the header row's 9083 and 3221 are extracted literally from its two labelled cells, alongside its unchanged total and values. The nine formerly emitted misleading other-produce quantities disappear.

**J — Country groups.** A standalone group marker is pending until its first country/sub-entry and survives the intervening article start; it is consumed by a country row. An explicitly printed United Kingdom line ends a preceding country group, preventing pending foreign/colonial markers from leaking into it. The reviewed British India/Arrack case changes six blank group records to British Colonies. **639 retained records** acquire a previously missing group. The broad blank-group count includes legitimate ungrouped United Kingdom rows and is not an error count.

## The 238-row second recheck

`recheck2.tsv` keeps every original sample field and adds source provenance, old verdict, new article/class/group/measure/country/unit/figure, explicit expected labels, article-only agreement, full judgement and reason. It matches to the round-two baseline to recover source row, then matches the new output by **table_id, source row, measure**. Article text and figures are not used to relocate the new row. A matching literal figure selects among component records sharing a measure.

The sample did not include source row. **237 samples have one baseline match.** Sample 176 has identical Japan/value 13182 records on source rows 69 and 70 of bb1905:p672, the two braced unit lines. Both new rows were checked and have identical reviewed labels/figure; the first is listed, both candidates are recorded, and the source-identity ambiguity is stated. It is not silently claimed that the sample uniquely identifies row 69.

| Original verdict | Yes, all reviewed fields | No | Removed | Cannot tell |
|---|---:|---:|---:|---:|
| ok | 201 | 4 | 0 | 0 |
| wrong_article | 23 | 8 | 0 | 0 |
| wrong_value | 0 | 2 | 0 | 0 |
| **Total** | **224** | **14** | **0** | **0** |

Article labels alone: **235 yes, three no**. Of the 31 original wrong-article cases, 28 now equal the stated page label; the three Durable spellings deliberately do not. Full agreement is stricter: five of those repaired article rows still lack the unattested 1902 class, so only 23 formerly wrong-article rows are marked yes overall. The 14 full disagreements are eight empty-class rows, one abbreviated class title, three Durable spellings, and two unchanged digit errors. No changed-but-unequal label is called fixed.

## Rerun of the earlier 240-row recheck

The original expectations were retained, including their comma/spelling requirements. `recheck.tsv` now has **197 yes, 16 no, 26 removed, one cannot tell**, versus 201 yes, 12 no, 26 removed, one cannot tell at the start of this job. The previously unresolved Burgundy/Wines sample 50 and Arms/Revolvers sample 162 now agree.

**Yes: six formerly agreeing records no longer satisfy the old exact expectations.** They are all retained rows with the same country, unit, measure and figure; the new heading stack adds an outer heading:

| First sample | Previous expected article | New article | Strict result |
|---|---|---|---|
| 51 | Claret— In bottle | Wines, still— Claret— In bottle | no |
| 52 | Claret— In bottle | Wines, still— Claret— In bottle | no |
| 53 | Claret— In bottle | Wines, still— Claret— In bottle | no |
| 54 | Claret— In wood | Wines, still— Claret— In wood | no |
| 158 | Rifles— Magazine | Arms— Rifles— Magazine | no |
| 163 | Rifles— Single | Arms— Rifles— Single | no |

Samples 51–54 inherit Wines, still from the literal multi-level run on bb1901:p582; 158 has Arms— followed by Rifles— on bb1904:p713; 163 follows Arms—contd. and Rifles— on bb1905:p681. The OCR supports retaining those outer headings under repair A, but the earlier review's abbreviated “as in file”/unit-only expectations do not explicitly verify the expanded full label. They therefore remain strict **no**, recorded separately in `recheck_round2_regressions.tsv`; they are not promoted to scan-certified fixes or hidden by rewriting the old expectations.

## What remains unrepaired

- The 1,710 empty 1902 export classes: the needed class text is absent from both permitted OCR sources for that run.
- The p721 abbreviated class title, including one sampled full-agreement failure; its OCR text is preserved.
- The two new OCR digit errors and three new Durable letter errors, intentionally unchanged. Earlier OCR spelling/digit disagreements also remain.
- Perfumery's ambiguous gal./cases block is withheld, not repaired. Existing unreadable/collapsed blocks, unsupported Tea readings, and other skipped layouts remain.
- Six earlier scan checks no longer equal their old shortened expected article labels after full hierarchy restoration. Their figures/countries remain; explicit scan certification of those expanded labels is outstanding.
- The unchanged first recheck still contains other disagreements and removed records. These targeted queries and sum checks do not certify every output label. In particular, unsampled bare sub-entries and damaged/wrapped labels outside the named families can remain unresolved.

## Reader's printed table before round two

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

## Reader's printed table after round two

```text
volume flow   figures  articles  with_total  all_agree
1901   import    6,645       330        279       224  80.3%   skipped rows 278
1901   export    6,588       181        128       103  80.5%   skipped rows 278
1902   import    6,396       319        268       147  54.9%   skipped rows 166
1902   export    6,852       181        134        91  67.9%   skipped rows 166
1903   import    5,865       288        242       200  82.6%   skipped rows 203
1903   export    6,655       168        134       114  85.1%   skipped rows 203
1904   import    6,264       426        282       236  83.7%   skipped rows 348
1904   export    6,216       158        111        91  82.0%   skipped rows 348
1905   import    6,822       464        301       266  88.4%   skipped rows 280
1905   export    7,032       164        130       104  80.0%   skipped rows 280
1906   import    7,311       485        335       290  86.6%   skipped rows 189
1906   export    6,426       169        126       111  88.1%   skipped rows 189
```

Skipped rows are source-row records counted once per volume and repeated on its two flow lines. Article-sum agreement is a diagnostic, not evidence that an article label matches the page.
