# Survey: what sections each Ceylon directory volume contains

You are mapping the contents of a run of printed directories so that later extraction jobs can be planned. This is
an inventory job: do not extract people or firms. Work only in `spine/directories/`; write outputs to
`spine/directories/survey/`. Standard-library Python only (`/home/jic823/miniforge3/bin/python`). No network. All
other paths are read-only.

## Sources
OCR root (read-only, outside the repository; never copy from it into the repository):
`/home/jic823/ceylon/ocr_chandra/out_chandra2/` on this machine (`/mnt/data/jic823/ocr_chandra/out_chandra2/` on the
office machine). `survey.py` takes the root from the environment variable `CEYLON_OCR_ROOT`, falling back to
whichever of the two exists. Each volume is a folder holding
`<name>/<name>_layout.jsonl`: one JSON object per PDF page with `pdf_page` and `blocks` (each with `label`,
`bbox`, `content` as HTML). Printed page numbers and running heads are usually in Page-Header blocks.
The registry `../sources/ocr_registry.tsv` lists every OCR folder with its collection, title, date, repository
(historyofceylontea.com or archive.org) and total page count. Use every folder whose registry row is a Ceylon
directory or handbook-and-directory volume and whose OCR is present on disk (only directory and handbook folders were copied to this machine). That includes the 24 folders whose
names contain "fergusons-ceylon-directory" or "FERGUSON_S_CEYLON_DIRECTORY", `FergusonsCeylonDirectory1920_43c2c5d7`,
the 1871–1899 "ceylon directory" / "handbook and directory" folders, and the archive.org `ceylonhandbook190x` /
`CeylonHandbook190x` volumes. Do not include estate-only extracts unless they are a full directory volume.
Many folders are partial: a suffix like `_p01001` and a page count below the registry total mean only some pages
have been OCR'd so far. Work out which PDF pages each folder holds and say so; do not guess at pages not held.

A finished example of extraction from one volume is in `ferguson_1922/` (README there; sections at PDF pages
462–467, 468–500 and 548–555 of the 1922 volume). Use it to recognise the three section types already done.

## The rule about these sources
Pages and OCR from historyofceylontea.com may not be reproduced; facts may be recorded. Headings, page numbers and
your own short descriptions are fine. Do not copy entries, table rows or running text into any output. No output
field longer than 200 characters.

## What to produce
`survey/volumes.tsv` — one row per volume folder: `ocr_folder`, `title`, `year`, `repository`, `pages_total`
(registry), `pdf_pages_held` (ranges, e.g. "1001-1607"), `pages_held`, `has_contents_or_index_page` (pdf pages of
any table of contents or index found), `notes`.

`survey/sections.tsv` — one row per section of each volume, covering every held page from first to last with no
gaps or overlaps (use class `unclassified` when you cannot tell): `ocr_folder`, `year`, `pdf_page_start`,
`pdf_page_end`, `printed_page_start`, `printed_page_end` (as read; blank if absent), `heading_as_printed` (the
section or running heading, short), `section_class`, `town_or_area` (when the section is for one place),
`attested` (any "corrected to ..." date or year range the section states), `layout` (short: "3-column table: firm |
staff | agencies", "name list in 3 columns", "year | names table", "running prose", "advertisements" ...),
`ocr_condition` (good / mixed / poor, from the share of pages whose expected table or list structure survived),
`confidence` (high / medium / low that the boundaries and class are right), `notes`.

Use these classes, adding a new one only when none fits (and define it in the README):
`mercantile_colombo` (firms with staff and agencies), `mercantile_outstation` (the same for another town),
`trade_lists` (names under trade headings: jewellers, money lenders, pawnbrokers, Chetty firms ...),
`associations` (chambers, planters' and other associations, clubs, societies: officers and members),
`banks_insurance`, `clergy_religious` (clergy, temples, churches, missions of any religion),
`education` (schools, colleges, staff), `professions` (lawyers, notaries, medical, surveyors),
`government_establishment` (civil service, departments, courts, councils), `municipal_local` (municipal councils,
local boards), `military_volunteer`, `consuls`, `shipping_port`, `estates_directory` (estates with proprietors,
agents, acreages), `planters_alphabetical`, `residents_alphabetical` (general alphabetical list of people),
`companies_register` (joint-stock companies with directors and capital), `press` (newspapers, periodicals),
`almanac_calendar`, `statistics_review` (statistical or descriptive essays), `gazetteer_places` (towns, villages,
post offices, distances), `advertisements`, `front_matter`, `index`, `unclassified`.

Method: build the map mostly by rule (headings, running heads, contents and index pages, changes in block layout),
then read pages yourself at every boundary you are unsure of. A contents page, where held, is the best guide: use
it and check it against the pages. Where a volume's held pages start mid-section, say so in `notes`.

`survey/survey.py` rebuilds both tables from the OCR plus a hand-made `survey/boundaries_overrides.tsv` (one row
per manual decision, with a reason).

## Evidence
- `survey/audit.tsv`: for each volume, 8 section rows chosen at random with a fixed seed (all rows if fewer than
  8). For each, open the first page, the last page and the page after the last, by reading the OCR yourself, and
  record: ocr_folder, pdf_page_start, class_agrees (yes/no), start_agrees, end_agrees, comment. Fix what you find
  and redo the failed rows; report the first-pass result honestly.
- `survey/coverage.tsv`: a matrix with one row per section class and one column per volume year, each cell the
  number of PDF pages of that class held ("0" if the volume's held pages have none; "?" when the relevant part of
  the volume is not held).
- `survey/README.md` (under 150 lines): what was surveyed; the coverage matrix summarised in words; which section
  classes recur across the most volumes in comparable layout (the best candidates for extraction over time), with
  page counts; which volumes are too partial to use yet and which pages are missing; three to five things that
  surprised you about how the sections change between 1871 and 1970; the audit result; known weak spots.
- `survey/validation.json`: per volume, sections cover held pages exactly once; no field over 200 characters;
  every class is in the list above or defined in the README.

The 1922 volume first, in full, checking that your map finds the three sections already extracted at the right
pages. Then the 1920–21 volume (archive.org, complete), then the rest in date order. Stop when all are done.
