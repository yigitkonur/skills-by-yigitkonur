# Worktree Patterns

Git worktrees are the isolation primitive that makes parallel Codex dispatch safe. One worktree per agent = one branch per agent = one commit stream per agent = predictable merges.

## Naming convention

Use `<wave>-<feature>` for the worktree directory and `<wave>/<feature>` for the branch. Example:

```
.worktrees/
├── wave1-reports/          (branch: wave1/reports-scheduled-pipeline)
├── wave2-nav/              (branch: wave2/nav-project-switcher)
├── wave2-rank/             (branch: wave2/rank-head-to-head)
└── wave3-citations/        (branch: wave3/citations-network-viz)
```

Why: `ls .worktrees/` tells you what's in flight at a glance. `git worktree list` shows full paths + branches.

## Always .gitignore the worktree directory

```
# .gitignore
.worktrees/
worktrees/
```

Without this, the parent repo's `git status` shows every file in every worktree as untracked. Noisy beyond belief and a real risk of committing worktree internals into main by accident.

## Also exclude worktree from build tool configs

The worktree directory lives inside the repo, so build tools discover it. Exclude in:

**tsconfig.json**
```json
{ "exclude": ["node_modules", ".worktrees/**"] }
```

**vitest.config.ts**
```ts
test: { exclude: ["**/node_modules/**", "**/.worktrees/**"] }
```

**eslint.config.mjs** (flat config)
```js
globalIgnores([".next/**", ".worktrees/**", "src/generated/**"])
```

Without these, running verification commands in main picks up broken/in-flight code from sibling worktrees. I have watched vitest accidentally run 2340 tests (baseline was 184) because it descended into 12 worktrees; 104 failed because sibling branches had bad in-flight state.

## Symlinking shared artifacts

`node_modules` is ~1-2 GB. Copying it to every worktree wastes disk and time. Symlink from parent:

```bash
cd .worktrees/<name>
ln -s ../../node_modules node_modules
ln -s ../../.env.local .env.local
```

`setup-worktree.sh` does both automatically.

**Caveat:** when an agent runs `npm install` inside its worktree, it writes to the shared node_modules. Only one agent can safely run `npm install` at a time. If two agents both need to add packages, serialize those commands.

## Per-worktree codegen

Prisma and other codegen tools write to a path inside the repo. The generated client has different content per branch if the schemas differ. You need to regenerate per worktree:

```bash
cd .worktrees/<name>
npx prisma generate
```

`setup-worktree.sh` runs this on creation. You'll need to re-run it if the branch changes (e.g., after `git reset --hard main`).

## Reset a worktree to current main

Useful when an agent bailed and you want to restart from the latest state:

```bash
cd .worktrees/<name>
git reset --hard main         # moves branch to main HEAD, discards any dirty
git clean -fd                 # removes untracked files the agent may have left
npx prisma generate           # regen codegen for the new schema
```

Then re-dispatch via `codex-wrapper.sh`.

## Remove a worktree

If a plan turned out to be unnecessary, or you want to recreate from scratch:

```bash
# In main workspace
git worktree remove .worktrees/<name> --force
git branch -D <branch-name>            # optional — if you don't want the branch either
```

`--force` is needed if the worktree has uncommitted changes.

## List worktrees + status

```bash
git worktree list                      # show all worktrees + their branch + commit
```

For a detailed cross-worktree audit:

```bash
for wt in .worktrees/*/; do
  name=$(basename "$wt")
  (cd "$wt" && echo "[$name] commits=$(git rev-list --count main..HEAD) dirty=$(git status --porcelain | wc -l | tr -d ' ')")
done
```

## Merge strategies

### Happy path: fast-forward impossible, merge commit created
```bash
git merge --no-ff <branch> -m "merge: ship <branch>"
```

### With known trivial conflicts (todo.md, changelogs)
```bash
git merge --no-ff -X ours <branch> -m "merge: ship <branch> (todo.md kept as ours)"
```

`-X ours` resolves auto-resolvable text conflicts by preferring main's version. Substantive file conflicts still require manual resolution.

### When a conflict needs careful handling (schema, shared lib file)

```bash
git merge --no-ff <branch>
# conflict detected
grep -n "<<<<<<<" <conflict-files>
# edit each conflict file to union the changes
git add <files>
git commit --no-edit
```

For prisma/schema.prisma specifically, almost every multi-plan merge needs a manual union because agents tend to add fields to the same model. Set expectations.

## When NOT to use worktrees

- **Tiny changes** (1-5 files, <100 lines). Just `codex exec` in the main workspace and commit manually.
- **Tasks that fundamentally touch shared config** (all plans edit the same file). Parallelism doesn't help; the merge cost dominates. Serialize.
- **Tasks that need interactive input** (Codex might pause for user clarification). `codex exec` is non-interactive by design, but if the plan is ambiguous, it'll bail.

## Cheap cleanup at session end

Worktrees with symlinked node_modules cost ~50 MB on disk (source + generated). You can keep them around across sessions — they're free. Delete only if you're rewriting or the branches are dead:

```bash
# Delete everything
for wt in .worktrees/*/; do
  git worktree remove "$wt" --force
done
git worktree prune
```
