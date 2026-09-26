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
   - **When to use**: Closely coupled execution (e.g. an implementer and its paired side-by-side reviewer, or a dev server running beside a test runner), provided terminal geometry permits readable splits.
   - **Command**: `herdr pane split --pane "$TARGET_PANE" --direction <right|down> --cwd "$PWD" --no-focus`
   - **Benefit**: Both panes remain visible simultaneously in the same viewport, enabling live observation without switching tabs.
2. **Tab in Existing Workspace**:
   - **When to use**: Independent read-only topic, background monitoring, review under constrained geometry, or inspection within the same repository that does NOT mutate files concurrently.
   - **Command**:
     ```bash
     # Extract workspace_id from caller envelope ({result: {pane: {workspace_id: ...}}}) with strict non-empty string guard
     WS_ID="$(herdr pane current --current | jq -er '.result.pane.workspace_id | select(type == "string" and length > 0)')" || {
       echo "ERROR: Failed to resolve valid caller workspace_id; aborting tab creation." >&2
       exit 1
     }
     herdr tab create --workspace "$WS_ID" --cwd "$PWD" --label "<NAME>" --no-focus
     ```
     *(Note: `--current` identifies the caller. To target another pane, use `herdr pane current --pane "$TARGET_PANE"`. Never create a tab without an explicitly verified, non-null workspace ID).*
   - **Benefit**: Keeps tabs grouped within the verified project workspace without sprawling across windows or creating unneeded disk checkouts.
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

## 2. Geometry & Projected Usable Dimensions

Splitting terminal panes without checking dimensions destroys readability. During planning, a manager pane was observed compressed to only 12 columns wide due to repeated right splits.

### Geometry Decision Rules & Projected Dimensions:
1. **Inspect Dimensions First**:
   ```bash
   herdr pane layout --current
   ```
2. **Projected Child Dimensions Calculation**:
   Terminal pane splits share physical space with border and separator lines (1 column or row):
   $$\text{Projected Child Width} = \left\lfloor \frac{\text{Parent Width} - 1}{2} \right\rfloor, \quad \text{Projected Child Height} = \left\lfloor \frac{\text{Parent Height} - 1}{2} \right\rfloor$$
   Each child pane must satisfy minimum usable dimensions ($\ge 80$ columns for readable code and diffs, $\ge 20$ rows for terminal context):
   - **Horizontal Split (`--direction right`)**:
     Permissible only when parent width satisfies $\ge 161$ columns ($2 \times 80 + 1$). Splitting a narrower parent divides columns in half, creating unreadable ~50–60-column viewports.
   - **Vertical Split (`--direction down`)**:
     Permissible when parent width $< 161$ columns but parent height satisfies $\ge 41$ lines ($2 \times 20 + 1$).
   - **Tab Fallback Under Constrained Geometry**:
     If *neither* orientation yields usable child dimensions ($\ge 80$ columns and $\ge 20$ rows), **do NOT split the pane further**. Open a dedicated review or tool tab instead:
     ```bash
     # Extract workspace_id from caller envelope ({result: {pane: {workspace_id: ...}}}) with strict non-empty string guard
     WS_ID="$(herdr pane current --current | jq -er '.result.pane.workspace_id | select(type == "string" and length > 0)')" || {
       echo "ERROR: Failed to resolve valid caller workspace_id; aborting tab creation." >&2
       exit 1
     }
     herdr tab create --workspace "$WS_ID" --cwd "$PWD" --label "review-${TASK_ID}" --no-focus
     ```
3. **Preserve User Focus**:
   - Always pass `--no-focus` when provisioning panes, tabs, or worktrees for background agents. Never steal active user focus unless explicitly requested.

---

## 3. Dynamic Coordinates & Caller Context

Herdr injects physical coordinate handles into each managed pane's environment at startup (`$HERDR_WORKSPACE_ID`, `$HERDR_TAB_ID`, `$HERDR_PANE_ID`).

### Discovery Invariants:
1. **Live vs. Static Coordinates**: Environment variables reflect coordinates at process launch and become stale if panes are moved or tabs reorganised. **Always query live coordinates with `--current`**:
   ```bash
   herdr pane current --current
   ```
2. **Targeting Own Pane**: Mandate `--current` for operations affecting the executing pane:
   ```bash
   herdr pane layout --current
   ```
3. **No UI-Focus Assumptions**: A bare command without `--pane` or `--current` may default to the UI-focused pane, which might belong to the human user or another client. Fail closed on stale context; always specify target IDs explicitly.
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
  - `herdr workspace close <WS_ID>` closes **ONLY** the Herdr UI workspace and pane processes. It leaves the Git worktree directory on disk and Git tracking intact. Retained linked checkouts can be completely intentional for ongoing, deferred, or dirty checkouts.
  - `herdr worktree remove --workspace <WS_ID>` unlinks the physical directory from disk, unregisters Git worktree tracking, and closes the workspace.
- **Ownership Verification & Disappearance Check**:
  - *Before* closing a tab or workspace: verify target identity, confirm ownership of all contained panes, and reconcile pending side effects.
  - *After* closing: verify that contained pane processes have cleanly disappeared. Never close a workspace containing unowned or user-active panes.
- **Refusal on Dirty Tree & No Force**:
  - `herdr worktree remove` automatically refuses if uncommitted changes or untracked files exist. In ordinary operation, `--force` is strictly prohibited; dirty or ambiguous checkouts are safely preserved with a recorded reason.
- **Local Branch Preservation**:
  - Removing a worktree checkout does NOT delete its local Git branch. Local branch deletion is a separate, safe engineering step that occurs strictly after worktree removal.

For complete 3-stage teardown gates and preservation rules, see [references/lifecycle-and-cleanup.md](lifecycle-and-cleanup.md).
