# Job: second repair of the reader for the Ceylon Blue Book trade ledgers, 1901–1906

You are working in `/home/jic823/Documents/ceylon/spine/bluebook`. You may edit `read_trade_old.py` and create
files under `jobs/trade_1901_1906_work/` (keep what is there); running the reader rewrites
`extracted/trade_1880_1906.tsv.gz`, `extracted/trade_1880_1906_checks.tsv` and
`extracted/trade_1880_1906_skipped.tsv`. Do not edit or delete anything else. No network access. Use
`/home/jic823/miniforge3/bin/python` (standard library only). Aim to finish within about 60 minutes.

## Situation

You (an earlier run) repaired this reader; `jobs/trade_1901_1906_work/README.md` describes what was done. A
second reader then checked a fresh random sample of 238 rows against the page images
(`jobs/trade_1901_1906_work/scan_check2_results.tsv`: table_id, pdf_page, flow, article_as_printed,
country_as_printed, measure, value_as_printed, verdict, class_and_group_ok, what_the_page_shows, comment).
Result: 205 right, 31 with a wrong article label (figure, country, column and unit all right), 2 OCR digit
errors (leave those). No figure was attached to the wrong country. The remaining faults, with the reader's
counts over the whole output:

A. **Three-level entries keep only two levels.** "Other— Dutiable" should be "Paper— Other— Dutiable";
   "Other— In wood" should be "Wines, still— Other— In wood"; "Arabian— Plantation" should be
   "Coffee— Arabian— Plantation". (795 rows start `Other— `, 654 start `Arabian— `.) Keep a stack of headings,
   not one.
B. **A sub-entry heading is dropped on a continuation page.** Under "Spices—" the next page lists "Wild"
   (Cinnamon, Wild), "Cloves and Mace", "Nutmegs", "Pepper", "Pepper (long)", "Vanilla", "Ginger" bare; under
   "Coffee—" a bare "Liberian" and (1901) "Plantation". A page that opens with "<Heading>—contd." or follows a
   page that ended inside a heading's sub-entries continues that heading. Use the membership you learn from
   all six volumes and both flows (a name seen as "Spices— Nutmegs" in one volume is a sub-entry of Spices in
   the others).
C. **A heading that lies in a block you skip is lost for the entries after it** (1906 pdf page 696: "Liquid
   Fuel" should be "Oil— Liquid Fuel"; the "Oil—" heading is in a skipped block). Record headings even when
   the rows around them are skipped.
D. **A heading wrongly kept.** "Silver— Pearls and Precious Stones" (249 rows, all six volumes): Pearls and
   Precious Stones is a top-level article. "Desiccated— Fresh" (372 rows): "Desiccated—contd." is a
   continuation of the sub-entry "Cocoanut— Desiccated", not a heading; "Fresh" is "Cocoanut— Fresh".
   In general "<X>—contd." where X is a known sub-entry continues that sub-entry and its heading.
E. **The previous one-line article fused into the next name** ("Arippe Cinchona Bark" for "Cinchona Bark").
F. **Label letter errors are OCR and must stay as read** ("Durable" for Dutiable): do not correct them.
G. **Quantity columns swapped on one page per volume.** On the "Paper—contd." import page the header prints
   "Quantities entered for home consumption" before "Total quantities imported" (tables bb1902:p636,
   bb1903:p668, bb1904:p676, bb1905:p695, bb1906:p698). Assign measures from each table's own header row,
   never by position alone, for every table.
H. **Class and group.** "1.—" and "L.—" are misreadings of the class numeral "I.—": keep them as read but
   make the class value consistent within a run of pages only when the page prints nothing else (do not
   invent text). A lettered sub-group such as "(b) Cotton" must persist onto a following page that prints
   only "(1) Textile—contd.". "I.—Live Animals—Cattle" on one line is class "I.—Live Animals", article
   "Cattle". 1,710 export rows of 1902 have an empty class: find out why and fix it if the page headings are
   in the tables or in `pages/1902.jsonl.gz`.
I. **Articles printed with two sub-columns of quantity** (Perfumery with gal. and cases on bb1904:p676; the
   "(Cotton, Kapok, and Spinning)" columns re-headed "Kapok or Tree Cotton" / "Cotton for Spinning" on
   bb1906:p714): do not emit their figures under the standard measures; skip them with a reason unless the
   rows make the two columns unambiguous, in which case put the sub-column name in the note as a component.
J. `country_group_as_printed` is empty on some rows that sit under "Br. Col.—": keep the group current.

## What to deliver

- The repaired `read_trade_old.py` (same output files and columns).
- `jobs/trade_1901_1906_work/README_round2.md`: for each of A–J what you changed and the before/after counts
  from a query; the per-volume table the reader prints, before and after.
- `jobs/trade_1901_1906_work/recheck2.tsv`: the 238 sampled rows matched to your new output by table_id,
  source row and measure, with the old verdict, your new article / class / group / measure, and whether the
  row now agrees with `what_the_page_shows` (yes / no / removed from output / cannot tell). Also rerun your
  first recheck (`recheck.tsv`, the earlier 240 rows) and report whether any row that agreed before no longer
  does. Do not claim a row is fixed unless the new label equals what the page shows.
- Say plainly what you did not manage to repair.

Never change a figure. Never invent a label that is not in the OCR rows.
