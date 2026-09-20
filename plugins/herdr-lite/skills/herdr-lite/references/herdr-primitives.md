# Herdr CLI Primitives & Command Reference

This reference is the canonical cheat-sheet for Herdr's socket API CLI primitives. It documents every core object, command syntax, JSON output structures, and `jq` coordinate extraction recipes.

All commands output structured JSON natively when called non-interactively. Do not pass `--json`.

---

## 1. Worktree Primitives (`herdr worktree`)

Manage Git worktrees paired with dedicated Herdr workspaces.

| Command | Syntax | Description |
|---|---|---|
| `create` | `herdr worktree create <REPO> <PATH> --branch <BRANCH>` | Creates a Git worktree, provisions an isolated Herdr workspace, and launches a root pane in Tab 1. |
| `list` | `herdr worktree list` | Lists all active worktree-backed workspaces. |
| `open` | `herdr worktree open <PATH>` | Re-opens an existing worktree checkout in a workspace. |
| `remove` | `herdr worktree remove <PATH>` | Safely unbinds and removes a worktree checkout. |

### Recipe: Create Worktree & Extract All Coordinates
```bash
WORKTREE_JSON="$(herdr worktree create "$REPO_ROOT" "$WORKTREE_PATH" --branch "$BRANCH_NAME")"

# Extract Workspace ID and initial Root Pane/Tab IDs:
WORKSPACE_ID="$(echo "$WORKTREE_JSON" | jq -er .result.workspace.workspace_id)"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.pane_id)"
IMPL_TAB_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.tab_id)"
```

---

## 2. Workspace Primitives (`herdr workspace`)

Workspaces are the top-level grouping containers in Herdr (analogous to multi-window workspaces).

| Command | Syntax | Description |
|---|---|---|
| `list` | `herdr workspace list` | Lists all workspaces with active tab counts. |
| `get` | `herdr workspace get --workspace <WS_ID>` | Inspects workspace details, tabs, and layout. |
| `focus` | `herdr workspace focus --workspace <WS_ID>` | Switches active TUI view to the target workspace. |
| `rename` | `herdr workspace rename --workspace <WS_ID> <LABEL>` | Sets human-readable workspace title. |
| `report-metadata` | `herdr workspace report-metadata --source <ID> <WS_ID> --token <KEY=VAL>` | Sets badge tokens or visual status in TUI sidebar. |
| `close` | `herdr workspace close --workspace <WS_ID>` | Closes the workspace and all contained tabs. |

---

## 3. Tab Primitives (`herdr tab`)

Tabs group one or more split panes within a specific workspace.

| Command | Syntax | Description |
|---|---|---|
| `create` | `herdr tab create --workspace <WS> --cwd <DIR> --label <NAME> [--no-focus]` | Creates a new tab inside an existing workspace. |
| `list` | `herdr tab list` | Lists all tabs across all workspaces. |
| `get` | `herdr tab get <TAB_ID>` | Inspects tab coordinates and contained panes. |
| `focus` | `herdr tab focus <TAB_ID>` | Focuses the tab in the active workspace. |
| `rename` | `herdr tab rename <TAB_ID> <LABEL>` | Renames the tab label. |
| `close` | `herdr tab close <TAB_ID>` | Closes the tab and all panes within it. |

### Recipe: Create Review Tab Inside Worktree Workspace
```bash
# Open Tab 2 for deep review inside the worktree's workspace:
REV_TAB_JSON="$(herdr tab create --workspace "$WORKSPACE_ID" --cwd "$WORKTREE_PATH" --label "review" --no-focus)"
REV_TAB_ID="$(echo "$REV_TAB_JSON" | jq -er .result.tab.tab_id)"
REV_PANE_ID="$(echo "$REV_TAB_JSON" | jq -er .result.root_pane.pane_id)"
```

---

## 4. Pane Primitives (`herdr pane`)

Terminal PTY execution surfaces.

| Command | Syntax | Description |
|---|---|---|
| `current` | `herdr pane current` | Returns caller's live coordinates (`pane_id`, `tab_id`, `workspace_id`, `cwd`). |
| `list` | `herdr pane list` | Returns JSON array of all active terminal panes. |
| `get` | `herdr pane get --pane <PANE_ID>` | Inspects pane details, session metadata, scrollback. |
| `layout` | `herdr pane layout --pane <PANE_ID>` | Shows tree layout coordinates ($x, y, w, h$). |
| `process-info` | `herdr pane process-info --pane <PANE_ID>` | Inspects foreground and child OS process tree. |
| `split` | `herdr pane split --pane <PANE_ID> --direction <right\|down> --cwd <DIR> [--no-focus]` | Splits an existing pane horizontally or vertically. |
| `focus` | `herdr pane focus --pane <PANE_ID>` | Sets active cursor focus to target pane. |
| `resize` | `herdr pane resize --pane <PANE_ID> --direction <left\|right\|up\|down> --cells <N>` | Adjusts split boundary. |
| `zoom` | `herdr pane zoom --pane <PANE_ID>` | Toggles full-tab maximization of the pane. |
| `read` | `herdr pane read --pane <PANE_ID> [--source <visible\|recent\|recent-unwrapped>] [--lines <N>]` | Captures raw terminal screen buffer. |
| `send-keys` | `herdr pane send-keys --pane <PANE_ID> <KEYS...>` | Sends key events (`enter`, `esc`, `ctrl+c`, etc.). |
| `send-text` | `herdr pane send-text --pane <PANE_ID> "<TEXT>"` | Injects raw text into the PTY. |
| `run` | `herdr pane run <PANE_ID> "<CMD>"` | Injects text followed by Enter into the pane. |
| `wait-output` | `herdr pane wait-output --pane <PANE_ID> --pattern "<REGEX>" [--timeout <MS>]` | Blocks until matching terminal output appears. |
| `close` | `herdr pane close <PANE_ID>` | Terminates PTY session and destroys pane. |

---

## 5. Agent Primitives (`herdr agent`)

High-level AI cognitive agent control plane over terminal panes.

| Command | Syntax | Description |
|---|---|---|
| `start` | `herdr agent start "<LABEL>" --kind <agy\|codex\|claude> --pane <PANE_ID> -- [--model <M>]` | Launches an AI agent CLI in an existing pane. |
| `prompt` | `herdr agent prompt <TARGET_PANE> "<TEXT>"` | Submits a prompt using bracketed paste (DEC Mode 2004). |
| `wait` | `herdr agent wait <TARGET_PANE> [--until <idle\|done\|blocked>] [--timeout <MS>]` | Blocks until agent reaches requested lifecycle state. |
| `read` | `herdr agent read <TARGET_PANE> [--source <recent-unwrapped\|visible\|recent>] [--lines <N>]` | Reads formatted agent transcripts or modals. |
| `send-keys` | `herdr agent send-keys <TARGET_PANE> <KEYS...>` | Sends keyboard navigation to interactive menus/modals. |
| `list` | `herdr agent list` | Lists all detected agents and their current status. |
| `get` | `herdr agent get <TARGET_PANE>` | Inspects agent session ID, model, and turns. |
| `explain` | `herdr agent explain <TARGET_PANE>` | Explains heuristic detection state and rules. |

---

## 6. Notification Primitives (`herdr notification`)

Post desktop / TUI toast notifications to inform the human user of agent milestones.

| Command | Syntax | Description |
|---|---|---|
| `show` | `herdr notification show "<TITLE>" [--body "<TEXT>"] [--sound <none\|done\|request>] [--position <POS>]` | Displays a visual banner in Herdr with optional audio alert. |

### Recipe: Alert on PR Approval
```bash
herdr notification show "Candidate Approved" \
  --body "Issue #${TASK_ID} passed all reviews and is queued for merge." \
  --sound done
```
