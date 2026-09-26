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
| `list` | `herdr worktree list [--json]` | Lists all active worktree-backed workspaces. |
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

## 5. Remote Forwarding Commands (`--machine`)

When executing across remote SSH machines:
- Pass `--machine <PROFILE>` to direct commands to a saved SSH forwarding profile in Herdr.
- Coordinates and IDs are server-scoped: a pane ID on machine `dev-box` is independent of a pane ID on machine `local`.
- Paths must be expressed as absolute paths or tilde (`~`) paths on the target machine.
- Remote operations execute headlessly over the socket protocol without requiring a local TUI window.
