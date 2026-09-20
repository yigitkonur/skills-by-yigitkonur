# herdr

Orchestrate coding agents, parallel subagents, isolated Git worktrees, and clean-context PR reviews using the Herdr multiplexer.

**Category:** orchestration

## Core Architecture & Key Capabilities

- **Role-First Multi-Agent Architecture**: Codex CTO and Engineering Manager (EM) orchestrate native AGY implementers, fresh technical reviewers, and integration executors across dedicated worktrees and panes (runtime != role).
- **Bidirectional Push-Notification Callback**: Eliminates passive polling across agent runtimes (OpenAI Codex, Google Antigravity CLI, Claude Code). Workers push completion notices directly back to the manager return pane (`herdr agent prompt <CALLER_PANE_ID>`).
- **Clean-Context Exact-SHA Reviews**: Dedicated fresh reviewer agents in clean context panes audit exact candidate commit diffs (`git checkout <SHA>`) with zero memory pollution. Any changed branch HEAD automatically invalidates stale reviews.
- **Two Durable Artifact Kinds**: Mutable manager checkpoint (`state.yaml` alone) and immutable YAML producer reports published outside disposable worktrees via a verified 4-step atomic publication pipeline.
- **Interactive Modal Bridge**: Resolves `agent_blocked` states mechanically via `herdr agent read --source visible` and pre-validated atomic keystrokes (`herdr agent send-keys <target> down enter`).
- **4 Screen Inspection Buffers & Degraded Mode**: Alternate Screen Buffer navigation via `recent-unwrapped`, `visible`, `recent`, and `detection`, plus verified native `herdr pane run` fallback for degraded AGY mode.
- **Dynamic Swarm Scaling**: Calibrates with 2 initial workers before dynamically expanding capacity; serializes heavy compilation and git integration while parallelizing code synthesis.

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
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
   ```

## Use

Invoke `/herdr`, or ask naturally:

- "Use Herdr to dispatch parallel AGY workers across isolated worktrees for these tasks."
- "Orchestrate an exact-SHA clean-context review of this candidate branch with a fresh reviewer agent."
- "Inspect the agent in the neighboring Herdr pane and resolve its blocked question."
- "Coordinate this multi-step refactor across Herdr tabs with push callbacks and atomic YAML reports."
