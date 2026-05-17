# run-corpus-research

Orchestrate a multi-file evidence corpus over an entity population —
per-entity packs, cross-entity comparisons, source ledgers, profile
pages, master summary. Wave-based dispatch of researcher subagents
that invoke the `run-research` skill for every web call. Filesystem
is the context channel between waves.

The skill itself lives at `skills/run-corpus-research/SKILL.md`.

**Category:** productivity

## Install

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-corpus-research
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
