# Workflow Playbook

The canonical 4-step orchestration recipe, derived from a real session that shipped 17 feature plans via 4 waves of parallel Codex dispatch.

## Step 0 — One-time repo prep

Before you dispatch anything, make the repo safe for parallel worktrees:

1. Add the worktree directory (default `.worktrees/`) to `.gitignore` and commit.
2. Exclude the worktree path from your tsc / vitest / eslint configs. Example for `tsconfig.json`:
   ```json
   { "exclude": ["node_modules", ".next/dev/types/**/*.ts", ".worktrees/**"] }
   ```
   Same for `vitest.config.ts` (`test.exclude`) and `eslint.config.mjs` (`globalIgnores([".worktrees/**"])`).
3. Decide on a monitor root. `/tmp/codex-monitor/` is a good default. Everything logs there.
4. Copy the three scripts (`codex-monitor.sh`, `codex-wrapper.sh`, `setup-worktree.sh`) into the monitor root and `chmod +x` them.
5. Pin the baseline: `git rev-parse HEAD > /tmp/codex-monitor/baseline.sha`. The monitor rules compute deltas from this.

## Step 1 — Set up worktrees

One worktree per plan. Name them after the branch they'll own, so when you `git worktree list` it's obvious what each one is for.

```bash
./setup-worktree.sh wave1-reports wave1/reports-scheduled-pipeline
./setup-worktree.sh wave2-nav      wave2/nav-project-switcher
./setup-worktree.sh wave2-rank     wave2/rank-head-to-head
# ... etc
```

`setup-worktree.sh` does three things for you: creates the worktree, symlinks `node_modules` and `.env.local` from the parent (saves ~2GB per worktree), and regenerates the Prisma client if the project uses Prisma.

## Step 2 — Start the monitor (once)

One monitor instance, not one-per-agent. It watches the whole fleet.

In Claude Code, use the **Monitor tool** pointing at `codex-monitor.sh`. Each stdout line becomes a notification in the conversation. The monitor also fires native macOS notifications via `osascript` if available — you can ignore one or the other.

Outside Claude, just backgrounded `./codex-monitor.sh &` works.

## Step 3 — Dispatch agents

One wrapper per plan, backgrounded. The wrapper owns the agent's entire lifecycle: codex exec → auto-commit → post-verify.

```bash
./codex-wrapper.sh wave1-reports p1-reports "$(cat <<'PROMPT'
YOU ARE A CODING AGENT. SKIP ALL META-SKILLS. DO NOT READ SKILL FILES.
DO NOT WRITE PLANNING DOCS. DO NOT ASK QUESTIONS. BEGIN EDITING IMMEDIATELY.
THE TASK:

Implement <plan>. Read only /path/to/plan.md. Deliverables:
1. <schema changes>
2. <new actions>
3. <UI wiring>
4. <tests>

DoD: npx tsc --noEmit = 0, npx vitest run passing, ≥2 commits.
Work in cwd only. Do not push. Follow existing {success, error?, data?} return shape.
PROMPT
)" &
```

**Dispatch all the plans of a wave in the same shell command**, each with `&` so they run in parallel. Expect to see process counts jump to `codex:N/wrap:M` where N = 2 × M (each wrapper spawns 2 codex procs).

## Step 4 — Watch the monitor, merge as work lands

The monitor fires every 60 seconds. Flags to act on:

- `silent-edit` — agent started writing. No action.
- `agent-done-committed` — **pay attention.** Run `cd .worktrees/<name> && git log main..HEAD` to see what landed, then merge.
- `streak:5x+` with no silent-edit — agent is stuck. Check its log (`/tmp/codex-monitor/logs/<name>.log`). Usually ruminating on plan reading or hit a 503.
- `main-dirty:N` — you or a tool accidentally wrote to main. Stop and investigate.

As each agent's work looks good:

```bash
# From main workspace (NOT inside a worktree)
cd /path/to/repo
git merge --no-ff -X ours wave1/reports-scheduled-pipeline \
  -m "merge: ship wave1/reports-scheduled-pipeline"
```

`-X ours` resolves trivial document-level conflicts (everyone edits `todo.md`) by keeping main's copy. Substantive file conflicts still stop and demand manual resolution.

### Post-merge verification

After each merge:

```bash
npx prisma generate   # if schema changed
npx tsc --noEmit      # must return 0
npx vitest run        # must pass
```

If tsc or tests fail, commit a `fix(post-merge): ...` to main before proceeding to the next merge. Don't let broken commits chain.

## Common failure modes

- **Agent bailed with no commits.** The wrapper log shows `[wrapper] no changes`. Check the raw codex log in the same file for `503 Service Unavailable` (Codex backend rate limit, resets in ~13 min) or the agent ruminating on superpowers skills without writing anything.
- **Agent committed but tsc fails.** Normal. Codex rarely gets everything perfect. The 3–10 errors are usually `Prisma.InputJsonValue` casts, `$queryRawUnsafe<T>` generics (strip them), or stale dynamic-imports. Fix in a commit on the agent's branch, then merge.
- **Multiple worktrees drift after a main merge.** Their branches diverged from main. If they haven't finished yet, leave them. If they committed already but you haven't merged, you can rebase or just let git handle the merge conflicts when you do merge.

## Re-dispatch after a bailout

1. `cd .worktrees/<name>`
2. `git reset --hard main` — throws away any broken state, syncs the branch to current main
3. `git clean -fd` — removes untracked files the agent may have left
4. `cd ../..` (back to main workspace)
5. Run the wrapper again with the same arguments. The branch still exists; the worktree reuses it.

## Ending the session

1. Kill the monitor (TaskStop in Claude, or just Ctrl+C in a terminal).
2. All worktrees are still on disk. They're cheap (symlinked node_modules). Leave them for next session or remove: `git worktree remove .worktrees/<name> --force`.
3. Delete stale branches if no longer needed: `git branch -D wave2/something`.
