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
    "prompt_file": "/abs/path/to/prompts/01-search-rewrite.md"
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
- `post_verify_cmd` is wired: `buildExecEntries` in `scripts/use-codex.mjs` threads it onto `mode_state.post_verify_cmd` (and `mode_state.exec.post_verify_cmd` for back-compat); `run-fleet.sh` prefers it over the auto-detect table below. Omit it to fall back to the auto-detect recipe per language.
- `label` (optional) is a human-readable display string surfaced through `mode_state.task.label` and `mode_state.exec.label`. Useful when `id` is terse (`01`, `02`) and the operator wants the manifest / monitor lines to read meaningfully (e.g. `"Bump react in web/"`). Defaults to `null`.
- `base_branch` / `base` (optional) overrides the per-task base branch the new branch is created from; the first one set wins, default `"main"`. Use this when one entry in a mixed fleet should branch off `develop` (or a feature branch) instead of `main`. The override propagates as `mode_state.exec.base_branch` for `setup-worktree.sh` to consume.

Per-run knobs flow through the dispatcher's CLI flags (`--concurrency N`, `--cwd <dir>`), not the tasks file.

## Pre-flight

Before any spawn:
1. `git rev-parse --is-inside-work-tree` succeeds.
2. cwd is the repo root (or `--cwd <path>` is provided to the dispatcher; there is no `--repo` flag).
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
python3 manifest-update.py entry --manifest "$MANIFEST" --entry "$task_id" \
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

# 5. Post-verify (auto-detected only; see table below).
verify_status="not-run"
if [ -n "$pv_cmd" ]; then
    if (cd "$WORKTREE" && eval "$pv_cmd" >/dev/null 2>&1); then
        verify_status="pass"
    else
        verify_status="fail"
    fi
fi

# 6. Mark entry terminal.
# verify_status=fail does NOT flip to `failed` today — it's recorded for
# operator review. The codex+commit+answer triad is the actual gate.
if [ "$CODEX_EXIT" = "0" ] && commits-landed-since-baseline; then
    status=done
else
    status=failed
fi
python3 manifest-update.py entry --manifest "$MANIFEST" --entry "$task_id" \
    --set "status=$status" --set "exit_code=$CODEX_EXIT" \
    --set "finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --set "verify_status=$verify_status"
```

The runner emits one stdout line per state transition:

```
START 01-search-rewrite
DONE  01-search-rewrite (runtime=187s verify=pass)
FAIL  02-cache-eviction (codex exit=1; runtime=42s; see <worktree>/.use-codex/02-cache-eviction.log)
SKIP  03-already-done
--- all jobs finished ---
```

## Auto-commit logic

If the agent committed during its run (it usually does for coding tasks), the wrapper sees a clean working tree and skips its own commit. If the agent did NOT commit (e.g. wrote files but bailed), the wrapper:
- Stages everything in the worktree via `git add -A` (`run-fleet.sh:381`). That means everything git considers tracked-and-modified or untracked-and-not-ignored. There is no baseline-aware diff filter and no per-file allowlist; if codex creates scratch files in the worktree (notes, intermediate artifacts, debug dumps), they get staged and committed too. Use `.gitignore` (or an explicit `Out-of-scope` clause in the prompt forbidding scratch files) to keep noise out.
- Generates a commit message: `<emoji> <type>(<scope>): <task-id> auto-commit` based on the task id's heuristic.
- Commits.
- Logs `[wrapper] auto-committed N files`.

If the wrapper sees nothing to commit AND codex exit is 0, the task is marked `failed` with `last_error="codex_exit_0_no_changes"` (the agent claimed success but produced no work — usually a meta-skill rumination loop).

### Audit-style / findings-only tasks

If the user's task produces a deliverable that is NOT a code change — accessibility audits, security findings, code reviews stored as markdown reports, design reviews — the success-gate above ("≥1 commit on branch since baseline") trips with `codex_exit_0_no_changes` because no code was modified. The fix is in the prompt: instruct codex to write the deliverable to a file inside the worktree AND commit it.

Verbatim form to drop into your prompt's Success criteria (copy-paste, adjust the path):

```
## Success criteria
- `audit/<task-id>.md` exists, non-empty, ≤ <ceiling> lines.
- File is committed: `git add audit/<task-id>.md && git commit -m "audit(<scope>): <one-line summary>"` ran cleanly before exit.
```

The wrapper sees the commit, the success gate passes, and the audit report is preserved as a regular tracked artifact. See `references/universal/prompt-discipline.md` for the success-criterion pattern.

## Post-verify auto-detection

`run-fleet.sh` detects the project type from files at the worktree root:

| Repo signal | POST_VERIFY_CMD |
|---|---|
| `tsconfig.json` (and `npx` available) | `npx --no-install tsc --noEmit` |
| `pyproject.toml` or `mypy.ini` (and `mypy` on PATH) | `mypy --strict .` |
| `Cargo.toml` (and `cargo` on PATH) | `cargo check --quiet` |
| `go.mod` (and `go` on PATH) | `go vet ./...` |
| (none of the above) | skip post-verify |

Per-task override via `tasks.json` `post_verify_cmd` is wired (see Inputs note): the runner prefers `mode_state.post_verify_cmd` (or `mode_state.task.post_verify_cmd`) over the auto-detect table when set. The runner writes `verify_status` (`pass` / `fail` / `not-run`) and `mode_state.post_verify_exit` into the manifest.

### Docs-only / asset-only tasks

When the worktree contains no language signal — pure documentation, copy edits, image assets, JSON config — none of the auto-detect rows match, so `verify_status` is `not-run`. This is **first-class behavior**, not a misconfiguration. The success gate degrades automatically:

- The post-verify clause drops out.
- The task is `done` on (codex exit 0) ∧ (≥ 1 commit) ∧ (`-o` answer file non-empty).

There is currently no built-in `package.json` row (no auto-pick of `pnpm test` / `npm test` / `bun test`); a JS-only repo without `tsconfig.json` will also fall through to `not-run`. If you need a JS test gate, run it manually after the fleet returns, or include the verify command in the prompt's `## Self-check` so the agent runs it before committing.

## Success gate

A task is `done` when ALL of these hold:
- `codex exit code == 0`.
- ≥ 1 new commit on the worktree's branch since baseline.
- `-o` answer file exists and is non-empty.
- Post-verify is `pass` OR `not-run` (no language signal). Post-verify `fail` does NOT currently flip the status to `failed` on its own — it's recorded as `verify_status=fail` in the manifest and the operator decides. The wrapper marks `done` regardless of post-verify outcome as long as the codex+commit+answer triad passes.

A task is `failed` when ANY of:
- `codex exit code != 0`.
- Codex exit 0 but `-o` answer file is empty AND the JSONL log is non-empty (drop-detection signal).
- Auto-commit failed (e.g. `pre-commit` hook rejected).
- `setup-worktree.sh` failed.
- The prompt path was missing.

Independent post-verify failure showing up as `done` with `verify_status=fail` is the current shape; if you need the verify to gate the status, treat `verify_status=fail` as a hand-off signal and re-dispatch via rescue with a refined prompt.

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
- Never reuse a worktree across runs without an explicit decision. A per-task `--reuse <id>` flag is not implemented today; reuse happens implicitly via `ALLOW_REUSE=1` inside `run-fleet.sh:250` when an entry's `worktree_path` is already recorded. Stale state contaminates new runs.
- Never raise concurrency past the default without `--i-have-measured`. Rate-limits cascade.
- Never put two tasks that share files in the same fleet. Serialize them.
- Never let post-verify mutate state. Post-verify is a check, not a setup step. The auto-detect commands above are read-only by design (`tsc --noEmit`, `cargo check`, `mypy --strict .`, `go vet ./...`); when per-task `post_verify_cmd` ships, keep it that way. Setup belongs in `setup-worktree.sh` or in the prompt itself.
