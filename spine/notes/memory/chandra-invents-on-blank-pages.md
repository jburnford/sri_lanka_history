---
name: chandra-invents-on-blank-pages
description: Chandra OCR writes plausible fake tables on blank or title pages; how to detect it and how accurate real pages are
metadata:
  type: project
---

Found 2026-11-16 on the Ceylon Blue Books: Chandra OCR invents tables on blank versos and section title pages with show-through (e.g. "quarterly statements Q1-Q4", "Bank of America"). On printed pages its numbers are good (about 2% misread for 3+ digit numbers in 1925-38 volumes, estimated against Tesseract).

**How to apply:** never trust a Chandra table without a check. What worked: (1) compare numbers per page with a Tesseract reading (PDF text layer via `pdftotext`, or archive.org `_hocr_searchtext.txt.gz` + `_hocr_pageindex.json.gz`); (2) no text in the second reading AND zero dark pixels inside the table bbox on the scan = invented (8 of 8 by eye). An empty Tesseract page alone usually means a sideways table, which Chandra reads correctly. Code: `spine/bluebook/confidence.py`, `second_reading.py`, `page_ink.py`. The user wants confidence levels on all data rather than discarding anything.

Related: [[plato-chandra-ocr]], [[ceylon-chandra-narval]].
