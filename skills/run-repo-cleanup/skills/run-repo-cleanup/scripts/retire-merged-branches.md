# retire-merged-branches.py

Deletes local + remote branches that are fully merged to `<base>`. **Dry-run by default.** Requires `--execute` to actually delete. Refuses to touch `main`, `master`, `default`, the currently checked-out branch, or any branch not merged into `<base>`.

## Usage

```bash
# Always dry-run first
python3 scripts/retire-merged-branches.py --base main

# Delete for real
python3 scripts/retire-merged-branches.py --base main --execute

# Only local (don't touch remote)
python3 scripts/retire-merged-branches.py --base main --local-only --execute

# Only remote (don't touch local)
python3 scripts/retire-merged-branches.py --base main --remote-only --execute
```

## Behavior

Reads from git + remote, decides, prints every action it would take (or did take). Each action line is tagged `[DRY] ` or `[DO]  ` so post-hoc auditing is trivial.

1. **Local branches:** `git branch --merged <base>` → filter out protected + current → `git branch -d <branch>`.
2. **Remote branches:** `git branch -r --merged <remote>/<base>` → filter out protected → `git push <remote> --delete <branch>`.

The underlying `git branch -d` uses a safe delete (refuses if not fully merged). Combined with the script's own protection list, the risk of data loss is minimal but **not zero** — a branch that's merged to `<base>` but whose commits exist nowhere else is a contradiction that shouldn't happen under normal workflows.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--base <ref>` | `main` | Branch to check merged-status against. |
| `--remote <name>` | `origin` | Remote name (only the fork, per fork-safety policy). |
| `--execute` | off (dry-run) | Actually perform deletions. |
| `--local-only` | off | Only retire local branches. |
| `--remote-only` | off | Only retire remote branches. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Nothing to retire, OR execute completed cleanly. |
| 1 | Dry-run with actionable branches present (stay in loop). |
| 2 | `--execute` mode with at least one deletion failure, OR not a git repo. |
| 3 | Refused due to safety check (protected branch, etc.). |

## Protections

Cannot delete (hard-coded):

- Any branch whose short name is `main`, `master`, `default`, or `HEAD`.
- The currently checked-out branch (via `git branch -d`'s own refusal).
- Any branch that isn't fully merged to `<base>` (via `git branch --merged`).

There is deliberately no `--force` flag. If you need to delete an un-merged branch, do it manually with `git branch -D` after reading the diff.

## When to run

- **Phase 5**, after the last PR of a session has merged and `git fetch --prune` is done.
- **Session start / end** as a tidy check if you suspect old merged branches are lingering.

Run the dry-run **first**, every time. Look at the list. Execute only when the list is what you expect.

## Safety

`--execute` mutates local AND remote state. The `--remote` flag defaults to `origin` (the private fork per the skill's fork-safety policy). Never set `--remote upstream`.

Before running with `--execute`, consider:
- Have you pulled latest from `--base`? Otherwise, branches that merged very recently may not show up as merged.
- Have you run `git fetch --prune`? Otherwise, deleted-on-remote branches may still appear locally.
- Do you have un-pushed work on any of the branches about to be deleted? (shouldn't happen after merge, but audit with `git log <branch>..HEAD --oneline` if unsure.)

## Sample output

```
base branch:    main
remote:         origin
current branch: main
mode:           DRY-RUN (no changes)

2 local branch(es) merged to main:
  [DRY] delete local: git branch -d feat/old-work
  [DRY] delete local: git branch -d docs/old-docs

1 remote branch(es) merged to origin/main:
  [DRY] delete remote: git push origin --delete feat/old-work

DRY-RUN complete. Re-run with --execute to actually retire.
```

## Recovery

If you accidentally delete a local branch, the commits are still in the reflog for ~90 days:

```bash
git reflog                     # find the SHA of the last commit on the deleted branch
git branch <name> <SHA>        # recreate
```

If you delete a remote branch and need it back, you can re-push from a local copy (if you still have one) or recreate from the SHA:

```bash
git push origin <local-branch>:<remote-branch>
```

## Extending

- Add `--days-merged <N>` to only retire branches merged more than N days ago (useful when you want a grace period).
- Add `--prefix <string>` to restrict to branches starting with a prefix.
