# Pilot: Colombo and Kandy firms, people and connections from Ferguson's Ceylon Directory (1922 volume)

You are extracting structured facts from the OCR of one printed directory, for a historical knowledge graph of
Ceylon. Work only in this folder (`spine/directories`). Write outputs to `ferguson_1922/`. Standard-library Python
only (`/home/jic823/miniforge3/bin/python`). No network. Read the OCR; do not modify anything outside this folder.

## Source
OCR (read-only): `/mnt/data/jic823/ocr_chandra/out_chandra2/1922-fergusons-ceylon-directory_4e422995/1922-fergusons-ceylon-directory/1922-fergusons-ceylon-directory_layout.jsonl`
One JSON object per PDF page: `pdf_page`, `blocks` (each with `label`, `bbox`, `content` as HTML). The printed page
number is in a Page-Header block (PDF page 468 is printed page 430).

Sections to extract, in this order (stop after C):
- **A. Kandy merchants, agents, &c.** PDF pages 548–555 (tables of firms / partners and assistants / addresses, then
  trade lists by heading: "MONEY LENDERS.", "JEWELLERS." ...).
- **B. List of Colombo merchants and agents**, "corrected up to December, 1921": PDF pages 468–500. Three columns:
  FIRMS AND ADDRESSES | PARTNERS AND ASSISTANTS | PRINCIPAL CORRESPONDENTS AND AGENCIES. Entries continue across
  pages ("(Contd)"); some pages lost their table structure in OCR (480, 484, 489) — handle them if you can do so
  reliably, otherwise list them as skipped.
- **C. Associations and banks**: PDF pages 461–467 (Ceylon Chamber of Commerce past officers by year and other
  association officers and members; banks, their agents and outstation branches). Find where the Chamber of
  Commerce section begins (it may start before 462).

## The rule about this source
The page images and OCR come from the History of Ceylon Tea website. **Facts may be recorded; their pages may not be
reproduced.** So: record names, roles, addresses, firm names, places and relationships as data fields. Do not copy
running text, whole table cells of prose, or page transcriptions into any output file. A field may hold a printed
name or short label exactly as printed (that is the fact); the long "General Merchants, Importers and Exporters,
Stationers, ..." descriptions become a list of short trade terms. Every record cites its place in the source
instead of quoting it.

## What to record (JSON Lines, UTF-8, one object per line)
`ferguson_1922/listings.jsonl` — one per firm or body as listed:
  `listing_id` (`ferg1922:p<pdf_page>:b<block index>:r<row or item index>`), `section` (A/B/C and the printed
  heading), `pdf_page`, `printed_page`, `name_as_printed`, `kind` (firm, bank, association, sole trader, other),
  `address_as_printed` (e.g. "Caffoor Bldgs., Main St., Fort"), `town` (Colombo, Kandy, or as printed), `trades`
  (list of short terms), `attested` (the date the list claims: "corrected to December 1921" for B; the year column
  for retrospective lists), `continues_from` (listing_id when an entry continues from a previous page: merge the
  content into the first listing and note the pages), `flags` (list: "ocr_doubtful", "structure_lost", ...).
`ferguson_1922/roles.jsonl` — one per person named in a listing:
  `role_id`, `listing_id`, `person_as_printed`, `surname`, `given_or_initials`, `honorifics` (J.P., Hon., Dr ...),
  `role_as_printed` (Proprietor, Partner, Assistant, Agent, Manager, Chief Clerk, Shroff, Chairman, Secretary ...;
  "listed" when the column gives a bare name), `role_class` (owner, partner, manager, staff, officer, member,
  licensee, unknown), `year` (for retrospective lists), `pdf_page`, `flags`.
`ferguson_1922/connections.jsonl` — one per relationship a listing prints between the firm and another body or place:
  `connection_id`, `listing_id`, `relation_as_printed` ("Agents for", "Agents & Secretaries for", "Correspondents",
  "Branches at", "Representatives of", "Agents for Shipping" ...), `relation_class` (agent_for, secretary_for,
  correspondent, branch_at, represents, insurer_agent, shipping_agent, other), `target_as_printed`,
  `target_kind` (company, estate company, bank, insurer, shipping line, place, person, unknown),
  `target_place_as_printed` (when a place is printed with it, e.g. "London"), `qualifier` (e.g. "Sterling Co.'s",
  "Rupee Co's"), `pdf_page`, `flags`. Expand ditto marks („) from the line above.
Keep printed spellings; never correct a name. When the OCR is clearly damaged, keep what is there and flag it.
A column heading defines the relationship: a name in the partners column is not an agency; say what the column was.

## Evidence you must produce
- `ferguson_1922/extract.py` (or several scripts) that rebuild all outputs from the OCR, plus any hand-made
  override table as a separate file with a reason per row. Prefer rules; where rules cannot decide, use your
  judgement on the specific entries and record those decisions in the override file.
- `ferguson_1922/audit.tsv`: 60 listings chosen at random with a fixed seed (20 per section), each compared field
  by field with the OCR by reading it yourself (not by rerunning the code): columns listing_id, field, extracted,
  agrees (yes/no), comment. Fix what the audit finds, then draw a fresh 30 and report that second result honestly.
- `ferguson_1922/README.md` (under 120 lines): counts per section (listings, roles, connections), pages skipped
  and why, the two audit results, the kinds of error remaining, and five worked examples that follow one person or
  firm across sections (e.g. someone who is a partner in B and a Chamber officer in C), cited by listing_id only.
- `ferguson_1922/validation.json`: every role and connection points to an existing listing; ids unique; no output
  field longer than 200 characters (a guard against copying prose).

Do A completely first and write its outputs before starting B: A is small and will show whether the schema works.
Stop when A, B and C are done. Do not start other sections or other volumes.
