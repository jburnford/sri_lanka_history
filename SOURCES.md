# Sources and what may be published here

This repository is public. The rule, set on 16 November 2026: material that came from archive.org or a similar
open library may be published, including OCR text; material harvested from the History of Ceylon Tea website
(historyofceylontea.com) may not be published as raw OCR or page images.

| Material | Came from | In this repository |
|---|---|---|
| Ceylon Blue Books (13 volumes so far) | archive.org; identifiers in `spine/bluebook/volumes.tsv` | Parsed tables and page text (`spine/bluebook/tables`, `pages`) and everything extracted from them |
| Casie Chitty, *The Ceylon Gazetteer* (1834) | archive.org item `in.ernet.dli.2015.94788` | OCR text and parsed entries |
| *Tropical Agriculturist* | github.com/jburnford/tropical-agriculturist (public) | Derived tables only: name counts, grounding decisions. The corpus stays in its own repository |
| Colonial Office List graph | github.com/jburnford/col_matching | Read at build time; not copied here |
| Empire Evolution graph | github.com/Working-Papers-in-Critical-Search/paper-002-empire-evolution | Read at build time; not copied here |
| Wikidata | wikidata.org (CC0) | Items read back by identifier (`spine/gazetteer`) and search results (`spine/cache`) |
| Catalogue of Life | ChecklistBank release 317005 (COL26.11, doi:10.48580/dgzy8, CC BY) | Name-match results (`spine/cache/col_match*.jsonl`) |
| History of Ceylon Tea website harvest | historyofceylontea.com | **Nothing.** Not used by `spine/` |
| Research assistant's person review | project staff | **Held back** (`spine/gold/`, `spine/grounding/people_review.jsonl`) until she agrees to be named or the files are anonymised |

Before adding a new folder to `.gitignore`'s allow-list, add a row here saying where its contents came from.
