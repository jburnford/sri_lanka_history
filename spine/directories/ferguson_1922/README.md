# Ferguson’s Ceylon Directory, 1922 pilot

| Section | PDF pages represented | Listings | Roles | Connections |
|---|---:|---:|---:|---:|
| A. Kandy merchants, agents and trade lists | 548–555 | 285 | 262 | 44 |
| B. Colombo merchants and agents | 468–500 | 153 | 997 | 1,716 |
| C. Associations and banks | 462–467 | 215 | 217 | 317 |
| **Total** | | **653** | **1,476** | **2,077** |

## Rebuild

From `spine/directories`, use the supplied Python interpreter.

```sh
/home/jic823/miniforge3/bin/python -B ferguson_1922/audit.py --rebuild
/home/jic823/miniforge3/bin/python -B ferguson_1922/extract.py
```

The extractor reads the layout JSONL from the specified local OCR path. It applies
`overrides.json`, whose entries identify the affected source row and explain the
decision. The audit builder uses the frozen manual comparisons in `audit_notes.json`.
Run `audit.py 1` or `audit.py 2` to display the recorded sample alongside the OCR.

Block and row indices start at zero and count any HTML table header row. For
multi-column lists of independent names, the item index counts individual names.
`source_locator` identifies the row or block that supplies a role or connection.
The first listing ID owns the merged entry. `continuation_pages` and
`continuation_sources` identify its later fragments. `continues_from` is null on
these retained first records. Locally repeated listings, such as a firm listed
under two trades, have separate IDs. Chamber rosters have one listing per year
within each printed roster so the attested year can be carried on both the
listing and its roles. Repeated agents under a ditto company row link to the
first listing for that company within the table.

A bare name in a staff column has role `listed` and the column label is in
`source_column`. Corporate bodies in that column have a connection carrying
the printed label and the direction from the listing to the named body.
Compound agency and secretary labels retain both printed terms and use
`secretary_for` as their class. The directory locality supplies the town for
local entries without a separately printed town. Name components are heuristic.
The printed strings carry the evidence for identity.

## Coverage and remaining uncertainty

- PDF 461 contains military directories. The earliest available Chamber
  material is the continuation on PDF 462, headed printed 424. The OCR index
  has no page headers for printed 419–423, so the opening Chamber material
  could not be recovered.
- All requested Kandy and Colombo PDF pages are represented. Colombo PDF 480
  has recoverable three-cell rows. PDF 484 has displaced role and agency
  fragments within the George Stewart entry. PDF 489 has four identifiable
  name blocks with assigned staff and agency blocks. These recoveries carry
  `structure_lost`.
- PDF 472 has mixed address and staff text in the Brown row. PDF 477 has
  agency fragments with incomplete names, and the staff continuation on PDF
  500 is illegible. The Colonial Tea Traders’ committee text on PDF 462
  and the fire insurance agents table on PDF 463 also contain displaced
  or incomplete fragments. Clear facts were retained.
- Printed numbers use the OCR page headers, including suspect readings.
  PDF 489 and 490 have null printed numbers because the numerical header
  is missing. The repeated Kandy reading on PDF 551 is flagged.
- Long agency lists can still contain missed or mis-segmented names,
  place suffixes or qualifiers, especially across narrow columns. Shared
  shipping and estate headings can leave the attribution ambiguous.
  Initials, honorifics, compound surnames and garbled OCR may also split
  imperfectly. The OCR spellings are preserved where the source is doubtful.

## Manual listing audit

| Round | Seed | A / B / C listings | Listing fields agreeing | Mismatches in A / B / C |
|---|---:|---:|---:|---:|
| 1 | 1922 | 20 / 20 / 20 | 763 / 782 | 4 / 12 / 3 |
| 2 | 1923 | 10 / 10 / 10 | 386 / 391 | 0 / 4 / 1 |

The 60 first-round listings were checked field by field against the source OCR.
Seventeen listings had at least one mismatch. After correction, a fresh draw
excluded the first 60 IDs. The second round found five mismatches on five
listings. Both rounds retain their as-reviewed values and verdicts in
`audit.tsv`. The final extracts incorporate both sets of corrections.
Indexed rows show the individual terms of a long trade array. The table above
counts the array as one listing field.

## Worked cross-section examples

1. F. C. Macdonald is the Mercantile Bank of India’s agent in the Kandy
   bankers list and again in the outstation banking entry.
   `ferg1922:p548:b4:r1`, `ferg1922:p467:b6:r0`
2. W. Sutherland Ross appears as a Bois Brothers director and as the
   Chamber’s 1921 vice chairman.
   `ferg1922:p470:b2:r3`, `ferg1922:p462:b3:r5`
3. W. H. Figg is a Whittall partner and appears on the 1904 Legislative
   Council representative roster.
   `ferg1922:p499:b2:r4`, `ferg1922:p462:b7:r23`
4. F. H. Yeats is listed among the directors of Webster Automatic Packeting
   Factory and as manager of the Mercantile Bank of India in Colombo.
   `ferg1922:p499:b2:r2`, `ferg1922:p466:b20:r0`
5. Walker, Sons & Co. appears in the Kandy engineers list and the Colombo
   merchants list, which names Kandy among its locations. The fire
   insurance association lists the firm as agent for Eastern Insurance.
   `ferg1922:p549:b4:r4`, `ferg1922:p498:b2:r1`, `ferg1922:p463:b13:r10`
