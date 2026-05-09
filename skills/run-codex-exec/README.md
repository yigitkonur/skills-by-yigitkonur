# run-codex-exec → orchestrate-codex (exec mode)

This skill has been folded into [`orchestrate-codex`](../orchestrate-codex/). Its exec-mode behavior — parallel `codex exec` agents in git worktrees with auto-commit and a live Monitor stream — lives there now under one source-of-truth flag policy and a manifest-backed lifecycle.

**Category:** orchestration

## Install orchestrate-codex instead

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/orchestrate-codex
```

Then dispatch in exec mode:

```bash
node <skill>/scripts/orchestrate-codex.mjs exec --tasks tasks.json
```

The recipe lives at `skills/orchestrate-codex/skills/orchestrate-codex/references/modes/exec.md`.

## Why the merge

- One entry point for all five codex modes (exec / batch / single / review / rescue) — agents stop guessing which sub-skill applies.
- Stale flags (`--full-auto`) replaced with the current codex 0.129.0 surface.
- Single source of truth for sandbox / model / effort policy in `codex-flags.sh`.
- Vendored copy of OpenAI's `codex-plugin-cc` scripts as the implementation foundation.
