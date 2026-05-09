---
name: run-codex-review
description: Use skill if you are looking for run-codex-review specifically — its content has merged into orchestrate-codex; use that skill's review mode for per-branch convergence loops.
---

# run-codex-review → orchestrate-codex (review mode)

This skill has been folded into `orchestrate-codex`. The review-mode behavior — per-branch convergence via native `codex exec review`, classifier + main-agent decisioning, round cap — lives there now, rewritten from scratch on top of OpenAI's vendored codex-plugin-cc scripts and the current codex CLI surface (`codex exec review --json -o`).

## What changed

- Uses the native `codex exec review` subcommand (codex CLI 0.121+) instead of the older `/codex:review` slash dispatch.
- No third-party review bots in the loop. Codex review is the only review source.
- Round cap tightened to 10 (down from 20). The new path is one codex call per round, not a multi-turn applier loop.
- Main agent owns evaluation (`/do-review`) and apply (`Edit`); no Applier sub-agent.
- PR creation stays out of scope — use the separate `ask-review` skill for that.

## How to use it now

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/orchestrate-codex

node <skill>/scripts/orchestrate-codex.mjs review --branches feat/auth feat/billing docs/quickstart
```

See `skills/orchestrate-codex/skills/orchestrate-codex/references/modes/review.md` for the review-mode recipe.
