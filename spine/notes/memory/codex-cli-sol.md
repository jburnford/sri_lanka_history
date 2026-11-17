---
name: codex-cli-sol
description: "How to hand jobs to Codex CLI: Sol 6.2 for bounded jobs, Astra 6.2 for the full project review (2026-11-17)"
metadata:
  node_type: memory
  type: reference
  originSessionId: bf056b45-6c5f-48bd-aaa7-d1b4913efc85
  modified: 2026-11-17T22:42:40.272Z
---

The user wants spare Codex tokens used for clear, bounded knowledge-graph jobs. On 2026-11-17 they said "we should switch to Sol 6.2".

Run: `/home/jic823/.codex/plugins/.plugin-appserver/codex exec -m gpt-6.2-sol -s workspace-write -C <dir> --skip-git-repo-check -o <last_message file> - < brief.md > codex.log 2>&1`, detached with `(setsid nohup ... &)`.

- Pass the model with `-m`; `~/.codex/config.toml` still says `gpt-6.1-sol` (the user's file, not edited by me).
- Do not add `< /dev/null`: it replaces the brief on stdin.
- Sol needs a written brief, test cases, and jobs that do not run too long. Sample its output against the sources before applying anything (see [[ceylon-spine-approach]]).

Later on 2026-11-17 the user said they will have "the new Astra 6.2" (`gpt-6.2-astra`, also in Codex's model list) do a full review of this project, starting from these memory files. Expect its findings to come back as review input; verify them against the sources like any other proposal. Orientation for it: [[ceylon-spine-state]].
