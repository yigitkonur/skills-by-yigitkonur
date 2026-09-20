# herdr

Orchestrate coding agents, parallel subagents, isolated Git worktrees, and clean-context PR reviews using the Herdr multiplexer.

**Category:** orchestration

## Core Capabilities

- **Role-First Multi-Agent Router**: CTO, Engineering Manager (EM), and native AGY implementers, reviewers, integration executors, and recovery executors all read the same skill — role selection determines which sections to execute. Runtime is not role.
- **Verified Registration**: Workers verify actual TUI runtime and model, then register with the manager. Proceed without ACK when preflight fully matches; preserve explicit acknowledgment on mismatch, restart, or unclear authority.
- **Bidirectional Push Notification**: Workers push completion notices directly to the manager return pane (`herdr agent prompt`). No passive polling. Bounded observation and report reconciliation serve as fallback.
- **Clean-Context Exact-SHA Review**: Fresh reviewer agents in dedicated panes audit exact candidate commit SHAs with zero context pollution. Changed HEAD automatically invalidates stale reviews.
- **Parallel Writers, Serial Integration**: Disjoint writers execute in parallel across isolated worktrees. The Integration Executor combines verified candidates serially into a moving baseline.
- **Canonical Reporting Contract**: Two durable artifact kinds — mutable manager checkpoint (`state.yaml`) and immutable YAML producer reports — published atomically via a single canonical contract.
- **Evidence-Preserving Cleanup**: Only owned, completed, clean resources are removed. Evidence is archived before teardown. No force removal without inventory.

## Requirements

Install Herdr and run agents inside Herdr-managed panes (`HERDR_ENV=1`):

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
