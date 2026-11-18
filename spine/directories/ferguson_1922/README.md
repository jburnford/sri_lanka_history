# Ferguson’s Ceylon Directory, 1922 pilot

## Rebuild

From `spine/directories`, use the supplied Python interpreter.

```sh
/home/jic823/miniforge3/bin/python -B ferguson_1922/extract.py
/home/jic823/miniforge3/bin/python -B ferguson_1922/tests_repair1.py
/home/jic823/miniforge3/bin/python -B ferguson_1922/coverage_check.py
```

Set `CEYLON_OCR_ROOT` to the directory containing the volume folder. The
extractor and audit viewer share the lookup. They try
`/home/jic823/ceylon/ocr_chandra/out_chandra2` and then
`/mnt/data/jic823/ocr_chandra/out_chandra2` when the variable is unset.
`overrides.json` records corrections for sections A and C.
`audit.py --rebuild` regenerates the original listing audit from `audit_notes.json`.
Run `audit.py 1` or `audit.py 2` to view those samples beside the OCR, or
`audit.py --repair-sample 1` or `2` to print the repair sample IDs.

Block and row indices start at zero and include any HTML table header.
Multi-column lists count individual names. `source_locator` identifies the
row or block supplying each role or connection. The first listing ID owns
merged entries. `continuation_pages` and `continuation_sources` identify later
fragments. `continues_from` is null on the retained first record. Chamber
rosters have one listing per year within each roster. Repeated agents under
a ditto company row link to the first listing for the company in that table.

A bare staff name has role `listed`, with the column label in `source_column`.
Compound agency and secretary labels retain both terms and use `secretary_for`.
The directory locality supplies the listing town when the entry gives none.

## Repair round 1

Before editing the scripts, the original rules ran against the local OCR by
changing the source path in memory. `listings.jsonl`, `roles.jsonl`,
`connections.jsonl`, `validation.json` and `audit.tsv` were byte-identical
to the committed files. All 653 listing IDs retain their original order.

| Section | PDF pages represented | Listings before → after | Roles before → after | Connections before → after |
|---|---:|---:|---:|---:|
| A. Kandy merchants, agents and trade lists | 548–555 | 285 → 285 | 262 → 262 | 44 → 44 |
| B. Colombo merchants and agents | 468–500 | 153 → 153 | 997 → 979 | 1,716 → 1,729 |
| C. Associations and banks | 462–467 | 215 → 215 | 217 → 217 | 317 → 317 |
| **Total** | | **653 → 653** | **1,476 → 1,458** | **2,077 → 2,090** |

The rebuild prints the complete set of 34 observed honorific spellings in
`validation.json`. These were checked as forms of titles, official positions,
or academic and professional post-nominals. Spacing and case variants are
kept, including the combined `J.P.M.M.C.`. Damaged credential fragments can
remain in the printed name with an OCR flag. Sentence-ending stops are removed
while abbreviation stops are kept.

Roles carry `per_pro`. Listings carry `other_names_as_printed`, with the
existing shared Galle listing still separately identified. Connections carry
`target_address_as_printed`. `has_agent` points to the agent acting for the
listing. Registered offices use `head_office`. Unspecific branch places are
flagged. Validation counts classifications and dropped phrases by listing ID.
The audit exposed a further pattern in the staff column. Department labels
and signatory notes could become people or attach to names. The parser now
recognizes those labels and separates them from the roster.

| Per-record audit | Seed | B / C listings | Records checked | Wrong | Missing |
|---|---:|---:|---:|---:|---:|
| Initial repairs | 4711 | 30 / 10 | 573 | 123 (21.5%) | 30 |
| After first-sample fixes | 4712 | 20 / 0 | 346 | 48 (13.9%) | 8 |

Both draws exclude the original audit and brief example IDs. The second also
excludes the first draw. `audit_repair1.tsv` keeps the verdicts and record IDs
from each review. Missing records have blank IDs and are counted separately.
The second sample includes one listing with zero roles and connections.
Further corrections followed that review, including split office locations and
misfiled trades. The numbers describe the reviewed snapshots.

## Colombo re-read

| Section | Listings before → after | Roles before → after | Connections before → after |
|---|---:|---:|---:|
| B. Colombo, PDF 468–500 | 153 → 153 | 979 → 957 | 1,729 → 1,790 |

`colombo_readings.jsonl` holds the readings in PDF order, including continuations
and detached blocks in `source_rows`. All listing IDs retain their order, and
the A and C lines in each export match `git show HEAD:<path>` byte for byte.
The repair tests now expect `A.I.M.M.` and `Effendi` in the honorific field.

`coverage_b.tsv` matched 12,814 of 13,619 OCR word tokens (94.09%).
Each of the 31 listings still below 90% was reread and has a reading note.
The check removes heading occurrences and rejoins line-end word breaks.

The second look drew 30 listings with seed 4713. Before fixes, 19 of 197
roles and 29 of 338 connections disagreed (48 of 535, 9.0%). Two connections
were missing. One listing had zero records. `audit_reread.tsv` preserves the
pre-fix verdicts and IDs. Corrections addressed matching faults outside the draw.

Check the interleaved staff on PDF 472, the agency fragments on PDF 477,
and the staff continuation on PDF 500 against the images first. The Cargills
agency continuation on PDF 474 also has interleaved columns.

Listings with doubtful OCR or recovered layout

`ferg1922:p468:b6:r1`, `ferg1922:p468:b6:r3`, `ferg1922:p468:b6:r4`, `ferg1922:p468:b6:r5`, `ferg1922:p468:b6:r7`, `ferg1922:p469:b2:r2`, `ferg1922:p469:b2:r3`, `ferg1922:p469:b2:r4`, `ferg1922:p470:b2:r2`, `ferg1922:p470:b2:r3`
`ferg1922:p471:b2:r1`, `ferg1922:p471:b2:r2`, `ferg1922:p471:b2:r3`, `ferg1922:p472:b2:r1`, `ferg1922:p472:b2:r3`, `ferg1922:p473:b2:r1`, `ferg1922:p473:b2:r2`, `ferg1922:p473:b2:r3`, `ferg1922:p474:b2:r2`, `ferg1922:p474:b2:r3`
`ferg1922:p475:b2:r4`, `ferg1922:p476:b2:r1`, `ferg1922:p476:b2:r2`, `ferg1922:p476:b2:r3`, `ferg1922:p476:b2:r4`, `ferg1922:p476:b2:r5`, `ferg1922:p476:b2:r6`, `ferg1922:p477:b2:r1`, `ferg1922:p477:b2:r2`, `ferg1922:p477:b2:r3`
`ferg1922:p478:b2:r1`, `ferg1922:p478:b2:r4`, `ferg1922:p479:b2:r7`, `ferg1922:p480:b2:r1`, `ferg1922:p480:b2:r2`, `ferg1922:p480:b2:r3`, `ferg1922:p480:b2:r4`, `ferg1922:p481:b2:r1`, `ferg1922:p481:b2:r2`, `ferg1922:p481:b2:r3`
`ferg1922:p481:b2:r4`, `ferg1922:p481:b2:r5`, `ferg1922:p481:b2:r6`, `ferg1922:p481:b2:r7`, `ferg1922:p482:b2:r1`, `ferg1922:p482:b2:r2`, `ferg1922:p482:b2:r5`, `ferg1922:p482:b2:r6`, `ferg1922:p483:b2:r4`, `ferg1922:p484:b2:r1`
`ferg1922:p485:b2:r2`, `ferg1922:p486:b2:r2`, `ferg1922:p486:b2:r3`, `ferg1922:p486:b2:r4`, `ferg1922:p486:b2:r5`, `ferg1922:p487:b2:r2`, `ferg1922:p487:b2:r5`, `ferg1922:p487:b2:r6`, `ferg1922:p488:b2:r2`, `ferg1922:p488:b2:r3`
`ferg1922:p489:b4:r0`, `ferg1922:p489:b6:r0`, `ferg1922:p489:b8:r0`, `ferg1922:p489:b10:r0`, `ferg1922:p490:b1:r1`, `ferg1922:p490:b1:r2`, `ferg1922:p490:b1:r3`, `ferg1922:p490:b1:r4`, `ferg1922:p491:b2:r5`, `ferg1922:p491:b2:r6`
`ferg1922:p492:b2:r3`, `ferg1922:p492:b2:r7`, `ferg1922:p493:b2:r1`, `ferg1922:p493:b2:r2`, `ferg1922:p494:b2:r2`, `ferg1922:p494:b2:r4`, `ferg1922:p494:b2:r7`, `ferg1922:p495:b2:r5`, `ferg1922:p496:b2:r2`, `ferg1922:p497:b2:r6`
`ferg1922:p497:b2:r8`, `ferg1922:p498:b2:r1`, `ferg1922:p499:b2:r3`, `ferg1922:p499:b2:r4`, `ferg1922:p500:b2:r4`

All Kandy and Colombo pages are represented. PDF 489 and 490 lack printed
page numbers in the OCR. The Chamber continuation starts on PDF 462.

## Original listing audit

| Round | Seed | A / B / C listings | Listing fields agreeing | Mismatches in A / B / C |
|---|---:|---:|---:|---:|
| 1 | 1922 | 20 / 20 / 20 | 763 / 782 | 4 / 12 / 3 |
| 2 | 1923 | 10 / 10 / 10 | 386 / 391 | 0 / 4 / 1 |

`audit.tsv` retains both historical reviews. The 60 first-round listings had
17 with at least one mismatch. The independent second draw had five with a
mismatch. The table counts each trade array as one listing field.

## Worked cross-section examples

1. F. C. Macdonald is the Mercantile Bank of India’s Kandy agent in both
   banking lists. `ferg1922:p548:b4:r1`, `ferg1922:p467:b6:r0`
2. W. Sutherland Ross is a Bois Brothers director and the Chamber’s 1921
   vice chairman. `ferg1922:p470:b2:r3`, `ferg1922:p462:b3:r5`
3. W. H. Figg is a Whittall partner and a 1904 Legislative Council
   representative. `ferg1922:p499:b2:r4`, `ferg1922:p462:b7:r23`
4. F. H. Yeats is a Webster Automatic Packeting Factory director and
   Mercantile Bank of India manager. `ferg1922:p499:b2:r2`, `ferg1922:p466:b20:r0`
5. Walker, Sons & Co. appears in the Kandy engineers list, the Colombo merchants
   list and the fire insurance table as Eastern Insurance’s agent.
   `ferg1922:p549:b4:r4`, `ferg1922:p498:b2:r1`, `ferg1922:p463:b13:r10`
