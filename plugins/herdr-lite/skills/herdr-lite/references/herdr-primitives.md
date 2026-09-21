# Herdr CLI Primitives & Command Reference

This reference is the canonical cheat-sheet for Herdr's socket API CLI primitives. It documents every core object, command syntax, JSON output structures, and `jq` coordinate extraction recipes.

All commands output structured JSON natively when called non-interactively. Do not pass `--json`.

---

## 1. Worktree Primitives (`herdr worktree`)

Manage Git worktrees paired with dedicated Herdr workspaces.

| Command | Syntax | Description |
|---|---|---|
| `create` | `herdr worktree create --cwd <REPO> --path <PATH> --branch <BRANCH> --label <LABEL> [--no-focus]` | Creates a Git worktree, provisions an isolated Herdr workspace, and launches a root pane in Tab 1 directly inside the worktree checkout. |
| `list` | `herdr worktree list` | Lists all active worktree-backed workspaces. |
| `open` | `herdr worktree open <PATH>` | Re-opens an existing worktree checkout in a workspace. |
| `remove` | `herdr worktree remove --workspace <WS_ID> [--force]` | Safely unbinds and removes a worktree checkout and workspace. Runs `git worktree remove` under the hood (never deletes local branch). |

### Recipe: Create Dedicated Worktree Workspace & Side-by-Side Review Pane
```bash
# 1. Provision dedicated worktree workspace (never use loose tabs with git worktree add!):
WORKTREE_JSON="$(herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --label "task-${TASK_ID}" --no-focus)"

# Extract Workspace ID and initial Root Pane ID:
WS_ID="$(echo "$WORKTREE_JSON" | jq -er .result.workspace.workspace_id)"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.pane_id)"

# 2. Launch implementer agent in Pane 1:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" --timeout 45000 -- --model "$IMPL_MODEL" --dangerously-skip-permissions

# 3. When worker reports DONE, split pane side-by-side in SAME tab:
SPLIT_JSON="$(herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus)"
REV_PANE_ID="$(echo "$SPLIT_JSON" | jq -er .result.pane.pane_id)"

# 4. Launch reviewer agent in Pane 2 (implementer pane remains ALIVE and readable):
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" --timeout 45000 -- --model "gemini-3.8-flash-high" --dangerously-skip-permissions

# 5. Full-Job Teardown: ONLY once PR is confirmed MERGED to main:
gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED" || { echo "PR not merged; aborting teardown"; exit 1; }
test -z "$(git -C "$WORKTREE_PATH" status --porcelain)" || { echo "Worktree dirty; aborting teardown"; exit 1; }
herdr pane close "$REV_PANE_ID" 2>/dev/null || true
herdr pane close "$IMPL_PANE_ID" 2>/dev/null || true
herdr worktree remove --workspace "$WS_ID" || { echo "Worktree removal failed; aborting teardown"; exit 1; }
git -C "$REPO_ROOT" branch -D "$BRANCH"
git -C "$REPO_ROOT" remote prune origin

# 6. Post-Milestone Retirement: When all issues/PRs are resolved, retire EM pane:
herdr pane close "$EM_PANE_ID"
```

---

## 2. Workspace Primitives (`herdr workspace`)

Workspaces are the top-level grouping containers in Herdr (analogous to multi-window workspaces).

| Command | Syntax | Description |
|---|---|---|
| `list` | `herdr workspace list` | Lists all workspaces with active tab counts. |
| `get` | `herdr workspace get <WS_ID>` | Inspects workspace details, tabs, and layout. |
| `focus` | `herdr workspace focus <WS_ID>` | Switches active TUI view to the target workspace. |
| `rename` | `herdr workspace rename <WS_ID> <LABEL>` | Sets human-readable workspace title. |
| `report-metadata` | `herdr workspace report-metadata --source <ID> <WS_ID> --token <KEY=VAL>` | Sets badge tokens or visual status in TUI sidebar. |
| `close` | `herdr workspace close <WS_ID>` | Closes the workspace and all contained tabs. |

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

### Recipe: Side-by-Side Review Pane Split in Worktree Workspace
```bash
# When worker reports DONE, split pane side-by-side (direction: right) in SAME tab:
SPLIT_JSON="$(herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus)"
REV_PANE_ID="$(echo "$SPLIT_JSON" | jq -er .result.pane.pane_id)"

# Launch reviewer agent in Pane 2 (implementer pane remains ALIVE and readable):
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" --timeout 45000 -- --model "gemini-3.8-flash-high" --dangerously-skip-permissions
```

---

## 4. Pane Primitives (`herdr pane`)

Terminal PTY execution surfaces.

| Command | Syntax | Description |
|---|---|---|
| `current` | `herdr pane current` | Returns caller's live coordinates (`pane_id`, `tab_id`, `workspace_id`, `cwd`). |
| `list` | `herdr pane list` | Returns JSON array of all active terminal panes. |
| `get` | `herdr pane get <PANE_ID>` | Inspects pane details, session metadata, scrollback. |
| `layout` | `herdr pane layout [--pane <PANE_ID>]` | Shows tree layout coordinates ($x, y, w, h$). |
| `process-info` | `herdr pane process-info [--pane <PANE_ID>]` | Inspects foreground and child OS process tree. |
| `split` | `herdr pane split --pane <PANE_ID> --direction <right\|down> --cwd <DIR> [--no-focus]` | Splits an existing pane horizontally or vertically. |
| `focus` | `herdr pane focus --direction <left\|right\|up\|down> [--pane <PANE_ID>]` | Sets active cursor focus to target pane. |
| `resize` | `herdr pane resize --pane <PANE_ID> --direction <left\|right\|up\|down> --cells <N>` | Adjusts split boundary. |
| `zoom` | `herdr pane zoom --pane <PANE_ID>` | Toggles full-tab maximization of the pane. |
| `read` | `herdr pane read <PANE_ID> [--source <visible\|recent\|recent-unwrapped>] [--lines <N>]` | Captures raw terminal screen buffer. |
| `send-keys` | `herdr pane send-keys <PANE_ID> <KEYS...>` | Sends key events (`enter`, `esc`, `ctrl+c`, etc.). |
| `send-text` | `herdr pane send-text <PANE_ID> "<TEXT>"` | Injects raw text into the PTY. |
| `run` | `herdr pane run <PANE_ID> "<CMD>"` | Injects text followed by Enter into the pane. |
| `wait-output` | `herdr pane wait-output <--match <TEXT>\|--regex <PATTERN>> <PANE_ID> [--timeout <MS>]` | Blocks until matching terminal output appears. |
| `close` | `herdr pane close <PANE_ID>` | Terminates PTY session and destroys pane. |

---

## 5. Agent Primitives (`herdr agent`)

High-level AI cognitive agent control plane over terminal panes.

| Command | Syntax | Description |
|---|---|---|
| `start` | `herdr agent start "<LABEL>" --kind <agy\|codex\|claude> --pane <PANE_ID> [--timeout <MS>] -- [--model <M>] [--dangerously-skip-permissions]` | Launches an AI agent CLI in an existing pane with auto-approved permissions. |
| `prompt` | `herdr agent prompt <TARGET_PANE> "<TEXT>"` | Submits a prompt using bracketed paste (DEC Mode 2004). |
| `wait` | `herdr agent wait <TARGET_PANE> [--until <idle\|done\|blocked\|working\|unknown>] [--timeout <MS>]` | Blocks until agent reaches requested lifecycle state. Without `--until`, defaults to matching `idle`, `done`, or `blocked`. Repeat `--until` for multiple states (e.g. `--until done --until idle`). |
| `read` | `herdr agent read <TARGET_PANE> [--source <recent-unwrapped\|visible\|recent>] [--lines <N>]` | Reads formatted agent transcripts or modals. |
| `send-keys` | `herdr agent send-keys <TARGET_PANE> <KEYS...>` | Sends keyboard navigation to interactive menus/modals. |
| `list` | `herdr agent list` | Lists all detected agents and their current status. |
| `get` | `herdr agent get <TARGET_PANE>` | Inspects agent session ID, model, and turns. |
| `explain` | `herdr agent explain <TARGET_PANE>` | Explains heuristic detection state and rules. |

### Recipe: CTO Active Supervision of the Engineering Manager (EM)
```bash
# 1. Deterministically wait for EM to complete generation or tool execution:
herdr agent wait "$EM_PANE_ID" --until idle --timeout 60000

# 2. Inspect EM's live terminal buffer to check lane dispatches, reviewer splits, and blockers:
herdr pane read "$EM_PANE_ID" --lines 100

# 3. Interrogate the EM if silent, stalled, or at a wave boundary:
herdr agent prompt "$EM_PANE_ID" "CTO STATUS INTERROGATION:
1. What is the status of active lanes?
2. Are any PRs waiting for serial merge?
3. What are the blockers or failed checks?
4. What is the DAG and plan for the next wave?"
```

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
