---
name: ceylon-data-layout
description: "Where Ceylon plantation project data, downloads, logs and research outputs live (survives crashes; /tmp scratch does not)"
metadata:
  node_type: memory
  type: project
  originSessionId: e88c642c-c305-4be4-9db9-86d4f6aeff75
  modified: 2026-11-06T21:18:25.423Z
---

Ceylon plantations/commodities knowledge-graph project (started 2026-11-05/06). Downloads go to the big data drive, not /tmp (a crash on 2026-11-06 wiped the /tmp scratchpad and its scripts).

- Blue Books (65 IA items, original PDFs, md5-verified): /mnt/data/jic823/ceylon_blue_books/<year>_<identifier>/, log dl_pdf.log, IA metadata in _ia_metadata/. Manifest: ~/Documents/ceylon/ceylon_manifest.json.
- Other sources (ChatGPT catalogue ceylon_other_sources.json/.docx, 55 records): /mnt/data/jic823/ceylon_other_sources/<SOURCEID>_<identifier or direct>/, download_log.tsv.
- Tropical Agriculturist: user's repo github.com/jburnford/tropical-agriculturist cloned at /mnt/data/jic823/tropical-agriculturist (OCR corpus + article index; already held, don't re-download).
- historyofceylontea.com harvest (LIVE site is up; Wayback only for removed/old-site content): /mnt/data/jic823/historyofceylontea_wayback/. 263 scanned publications (150 Planters' Assoc, 65 Ferguson, 47 other); 85 site PDFs saved; ~95.5k page GIFs + registries (7,279 estates / 886 planters live) via detached _scripts/pipeline.sh then post_pipeline.sh, plus wayback_run2.sh; resumable — rerun those to restart; progress: _scripts/status.sh. Started 2026-11-06, expected to finish ~2026-11-11.
- Merged new sources from 4 research agents (127 records, 399 IA items, 57 direct PDFs, ~37 GB): /mnt/data/jic823/ceylon_new_sources/{ia/<identifier>/,direct/<host>/}, merged_new_sources.json maps items->record ids, dl_new.log. Downloader: /mnt/data/jic823/ceylon_scripts/dl_new.py (rerun to resume).
- IA texts sweep (Ceylon pre-1948, 4,194 candidates reviewed; 805 queued = one copy per work + distinct volumes): /mnt/data/jic823/ceylon_ia_sweep/<category>/<identifier>/, queue download_queue.tsv, log download_log.tsv; downloader ceylon_scripts/dl_sweep.py (rerun to resume). Review outputs in /mnt/data/jic823/ia_sweep/. User wants ONE copy per book (no duplicates) and NO Tropical Agriculturist (already held).
- User-supplied files identified: /mnt/data/jic823/ceylon_user_added/ (README.tsv); 103134.pdf = Nicholas, Planter's Handbook: Labour in Ceylon (1926) = catalogue lead CROP13.
- New-source research JSONs: ~/Documents/ceylon/research/ (BRIEF.md = shared agent brief).

Top-level guide: /mnt/data/jic823/README_CEYLON.md; master index CEYLON_HOLDINGS_INDEX.tsv + CEYLON_HOLDINGS_SUMMARY.md (built by ceylon_scripts/build_index.py). Unattended supervisor ceylon_scripts/run_all.sh (log run_all.log) started 2026-11-06 21:18Z; archive.org passes done 2026-11-07. On 2026-11-10 harvest had stopped on a local DNS outage (not a block) at registries step (~1.6k/7.3k estates); restarted pipeline + a waiter that runs post_pipeline.sh, and relaunched run_all.sh to retry ~100 IA files that failed during archive.org outages (they return 200 now).

**Why:** user wants work resumable after crashes. **How to apply:** keep scripts/logs on /mnt/data or in the project dir; downloaders skip md5-matching files so reruns resume.

Place-name sweep (2026-11-10): user's Wikidata geography (~/Documents/ceylon/geography/wikidata-*.csv) -> labels via QLever (/mnt/data/jic823/place_sweep/wikidata_labels.tsv) -> 4,965 place terms -> archive.org title/subject search (place_hits.jsonl) -> filters (ceylon_scripts/place_filter.py, place_context.py) -> 349 candidates, hand-reviewed -> 16 queued (place_queue.tsv) into ceylon_ia_sweep/. Lesson: place names add little on archive.org (most hits are Indian namesakes: Mannar in Kerala, Tirunelveli, Puttur, Nalanda); best finds were Jaffna tobacco trade papers in Kerala Legislative Assembly proceedings and Dutch Jaffnapatam memoirs.

Full-text sweep (2026-11-10): archive.org OCR full-text API https://be-api.us.archive.org/fts/v1/search?q=...&size=100&from=N (works without login; meta_year filter drops undated, so filter locally). 101 Ceylon-specific queries (/mnt/data/jic823/fts_sweep/queries.txt) -> 62k items -> 3,239 with >=3 query hits reviewed by 4 agents (review_out_*.tsv) -> 435 works queued (fts_download_queue.tsv) into ceylon_ia_sweep/; ceylon_scripts/run_fts.sh retries + rebuilds index. Far more productive than catalogue or place-name search. 41k lower-scoring hits with snippets remain in fts_candidates.tsv; general serial runs (Economist, Rubber World, Who's Who) rated low wholesale, not snippet-checked.

GIS (2026-11-11): GeoNames LK dump at /mnt/data/jic823/gis/geonames/LK.txt has ~6,000 estate features (EST 3118, ESTX 1588 divisions, ESTR rubber 676, ESTO 447, ESTT tea 240) with coords + old alternate names. ceylon_scripts/estate_geo_match.py matches historyofceylontea registry pages (name + post town within 25 km) -> gis/estates_geonames_match.tsv (first pass 1,030/3,323 placed). Harvest had stopped 2026-11-10 18:05Z on site 5xx; restarted 2026-11-11 with post_pipeline waiter.

Maps (2026-11-11): /mnt/data/jic823/gis/maps/ (archive_org/ = 70 David Rumsey mirrors + 29 Tamil Virtual Academy charts; utexas_pcl/ceylon_1914.jpg), inventory MAPS_INVENTORY.tsv (ceylon_scripts/maps_inventory.py; downloader dl_ia_maps.py). Blocked/not automatable: LoC & Gallica (Cloudflare challenge), Wikimedia Commons API (429 without contact UA — don't use user's email), David Rumsey site (robots disallows /luna/servlet/as search+export, crawl-delay 500), Leiden digital collections (robots disallows /search/, connection reset). Survey of Ceylon one-inch sheets not on archive.org.

Book timeline (2026-11-11): ~/Documents/ceylon/timeline/ — de Silva, A History of Sri Lanka (1981) read chapter by chapter into chapters/chNN.json, merged by scripts/merge_timeline.py into desilva_timeline.json (events/people/places/orgs/relations/statistics, each with book+page citation; places linked to the local Wikidata labels). ocr_checks.json = readings to verify against the Chandra re-OCR (see [[plato-chandra-ocr]]). User wants every detail cited to book and page.
de Silva Chandra OCR text: /mnt/data/jic823/ceylon_desilva_chandra/ (pages_aligned/ per scan page). Speechify listening copy (user reads via Speechify; wants plain text-only PDF, no page images/footnotes): ~/Documents/ceylon/reading_copy/.
