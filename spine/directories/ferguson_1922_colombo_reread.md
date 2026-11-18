# Colombo re-read: Ferguson 1922, section B, read entry by entry

Read `ferguson_1922_pilot.md` (schema, and the rule that facts may be recorded but the source's text may not be
reproduced), `ferguson_1922_repair.md` and `ferguson_1922/README.md` first. Work only in
`spine/directories/ferguson_1922/`. Standard-library Python only (`/home/jic823/miniforge3/bin/python`). No
network. OCR root: environment variable `CEYLON_OCR_ROOT`, as `extract.py` already handles.

## Why
Two rounds of parsing rules left about 14% of the roles and connections in the Colombo list (section B, 153
listings, PDF pages 468–500) wrong, by your own per-record audit. The staff and agency cells are free text with
headings, sub-headings, run-on names and ditto marks; rules do not hold. Sections A and C are fine: do not change
their output at all (their three output files must keep exactly the same lines for A and C records).

## The job
Replace rule output for section B with a **reading**: for each of the 153 Colombo listings, read its OCR cells
yourself (the first row and every continuation row) and write down what it says as records. Do not write a better
parser. A helper script may print the cells of one listing and the current rule output as a draft to correct, but
every listing's records must be decided by you reading that listing. Work page by page in PDF order and save as
you go.

Write `ferguson_1922/colombo_readings.jsonl`: one line per listing, with `listing_id` (unchanged ids),
`source_rows` (the listing_id-style locators of every row read, including continuations), the listing fields
(`name_as_printed`, `other_names_as_printed`, `kind`, `address_as_printed`, `town`, `trades`, `flags`), `roles`
(list) and `connections` (list), and `reading_notes` (your own short remark where the print or OCR is unclear;
never a quotation). Then change `extract.py` so that for section B it builds listings, roles and connections from
this file (role and connection ids numbered in order within the listing), and keep the rules only for A and C.
`overrides.json` entries for section B that the readings supersede should be removed.

Fields for roles, beyond the existing ones: `department_as_printed` (a heading inside the staff cell that governs
the names after it, e.g. a works, stores, garage or branch heading; null when none), and `location_as_printed`
(when a person is printed at a branch or town). Existing: `person_as_printed`, `surname`, `given_or_initials`,
`honorifics`, `role_as_printed`, `role_class`, `per_pro`, `flags`.
Fields for connections, beyond the existing ones: `group_heading_as_printed` (the heading inside the agencies cell
that governs the entry: "Shipping", "Insurance", "Sterling Co.'s", "Rupee Co's", "Estates", "London Agents" ...;
keep `qualifier` equal to it for compatibility). Existing: `relation_as_printed`, `relation_class`,
`target_as_printed`, `target_kind`, `target_place_as_printed`, `target_address_as_printed`, `flags`.

Rules of reading (each came from an audit failure):
1. A heading governs every name under it until the next heading. A person under a "Directors" heading is a
   director; an estate under "Agents & Secretaries" is that, not plain agency.
2. A role title is the whole printed title ("Tea Stores Manager", "Works Engineers"), not its last word, and a
   department or title word is never a person.
3. Direction matters. "London Agents: X" means X acts for the listing (`has_agent`). "Agents for X" means the
   listing acts for X (`agent_for`, or `insurer_agent` / `shipping_agent` / `secretary_for` by heading).
4. One record per body. Where OCR ran two company names together, split them if both names are clear, otherwise
   keep one record and flag `ocr_doubtful` with a note.
5. A place or street after a name goes in the place and address fields, not in the name. A list of branch towns is
   one `branch_at` per town.
6. The firm's own description is `trades`; slogans are not recorded.
7. Expand ditto marks from the line above. Keep printed spellings. Flag doubt; do not guess silently.
8. If a cell is too damaged to read, record what is certain, flag `structure_lost`, and say so in `reading_notes`.

## Checks
- `ferguson_1922/tests_repair1.py` must still pass (update it only where a field moved, and say what changed).
- `ferguson_1922/coverage_check.py` writes `coverage_b.tsv`: for each Colombo listing, the number of word tokens
  in its OCR cells (after removing punctuation, ditto marks and the words of printed headings), the number that
  appear in some output field of that listing, and the share. No source text in the file: counts only, plus up to
  five uncovered tokens per listing as a pointer. Read every listing below 90% again and fix it or explain it in
  `reading_notes`. This is a test for missed records; it does not show that records are right.
- A second look: after all 153 are read, draw 30 listings with seed 4713 and read each cell again from the start,
  scoring every role and connection (`audit_reread.tsv`: listing_id, record_id, kind, agrees yes/no, comment; plus
  `missing_role` / `missing_connection` lines). Fix what you find in all listings showing the same fault, not only
  the sampled ones. Report the result as found, before the fixes.
- Validation as before: unique ids, valid references, no field over 200 characters, counts by class, and that the
  A and C records are unchanged from the committed files (compare with `git show HEAD:<path>`; reading git is
  allowed, do not commit).
- Update `README.md` (under 140 lines): a "Colombo re-read" section with counts before and after, the coverage
  result, the second-look result, the listings that remain doubtful (ids only), and what a later reader should
  check first.

An independent reader will then sample the result against the OCR. Stop when section B is done.
