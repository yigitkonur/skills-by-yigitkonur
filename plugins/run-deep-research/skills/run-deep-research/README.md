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

1. **Project-level install (recommended):**
   Omitting the `-g` flag installs the skill directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global agent conflicts.

   ```bash
   # This skill only
   npx -y skills add -y yigitkonur/skills-by-yigitkonur/skills/run-deep-research

   # Or the full pack
   npx -y skills add -y yigitkonur/skills-by-yigitkonur
   ```

2. **Global install (user-level):**
   Installs across all supported global agents (`~/.agents/skills`).

   ```bash
   # This skill only
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-deep-research

   # Or the full pack
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
   ```

   > [!NOTE]
   > If global installation reports `PromptScript does not support global skill installation`, you can safely ignore it. PromptScript is project-scoped by design; the skill is already installed for all other agents. To avoid this warning completely, run the project-level command above without `-g`.
