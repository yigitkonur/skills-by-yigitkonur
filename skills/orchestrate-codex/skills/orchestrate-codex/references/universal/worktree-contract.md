# Worktree contract

Worktrees isolate per-task work. The skill creates them, names them, populates them with shared artifacts, and removes them on success — all gated, all reproducible.

## Naming

```
<repo-parent>/<repo-basename>-wt-<mode>-<slug>
```

Examples:
- `~/dev/myrepo-wt-exec-search-rewrite`
- `~/dev/myrepo-wt-review-feat-auth`
- `~/dev/myrepo-wt-single-bigref`

The `<mode>` token in the path makes provenance obvious in `git worktree list`. A future user (or audit script) sees `myrepo-wt-exec-search-rewrite` and knows immediately which orchestrate-codex run produced it.

The `<slug>` is the `entries[i].slug` from the manifest. The mapping is 1-to-1: one slug → one worktree path. If the worktree path is gone but the manifest entry still references it, rescue prunes (`git worktree prune`) and recreates.

### Slug disambiguation across tracks

Ids must be globally unique within a single `tasks.json`. The dispatcher's `buildExecEntries` (`scripts/orchestrate-codex.mjs:530`) refuses the run with `duplicate id: <id>` if two entries share an id. This bites when the operator's natural slug is the package name and multiple upgrade tracks touch the same package — e.g. one fleet that bumps `react` in `web/` and another that bumps `eslint` in `web/`, both naturally slugged `web`.

Fix by track-prefixing the id (and therefore the worktree path):

- `react-web`, `eslint-web` — two distinct ids, two distinct worktrees, both modifying files inside the `web/` package on different branches.
- The branch can keep the operator's preferred name (`bump/react/web`, `bump/eslint/web`) — `branch` and `id` are independent fields.

Same-package work across tracks ⇒ different ids ⇒ different worktrees. The 1-to-1 mapping (one slug → one worktree path) is preserved because the slug carries the track prefix.

`<repo-parent>` is `dirname(workspace_root)`. `<repo-basename>` is `basename(workspace_root)`. The skill never creates worktrees inside the source repo by default — in-repo placement (`.worktrees/`) pollutes `git status` and forces every consumer to update `.gitignore`. Set `WORKTREE_DIR_NAME=.worktrees` to opt in if isolation requirements demand it.

## `.gitignore` requirement

Even though worktrees live outside the source repo by default, the skill writes `.gitignore` that covers `<repo-basename>-wt-*` in case a worktree is accidentally created inside the repo (for example, a user runs the skill with the repo as a sibling of the worktree dir). Pre-flight checks `.gitignore` for this pattern and adds it if missing.

## Lifecycle

```
queued
   │ scripts/setup-worktree.sh <slug> <branch> <base>
   ▼
created       — worktree on disk; node_modules / .env.local symlinked; codegen run
   │ runner runs codex exec
   ▼
populated     — codex wrote files; possibly committed
   │ wrapper auto-commit (if codex didn't commit)
   ▼
committed     — at least one commit on the worktree's branch
   │ post-verify runs
   ▼
verified      — post-verify exit 0 (or skipped per language recipe)
   │ runner sets manifest.status = done
   ▼
done          — branch merge is operator-driven (skill never auto-merges)
   │ user merges branch into main externally
   ▼
merged        — branch on main; worktree eligible for cleanup
   │ scripts/cleanup-worktrees.py --execute --base main
   ▼
removed       — worktree gone; manifest entry preserved (terminal status)
```

State `failed` short-circuits the lifecycle: the worktree is preserved with a `.fleet-failure-<slug>.md` marker file in its root. The user inspects, decides whether to recover the work or remove. Cleanup refuses dirty/unmerged worktrees unless `--force-abandon <id>`.

## Symlinks and codegen

`setup-worktree.sh` populates each new worktree with shared artifacts the agent will need at runtime:

| Source path | Symlink to | When |
|---|---|---|
| `<source-repo>/node_modules` | `<worktree>/node_modules` | If `node_modules` exists in the source |
| `<source-repo>/.env.local` | `<worktree>/.env.local` | If present (gitignored env) |
| `<source-repo>/.env.development` | `<worktree>/.env.development` | If present |

Symlinks are relative paths (e.g. `../<source-basename>/node_modules`) so moving the entire `<repo-parent>/` tree as a single unit doesn't break links. **Do not "fix" these to absolute paths** — absolute paths bind the worktree to its current filesystem location and break the moment the user moves their dev tree (a common operation when switching machines, reorganizing `~/dev`, or migrating across filesystems). Verified at `scripts/setup-worktree.sh` (B4 derailment).

Codegen runs after symlinks are in place:

| Repo signal | Command run |
|---|---|
| `prisma/schema.prisma` | `npx prisma generate` |
| `openapi.yaml` + `package.json` script `generate:openapi` | `pnpm run generate:openapi` |
| `proto/` + `buf.yaml` | `buf generate` |

Custom codegen: configure via `<source-repo>/.orchestrate-codex.yaml` (path TBD; not yet implemented; per-repo override mechanism deferred).

## Reuse rule

If `pwd` is already inside a worktree:
- For exec / batch / review modes — never reuse. Each entry needs isolation. The dispatcher creates fresh worktrees regardless of cwd.
- For single mode — the skill asks: "Reuse this worktree, or create a fresh `../<repo>-wt-single-<slug>`?" Reuse is right when the user has set up state they want to keep (deps installed, branch checked out, half-finished work). Fresh is right when isolation matters more.

If `--reuse-worktree` is passed explicitly to single mode, no question is asked — reuse happens.

A worktree is identified as such by `git rev-parse --show-toplevel` returning a path that includes `-wt-<mode>-` OR by the path being listed in `git worktree list` from a parent repo.

## Cleanup gate

`scripts/cleanup-worktrees.py --execute --base main` removes worktrees whose:
1. Manifest entry is `done` AND
2. Branch is merged into `<base>` (`git branch --merged <base>` includes it).

Refuses to remove:
- Dirty worktrees (`git status --short` non-empty) — unless `--force-abandon <id>` for that specific entry.
- Worktrees whose branches are not yet merged.
- Worktrees not registered in the manifest (these are someone else's; do not touch).

Default behavior is dry-run. `--execute` is the gate. `--force-abandon <id>` is per-entry and surfaces in the audit trail (history row records the abandon).

## Recovery from interrupted setup

If `setup-worktree.sh` is interrupted partway through (e.g. Ctrl-C during `prisma generate`):
1. The worktree may exist on disk but with stale codegen.
2. Re-running `setup-worktree.sh` with `ALLOW_REUSE=1` re-symlinks and re-runs codegen idempotently.
3. If the worktree is corrupt (e.g. `.git/` link is broken), `git worktree remove --force <path>` it and re-run setup.

The runner detects "worktree exists, manifest entry expects setup not yet done" via the `mode_state.worktree_setup_complete=true` flag the setup script writes. If the flag is missing, setup re-runs.

## Worktrees vs branches

- Branch names are user-owned. The skill records every branch it pushed to (`mode_state.branch`) but does not invent branch names without explicit input from `tasks.json` or `--branches`.
- Worktree names are skill-owned. The slug is part of the path; the user does not name worktrees.
- A branch can have at most one worktree at a time (git limitation). The skill respects this — never creates two worktrees off the same branch.

## Anti-patterns

- Creating worktrees inside the source repo (`<repo>/.worktrees/<slug>`). Pollutes `git status`, forces `.gitignore` updates, breaks `git submodule` workflows.
- Reusing a worktree for a new entry. Stale state contaminates the new run. Either remove and recreate, or use a fresh slug.
- Hand-creating a worktree with `git worktree add` outside the skill's tooling. The manifest doesn't know about it; cleanup won't manage it; rescue can't recover it.
- Removing a worktree via `git worktree remove` outside the skill's tooling. The manifest still references it; rescue thinks it should exist; subsequent runs may try to recreate.
- Symlinking `node_modules` to a relative path that escapes the worktree (`../<source>/node_modules`) — fine when source/worktree are siblings, breaks if the user moves the tree. The skill uses relative paths but only one level up.
- Hand-killing a `prisma generate` mid-codegen — leaves partial generated client; subsequent codex invocations fail with cryptic type errors. Re-run `setup-worktree.sh` with `ALLOW_REUSE=1` to recover.

## Forensics

After a failed run, useful commands:

```bash
# Which worktrees exist?
git -C <source-repo> worktree list

# What state are they in?
python3 <skill-root>/scripts/list-worktrees.py --json | jq '.'

# Which manifest entries reference them?
# IMPORTANT: audit-fleet-state.py defaults workspace_root to cwd. If you invoke
# from a directory that is NOT the workspace, orphan-worktree detection runs
# against the wrong tree. Either cd into the workspace first OR pass
# --workspace-root <path>. The canonical workspace_root is recorded inside the
# manifest's top-level metadata; cross-check before running the audit from
# elsewhere.
cd <workspace-root> && \
    python3 <skill-root>/scripts/audit-fleet-state.py --manifest <path> --json \
        | jq '.entries[] | {id, status, worktree_path}'

# Are any orphaned (worktree on disk, not in manifest)?
# audit-fleet-state.py emits these under .orphan_worktrees[]. Detection is
# verified working — a worktree that exists on disk under the contract path
# (`<repo-parent>/<repo-basename>-wt-*`) but has no matching manifest entry
# surfaces here (B10 derailment confirmed this for both exec and review modes).
python3 <skill-root>/scripts/audit-fleet-state.py \
    --workspace-root <workspace-root> --manifest <path> --json \
    | jq '.orphan_worktrees[]'
```
