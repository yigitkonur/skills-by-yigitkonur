# herdr-raycast

Driving Herdr from Raycast AI Chat, outside any pane: workspaces, tabs, panes,
worktrees and coding agents (claude, codex, agy) on this Mac or on a saved SSH
machine, through Raycast's bash tool.

The companion of [herdr](../herdr/), which runs inside a Herdr pane. From
Raycast there is no `HERDR_ENV` and no caller pane, so every command names its
server and target. The chat keeps a ledger, waits on agents with background
tasks, hands out briefs small enough for one turn and checks results on the
machine.

**Category:** orchestration

## Install

**With the `skills` CLI (global, user-level):**

```bash
npx -y skills add yigitkonur/skills-by-yigitkonur/skills/herdr-raycast -y -g -a universal
```

This puts the skill in `~/.agents/skills`. Raycast discovers skills in its
skill folders (Raycast Manual, AI, Skills); on the author's Mac it listed skills
from both `~/.agents/skills` and `~/.claude/skills`.

## Run

- Raycast AI Chat on macOS with the bash tool, background tasks included.
- The herdr CLI 0.9.3 on `PATH` locally and on every saved machine
  (`herdr machine list --json`).
- Raycast loads the skill when a chat is about Herdr, or when you mention it
  with `@`.
- For one Raycast AI folder per project, paste [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md)
  (everything below its rule) into the folder's instructions and fill in its
  Project card. It keeps the always-on rules (load the skill, keep the ledger,
  never lose a waiting agent, ask through the question tool) when the skill is
  not loaded or compaction has dropped it.
- [tests/README.md](tests/README.md) holds the lint (`python3 tests/lint.py`),
  the live cases and what to run again after a Herdr, harness or Raycast update.

Raycast links a loaded skill into a temporary folder through a symlink to the
real folder, and on 2026-10-03 (Raycast 2.6.2.0) it wrote an older cached
SKILL.md back through that link eight times. Keep the skill under git and commit
right after each edit; see "Raycast rewrites SKILL.md" in
[tests/README.md](tests/README.md).
