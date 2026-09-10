# test-by-mcpc-cli

Drive mcpc 0.6.x to test or smoke-check MCP servers over stdio or Streamable HTTP, including sessions, schemas, tasks, protocol versions, and JSON automation.

**Category:** testing

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install test-by-mcpc-cli@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended):**
   Omitting the `-g` flag installs the skill directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global agent conflicts.

   ```bash
   # This skill only
   npx -y skills add -y yigitkonur/skills-by-yigitkonur/skills/test-by-mcpc-cli

   # Or the full pack
   npx -y skills add -y yigitkonur/skills-by-yigitkonur
   ```

2. **Global install (user-level):**
   Installs across all supported global agents (`~/.agents/skills`).

   ```bash
   # This skill only
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/test-by-mcpc-cli

   # Or the full pack
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
   ```

   > [!NOTE]
   > If global installation reports `PromptScript does not support global skill installation`, you can safely ignore it. PromptScript is project-scoped by design; the skill is already installed for all other agents. To avoid this warning completely, run the project-level command above without `-g`.
