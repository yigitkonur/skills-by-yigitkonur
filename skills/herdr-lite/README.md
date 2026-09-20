# herdr-lite

Orchestrate coding agents with native Git worktrees, PR-driven state tracking, and side-by-side review-and-fix panes using the Herdr multiplexer.

**Category:** orchestration

## Core Capabilities

- **AGY-First Direct Orchestration**: Run lightweight, agile multi-agent workflows without requiring a Codex CTO/EM hierarchy, `state.yaml` checkpointing, or disk-based YAML reporting.
- **Native Infrastructure State Machine**: Uses Git worktrees, GitHub Issues, Pull Requests, and commit SHAs as the living project state machine.
- **Single-Call Worktree Provisioning**: Automatically provisions isolated workspaces and root panes in one atomic command (`herdr worktree create`).
- **Sibling Review-and-Fix**: Pairs each implementer with an independent side-by-side reviewer (`gemini-3.8-flash-high`) who audits exact candidate SHAs, authors missing test patches directly, and posts GitHub PR review approvals.
- **Strict Invariant Safeguards**: Codifies PR #88 engineering physics—exact-SHA review binding, 2-round failure bounds, mandatory `idle` waiting before AGY prompt injection, modal bridge handling, and clean-only worktree removal gates.

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
/plugin install herdr-lite@yigitkonur
```

**With the `skills` CLI:**

```bash
# Project-level install (recommended)
npx -y skills add yigitkonur/skills-by-yigitkonur/skills/herdr-lite -y

# Global install (user-level)
npx -y skills add yigitkonur/skills-by-yigitkonur/skills/herdr-lite -y -g -a universal
```

## Use

Invoke `/herdr-lite`, or ask naturally:

- "Use Herdr-Lite to dispatch parallel worktrees for these 3 GitHub issues with side-by-side reviewers."
- "Orchestrate an implementer and a gemini-3.8-flash-high reviewer in a new worktree for this bug."
- "Review and fix this candidate branch in a split pane with automated PR approval."
- "Clean up finished Herdr-Lite worktrees and retire worker panes safely."
