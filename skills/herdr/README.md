# herdr

Orchestrate coding tasks, parallel subagents, isolated Git worktrees, and clean-context PR reviews using the Herdr multiplexer.

**Category:** orchestration

## Core Architecture & Key Capabilities

- **Single-Model Multi-Agent Fleet**: Orchestrate subagents running on the same model in dedicated worktree tabs and split panes.
- **Bidirectional Push-Notification Callback**: Eliminates passive polling across all agent runtimes (Claude Code, Antigravity CLI, Codex, Gemini, Cursor). Workers push completion notices directly back to the orchestrator pane (`herdr agent prompt <CALLER_PANE_ID>`).
- **Clean-Context PR Reviews**: Implementer opens Draft PR → Fresh Reviewer agent in a clean pane/tab audits the diff (`gh pr diff`) with zero context pollution → Feedback applied → Promoted to Ready (`gh pr ready`) → Merged serially.
- **Merge Conflict Resolution**: Rebase on target (`git rebase origin/main`), resolve conflict markers, verify tests, and push with lease (`git push --force-with-lease`).
- **The Interactive Modal Bridge**: Handles `agent_blocked` via `herdr agent read --source visible` and sends atomic pre-validated keystrokes (`herdr agent send-keys <target> down enter`).
- **4 Memory Buffers**: Resolves Alternate Screen Buffer limitations via `recent-unwrapped` and filesystem handbacks.

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

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/herdr
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## Use

Invoke `/herdr`, or ask naturally:

- "Use Herdr to spin up 3 parallel workers in isolated worktrees for these issues."
- "Open a draft PR for this feature, review it in a clean context with a reviewer agent, and merge it."
- "Inspect the agent in the neighboring Herdr pane and resolve its blocked question."
- "Coordinate this multi-step refactor across Herdr tabs with push callbacks."
