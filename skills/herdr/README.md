# herdr

Control Herdr panes, tabs, workspaces, worktrees, commands, or coding agents when Herdr is explicitly requested.

**Category:** orchestration

## Requirements

Install Herdr first and run the agent inside a Herdr-managed pane (`HERDR_ENV=1`):

```bash
brew install herdr
# or
curl -fsSL https://herdr.dev/install.sh | sh
```

Herdr documentation: [herdr.dev/docs](https://herdr.dev/docs/)

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install herdr@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended):**
   Omitting the `-g` flag installs the skill directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global agent conflicts.

   ```bash
   # This skill only
   npx -y skills add -y yigitkonur/skills-by-yigitkonur/skills/herdr

   # Or the full pack
   npx -y skills add -y yigitkonur/skills-by-yigitkonur
   ```

2. **Global install (user-level):**
   Installs across all supported global agents (`~/.agents/skills`).

   ```bash
   # This skill only
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/herdr

   # Or the full pack
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
   ```

   > [!NOTE]
   > If global installation reports `PromptScript does not support global skill installation`, you can safely ignore it. PromptScript is project-scoped by design; the skill is already installed for all other agents. To avoid this warning completely, run the project-level command above without `-g`.

## Use

Invoke `/herdr`, or ask naturally:

- “Use Herdr to split a pane on the right and start a Claude reviewer.”
- “Inspect the agent in the neighboring Herdr pane and tell me why it is blocked.”
- “Use Herdr to run the tests in a new pane without changing my focus.”
- “Monitor these Herdr agents and notify me when one settles.”

The skill is intentionally prose-first: the agent discovers the installed CLI, selects the appropriate workspace/tab/pane/agent primitive, and verifies state after every action. Long-running monitoring uses Herdr’s socket event subscriptions rather than polling.
