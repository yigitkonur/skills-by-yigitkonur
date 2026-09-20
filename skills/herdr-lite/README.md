# herdr-lite

Orchestrate coding agents with native Git worktrees, PR-driven state tracking, and streaming review tabs using the Herdr multiplexer.

**Category:** orchestration

## Core Capabilities

- **AGY-First Direct Orchestration**: Run lightweight, agile multi-agent workflows without requiring a Codex CTO/EM hierarchy, `state.yaml` checkpointing, or disk-based YAML reporting.
- **Automatic Ticket Intake & Multi-Wave Scheduling**: When invoked without existing issues, automatically decomposes discussions or bugs into vertical tracer-bullet tickets (`gh issue create`) and schedules up to 5 waves based on blocking dependencies.
- **Native Worktree Workspace Topology**: Each task receives an isolated workspace via `herdr worktree create` containing Tab 1 (`impl`) for the implementer and Tab 2 (`review`) for the reviewer.
- **Continuous "Write Back to Me" Callback Loop**: Implementers and reviewers report completion directly to the orchestrator, advancing tasks and triggering successive waves without stalling.
- **Event-Driven Streaming Review**: As soon as any worker opens a PR and reports `DONE`, a dedicated review tab is immediately spawned inside that worktree workspace without waiting for other parallel workers to finish (no lockstep barrier).
- **Deep Review-and-Fix with Domain Skills**: Pairs each implementer with an independent reviewer (`gemini-3.8-flash-high`) who audits exact candidate commit SHAs using domain skills (`code-review`, `tdd`, `audit-completion`), directly authors test/bug patches, and posts GitHub PR approvals.
- **Serial Merge & Conflict Integration**: Lands approved candidates serially onto moving `main`, applying `resolving-merge-conflicts` skill principles to resolve rebasing conflicts cleanly.
- **Full Primitives Exposure**: Directly leverages Herdr's entire CLI surface (`worktree`, `workspace`, `tab`, `pane`, `agent`, `notification`).
- **Strict Invariant Safeguards**: Preserves PR #88 engineering physics—exact-SHA review binding, 2-round failure bounds, mandatory `idle` waiting before AGY prompt injection, modal bridge handling, and clean-only worktree removal gates.

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

- "Decompose this debugging session into GitHub issues and run them across parallel worktrees with Herdr-Lite."
- "Use Herdr-Lite to dispatch parallel worktrees for these GitHub issues with streaming review tabs."
- "Orchestrate an implementer and a gemini-3.8-flash-high reviewer in a new worktree for this bug."
- "Review and patch this candidate branch in a review tab with automated PR approval."
- "Serially rebase and merge these approved candidate PRs onto main, resolving any conflicts."
- "Clean up finished Herdr-Lite worktrees and retire worker workspaces safely."
