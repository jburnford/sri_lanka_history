---
name: wikidata-local-dump
description: "Shared local Wikidata JSON dump on the external drive, for all knowledge-graph projects"
metadata:
  node_type: memory
  type: reference
  originSessionId: bf056b45-6c5f-48bd-aaa7-d1b4913efc85
  modified: 2026-11-16T15:39:58.147Z
---

A full Wikidata JSON dump lives at `/mnt/data/jic823/wikidata/<YYYYMMDD>/` (first snapshot: `20261109`, `wikidata-20261109-all.json.gz`, about 157 GB, download started 2026-11-16; README and sha1 sums alongside). The user asked for it on 2026-11-16 to be shared across projects, not just Ceylon: the goal is to expand to Canada and other colonies.

Use it (or a slim extract built from it) for exact-name lookup and for verifying types, country, coordinates and dates, instead of the rate-limited Wikidata API or QLever. Candidate search by meaning still comes from the WikidataMCP vector search. Cite the snapshot date in grounding decisions. Check the download finished and passes `sha1sum -c` before relying on it.

Related: [[ceylon-data-layout]], [[ceylon-spine-approach]].

**Status 2026-11-17:** download complete, `sha1sum -c` OK. Slim extract finished: `/mnt/data/jic823/wikidata/20261109/slim/` (122 parquet parts + `_manifest.json`, 8.8 GB, 122,217,527 items; log `/mnt/data/jic823/wikidata/pipeline.log`). The grounding scripts still use the API/QLever; switching them to the extract is not done.
