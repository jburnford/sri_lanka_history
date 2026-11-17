---
name: ceylon-spine-state
description: "Orientation to the Ceylon knowledge graph as of 2026-11-17 — where the docs are, how to rebuild, what is trusted, what is open (written for an outside reviewer too)"
metadata:
  node_type: memory
  type: project
  originSessionId: bf056b45-6c5f-48bd-aaa7-d1b4913efc85
  modified: 2026-11-17T22:44:14.432Z
---

State on 2026-11-17 (it changes daily: trust the in-repo docs over this note).

**Read first, in the repo `~/Documents/ceylon` (public: `jburnford/sri_lanka_history`, branch `main`):**
`README.md`, `SOURCES.md`, `spine/README.md`, `spine/STATUS.md` (what is built, counts, open questions), `spine/UPSTREAM_ERRORS.md`, `spine/bluebook/README.md`, `spine/bluebook/extracted/trade_README.md`, `spine/bluebook/page_readings/README.md`.

**Design:** decision files under `spine/` are the source of truth; Neo4j `neo4j-ceylon-spine` (bolt 7691, http 7478) is a disposable projection rebuilt by `spine/load_graph.py` (python: `/home/jic823/miniforge3/bin/python`). Built on the Colonial Office List graph (`col_matching/`) and Empire Evolution (`empire-evolution/`), joined by Wikidata QIDs. Never write a QID from memory. Logins are in `neo4j-local/auth*.env`: keep them out of output and handoffs.

**Main parts:**
- Journal (Tropical Agriculturist) entities grounded to Wikidata: `spine/ground_names_wd.py`, `ground_places_wd.py`, overlays in `spine/grounding/` (`name_decisions.jsonl`, `name_rejections.jsonl`, `place_review_notes.jsonl`). Coverage of records: places 77.5%, commodities 70.2%, taxa 56.5%, organisations 5.8%.
- Blue Books 1863–1938 (63 volumes, 48,091 OCR tables) in `spine/bluebook/`: every table has a confidence level (`table_confidence.tsv.gz`: summed / two_readings / partly / unconfirmed / suspect), see [[chandra-invents-on-blank-pages]]. Extracted: acreage, officials (167,416 person-years; 6,100 matched to the Colonial Office List), trade ledgers 1907–1928, trade by country and class 1922–1938, the Statistical View annual series. `link_observations.py` loads only files in its `ACCEPTED` list.
- Codex job folders (brief, input, output, summary): `spine/grounding/review_jobs*/`, `spine/grounding/org_job/`, `spine/bluebook/jobs/`. See [[codex-cli-sol]].

**Known weak points (what a review should press on):**
- Trade ledgers 1901–1906 (`read_trade_old.py`, `extracted/trade_1880_1906.tsv.gz`): not loaded; two scan checks scored 63% then 86%; third check was running on 2026-11-17. 1902 tea exports are missing from the output.
- Trade ledgers 1880–1900 (Codex): only 1,288 of 2,760 articles agree with printed totals; not loaded. 1863–1877 untouched.
- The 1907–1928 trade sample (297 of 312 right) was not re-read after the fixes; tea 1907 and 1917 incomplete.
- Officials extractor only spot-checked; the 1928 acreage table not checked against the page.
- Reviewed name matches are labelled as reviewed proposals (medium); some rejections say "rejected by a person" though a Claude review made them.
- Organisation authority list (`org_job/`, 1,222 bodies from 2,265 names) is a Codex proposal, sampled but not loaded.
- Local data ready but unused: Wikidata slim extract (`/mnt/data/jic823/wikidata/20261109/slim`, 122 parts, done 2026-11-17) and the History of Ceylon Tea page index (`spine/links/hoct/`, git-ignored; publish links only, see [[sri-lanka-history-repo]]).

**Who owns what:** this session = knowledge graph (`spine/`); another Claude session = GIS/atlas and the 1834 Casie Chitty gazetteer files; a third downloads OCR from narval ([[ceylon-chandra-narval]]). Shared checkout: pull first, path-limited commits, never force.

Related: [[ceylon-spine-approach]], [[ceylon-data-layout]], [[wikidata-local-dump]].
