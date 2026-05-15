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

- Worktree at `../<repo>-wt-<mode>-<slug>` (sibling of the repo). The `<mode>`
  segment is folded in so two modes targeting the same slug don't collide.
- Symlinks (relative paths so a moved `<repo-parent>/` tree keeps working):
  - `node_modules` (when `LINK_NODE_MODULES=1`, the default, AND the source has `node_modules/`)
  - one env file named by `LINK_ENV_FILE` (default `.env.local`; set
    `LINK_ENV_FILE=` to skip; alternate names like `.env.development` are
    enabled by passing `LINK_ENV_FILE=.env.development`)
- Codegen: `npx --no-install prisma generate` when `prisma/schema.prisma`
  exists in the source AND `package.json` exists in the worktree (auto-detected
  unless `PRISMA_GENERATE` is set explicitly).
- Final stdout breadcrumb `WORKTREE_PATH=<abs path>` (consumed by run-fleet /
  run-review to capture the resolved path).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Worktree ready (or reused with `ALLOW_REUSE=1`) |
| 1 | Not a git repo OR worktree already exists with `ALLOW_REUSE=0` |
| 2 | Base branch unknown (not in local refs or `origin/`) |
| 3 | `git worktree add` failed |

## Behavior

- Refuses to create the worktree inside the source repo (would pollute `git status`).
- Symlinks are relative paths (`../<source>/node_modules`) so moving the entire `<repo-parent>/` tree doesn't break links.
- Codegen errors don't roll back the worktree — they surface for the user to inspect.

## Notes

The runner (`run-fleet.sh`, `run-review.sh`) calls this before every entry's first attempt. On retry (rescue), `ALLOW_REUSE=1` is set so the same worktree is reused.

If a worktree exists but is corrupt (dangling `.git/` link), `git worktree remove --force <path>` first, then re-run setup.
