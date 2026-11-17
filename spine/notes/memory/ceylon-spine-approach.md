---
name: ceylon-spine-approach
description: "How the user wants the Ceylon knowledge graph built after the Nov 2026 review — foundation projects, nuance, fix upstream"
metadata:
  node_type: memory
  type: feedback
  originSessionId: bf056b45-6c5f-48bd-aaa7-d1b4913efc85
  modified: 2026-11-16T15:39:58.162Z
---

Guidance from the user on 2026-11-16, while re-planning the Ceylon knowledge graph:

- **Review, don't follow.** The earlier Ceylon graph (`kg/`, Neo4j `neo4j-ceylon`) was built by Codex, which the user does not fully trust. They asked me to rethink the plan and judge whether the path is right, not continue it. They said the old Neo4j database may be deleted if a restart makes sense.
- **Build on the foundation projects.** Ceylon is the first project meant to stand on the Colonial Office List graph (`ceylon/col_matching`) and the Empire Evolution graph (`ceylon/empire-evolution`, cloned 2026-11-16), joined through Wikidata QIDs. The long-term goal is many interoperable projects (Canada, other colonies).
- **Hold as much nuance as possible.** When a choice is between two representations (lasting geographic place vs period polity; a territory's independent dates vs its whole existence), keep both rather than collapsing to one.
- **Fix errors upstream as we go.** Errors are expected in all three gazetteers (Colonial Office List, Empire Evolution, Wikidata's Sri Lanka items). I may edit the local checkouts of the two repos to fix them, and should keep a running list in `ceylon/spine/UPSTREAM_ERRORS.md`. Committing or pushing was not discussed: ask first.

**Why:** the user's argument (their Working Papers in Critical Search paper) is that Wikidata grounding lets separate projects compose; a Ceylon graph that ignores the base projects defeats the point.

**How to apply:** new work goes in `ceylon/spine/` with decision files as the source of truth and Neo4j as a rebuildable projection (my recommendation, which the user accepted implicitly by telling me to proceed). Check any place or polity question against both upstream graphs before grounding afresh. My interpretation, not their words: "nuance" also means recording uncertainty and review status on every decision rather than forcing a match.

Related: [[wikidata-local-dump]], [[ceylon-data-layout]].
