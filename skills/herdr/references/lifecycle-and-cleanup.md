# Lifecycle and cleanup

Read when retiring a finished job or removing its checkout. This is the single
cleanup contract for both modes. Pane closure, checkout removal and branch
removal are separate decisions; a blocked deletion never keeps a finished TUI
alive just to wait for a PR merge.

## 1. Close finished owned panes promptly

Before closure:

1. Read the handback and actual evidence; record result, failures and file paths.
2. Confirm no unresolved terminal operation or child process needs the pane.
3. Resolve ownership: keep an author with assigned review fixes, or explicitly
   reassign those fixes and preserve the handoff before closing the author.
4. Preserve required session/result evidence outside the disposable terminal.
5. Verify the pane belongs to this task and is finished, then close by ID:

```bash
herdr pane close "$PANE_ID"
```

The command uses a positional ID, not `--pane`. Do not close root, a live EM,
an unrelated pane, or a task awaiting input/fixes. Finished pane closure does not
require a clean Git tree, approved PR or merge. Dirty work remains on disk.

## 2. Preserve or remove the worktree

Default to preserving unmerged/undelivered/dirty work. If removal is authorized,
verify the exact owned worktree and all these gates:

- Tracked, staged and untracked files are clean, or every needed artifact has
  been explicitly preserved in a verified durable location.
- Ignored outputs have been inspected too; ordinary `git status` omits them.
- Candidate delivery/merge or an explicit preservation plan is verified; do not
  infer safety from a PR being open or a pane being closed.
- No agent, dev server, test or other process still uses the checkout.
- Session/result/check artifacts needed later are outside the removed directory.

Discover current `herdr worktree remove --help`. On the inspected CLI, removal
uses the owned worktree workspace ID, not a checkout path:

```bash
herdr worktree remove --workspace "$WORKTREE_WORKSPACE_ID"
```

Never pass `--force`. A refusal means retain and report the reason. Reconcile
returned state and actual files; do not run an extra Git removal blindly.
A workspace close may retain or remove its attached worktree according to build
behavior; do not use it as a deletion shortcut without verifying its semantics.

## 3. Remove a delivered branch only when safe

If authorized, remove only this task's branch using safe `git branch -d` from a
checkout where that branch is not active. If Git refuses, preserve the branch
and explain. Never fall back to `-D`, global remote pruning, host-wide worktree
pruning, or a goal of leaving only one worktree. Remote branch deletion requires
its own authorized delivery context.

## Handoff and abandonment

On a crash, quota limit or pause, preserve dirty files and candidate identity;
report remaining processes and pending delivery. A manager replacement adopts
registered sessions before dispatch. Never erase evidence to make status green.
Finish by naming retained work and why it remains, rather than “all cleaned” when
only panes were retired.
