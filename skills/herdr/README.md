# herdr

Orchestrate or control Herdr agents, panes, tabs, and worktrees when explicitly requested.

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

The skill discovers the installed CLI and keeps one current task table. Independent
work runs in separate tabs and worktrees; related reviews use panes in the same
tab. Workers stay interactive so you can follow their progress and take over.

Monitoring uses bounded native WAIT commands followed by a short READ, with
separate handling for host yields, timeouts, lost observers and stopped workers.
It does not create custom polling daemons or promise background wakeups that
your host cannot provide.

For issue-driven projects, the workflow covers shared-contract ownership,
separate worker/build/install budgets, standalone mission briefs, PR discovery,
draft-to-ready handoffs, proportionate review, serial integration and prompt
terminal cleanup. Closing a terminal never substitutes for merging its work.

Install this skill on its own or with the pack. Local `dispatch`, `implement`
and merge-conflict skills are optional companions; the core workflow is included
here. Agent kind/model, test commands and delivery authority come from your
request and project, rather than a fixed provider or approval policy.

Try: “Use Herdr to group the confirmed issues into up to 20 independent
worktrees, keep the agents interactive, and deliver each outcome through a
reviewed PR. Show the dependency and resource plan first.”
