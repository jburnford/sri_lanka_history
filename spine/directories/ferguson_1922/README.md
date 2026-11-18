# Ferguson’s Ceylon Directory, 1922 pilot

## Rebuild

From `spine/directories`, use the supplied Python interpreter.

```sh
/home/jic823/miniforge3/bin/python -B ferguson_1922/extract.py
/home/jic823/miniforge3/bin/python -B ferguson_1922/tests_repair1.py
```

Set `CEYLON_OCR_ROOT` to the directory containing the volume folder. The
extractor and audit viewer share the lookup. They try
`/home/jic823/ceylon/ocr_chandra/out_chandra2` and then
`/mnt/data/jic823/ocr_chandra/out_chandra2` when the variable is unset.
`overrides.json` records corrections with their source rows and reasons.
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

## Coverage and remaining uncertainty

- PDF 461 is military. The available Chamber continuation starts on PDF 462,
  printed 424. The OCR index lacks headers for printed 419–423.
- All requested Kandy and Colombo pages are represented. Recovered layouts
  on PDF 480, 484 and 489 carry `structure_lost`. PDF 489 and 490 lack printed
  page numbers in the OCR. The repeated page number on PDF 551 is flagged.
- PDF 472 interleaves Brown’s staff and addresses. PDF 477 has incomplete
  principal names, and PDF 500 has an illegible staff continuation. Parts of
  the Colonial Tea Traders’ roster and fire insurance tables are displaced.
- Consecutive company names without separators, regional qualifiers in branch
  lists, shared agency groups, compound surnames and damaged initials still
  need source review. Unclear group ownership can affect attribution.

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
