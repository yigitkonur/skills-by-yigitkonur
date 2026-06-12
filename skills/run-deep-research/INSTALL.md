# run-deep-research

Orchestrate a multi-file evidence corpus on disk over a population of 5+
entities or a market / vendor category — per-entity packs, cross-axis
comparison rollups, source ledgers, optional profile pages, master summary.
Opens with a batched `AskUserQuestion` intake (executor / scale / framing /
scope), then wave-dispatches research that invokes the `run-research` discipline
for every web call. Research runs on a chosen executor — Claude subagents or
parallel `codex exec` jobs. Filesystem is the context channel between waves.

The skill itself lives at `skills/run-deep-research/SKILL.md`.

**Category:** productivity

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-deep-research
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
