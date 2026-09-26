# Topology, Worktrees & Geometry Rules

Organize terminal execution surfaces using Herdr's native topology primitives. Selecting the correct boundary prevents workspace sprawl, resource collisions, and unreadable layouts.

---

## 1. The Four-Tier Topology Hierarchy

Match the primitive to the actual scope and isolation requirements:

```
[ Isolation Need ]                   [ Recommended Primitive ]
Same issue / paired review  ──────►  Sibling pane in current tab (herdr pane split)
Independent read-only topic ──────►  Tab in current workspace (herdr tab create)
Dirty / concurrent writes   ──────►  Native Git worktree workspace (herdr worktree create)
Independent repository      ──────►  New workspace (herdr workspace create)
```

1. **Sibling Pane in Same Tab**:
   - **When to use**: Closely coupled execution (e.g. an implementer and its paired side-by-side reviewer, or a dev server running beside a test runner).
   - **Command**: `herdr pane split --pane "$TARGET_PANE" --direction <right|down> --cwd "$PWD" --no-focus`
   - **Benefit**: Both panes remain visible simultaneously in the same viewport, enabling live observation without switching tabs.
2. **Tab in Existing Workspace**:
   - **When to use**: Independent read-only topic, background monitoring, or inspection within the same repository that does NOT mutate files concurrently.
   - **Command**: `herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$PWD" --label "<NAME>" --no-focus`
   - **Benefit**: Keeps tabs grouped within the same project workspace without sprawling across windows.
3. **Native Worktree Workspace**:
   - **When to use**: Any task requiring dirty or concurrent write isolation in the same repository.
   - **Command**:
     ```bash
     herdr worktree create \
       --cwd "$REPO_ROOT" \
       --path "$WORKTREE_PATH" \
       --branch "$BRANCH_NAME" \
       --base "$BASE_REF" \
       --label "task-${TASK_ID}" \
       --no-focus
     ```
   - **Benefit**: Creates the isolated Git worktree checkout, provisions a dedicated Herdr workspace bound to it, and starts Pane 1 directly inside the directory in one atomic operation.
4. **Independent Dedicated Workspace**:
   - **When to use**: Only when working on a genuinely separate repository or detached external service.
   - **Command**: `herdr workspace create --label "<REPO_NAME>"`

---

## 2. Geometry & The Unreadable Pane Trap

Splitting terminal panes without checking dimensions destroys readability. During planning, a manager pane was observed compressed to only 12 columns wide due to repeated right splits.

### Geometry Decision Rules:
1. **Inspect Dimensions First**:
   ```bash
   herdr pane layout --pane "$HERDR_PANE_ID"
   ```
2. **Split Direction Rules**:
   - If the target pane is **wide** ($\ge 120$ columns): split `--direction right`.
   - If the target pane is **narrow** ($< 120$ columns) or **tall**: split `--direction down`.
   - **Never execute repeated same-direction splits** that reduce a pane below 80 columns or 20 rows.
3. **Preserve User Focus**:
   - Always pass `--no-focus` when provisioning panes, tabs, or worktrees for background agents. Never steal active user focus unless explicitly requested.

---

## 3. Dynamic Coordinates & Caller Context

Herdr injects physical coordinate handles into each managed pane's environment:
- `$HERDR_WORKSPACE_ID`: e.g. `w1`
- `$HERDR_TAB_ID`: e.g. `w1:t1`
- `$HERDR_PANE_ID`: e.g. `w1:p1`

### Discovery Invariants:
1. **Live vs. Static Coordinates**: Environment variables reflect coordinates at process startup. If a pane is moved across tabs or workspaces, environment variables become stale. **Always query live coordinates**:
   ```bash
   herdr pane current
   ```
2. **Targeting Own Pane**: Prefer `--current` for operations affecting the executing pane:
   ```bash
   herdr pane layout --current
   ```
3. **No UI-Focus Assumptions**: A bare command without `--pane` or `--current` may default to the UI-focused pane, which might belong to the human user or another client. Always specify target IDs explicitly.
4. **Opaque Handles**: Treat all IDs as opaque strings. Do not invent suffixes or assume numeric sequences.

---

## 4. Worktree Lifecycle & Teardown Distinctions

Herdr provides dedicated worktree primitives over the socket API:

| Task | Command | Mechanics |
|---|---|---|
| **Create** | `herdr worktree create` | Atomic Git worktree checkout + dedicated Herdr workspace. |
| **Open** | `herdr worktree open` | Attaches an existing worktree checkout as a Herdr workspace. |
| **List** | `herdr worktree list` | Enumerates all active worktree-backed workspaces. |
| **Remove** | `herdr worktree remove --workspace <WS_ID>` | Unlinks worktree checkout from disk and closes Herdr workspace. |

### Critical Worktree Invariants:
- **`workspace close` vs `worktree remove`**:
  - `herdr workspace close <WS_ID>` closes **ONLY** the Herdr UI workspace and pane processes. It leaves the Git worktree directory on disk and Git tracking orphaned!
  - `herdr worktree remove --workspace <WS_ID>` removes the physical directory from disk, unregisters Git worktree tracking, and closes the workspace.
- **Refusal on Dirty Tree**:
  - `herdr worktree remove` automatically refuses if uncommitted changes or untracked files exist. Never pass `--force` without verifying changes are safely disposable.
- **Local Branch Preservation**:
  - Removing a worktree checkout does NOT delete its local Git branch. Local branch deletion is a separate step that must occur after worktree removal.
