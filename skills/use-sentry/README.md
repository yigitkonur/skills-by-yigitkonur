# use-sentry

Comprehensive Sentry intelligence and operations suite. Use when initializing Sentry in any project from scratch (with web research up to 20 keywords for stack-specific patterns like MCP servers or scrapers), auditing an existing Sentry setup across 4 enterprise feature pillars, or debugging production incidents, stack traces, and slow spans using the token-efficient 4-rung CLI funnel.

**Category:** observability

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install use-sentry@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended):**
   Omitting the `-g` flag installs the skill directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global agent conflicts.

   ```bash
   # This skill only
   npx -y skills add -y yigitkonur/skills-by-yigitkonur/skills/use-sentry

   # Or the full pack
   npx -y skills add -y yigitkonur/skills-by-yigitkonur
   ```

2. **Global install (user-level):**
   Installs across all supported global agents (`~/.agents/skills`).

   ```bash
   # This skill only
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/use-sentry

   # Or the full pack
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
   ```

   > [!NOTE]
   > If global installation reports `PromptScript does not support global skill installation`, you can safely ignore it. PromptScript is project-scoped by design; the skill is already installed for all other agents. To avoid this warning completely, run the project-level command above without `-g`.
