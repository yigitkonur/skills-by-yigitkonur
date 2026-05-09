---
name: run-codex-exec
description: Use skill if you are looking for run-codex-exec specifically — its content has merged into orchestrate-codex; use that skill's exec mode for parallel codex agents in worktrees.
---

# run-codex-exec → orchestrate-codex (exec mode)

This skill has been folded into `orchestrate-codex`. The exec-mode behavior — parallel `codex exec` agents in git worktrees with auto-commit, post-verify, and a live Monitor stream — lives there now, with a single source-of-truth flag policy (`--dangerously-bypass-approvals-and-sandbox`, `gpt-5.5`, `xhigh`) and a manifest-backed run lifecycle.

## What changed

- The flag set is centralized in `scripts/codex-flags.sh`. No more per-script defaults; no more `--full-auto` (deprecated upstream).
- The runner (`run-fleet.sh`) reads tasks from a manifest, fans out via `xargs -P`, auto-commits on success, surfaces failures.
- The Monitor stream is mode-aware: one ticker for the whole fleet, manifest counts in every line.
- Rescue mode resumes partial runs without manual manifest editing.

## How to use it now

```bash
# Install orchestrate-codex.
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/orchestrate-codex

# Then run via the dispatcher.
node <skill>/scripts/orchestrate-codex.mjs exec --tasks tasks.json
```

See `skills/orchestrate-codex/skills/orchestrate-codex/references/modes/exec.md` for the exec-mode recipe.
