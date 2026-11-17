---
name: london-gazette-separate
description: /mnt/data/gazette is the London Gazette (separate project) — never mix into Ceylon outputs; Ceylon Gazettes are ~/Documents/ceylon/gazettes
metadata:
  node_type: memory
  type: project
  originSessionId: e88c642c-c305-4be4-9db9-86d4f6aeff75
  modified: 2026-11-12T20:47:32.817Z
---

/mnt/data/gazette/ (pdfs/gazette_NNNNNN.pdf, metadata.csv from 1665, chandra2 OCR) is the **London Gazette** — a related but different project of the user's. The **Ceylon Government Gazettes** are ~/Documents/ceylon/gazettes/<year>/ (diglib.natlib.lk, downloaded by the user's own download_gazettes.py; `.items/<handle>` caches DSpace pages with DC metadata: title, issued date, citation_pdf_url).

**Why:** user corrected (2026-11-12) when building the Zotero library: "only the Ceylon Gazettes; not the London ones".
**How to apply:** exclude /mnt/data/gazette from any Ceylon index, library, KG or OCR work unless the user asks. See [[ceylon-data-layout]], [[plato-chandra-ocr]].
