# herdr

Orchestrate coding agents, parallel subagents, isolated Git worktrees, and clean-context PR reviews using the Herdr multiplexer.

**Category:** orchestration

## Core Capabilities

- **Role-First Multi-Agent Router**: CTO, Engineering Manager (EM), and multi-harness executors (AGY, Codex, Claude Code, Cursor) all read the same skill — role selection determines which sections to execute. Runtime is not role.
- **Harness-Agnostic Fleet Architecture**: Runs seamlessly with Google Antigravity (AGY), OpenAI Codex CLI, Claude Code, or Cursor. Codex is strictly optional; Antigravity natively supports both leadership orchestration (CTO/EM) and task execution.
- **Unbounded Event-Driven Longevity**: Agents operate continuously without arbitrary step or execution limits. Workflows are bounded by disk-backed state checkpoints (`state.yaml`), token-efficient push callbacks, and finite failure budgets (2-strike limit) rather than artificial execution caps.
- **Two-Pane Leadership Topology**: CTO (left) and EM (right) share exactly one leadership tab. Workers and reviewers operate in separate, task-specific tabs or worktree workspaces.
- **Mandatory `/teamwork-preview /herdr` Contract**: Dispatched workers initialize collaborative sub-teams and follow the Herdr operating contract out of the box.
- **Small Coupled Work Default**: Default to 1 whole-change writer and 1 independent reviewer for cohesive tasks; parallelize across isolated worktrees only for genuinely independent deliverables.
- **Conditional Registration**: Workers verify actual TUI runtime and model, then register with the manager. Proceed without waiting for ACK when preflight fully matches; preserve explicit acknowledgment on mismatch, restart, or unclear authority.
- **Cheap Communication & Durable Evidence**: Routine progress and technical questions use short native messages; durable immutable YAML reports are reserved for handback candidates, review decisions, and material blockers.
- **Exact-SHA Review & Finite Failure Bounds**: Fresh reviewer agents in dedicated panes (or side-by-side split) audit exact candidate commit SHAs in clean context. Changed HEAD invalidates stale reviews; same reviewer may issue new-HEAD delta decisions. Two-failure limit enforces escalation rather than endless retries.
- **Early Coherent Candidate & Serial Integration**: Designated writer composes whole-candidate changes locally for unified checks without per-file approval bottlenecks; Integration Executor combines verified candidates serially into a moving baseline.
- **Two-Stage Retrospective Lifecycle**: Terminal panes are retired cleanly upon verified handback; worktree cleanup is a separate gate where clean checkouts are removed, while dirty checkouts and active leadership panes are preserved.

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
