# Repair round 1: Ferguson 1922 pilot, Colombo agency cells and name parsing

You are repairing an existing extraction. Read `ferguson_1922_pilot.md` (the original brief: schema, source path,
and the rule that facts may be recorded but the source's text may not be reproduced) and `ferguson_1922/README.md`
first. Work only in `spine/directories/ferguson_1922/`. Standard-library Python only
(`/home/jic823/miniforge3/bin/python`). No network. Change `extract.py` and `overrides.json`; all outputs must
still rebuild from the OCR by running `extract.py`. Keep every existing `listing_id` stable.

**Where the OCR is on this machine.** The path in the pilot brief (`/mnt/data/jic823/ocr_chandra/out_chandra2/...`)
is on another machine. Here the same folders are under `/home/jic823/ceylon/ocr_chandra/out_chandra2/` (read-only,
outside the repository; never copy from it into the repository). Change `extract.py` and `audit.py` to take the OCR
root from the environment variable `CEYLON_OCR_ROOT`, falling back to whichever of the two roots exists, so the
rebuild works on both machines. First rebuild with the unchanged rules and confirm the outputs are byte-identical
to the committed ones before changing anything; say so in the README.

An independent reader compared 15 fresh listings with the OCR. The simple lists (section A, the Chamber rosters,
the insurance and bank tables) were right. Three of the five Colombo (section B) listings had faults in roles or
connections that the first audit did not count, because it scored listing fields and not each role and connection.

## Faults to fix as rules (each example is a test case: it must come out as shown)

1. **Initials read as honorifics.** `ferg1922:p481:b2:r5` "R. C. Short." has honorifics `["C. Short."]`;
   `ferg1922:p481:b2:r2` "E. R. Park." has `["R. Park."]`. Honorifics must come only from a closed list of
   post-nominals and titles (J.P., M.M.C., A.C.A., A.M.I.E.S., Hon., Dr., Sir, Capt., ...). Expected: `[]` for both.
   Print the full list of distinct honorific values after the fix and check each is a real title or post-nominal.
2. **Sentence full stops kept on names.** "J. M. Menzies.", "W. H. Atkinson.", "L. H. Watkinson.", and targets such
   as "The City Line." Remove a final full stop that ends the phrase; keep one that belongs to an abbreviation
   (Ltd., Co., Bros., Jr., St., J.P.). Surname and initials must be unaffected.
3. **Trade descriptions filed as agencies.** `ferg1922:p499:b2:r2` (Webster Automatic Packeting Factory): the
   closing phrase listing the firm's own trades is recorded as an `agent_for` connection with target kind
   "estate company", and `trades` is empty. Expected: no such connection; `trades` =
   ["Tea Buyers", "Blenders", "Packers", "Exporters", "Estate Agents"]. Apply to every listing where the agencies
   column ends or begins with the firm's own description.
4. **Slogans filed as correspondents.** `ferg1922:p481:b2:r2` (Dunlop): a promotional phrase is recorded as a
   connection of class `correspondent`. Expected: no connection; nothing recorded for it (it is not a fact about
   a relationship). Put the listing_id in a `dropped_phrases` count in validation.json, without the text.
5. **Branch addresses split into pieces.** Same Dunlop listing: the branches are four towns, each printed with a
   street address, but the output has ten `branch_at` records (street names, a house number, and the towns).
   Expected: four `branch_at` connections with `target_as_printed` Bombay, Calcutta, Madras, Delhi, and a new field
   `target_address_as_printed` holding the street part for each ("Dadysett Road, Chowpatti"; "8, Lindsay Street";
   "16/2, Mount Road"; "Mori Gate"). Add `target_address_as_printed` (null when absent) to every connection. The
   same listing's registered office and `ferg1922:p481:b2:r5` head office should use the same pattern: the town in
   `target_place_as_printed`, the street in `target_address_as_printed`, relation class `head_office` (new class;
   also use it for "Head Office" in `ferg1922:p497:b2:r1`, target Moscow).
6. **Place wrongly cut from a name.** `ferg1922:p499:b2:r2`: target "Tea Planters, Ltd., Bale &" with place
   "Paris". Expected: target "Tea Planters, Ltd.", place "Bale & Paris". `ferg1922:p470:b2:r3`: a London street
   address is split into a truncated target ending "12, Feuchurch" and a separate connection whose target is
   "Street". Expected: one connection per body, with the street in `target_address_as_printed` and "London, E. C."
   as place; no connection whose target is a bare street word, number or town fragment.
7. **"per pro" dropped.** In `ferg1922:p468:b6:r5` three assistants are printed with "per pro" and four without;
   the output does not distinguish them. Add a boolean `per_pro` to every role (true only where printed with that
   person) and expect: Bell, Kenyon, Bostock true; Francillon, Howard-Smith, Edge, Spence false.
8. **Second names of a firm dropped.** `ferg1922:p468:b6:r5` prints a second firm name for Galle under the first.
   Add `other_names_as_printed` (list) to listings and fill it there. Do not use it for "(See Advt.)".
9. **A listed firm that acts as agent for the entry.** `ferg1922:p497:b2:r1`: the staff column names another firm
   followed by "Agents". The output has relation class `other`. Add relation class `has_agent` (the target acts
   for the listing) and use it there and in the section C tables where a column headed AGENTS names the local
   agent of an insurer or bank (for example `ferg1922:p467:b3:r0`, `ferg1922:p464:b3:r25`). In those section C
   rows, do not fill `target_place_as_printed` unless a place is printed in that row.
10. **Places left out.** `ferg1922:p497:b2:r1` drops the general phrase about other cities after the four named
    branches. Record it as one more `branch_at` with the phrase as printed and flag `unspecific_place`.
11. Truncation marks from narrow columns ("[Ld.", "[grad", "[Co") left inside targets. Join the bracketed overflow
    to the word it completes where that is unambiguous ("Co., Ltd."; "Petrograd"), otherwise drop the stray
    bracket and flag `ocr_doubtful`.

Look for other instances of the same eleven patterns across all of sections A, B and C, not only the examples.
If you find a twelfth pattern while auditing, fix it and describe it.

## Evidence
- `ferguson_1922/tests_repair1.py`: asserts every expected value above against the rebuilt outputs; must pass.
- `ferguson_1922/audit_repair1.tsv`: a new audit that scores **each role and each connection**, not listing
  fields. Draw 30 section B listings and 10 section C listings with seed 4711, excluding every listing_id in
  `audit.tsv` and the ids named in this brief. For each: one line per extracted role and connection
  (record_id, kind, agrees yes/no, comment), plus one line per role or connection that is printed in the OCR but
  missing from the output (record_id blank, kind `missing_role` or `missing_connection`, short comment naming it).
  Read the OCR yourself. Then fix what you found, and draw a second sample of 20 B listings (seed 4712, excluding
  all earlier ones) scored the same way after the fixes. Report both honestly, including if the second is no
  better.
- Update `README.md` (still under 120 lines): add a "Repair round 1" section with counts before and after, the
  two per-record audit results (records checked, wrong, missing), and what remains unreliable. Update
  `validation.json` (same checks, plus counts of each `relation_class` and `role_class`).
- Outputs must still obey the 200-character field limit and contain no running prose from the source.

Stop when this is done. Do not start other sections or volumes.
