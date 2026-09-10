# update-agent-config

Auditing AGENTS.md/CLAUDE.md/REVIEW.md hierarchies for drift after refactors: stale file:line refs, recounts, invalidated rules, folder-coverage maps, or deciding which gap folders earn a folder-scoped AGENTS.md.

**Category:** configuration

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install update-agent-config@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended):**
   Omitting the `-g` flag installs the skill directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global agent conflicts.

   ```bash
   # This skill only
   npx -y skills add -y yigitkonur/skills-by-yigitkonur/skills/update-agent-config

   # Or the full pack
   npx -y skills add -y yigitkonur/skills-by-yigitkonur
   ```

2. **Global install (user-level):**
   Installs across all supported global agents (`~/.agents/skills`).

   ```bash
   # This skill only
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/update-agent-config

   # Or the full pack
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
   ```

   > [!NOTE]
   > If global installation reports `PromptScript does not support global skill installation`, you can safely ignore it. PromptScript is project-scoped by design; the skill is already installed for all other agents. To avoid this warning completely, run the project-level command above without `-g`.
