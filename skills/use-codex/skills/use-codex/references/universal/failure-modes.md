# Failure modes — universal taxonomy and per-row remediation

Seven universal rows. Per-mode extensions appear at the bottom. The spine carries the summary; this file carries the remediation.

## Contents

- 1. Rate-limit / 503
- 2. Hung process
- 3. MCP-active JSON drop
- 4. Output truncation
- 5. Worktree dirty unexpected
- 6. Manifest collision
- 7. State dir missing
- Per-mode extensions

## 1. Rate-limit / 503

**Trigger signal:**
- `503 Service Unavailable` in the entry's JSONL log or wrapper log.
- `[ERR] codex exited 1 after T seconds` with no `agent_message` event.
- A wave of FAIL events within ~30 seconds of each other across multiple entries.

**Why:** The codex backend rate-limited the user's auth. The current 503 cooldown is empirically ~13 minutes but can stretch to ~45 minutes under heavy load.

**First-line mitigation:**
1. Stop dispatching new entries. Existing in-flight entries that already started can finish.
2. Wait at least 15 minutes from the most recent 503.
3. Run rescue mode with "redo failures only." `rescue-detect.py` will classify the rate-limited entries as `failed`.
4. **Halve the concurrency cap immediately on first redispatch when rate-limit was the cause** (`JOBS=2 ./run-fleet.sh ...` from a default `JOBS=5`). Use the original cap only when the failure was unrelated to rate limits (network blip, MCP dropout, hung process). If 503s persist after halving, halve again and wait another 15 minutes. This matches the cascade policy in `references/universal/concurrency.md`.

**Why never touch DONE entries:** rate-limit retries should never re-run already-successful work. The audit cost is real (re-validating commits) and the token cost is wasted.

**Multi-Claude-session auth-tier sharing.** The Anthropic auth tier (and the codex/OpenAI auth tier driving spawns) is shared across every session running on the same account. If you have multiple Claude / use-codex / codex-cli sessions live concurrently, persistent rate-limits often mean another session is consuming the budget — the local concurrency cap is irrelevant if a sibling session is already saturating the tier. Pause the other sessions or coordinate dispatch order before redispatching; otherwise a halved cap still hits the same wall.

**Anti-pattern:** auto-retry inside the runner. The runner does not retry. Rescue is operator-confirmed by design.

## 2. Hung process

**Trigger signal:**
- No JSONL events for ≥ 25 minutes (the wrapper's wall-clock cap; configurable).
- `streak:6x` flag in `codex-monitor.sh` ticks (six consecutive ticks with no commit advance).
- Wrapper log shows the agent in `[CMD>] ... ` with no `[CMD✓]` for >25 minutes.

**Why:** Codex hung on a remote tool call (codebase search API, MCP server, web search), got stuck in a planning rumination loop, or hit a network glitch with no retry.

**First-line mitigation:**
1. Check the entry's `jsonl_path` for the last event timestamp. If recent (<5 min), wait — the agent may be working on a slow tool call.
2. If the last event is older than 25 minutes:
   - Identify the codex PID via `pgrep -f "codex exec.*$<entry-id>"` or read the wrapper log.
   - Confirm the PID belongs to this run (manifest has it) before any kill.
   - Surface to the user: "<entry-id> hung; OK to terminate?" — destructive action gate.
   - On user OK: `kill -TERM <pid>`; wait 10 s; `kill -KILL <pid>` if still alive.
3. Mark the entry `failed` with `last_error="hung_25min"`.
4. Eligible for rescue redispatch.

**Anti-pattern:** killing a codex PID without confirming it belongs to the current run. Stale `codex resume` sessions from prior interactive runs may have similar process names.

## 3. MCP-active JSON drop

**Trigger signal:**
- The entry's `jsonl_path` is suspiciously short (<5 events) or missing the `agent_message phase=final_answer` event.
- Worker exit code is 0.
- The `-o` answer file is non-empty.

**Why:** Upstream issue [#15451](https://github.com/openai/codex/issues/15451). When MCP servers are configured (`~/.codex/config.toml` has `mcp_servers` populated), the `--json` stream may silently drop events. The agent ran fine; the events just didn't flow through stdout.

**First-line mitigation:**
1. Verify the answer file is non-empty AND contains plausible content (not "I cannot..." or empty).
2. Mark the entry `done` with advisory `last_error="json_event_dropped"`.
3. Audit (`audit-fleet-state.py`) surfaces these so a human can spot-check.
4. No retry needed.

**Anti-pattern:** marking the entry `failed` because JSONL events were missing. The `-o` file is the source of truth for "did codex produce output."

## 4. Output truncation

**Trigger signal:**
- `audit-sizes.sh` flags the entry as `[SMALL]` (under `MIN_BYTES`, default 10000).
- The answer file ends mid-sentence or has a trailing "..." pattern.

**Why:** Three possibilities:
- The input was thin (parked domain, niche product, deleted resource). The agent did its best with what was there.
- The agent ran into a token budget cap (rare but possible).
- The prompt template was over-constrained ("answer in 100 words") and the agent obeyed.

**First-line mitigation:**
1. **Read the head of the file.** Always inspect before deciding.
2. If the content is correct-but-thin (e.g. parked domain), accept it. Mark `last_error="thin_source"` for the audit trail.
3. If the content is genuinely truncated, archive the answer (`mv answers/<id>.md answers/.prev/`), then re-run that entry alone (`JOBS=1 ./run-batch.sh --only <id>`). Do not auto-retry — there's a real chance the second run is also short and you've lost the original.
4. If the content has hallucinations, do not retry — re-prompt. Edit the template to add a "do not fabricate" constraint and re-render.

**Anti-pattern:** auto-retry-by-size. Codex is non-deterministic; a retry can produce a smaller (or larger but worse) output than the original. Always inspect first.

## 5. Worktree dirty unexpected

**Trigger signal:**
- Post-run `git -C <worktree> status --short` returns non-empty in an exec mode worktree where the wrapper was supposed to commit.
- Wrapper log shows `[wrapper] no changes` despite the agent claiming completion.

**Why:** Codex wrote files but didn't `git add` + commit them, or wrote to gitignored paths, or the wrapper's auto-commit logic failed (e.g. on a `pre-commit` hook that rejected).

**First-line mitigation:**
1. Mark the entry `failed` with `last_error="dirty_worktree_no_commits"`. **Do NOT auto-commit** — the user owns the staging decision for surprises.
2. Surface in the deliverable: "entry <id> has dirty worktree at <path>; review before retry."
3. The user inspects, decides whether to commit-as-is, discard, or fix and commit.
4. After the user resolves, optional rescue redispatch.

**Anti-pattern:** the runner auto-committing whatever's in the worktree. Auto-commit only fires when the agent itself has not committed AND the wrapper sees ≥ 1 staged-or-modified file matching the pre-flight scope. Surprises are surfaced.

## 6. Manifest collision

**Trigger signal:**
- Second invocation of `manifest-update.py` cannot acquire `manifest.lock` within 30 seconds.
- Dispatcher emits `error.code = "concurrent_run_in_progress"`.

**Why:** Two Claude Code sessions (or two runs in the same session) tried to write the same manifest. Most often: the user invoked the skill twice in quick succession.

**First-line mitigation:**
1. The dispatcher refuses cleanly. Do not corrupt the manifest by force-writing.
2. Inspect the lock file: `lsof manifest.lock` shows which process holds it. If stale (process is gone), remove the lock manually.
3. Do not start a parallel run on the same manifest. Use a separate cwd/state root if concurrent orchestration is truly required.

**Anti-pattern:** removing the lock without checking `lsof`. A live writer mid-update will produce a corrupt manifest if you yank the lock.

## 7. State dir missing or unwritable

**Trigger signal:**
- Bootstrap or dispatcher cannot create `resolveStateDir(cwd)/use-codex`.
- `${CLAUDE_PLUGIN_DATA}` is set to an unwritable path, or `${TMPDIR:-/tmp}/codex-companion` is unwritable.

**Why:** The state root is on a read-only filesystem, permissions are wrong, or another tool removed a parent directory.

**First-line mitigation:**
1. Surface the exact state root and stop. Likely a system-level permission issue.
2. The user fixes `${CLAUDE_PLUGIN_DATA}`, `${TMPDIR}`, or permissions; re-run.

**Anti-pattern:** inventing a third state path. The dispatcher, bootstrap, and rescue must all use `codex-cc/lib/state.mjs` semantics.

## Per-mode extensions

### exec mode

| Failure | Trigger | Mitigation |
|---|---|---|
| Worktree codegen failure | `setup-worktree.sh` exits non-zero (e.g. `prisma generate` failed) | Surface; do not dispatch the entry. The codegen failure usually means the worktree is mis-set-up. Re-run setup-worktree.sh after fixing. |
| Auto-commit conflict on shared file | Two sibling worktrees both modify the same file (e.g. `prisma/schema.prisma`) | Merge conflicts surface at user-merge time, not at runner time. The runner commits to its own branch. The user resolves the union manually. |
| Post-verify failure on a clean commit | `tsc --noEmit` exits non-zero after auto-commit | Mark the entry `failed` with `last_error="post_verify_tsc_errors=N"`. The commits are still on the branch; the user reviews and decides whether to fix manually or rescue. |
| Killed runner left orphan codex children | `kill -TERM <runner-pid>` kills the bash runner but `xargs -P` and codex grandchildren survive | `run-fleet.sh` lacks a `trap` that propagates SIGTERM/SIGINT to the process group; descendants orphan and keep consuming tokens (C1 derailment). Mitigation today: after killing the runner, run `pkill -f '<repo-basename>-wt-exec'` to clean up workers, then `pgrep -f 'codex exec'` to confirm zero residual procs before re-dispatch. **Do this before invoking rescue mode** — otherwise the rescue spawn races with surviving children writing to the same worktrees. After the runner ships a `trap 'kill 0' SIGTERM SIGINT`, this row collapses to "kill the runner pid; descendants follow". |
| Entry marked `failed` but worktree has commits past base | Runner's "no answer" detection fires even when the codex child already committed real work; manifest flips to `failed/empty answer` while `git rev-list --count base..HEAD > 0` on that worktree | Caught by `rescue-detect.py`'s evidence object (`worktree_committed_past_base=true`), but the classifier currently keys on `manifest.status` and still reports the entry as `failed` (C1 derailment). Mitigation: cross-check `audit-fleet-state.py --json` AND walk each `worktree_committed_past_base=true` entry; if the commit looks like a legitimate landing of the requested work, flip the manifest to `done` via `manifest-update.py entry --set status=done` instead of re-running. Re-running is idempotent (the runner skips on clean) but wastes a turn. |

### batch mode

| Failure | Trigger | Mitigation |
|---|---|---|
| Slug collision | Two input rows render to the same slug | `render-prompts.sh` hard-fails. Disambiguate the input and re-render. |
| Skip-existing race | Two runners over the same workdir | The skip-existing guard works at job start, not file-write time. Two runners would race. The dispatcher refuses concurrent runs; use separate workdirs for separate batches. |
| Audit shows EVERYTHING below floor | `audit-sizes.sh` flags 100% of entries | The template is wrong. Inspect the template; adjust; re-render; re-run. Do not retry the same template — it'll produce the same thin outputs. |

### single mode

| Failure | Trigger | Mitigation |
|---|---|---|
| `turn.completed` event never arrives | Stream ends without the terminal event | The agent crashed mid-turn. Check `jsonl_path` for the last event; check `pgrep` for the codex PID. If the PID is dead, mark `failed`. If alive, wait 5 min, then surface. |
| `-o` file empty | Codex produced no final answer | Could be MCP dropout (rare in single mode) or codex thought there was nothing to say. Inspect the JSONL for an `agent_message` event; if present, the JSONL has the answer. If not, the agent legitimately produced nothing — surface for user. |

### review mode

| Failure | Trigger | Mitigation |
|---|---|---|
| Round 10 reached | `cap_reached` terminal | Surface the remaining artifacts. The user decides whether to split the branch or rerun after fixes. |
| Major findings present | `blocked` terminal | Main agent evaluates with `do-review` or local equivalent, applies accepted fixes, then reruns review. |
| Classifier JSON malformed | `classify-review-feedback.py` exits 2 | The normalizer/classifier contract broke. Surface raw output; skill version may need to bump. |
| Branch CI failed before review even started | Pre-flight detected unmerged red CI | Surface immediately. Do not dispatch review on a red branch — codex will flag CI errors as findings, polluting the review. |

### rescue mode

| Failure | Trigger | Mitigation |
|---|---|---|
| Manifest schema_version newer than skill | `manifest.schema_version` > the skill's `SCHEMA_VERSION` constant | Surface and refuse. The user upgrades the skill (or pulls the latest pack) before resuming. Do NOT attempt to silently downgrade or strip unknown fields — newer schemas can carry semantically-required state the old code can't reason about. The forward-incompatible refusal is the contract; it lets the user's manifest survive a skill rollback unbroken. |
| Worktree exists but branch deleted | `git worktree list` shows the path; `git rev-parse <branch>` fails | The branch was deleted out from under the worktree. `git worktree prune` first; then ask user whether to recreate the branch from `manifest.entries[i].codex_thread_id` or skip. |
| codex-companion state pruned past MAX_JOBS=50 | `~/.../jobs/<id>.json` for the entry doesn't exist | Cannot correlate by jobId. `rescue-detect.py` falls back to filesystem signals (worktree commits, log size, exit code). Surface "limited rescue context" warning. |
| Classification `unknown` due to missing `mode_state.codex_session_id` | The runner did not (or could not) capture `codex_session_id` (or `codex_thread_id`) into the manifest entry, so `rescue-detect.py` has no thread to correlate with codex-companion's `jobs/` records | Stale or partial runs can leave entries with `mode_state.codex_session_id` unset (e.g. the runner crashed before the JSONL `thread.started` event was extracted, or the manifest was hand-rolled). Classifier returns `unknown` with reason "no codex_session_id". Mitigation: inspect `<jsonl_path>` directly with `jq 'select(.type=="thread.started") | .thread_id'` and either (a) write the thread id back into the manifest via `manifest-update.py entry --set mode_state.codex_session_id=<uuid>` then re-classify, or (b) treat the entry as a clean-slate redo (drop the entry, re-render the prompt, dispatch fresh). |
| Rescue dispatcher classifies but does not re-spawn | (Historical — no longer current.) `node use-codex.mjs rescue` (no `--apply`) is classify-only by design: it returns an envelope with classification + `next_action.choices`. The runner is spawned only when `--apply <subset>` is passed. | Pass `--apply failed-only`, `--apply never-started-only`, `--apply all-non-done`, or `--apply ids:s1,s2,...` to redispatch. `handleRescue` (`use-codex.mjs:2160-2240`) then runs `preRescueCleanup`, flips selected entries to `queued` via `manifest-update.py --execute`, builds the original mode's runner args (with single-mode resume-thread / resume-last threading per the C-FIX-3 wiring), and spawns the runner detached. Add `--dry-run` to preview without mutating the manifest. |

## When to escalate to the user

Always:
- BLOCKED status (manifest entry that needs human decision).
- `apply_failed_after_evaluation` items (review mode).
- Three consecutive failed rescue attempts on the same entry.
- Manifest schema_version mismatch.
- Plugin-data dir issues that fallback can't resolve.

Never silently:
- Skip a DoD criterion the runner can't meet.
- Auto-retry past attempt 3 on the same entry.
- Mark a `running` entry `failed` without confirming the worker is actually dead.
