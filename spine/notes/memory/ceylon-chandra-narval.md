---
name: ceylon-chandra-narval
description: "Chandra 2 OCR of ALL Ceylon PDFs on narval (started 2026-11-13); remember to upload + OCR later Ceylon Gazette years when the user's download finishes"
metadata:
  node_type: memory
  type: project
  originSessionId: e88c642c-c305-4be4-9db9-86d4f6aeff75
  modified: 2026-11-13T16:20:09.709Z
---

User asked (2026-11-13) to run every Ceylon PDF through Chandra 2 on narval (`ssh narval`, A100 40GB nodes, account def-jic823_gpu).
Scale at start: library 1,877 PDFs / 773k pages / 131 GB + Ceylon Gazettes 16,816 PDFs / 207k pages (1889–1915 so far).
Manifest: /mnt/data/jic823/ocr_chandra/manifest.tsv (ceylon_scripts/ocr_manifest.py — rerun to add new Gazette PDFs; it keeps old rows).
Narval building blocks reused from ~/projects/def-jic823/sessional_v2 (run_volume_narval.slurm, check_doc.py), vllm.sif in
/project/def-jic823/canada50/containers, model in /project/def-jic823/hf_cache.

Upload DONE 2026-11-13 17:56Z: all 18,693 PDFs (150.5 GB) size-verified in narval:/scratch/jic823/ceylon_ocr/pdfs/ (same relative paths as manifest `rel`; Gazettes under ceylon_gazettes/<year>/), manifest at /scratch/jic823/ceylon_ocr/manifest.tsv. Upload script: ceylon_scripts/ocr_upload.sh (rsync, resumable). Job scripts staged in /project/def-jic823/ceylon_ocr/ (run_bundle.slurm, chandra_ceylon.py saves _layout.jsonl, check_ceylon.py, make_bundles.py; chandra --page-range is 0-based); test job cancelled; user said they'd handle running on narval — don't submit jobs unless asked.

**PENDING:** the user's Ceylon Gazette download (~/Documents/ceylon/gazettes, download_gazettes.py, runs to 1948) was still going;
when it completes (expected a few days after 2026-11-13) rerun the manifest, upload the new PDFs and OCR them. Also make the
corresponding new Zotero gazette import (zotero_build.py gazettes).
Gazettes mix English, Sinhala and Tamil scripts — user curious whether Chandra handles them; check and report.

**How to apply:** at the start of any Ceylon session, check whether the gazette download finished and the new years were sent to narval.
Not the London Gazette ([[london-gazette-separate]]). See [[plato-chandra-ocr]], [[ceylon-data-layout]].

**Status 2026-11-17 (pasted by the user):** a separate session downloads finished OCR to `/mnt/data/jic823/ocr_chandra/out_chandra2/`: 614k of 980k pages (63%); Blue Books 100%, IA sweep 80%, other sources 76%, new sources 60%, History of Ceylon Tea 39%, Ceylon Gazettes 25%. Every piece is listed in `~/Documents/ceylon/spine/sources/ocr_registry.tsv`.
