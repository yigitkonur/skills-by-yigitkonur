# Topology and worktrees

Read before provisioning. Verify caller and intended repository separately.
Root keeps its pane; ordinary jobs get visible task tabs in its workspace.
Native worktrees belong to the intended repository's own project group.

## Choose by ownership

| Work | Placement | Checkout |
|---|---|---|
| Independent read-only jobs | Separate tabs | Shared checkout allowed |
| One coupled change | One writer tab | Existing checkout or one isolated worktree |
| Concurrent writers in the same repository | One task tab per writer/worktree | Separate worktrees required |
| Related independent review | Split in that task's tab | Frozen candidate, read-only |
| Split cannot fit | Review tab in the same project group | Same frozen candidate |

Do not split a coupled change into arbitrary file lanes. Disjoint-looking files
can share generated outputs, lockfiles or contracts; isolate concurrent writes.
Read-only reviewers must not run checks that mutate the author's candidate;
use a separate snapshot/worktree if a check writes output.

## Create and register one surface

```bash
herdr tab create --workspace "$WORKSPACE_ID" --cwd "$CHECKOUT" --label "$JOB_LABEL" --no-focus
```

Parse returned JSON and record workspace, tab, pane and terminal IDs. Verify the
pane is a shell and its cwd is the intended checkout before agent start. Names
are unique labels, not a replacement for returned opaque IDs.

For concurrent writes use native Herdr worktrees:

```bash
herdr worktree create --workspace "$REPO_WORKSPACE_ID" --path "$WORKTREE_PATH" --branch "$BRANCH" --base "$BASE" --label "$JOB_LABEL" --no-focus
```

First inspect `herdr workspace get "$REPO_WORKSPACE_ID"` and compare its worktree
repository to the intended Git root. A pane's cwd does not establish workspace
repository identity. If no verified repository workspace exists, use the exact
inspected repository instead:

```bash
herdr worktree create --cwd "$REPO" --path "$WORKTREE_PATH" --branch "$BRANCH" --base "$BASE" --label "$JOB_LABEL" --no-focus
```

Choose **one** source selector: `--workspace` or `--cwd`, never both. On tested
0.9.1, the combined form was rejected as syntax; the cwd form also established
the repository's primary workspace when it was not open. Record all created
surfaces, including that primary workspace, for scoped cleanup. Use explicit
new path/branch and a verified base. Inspect `herdr worktree list` for the same
source and preserve returned workspace/repository membership. Child workspace
IDs differ from the root caller. Do not relabel or attach work to another
project. If creation partly succeeds, reconcile Git and Herdr before retrying.

## Pair the reviewer

Freeze a coherent candidate before dispatch. Query the actual task layout:

```bash
herdr pane layout --pane "$AUTHOR_PANE"
```

Use returned geometry and the installed build's actual split behavior. The live
0.9.1 right split succeeded and returned two 60-column panes; a hard-coded
80-column minimum would have incorrectly skipped it. Inspect the resulting
native UI for usability rather than assuming a universal minimum.

```bash
herdr pane split --pane "$AUTHOR_PANE" --direction right --cwd "$REVIEW_CHECKOUT" --no-focus
```

If geometry is insufficient or split fails for capacity, create a related review
tab in the same worktree/project group. Parse its IDs; do not repeatedly split.
The reviewer gets read-only authority and exact candidate identity. The author
stays paused from writes while reviewing its checkout. Any candidate change
invalidates approval and needs review of the resulting candidate/delta.

## Capacity and adoption

Measure active harnesses, quotas and machine load; include AGY internal teamwork
agents in the count. There is no fixed Simple cap or wave count. On insufficient
capacity, serialize or retire completed owned panes first.

An explicitly adopted session needs verified pane/process/session, cwd, role,
owned changes, pending message and live return route. Update its supervisor
route only after adoption; do not launch a duplicate worker or steal another
project's pane. Cleanup has its own independent gates.
