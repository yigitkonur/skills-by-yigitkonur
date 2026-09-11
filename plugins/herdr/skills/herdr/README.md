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

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/herdr -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/herdr/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/herdr -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```

## Use

Invoke `/herdr`, or ask naturally:

- “Use Herdr to split a pane on the right and start a Claude reviewer.”
- “Inspect the agent in the neighboring Herdr pane and tell me why it is blocked.”
- “Use Herdr to run the tests in a new pane without changing my focus.”
- “Monitor these Herdr agents and notify me when one settles.”

The skill is intentionally prose-first: the agent discovers the installed CLI, selects the appropriate workspace/tab/pane/agent primitive, and verifies state after every action. Long-running monitoring uses Herdr’s socket event subscriptions rather than polling.
