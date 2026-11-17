---
name: polite-crawling
description: User wants scraping of small heritage sites (e.g. historyofceylontea.com) to be slow and respectful
metadata:
  node_type: memory
  type: feedback
  originSessionId: e88c642c-c305-4be4-9db9-86d4f6aeff75
  modified: 2026-11-06T18:07:49.923Z
---

When harvesting small heritage/research websites, crawl respectfully: one connection, >=2 s between requests, honour Retry-After, stop on 403/blocking, never re-fetch saved files, fetch only needed content.

**Why:** user said "be respectful" when we found historyofceylontea.com live (2026-11-06); these are volunteer-run sites they value as sources.
**How to apply:** default to slow serial crawls for such sites; prefer the live site over Wayback when it's up, but don't hammer either. See [[ceylon-data-layout]].
