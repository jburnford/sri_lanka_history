---
name: sri-lanka-history-repo
description: "Public GitHub repo for the whole Ceylon project, its local root, and the rule on what may be published"
metadata:
  node_type: memory
  type: project
  originSessionId: bf056b45-6c5f-48bd-aaa7-d1b4913efc85
  modified: 2026-11-16T18:52:56.794Z
---

On 2026-11-16 the user named `https://github.com/jburnford/sri_lanka_history` (public) as the repo for the whole Ceylon project. Codex is building an online atlas from the GIS data in the same repo (its working folder that day: `~/Documents/ceylon/sites/ceylon-hgis-atlas`).

Local clone: I ran `git init` at `~/Documents/ceylon/` itself (branch `main`, remote `origin`), with a root `.gitignore` that ignores everything except an allow-list (`README.md`, `SOURCES.md`, `spine/`). Add a folder to the allow-list, and a row to `SOURCES.md`, before committing it. `col_matching/` and `empire-evolution/` are separate nested repos and stay ignored.

**Publication rule (user's words, paraphrased):** raw OCR from the Ceylon Tea History website (historyofceylontea.com) cannot go online; anything from archive.org or similar can. The Blue Books and the 1834 Casie Chitty gazetteer are archive.org items, so their OCR text is publishable.

**Refined by the user on 2026-11-17:** facts taken from History of Ceylon Tea material (estate names, acreages, people, dates) may be published; their pages and OCR text may not be reproduced. Link to their page as the source. "We're not trying to rebuild or compete with them; if they've already done the work, link to their work." So before extracting something from their copies, check whether their site already offers it as data, and link instead of redoing it.

**How to apply:** check the source of any text-bearing file before staging it. My own caution, not the user's instruction: the research assistant's review files that name them (`spine/gold/`, `spine/grounding/people_review.jsonl`) are git-ignored until the user says they may be named. The user said "push the data" on 2026-11-16 and I pushed (remote set to SSH; HTTPS has no login; Codex pushes atlas commits to the same branch, so fetch and merge first, never force).

Related: [[ceylon-data-layout]], [[ceylon-spine-approach]].

**Division of work (user, 2026-11-17):** another Claude session owns the GIS database and atlas; this session's scope is the knowledge graph (`spine/`). Don't edit GIS/atlas files (`docs/atlas.js`, `export_atlas.py`, `geography/`); report problems found there instead.
