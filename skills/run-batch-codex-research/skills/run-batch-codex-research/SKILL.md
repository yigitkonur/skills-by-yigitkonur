---
name: run-batch-codex-research
description: Use skill if you are migrating from retired run-batch-codex-research to orchestrate-codex batch mode for codex template fanout.
---

# run-batch-codex-research

This is a retired compatibility shim. Do not restore the old standalone implementation here.

Install and use `orchestrate-codex` batch mode instead:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/orchestrate-codex
```

For template-by-input codex fanout, load `orchestrate-codex` and choose batch mode. Read `skills/orchestrate-codex/skills/orchestrate-codex/references/modes/batch.md` for the active batch contract.

If older notes mention `--cmd`, treat it as an internal migration detail, not a public trigger.
