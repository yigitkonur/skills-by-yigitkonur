# Exec mode — parallel codex agents in worktrees

Fan-out N coding tasks across N git worktrees. Each task gets a fresh worktree, a deterministic branch, a `codex exec --json` invocation, and an auto-commit at the end. The user merges the resulting branches manually.

## Contents

- When to pick exec mode
- Inputs
- Pre-flight
- Runner behavior
- Output contract
- Recovery

## When to pick exec mode over alternatives

- Multiple tasks (≥ 2) that touch disjoint files. Parallelism wins.
- Tasks isolable enough that merge conflicts don't dominate. If every task edits `prisma/schema.prisma`, serialize instead.
- Each task needs ≥ 5 minutes of agent time (otherwise overhead exceeds parallelism win).
- The agent's work should auto-commit so the orchestrator doesn't babysit completion.

## Inputs

The dispatcher accepts a `tasks.json` file. The shape is a top-level JSON array (not a wrapper object); each element is one task:

```json
[
  {
    "id": "01-search-rewrite",
    "branch": "wave1/search-rewrite",
    "prompt_file": "/abs/path/to/prompts/01-search-rewrite.md",
    "post_verify_cmd": "pnpm test"
  },
  {
    "id": "02-cache-eviction",
    "branch": "wave1/cache-eviction",
    "prompt_file": "/abs/path/to/prompts/02-cache-eviction.md"
  }
]
```

Field rules per element:
- `id` (or `slug`) is the stable per-task key; must be unique. Auto-generated as `01`, `02`, ... if omitted.
- `branch` (optional) is created on dispatch (or reused if already present and clean). If omitted the dispatcher derives one from the id.
- `prompt_file` is the path to a rendered prompt; see `references/templates/exec.tmpl.md`. Pass either `prompt_file` (path) or `prompt` (inline text).
- `post_verify_cmd` is optional; defaults auto-detect per language recipe (`tsc --noEmit`, `mypy`, `cargo check`, `go vet`).

Per-run knobs flow through the dispatcher's CLI flags (`--concurrency N`, `--cwd <dir>`), not the tasks file.

## Pre-flight

Before any spawn:
1. `git rev-parse --is-inside-work-tree` succeeds.
2. cwd is the repo root (or `--repo <path>` is provided).
3. main is clean (`git status --short` empty on main; if you're on a feature branch, the branch is clean).
4. No in-progress merge / rebase / cherry-pick / bisect.
5. `.gitignore` covers `../<repo>-wt-*`.
6. Baseline tests pass (`pnpm test` or equivalent). Codex-mid-broken-baseline produces broken commits.
7. Every task's `prompt_file` exists and is non-empty.
8. Every task's `branch` does NOT already exist on `origin` (fresh fleet) OR exists with a clean reusable worktree (rescue resume).

## Per-task spawn flow

`run-fleet.sh` does this for each task in parallel (capped at `concurrency_cap`):

```bash
# 1. Set up worktree.
bash setup-worktree.sh "$task_id" "$task_branch" "$base_branch"
# Worktree is at ../<repo>-wt-exec-<task_id> (per worktree-contract.md naming).

# 2. Mark entry running.
python3 manifest-update.py --manifest "$MANIFEST" --entry "$task_id" \
    --set 'status=running' --set "started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --set 'attempts++'

# 3. Spawn codex exec with the universal flag set + per-spawn additions.
. codex-flags.sh
codex exec "${CODEX_FLAGS[@]}" \
    --json \
    -o "$LOG_DIR/$task_id.last-message.md" \
    -C "$WORKTREE" \
    "$(cat "$prompt_file")" \
    2>&1 | tee "$LOG_DIR/$task_id.jsonl"

CODEX_EXIT=${PIPESTATUS[0]}

# 4. Auto-commit (only if codex exited 0 AND worktree has changes).
if [ "$CODEX_EXIT" = "0" ] && [ -n "$(git -C "$WORKTREE" status --porcelain)" ]; then
    git -C "$WORKTREE" add -A
    git -C "$WORKTREE" commit -m "$(generate_commit_message "$task_id")"
fi

# 5. Post-verify (per the auto-detected POST_VERIFY_CMD).
(cd "$WORKTREE" && eval "$post_verify_cmd") || POST_VERIFY_EXIT=$?

# 6. Mark entry terminal.
if [ "$CODEX_EXIT" = "0" ] && commits-landed-since-baseline && [ "${POST_VERIFY_EXIT:-0}" = "0" ]; then
    status=done
else
    status=failed
fi
python3 manifest-update.py --manifest "$MANIFEST" --entry "$task_id" \
    --set "status=$status" --set "exit_code=$CODEX_EXIT" \
    --set "finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --set "mode_state.post_verify_exit=${POST_VERIFY_EXIT:-0}"
```

The runner emits one stdout line per state transition:

```
START 01-search-rewrite
DONE 01-search-rewrite (commits=3, post_verify=0)
FAIL 02-cache-eviction (codex_exit=1, see logs/02-cache-eviction.log)
SKIP 03-already-done
--- all jobs finished ---
```

## Auto-commit logic

If the agent committed during its run (it usually does for coding tasks), the wrapper sees a clean working tree and skips its own commit. If the agent did NOT commit (e.g. wrote files but bailed), the wrapper:
- Stages everything that's both a) modified vs baseline and b) not gitignored.
- Generates a commit message: `<emoji> <type>(<scope>): <task-id> auto-commit` based on the task id's heuristic.
- Commits.
- Logs `[wrapper] auto-committed N files`.

If the wrapper sees nothing to commit AND codex exit is 0, the task is marked `failed` with `last_error="codex_exit_0_no_changes"` (the agent claimed success but produced no work — usually a meta-skill rumination loop).

## Post-verify auto-detection

`run-fleet.sh` (and `setup-worktree.sh`) detect the project type:

| Repo signal | POST_VERIFY_CMD |
|---|---|
| `tsconfig.json` | `tsc --noEmit` |
| `pyproject.toml` (with `[tool.mypy]`) | `mypy .` |
| `Cargo.toml` | `cargo check` |
| `go.mod` | `go vet ./...` |
| (none of the above) | skip post-verify |

Per-task override via `tasks.json` `post_verify_cmd`. The check runs inside the worktree and its exit code is captured into `mode_state.post_verify_exit`. Non-zero is `failed`.

## Success gate

A task is `done` when ALL of:
- `codex exit code == 0`.
- ≥ 1 new commit on the worktree's branch since baseline.
- `-o` answer file exists and is non-empty.
- Post-verify exit code is 0 (or post-verify was skipped per language recipe).

A task is `failed` when ANY of:
- `codex exit code != 0`.
- Codex exit 0 but no commits landed (meta-skill rumination, agent bailed without a marker).
- Worktree is dirty post-run (unexpected uncommitted changes).
- Post-verify failed.

## Recovery

| Symptom | Mitigation |
|---|---|
| Single task FAIL with 503 | Wait 15 min; rescue redo failures only. |
| Multiple tasks FAIL with 503 simultaneously | Backend rate-limited the user. Wait 15 min; halve concurrency on retry. |
| Task exit 0 with no commits | Inspect the JSONL log for meta-skill rumination. Tighten the SUBAGENT-STOP prefix in the prompt template; rescue redo. |
| Task auto-committed but post-verify failed | Inspect the commit; either fix manually + amend OR rescue redo with a refined prompt. |
| Worktree dirty post-run | Surfaced as `BLOCKED-DIRTY`. The user inspects, decides commit / discard / fix. The auto-commit will not help here — the dirtiness usually means the agent wrote to gitignored paths or a `pre-commit` hook rejected. |
| Conflicts when merging branch back to main | Expected for shared files (`prisma/schema.prisma`, `src/lib/query-keys.ts`). Resolve manually; the runner does not auto-merge. |

Full failure-mode taxonomy: `references/universal/failure-modes.md`.

## Cleanup

After every task is terminal:
1. `python3 cleanup-worktrees.py --execute --base main` — removes worktrees whose branches are merged. Refuses dirty/unmerged unless `--force-abandon <id>`.
2. Manifest deleted by the cleanup script after every entry is `done` or `skipped`.
3. Failed entries' worktrees are preserved for inspection; the user removes manually after deciding.

## Anti-patterns

- Never auto-merge to main. Merging is operator-driven.
- Never reuse a worktree across runs without explicit `--reuse <id>`. Stale state contaminates new runs.
- Never raise concurrency past the default without `--i-have-measured`. Rate-limits cascade.
- Never put two tasks that share files in the same fleet. Serialize them.
- Never set a `post_verify_cmd` that mutates state (e.g. `pnpm install`). Post-verify is a check, not a setup step. Setup happens in `setup-worktree.sh`.
