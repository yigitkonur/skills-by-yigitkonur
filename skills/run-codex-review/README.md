# run-codex-review → orchestrate-codex (review mode)

This skill has been folded into [`orchestrate-codex`](../orchestrate-codex/). Its review-mode behavior — per-branch convergence loops with classifier and main-agent decisioning — lives there now, rewritten on top of native `codex exec review` (codex CLI 0.121+) and OpenAI's vendored codex-plugin-cc scripts.

**Category:** orchestration

## Install orchestrate-codex instead

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/orchestrate-codex
```

Then dispatch in review mode:

```bash
node <skill>/scripts/orchestrate-codex.mjs review --branches feat/auth feat/billing
```

The recipe lives at `skills/orchestrate-codex/skills/orchestrate-codex/references/modes/review.md`.

## Why the merge

- Native `codex exec review` replaces the older `/codex:review` slash-dispatch.
- No third-party bots in the loop — codex is the only review source.
- Round cap tightened to 10 (down from 20).
- Main agent owns evaluation and apply; no Applier sub-agent.
- PR creation stays in `ask-review`; merge stays in the user's flow.
