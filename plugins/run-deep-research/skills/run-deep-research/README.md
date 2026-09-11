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

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-deep-research@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-deep-research -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/run-deep-research/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-deep-research -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```
