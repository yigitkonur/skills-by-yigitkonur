---
name: run-batch-codex-research
description: Use skill if you are looking for run-batch-codex-research specifically — its content has merged into orchestrate-codex; use that skill's batch mode for template-fanout codex runs.
---

# run-batch-codex-research → orchestrate-codex (batch mode)

This skill has been folded into `orchestrate-codex`. The batch-mode behavior — template × N inputs with bounded concurrency, idempotent skip-existing, output-size auditing — lives there now, with the central flag policy and the universal manifest contract.

## What changed

- Codex-only by name. The `--cmd` lever for swapping in another LLM CLI is internal; no longer a user-facing knob.
- Pairs `--json` with `-o <answer-file>` on every spawn (the `-o` file is the truth for "did codex produce output" when MCP causes JSONL dropout).
- Manifest-backed: every input row is a manifest entry; rescue redoes failures without re-running successes.
- Concurrency cap default 10 (unchanged); soft-gate `--i-have-measured` flag at >20 (new).

## How to use it now

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/orchestrate-codex

node <skill>/scripts/orchestrate-codex.mjs batch --inputs inputs.txt --template template.md
```

See `skills/orchestrate-codex/skills/orchestrate-codex/references/modes/batch.md` for the batch-mode recipe.
