---
name: run-codex-review
description: Use skill if you are following the deprecated codex review install path and need the current orchestrate-codex review mode.
---

# run-codex-review

This is a deprecated compatibility shim. Do not restore the old implementation here.

Use `orchestrate-codex` instead:

```bash
node skills/orchestrate-codex/skills/orchestrate-codex/scripts/orchestrate-codex.mjs review --branches <branch-list>
```

For PR handoff, use `ask-review`. For dirty branch/worktree cleanup, use `run-repo-cleanup`.
