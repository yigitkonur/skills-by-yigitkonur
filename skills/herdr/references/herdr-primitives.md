# Herdr CLI Primitives & Command Reference

Complete command reference for Herdr client/server 0.9.0 (protocol 22). All non-interactive CLI commands return structured JSON natively on stdout. Do not pass `--json` to commands that already output JSON by default.

---

## 1. Agent Commands (`herdr agent`)

Control and inspect coding agents occupying terminal panes.

| Subcommand | Syntax | Description |
|---|---|---|
| `start` | `herdr agent start <NAME> --kind <KIND> --pane <PANE_ID> [--timeout <MS>] [-- <AGENT_ARGS>...]` | Launches an agent in an existing shell pane. Supported kinds: `pi`, `claude`, `codex`, `gemini`, `cursor`, `devin`, `agy`, `cline`, `omp`, `opencode`, `copilot`, `droid`, `amp`, etc. |
| `prompt` | `herdr agent prompt <TARGET> <TEXT> [--wait] [--until <STATUS>] [--timeout <MS>]` | Submits prompt text using bracketed paste (DEC Mode 2004). If `--wait` is set, waits for settled state. |
| `wait` | `herdr agent wait <TARGET> [--until <STATUS>] [--timeout <MS>]` | Blocks until target reaches requested state (`idle`, `working`, `blocked`, `done`, `unknown`). Default matches `idle`, `done`, `blocked`. |
| `read` | `herdr agent read <TARGET> [--source <SRC>] [--lines <N>] [--format <FMT>]` | Reads formatted terminal screen. Sources: `visible`, `recent`, `recent-unwrapped`, `detection`. Formats: `text`, `ansi`. |
| `send-keys` | `herdr agent send-keys <TARGET> <KEYS...>` | Sends logical key tokens (`esc`, `enter`, `up`, `down`, `tab`, `ctrl+c`). Canonical Escape token is `esc`. |
| `list` | `herdr agent list` | Lists all detected live agents across workspaces. |
| `get` | `herdr agent get <TARGET>` | Shows detailed agent metadata (session ID, model configuration, turn status). *Caution*: `agent get` reflects Herdr's configured/detected metadata, but does NOT prove the live model active in memory; verify model via TUI header or runtime query. |
| `rename` | `herdr agent rename <TARGET> <NEW_NAME>` | Renames an agent handle. |
| `focus` | `herdr agent focus <TARGET>` | Moves cursor/window focus to the agent pane. |
| `explain` | `herdr agent explain <TARGET> [--json]` | Explains heuristic detection state and rules. |

### Lifecycle States:
- `idle`: Ready for input. Server marks viewed completions as idle.
- `working`: Active execution, tool call synthesis, or inference turn underway. (Does NOT prove a specific prompt was consumed).
- `blocked`: Agent is waiting at an interactive modal, confirmation prompt, or question dialog.
- `done`: Ready for input, with unread completion output.
- `unknown`: Agent process detected, but Herdr cannot confidently classify its screen state.

---

## 2. Pane Commands (`herdr pane`)

Control raw terminal PTY execution surfaces, layout splits, and operating system processes.

| Subcommand | Syntax | Description |
|---|---|---|
| `current` | `herdr pane current [--current]` | Returns caller's live coordinates (`pane_id`, `tab_id`, `workspace_id`, `cwd`). |
| `list` | `herdr pane list [--workspace <ID>]` | Lists all terminal panes. |
| `get` | `herdr pane get <PANE_ID>` | Inspects pane details, session metadata, and process state. |
| `layout` | `herdr pane layout [--pane <ID>] [--current]` | Shows spatial layout coordinates ($x, y, w, h$). |
| `process-info` | `herdr pane process-info [--pane <ID>]` | Returns process tree (PID, command, children, foreground process). |
| `split` | `herdr pane split [--pane <ID>] [--current] --direction <right\|down> [--cwd <DIR>] [--no-focus]` | Splits pane horizontally (`right`) or vertically (`down`). |
| `read` | `herdr pane read <PANE_ID> [--source <SRC>] [--lines <N>]` | Captures raw terminal buffer output. |
| `send-keys` | `herdr pane send-keys <PANE_ID> <KEYS...>` | Sends key events to pane PTY (`esc`, `enter`, `ctrl+c`, etc.). |
| `send-text` | `herdr pane send-text <PANE_ID> "<TEXT>"` | Injects literal text into PTY without trailing newline. |
| `run` | `herdr pane run <PANE_ID> "<CMD>"` | Injects text and sends Enter atomically. |
| `wait-output` | `herdr pane wait-output <--match <TEXT>\|--regex <PAT>> <PANE_ID> [--timeout <MS>]` | Blocks until matching terminal output appears in recent buffer. |
| `resize` | `herdr pane resize --pane <ID> --direction <left\|right\|up\|down> --cells <N>` | Adjusts split boundary. |
| `zoom` | `herdr pane zoom --pane <ID>` | Toggles full-tab maximization of the pane. |
| `close` | `herdr pane close <PANE_ID>` | Terminates PTY session and destroys the pane. |

---

## 3. Worktree Commands (`herdr worktree`)

Manage Git worktree-backed workspaces over the socket API.

| Subcommand | Syntax | Description |
|---|---|---|
| `create` | `herdr worktree create --cwd <REPO> --path <PATH> --branch <BRANCH> [--base <REF>] [--label <LBL>] [--no-focus] [--trust-repository]` | Creates a Git worktree, opens a dedicated Herdr workspace bound to it, and launches Pane 1 inside the checkout. |
| `open` | `herdr worktree open --cwd <REPO> --path <PATH> [--branch <BRANCH>] [--label <LBL>] [--no-focus]` | Opens an existing worktree checkout as a Herdr workspace. |
| `list` | `herdr worktree list` | Enumerates all worktree-backed workspaces. |
| `remove` | `herdr worktree remove --workspace <WS_ID> [--force]` | Unlinks worktree checkout from disk and closes workspace. Refuses dirty trees unless `--force` is passed. |

---

## 4. Workspace & Tab Commands (`herdr workspace`, `herdr tab`)

Organize top-level window groups and contained tabs.

### Workspace:
- `herdr workspace list`: Lists all active workspaces.
- `herdr workspace create [--label <TEXT>]`: Creates a new independent workspace.
- `herdr workspace get <WS_ID>`: Shows tabs and panes in workspace.
- `herdr workspace close <WS_ID>`: Closes Herdr UI workspace and session processes. (Does NOT delete Git worktrees).

### Tab:
- `herdr tab create --workspace <WS_ID> [--cwd <DIR>] [--label <TEXT>] [--no-focus]`: Creates a new tab.
- `herdr tab list`: Lists all tabs across workspaces.
- `herdr tab get <TAB_ID>`: Inspects tab coordinates and contained panes.
- `herdr tab close <TAB_ID>`: Closes the tab and all contained panes.

---

## 5. Saved SSH Machines (`herdr --machine`)

Control a remote Herdr server instance via saved SSH connection profiles:

```bash
herdr --machine <label-or-id> agent list
herdr --machine <label-or-id> pane list
herdr --machine <label-or-id> agent prompt <remote-agent-name> "<PROMPT>" --wait
```

### Machine Invariants:
1. **Profile Identification**: Selector must be an enabled saved profile ID or unique label. Do NOT pass raw SSH hostnames.
2. **Dedicated Scope**: Commands run against the remote profile's session without an open TUI. Never combine `--machine` with `--session` or `--remote`.
3. **ID Scope**: Identifiers (`w1:p1`, etc.) are scoped to that specific server; local IDs do not target remote panes.
4. **Remote Paths**: Remote worktree paths must be absolute, `~`, or start with `~/`.
5. **Connection Failure Recovery**: A connection drop does NOT prove a mutating command failed; inspect remote state before retrying.

---

## 6. Notification Commands (`herdr notification`)

Post desktop and TUI notifications to inform the human user of milestones.

- `herdr notification show "<TITLE>" [--body "<TEXT>"] [--sound <none|done|request>]`: Displays a toast banner in Herdr with optional audio alert.

---

## 7. Dynamic Coordinates & Recipe Extraction

Always use dynamic queries with `--current` or explicit verified IDs:

```bash
# Capture live caller pane and tab explicitly:
SELF_PANE="$(herdr pane current --current | jq -r .result.pane.pane_id)"
SELF_TAB="$(herdr pane current --current | jq -r .result.pane.tab_id)"

# Create worktree workspace and extract handles:
WT_RES="$(herdr worktree create --cwd "$PWD" --path "../feature-x" --branch "feat/x" --label "feature-x" --no-focus)"
WS_ID="$(echo "$WT_RES" | jq -r .result.workspace.workspace_id)"
ROOT_PANE="$(echo "$WT_RES" | jq -r .result.root_pane.pane_id)"

# Split pane using explicit parent handle:
SPLIT_RES="$(herdr pane split --pane "$ROOT_PANE" --direction right --no-focus)"
REV_PANE="$(echo "$SPLIT_RES" | jq -r .result.pane.pane_id)"
```
