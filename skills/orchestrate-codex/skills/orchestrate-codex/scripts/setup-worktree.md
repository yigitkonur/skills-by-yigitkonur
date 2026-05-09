# setup-worktree.sh

Creates a git worktree, links shared artifacts, runs codegen.

## Inputs

```bash
bash setup-worktree.sh <slug> <branch> [<base>]
```

| Arg | Required | Notes |
|---|---|---|
| `<slug>` | yes | The mode-prefixed slug (`exec-search-rewrite`, `review-feat-auth`, `single-bigref`). Forms the worktree path. |
| `<branch>` | yes | The branch the worktree checks out. Created from `<base>` if missing. |
| `<base>` | no | Defaults to `main`. The branch off which `<branch>` is created if it doesn't exist. |

| Env | Default | Effect |
|---|---|---|
| `ALLOW_REUSE` | `0` | Set to `1` to re-run setup against an existing worktree (idempotent). |

## Outputs

- Worktree at `../<repo>-wt-<slug>`.
- Symlinks: `node_modules`, `.env.local`, `.env.development` (if present in source).
- Codegen run: `npx prisma generate` if `prisma/schema.prisma` exists; `pnpm run generate:openapi` if `openapi.yaml` + `package.json` script present; `buf generate` if `proto/` + `buf.yaml`.
- Marker file `.worktree-setup-complete` in worktree root for re-run detection.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Worktree ready |
| 1 | Not a git repo |
| 2 | Worktree already exists AND `ALLOW_REUSE=0` |
| 3 | Codegen failed (worktree exists; user investigates) |

## Behavior

- Refuses to create the worktree inside the source repo (would pollute `git status`).
- Symlinks are relative paths (`../<source>/node_modules`) so moving the entire `<repo-parent>/` tree doesn't break links.
- Codegen errors don't roll back the worktree — they surface for the user to inspect.

## Notes

The runner (`run-fleet.sh`, `run-review.sh`) calls this before every entry's first attempt. On retry (rescue), `ALLOW_REUSE=1` is set so the same worktree is reused.

If a worktree exists but is corrupt (dangling `.git/` link), `git worktree remove --force <path>` first, then re-run setup.
