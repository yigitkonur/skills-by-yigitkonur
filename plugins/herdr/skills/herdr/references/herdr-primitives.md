# Herdr CLI Primitives & Command Reference

Command reference for selected Herdr client/server 0.9.0 (protocol 22) primitives. Selected non-interactive CLI commands return structured JSON natively on stdout; screen buffer reads (`herdr pane read`, `herdr agent read`), help text, and status modes emit plain text or ANSI.

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
| `current` | `herdr pane current --current` | Returns caller's live coordinates (`pane_id`, `tab_id`, `workspace_id`, `cwd`). Always pass `--current`. |
| `list` | `herdr pane list [--workspace <ID>]` | Lists all terminal panes. |
| `get` | `herdr pane get <PANE_ID>` | Inspects pane details, session metadata, and process state. |
| `layout` | `herdr pane layout [--pane <ID>] [--current]` | Shows spatial layout coordinates ($x, y, w, h$). |
| `process-info` | `herdr pane process-info [--pane <ID>]` | Returns process tree (PID, command, children, foreground process). |
| `split` | `herdr pane split [--pane <ID>] [--current] --direction <right\|down> [--cwd <DIR>] [--no-focus]` | Splits pane horizontally (`right`) or vertically (`down`). |
| `read` | `herdr pane read <PANE_ID> [--source <SRC>] [--lines <N>]` | Captures raw terminal buffer output (plain text/ANSI). |
| `send-keys` | `herdr pane send-keys <PANE_ID> <KEYS...>` | Sends key events to pane PTY (`esc`, `enter`, `ctrl+c`, etc.). |
| `send-text` | `herdr pane send-text <PANE_ID> "<TEXT>"` | Injects literal text into PTY without trailing newline. |
| `run` | `herdr pane run <PANE_ID> "<CMD>"` | Injects text and sends Enter atomically. |
| `wait-output` | `herdr pane wait-output <--match <TEXT>\|--regex <PAT>> <PANE_ID> [--timeout <MS>]` | Blocks until matching terminal output appears in recent buffer. |
| `resize` | `herdr pane resize --pane <ID> --direction <left\|right\|up\|down> --amount <FLOAT>` | Adjusts split boundary fractionally (per installed 0.9.0 help). |
| `zoom` | `herdr pane zoom --pane <ID>` | Toggles full-tab maximization of the pane. |
| `close` | `herdr pane close <PANE_ID>` | Terminates PTY session and destroys the pane. |

---

## 3. Worktree Commands (`herdr worktree`)

Manage Git worktree-backed workspaces over the socket API.

| Subcommand | Syntax | Description |
|---|---|---|
| `create` | `herdr worktree create --cwd <DIR> --path <PATH> --branch <BRANCH> [--base <REF>] [--label <LBL>] [--no-focus]` | Provisions Git worktree, dedicated workspace, and initial root pane. |
| `open` | `herdr worktree open --cwd <DIR> --path <PATH> [--label <LBL>] [--no-focus]` | Attaches existing worktree directory as a Herdr workspace. |
| `list` | `herdr worktree list [--workspace <ID>] [--cwd <PATH>] [--trust-repository]` | Lists active worktree-backed workspaces (per installed 0.9.0 help; does not support `--json`). |
| `remove` | `herdr worktree remove --workspace <ID> [--force]` | Unlinks worktree checkout from disk and closes Herdr workspace. Refuses dirty trees unless `--force` is passed. |

---

## 4. Workspace & Tab Commands (`herdr workspace`, `herdr tab`)

| Subcommand | Syntax | Description |
|---|---|---|
| `workspace list` | `herdr workspace list` | Lists all active workspaces. |
| `workspace create` | `herdr workspace create [--label <LBL>]` | Creates a new independent workspace. |
| `workspace close` | `herdr workspace close <ID>` | Closes Herdr UI workspace and pane processes only (preserves Git worktree on disk). |
| `tab list` | `herdr tab list [--workspace <ID>]` | Lists tabs within a workspace. |
| `tab create` | `herdr tab create [--workspace <ID>] [--cwd <DIR>] [--label <LBL>] [--no-focus]` | Creates a new tab inside an existing workspace. |
| `tab close` | `herdr tab close <ID>` | Closes a tab and its contained panes. |

---

## 5. Notification Commands (`herdr notification`)

| Subcommand | Syntax | Description |
|---|---|---|
| `show` | `herdr notification show <TITLE> [--body <TEXT>] [--position <POSITION>] [--sound <SOUND>]` | Displays a desktop toast alert. Options: `--position <top-left\|top-right\|bottom-left\|bottom-right>`, `--sound <none\|done\|request>`. |

---

## 6. Remote Forwarding Commands (`--machine`)

When executing across remote SSH machines (per upstream lines 91–105):
- **Server-Scoped Handles**: IDs and live agent names are scoped to one server. Two saved SSH machines can both have `w1:p1` or an agent named `reviewer`. Selecting a machine in the TUI does not retarget commands running in your pane: without `--machine`, commands use the inherited local session and socket context.
- **Global Machine Prefix**: To control a saved SSH machine, use the same global prefix for discovery and every later command:
  ```bash
  herdr --machine <label-or-id> agent list
  herdr --machine <label-or-id> pane list
  herdr --machine <label-or-id> agent prompt <remote-agent-name> "Reply with your current status." --wait --timeout 120000
  ```
- **Target Selection**: The selector must be an enabled saved profile ID or a unique, case-sensitive label, not an arbitrary SSH hostname. Commands use that profile's remote session without an open TUI.
- **Flag Separation**: Do NOT combine `--machine` with `--session` or `--remote`. Discover IDs on that machine; inherited local IDs and `--current` do not identify remote panes.
- **Server Compatibility & Non-Fallback**: Both installations must support machine API forwarding, and the remote server must already be running and API-compatible. Forwarding never installs, starts, or restarts a server, and never falls back to Local. Local configuration, session management, installation commands, and interactive attachment are not forwarded.
- **Path Constraints**: Remote worktree paths must be absolute, `~`, or start with `~/`; plugin link paths must be absolute.
- **Dropped Connection Inspection**: A connection failure does not prove a mutation was not applied: inspect remote state before retrying.
- **Profile Management**: `herdr machine list` lists saved connection profiles, not a cross-machine pane inventory (add `--json` for scripts). Profile management (add, remove, enable, disable) is user-authorized only. Removing a profile disconnects the client but does not stop remote sessions. Adding a machine uses the remote default session unless `--remote-session` is explicitly supplied. Setup asks before stopping an incompatible server (defaults to No; requires user consent). Experimental handoff is not part of `machine add`.
