# run-batch-codex-research → orchestrate-codex (batch mode)

This skill has been folded into [`orchestrate-codex`](../orchestrate-codex/). Its batch-mode behavior — one prompt template applied to N inputs with bounded concurrency, idempotent skip-existing, output-size auditing — lives there now under a single source-of-truth flag policy.

**Category:** orchestration

## Install orchestrate-codex instead

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/orchestrate-codex
```

Then dispatch in batch mode:

```bash
node <skill>/scripts/orchestrate-codex.mjs batch --inputs inputs.txt --template template.md
```

The recipe lives at `skills/orchestrate-codex/skills/orchestrate-codex/references/modes/batch.md`.

## Why the merge

- Codex-only by design. The `--cmd` lever for swapping in another LLM CLI is internal-only.
- Always pairs `--json` with `-o <answer-file>` (defends against MCP-active JSONL dropout).
- Manifest-backed: rescue redoes failures without re-running successes.
- Soft `--i-have-measured` gate at concurrency > 20.
