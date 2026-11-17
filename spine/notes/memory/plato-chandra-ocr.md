---
name: plato-chandra-ocr
description: How to run Chandra OCR 2 on the plato SLURM cluster (ssh plato) without disturbing the user's other jobs
metadata:
  type: reference
---

`ssh plato` is a SLURM login node (no GPU on the login node). Chandra OCR 2 runs as an all-in-one sbatch job
(vLLM in apptainer + `chandra` CLI from `~/chandra_plato/venv`): copy `~/chandra_plato/run_chandra_sp_rx.sh`,
change job name, `PDF_DIR`, `OUTPUT_DIR`, and `sbatch` it (account hpc_p_clifford, MIG slice `gpu:3g.40gb:1`).
Put inputs/outputs under `~/projects/def-jic823/<project>/`. The user usually has long-running self-chaining
jobs there (e.g. gazette-ocr / gazette-mig / gazette-up) — submit a separate job, never touch those.

First use for Ceylon (2026-11-11): de Silva *History of Sri Lanka* re-OCR, `run_chandra_desilva.sh`,
output `~/projects/def-jic823/ceylon_desilva/out`; feeds the recheck list in [[ceylon-data-layout]]
(`~/Documents/ceylon/timeline/ocr_checks.json`).

Chandra also runs locally on the GB10 (model cached in ~/.cache/huggingface, vllm in miniforge, `chandra` CLI in ~/Documents/gazette_ocr/venv): see /mnt/data/jic823/ceylon_scripts/chandra_desilva_local.sh. Always pass `--paginate_output` when page-level citations matter — without it the .md has no page breaks (metadata.json only has per-page chunk counts) and pages must be re-aligned.
