# Single mode — one big mission with live stream

Run one focused codex task with full Monitor visibility. The agent gets `[CMD>]`, `[CMD✓]`, `[THINK]`, `[SAID]` lines as they happen. Use this when the work is too big for a casual `codex exec` invocation but doesn't have N parallel siblings.

## Contents

- When to pick single mode
- Inputs
- Pre-flight
- Spawn flow
- Success gate
- When `cwd` is already a worktree
- Why pipe through codex-json-filter.sh
- Aborting a running mission
- Recovery
- Cleanup
- Anti-patterns

## When to pick single mode

- One task, ≥ 5 minutes of agent time, benefits from observability.
- The user wants to see codex's reasoning live (so they can intervene if it drifts).
- You need the discipline of a manifest entry (rescue + audit) without fleet overhead.
- Research / summarization / generation that doesn't fit the template-fanout shape of batch mode.

When to skip:
- N parallel tasks → exec mode.
- N parallel research jobs from one template → batch mode.
- Trivial one-shot (< 5 minutes, no observability needed) → just type `codex exec` directly.

### Sizing for huge audits

For audits or reads spanning > ~50 files, expect context-window pressure. Codex's effective context is finite (gpt-5.5 xhigh has a generous budget but not unlimited). For very large reads, consider: (a) splitting into multiple single-mode runs by directory, (b) asking codex to traverse the tree directory-by-directory rather than reading everything at once, (c) using exec mode to fan out by file group. Context-exhaustion failures are not auto-recoverable today (`codex exec resume --last` is Planned but not wired).

## Inputs

The dispatcher accepts:

```
node run-codex-2.mjs single \
    (--prompt-file /abs/path/to/prompt.md | --prompt "<text>") \
    [--cwd /abs/path/to/repo] \
    [--out /abs/path/to/answer.md] \
    [--monitor-root /abs/path/to/dir] \
    [--run-id <id>]
```

The dispatcher's full `valueOptions` for single mode are: `prompt`, `prompt-file`, `out`, `cwd`, `monitor-root`, `run-id`, `output-schema`, `resume-thread`. Boolean options: `reuse-worktree`, `resume-last`, `force-new-run`, `dry-run` (see `handleSingle` in `scripts/run-codex-2.mjs`). Any unrecognized flag is rejected by the strict parser.

If `--cwd` is omitted, the dispatcher uses `pwd`. **Single mode runs in `cwd` directly — it does NOT create a worktree, does NOT require a git repo, and does NOT touch `.gitignore`.** A non-git working directory (e.g. a research folder, a mounted notebook, a scratch dir) is fully supported; codex runs in place. If you want isolation in a real repo, create a worktree yourself first and pass it as `--cwd`.

The prompt file follows `references/templates/single.tmpl.md`.

### `--reuse-worktree`

`--reuse-worktree` is wired end-to-end: the dispatcher (`handleSingle` in `scripts/run-codex-2.mjs`) declares it as a boolean option, persists it on the entry's `mode_state.single.reuse_worktree`, and forwards `--reuse-worktree` to `run-single.sh`. Today the runner accepts the flag and threads it through; semantically single mode runs in `--cwd` directly either way (no worktree is created), so the flag's effect is to record the operator's intent on the manifest entry. If you've already cd'd into a worktree, you can either omit the flag (cwd-driven) or pass `--reuse-worktree` to make the intent explicit:

```bash
cd ../myrepo-wt-feat-auth
node /path/to/run-codex-2.mjs single \
    --prompt-file ./prompt.md \
    --cwd "$PWD" \
    --reuse-worktree
```

## Pre-flight

1. `codex login status` exits 0 — **warn unless `~/.codex/config.toml` declares no `model_provider`.** Some setups (vendored OpenAI key in env, ChatGPT subscription, custom auth shim) leave `codex login status` non-zero even when `codex exec` works fine. Treat a non-zero `codex login status` as a soft warning and proceed; only hard-fail if `codex exec --help` itself errors.
2. `--prompt-file` exists OR `--prompt` is provided.
3. cwd exists and is writable. (No git check; single mode is non-worktree.)
4. If you've cd'd into an existing worktree, you're fine — single mode runs in cwd unmodified. The "reuse vs. fresh worktree" decision is yours, made before invoking.

## Spawn flow

`run-single.sh` does one shot:

```bash
. codex-flags.sh
cat "$PROMPT_FILE" | codex exec "${CODEX_FLAGS[@]}" \
    --json \
    -C "$CWD" \
    -o "$OUT" \
    2>"$ERR_LOG" \
    | tee "$LOG_PATH" \
    | CODEX_FILTER_LEVEL="$FILTER_LEVEL" bash codex-json-filter.sh
```

stderr is redirected to a separate `$ERR_LOG` file (NOT merged with `2>&1`) because codex emits deprecation warnings, auth/rate-limit notices, and other diagnostics on stderr; merging would corrupt the JSONL filter's input. The pipe is the Monitor: `codex-json-filter.sh` emits one human-readable line per JSONL event. The `tee` keeps the raw stream on disk for post-mortem.

### What `-o` actually writes

`-o <file>` writes the agent's **final assistant message verbatim** — exactly what the agent decided to say at the end, with no framing, no header, no metadata. This means:

- For prose deliverables (research summaries, plans, narrative answers), `-o` is the right output target.
- For **structured deliverables (JSON, YAML, TOML, raw HTML, anything that must parse)**, the prompt MUST forbid code fences and prose framing; otherwise the file will contain ` ```json\n{...}\n``` ` plus a chatty preamble and your downstream parser will break. Pin this in the prompt's `## Output format` section, e.g.:
  > Reply with ONLY the JSON object. No code fences. No prose before or after. The first character of your reply must be `{` and the last must be `}`.
- The file is overwritten on every run; there is no append mode.
- An empty `-o` file after `codex exit 0` means the agent had no final message to emit (a bailout, a refusal, or a malformed prompt). The runner treats empty + exit 0 as `failed` with `last_error="empty answer"`.

The runner emits these lines (verbosity-dependent):

```
[START] thread=t-1234
[CMD>] git status
[CMD✓] git status (exit 0, 0.1s)
[THINK] Plan: 1) read schema, 2) ...
[CMD>] pnpm install
[CMD✓] pnpm install (exit 0, 14.2s)
[SAID] Done. New migration is at db/migrations/20260508_add_users.sql.
[TURN<] tokens=in:8234/out:1567/cached:1200
--- single done (single: done) ---
```

The final `--- single done (<id>: <status>) ---` line is the terminal sentinel. `run-single.sh` appends a `{"type":"run-codex-2.done","entry_id":...,"status":...}` event to the JSONL log AFTER the terminal manifest write; `codex-json-filter.sh` translates it. Live-watch operators (`tail -F <jsonl> | codex-json-filter.sh`) see this line and know to `TaskStop` the Monitor — no need to pgrep manually or guess at `[TURN<]`. Status is `done` on success, `failed` on codex non-zero or empty `-o`.

## Success gate

The three artifacts and what each is for:

| Artifact | Path | Role |
|---|---|---|
| `-o` answer file | `--out` (default `<monitor_root>/single-<run_id>.md`) | **Source of truth.** Non-emptiness is the deliverable signal. |
| JSONL log | `<answer_dir>/<entry_id>.jsonl` | **Supplementary.** Use for post-mortem, thread-id extraction, MCP-drop diagnostics. May be incomplete under MCP-active dropout. |
| Manifest entry | `<state>/manifest.json` | **Audit.** What `audit-fleet-state.py` and rescue read. Status / exit_code / codex_thread_id. |

A single task is `done` when ALL of:
- `codex exit code == 0`.
- `-o` answer file exists and is non-empty (the gate the runner checks).

The runner does NOT inspect the JSONL stream for `turn.completed` before declaring `done`; non-empty `-o` is enough. If the JSONL stream is empty (MCP dropout) but `-o` is non-empty, that's still `done` — the answer file is canonical.

### Audit-style / findings-only tasks

This success gate makes single mode the right route for findings-only deliverables (audit reports, code reviews stored as markdown, analysis writeups, scoped recommendation docs). Unlike exec mode (which requires ≥1 commit on the worktree's branch and trips `codex_exit_0_no_changes` for non-code deliverables — see `references/modes/exec.md` "Audit-style" subsection), single mode's gate is just "non-empty `-o`". No commit required, no worktree dance, no `tasks.json`. Pass `--out audit-report.md` (relative paths resolve against `--cwd`, default cwd) to land the deliverable where the operator wants it. The expected verbose stream for an audit task is `[THINK]`-heavy with one long `[SAID]` and few-or-no `[CMD]` markers — different shape from a coding task and worth knowing for live-watch sanity-checking.

A single task is `failed` when ANY of:
- `codex exit code != 0` (runner exits 1).
- `codex exit 0` but `-o` answer file is empty (runner exits 2).
- The runner itself crashed before writing a terminal manifest row (rescue will see `running` with a dead pid).

## When `cwd` is already a worktree

Single mode runs in cwd unmodified — it never creates or migrates worktrees. If `pwd` is already under `../<repo>-wt-*`, codex runs in that worktree. If `pwd` is the main checkout, codex runs in main. If `pwd` is a non-git scratch dir, codex runs there.

The "reuse vs. fresh worktree" decision is the operator's, made before invoking single mode:

- **Reuse** an existing worktree (deps installed, specific branch, half-finished work): `cd ../myrepo-wt-feat-auth && node run-codex-2.mjs single --prompt-file ./prompt.md --cwd "$PWD"`.
- **Fresh worktree** for isolation: create it manually first via `git worktree add ../myrepo-wt-single-<slug> <branch>`, then invoke single mode with `--cwd ../myrepo-wt-single-<slug>`.
- **No git at all**: just invoke from the cwd you want; single mode doesn't care.

Pass `--reuse-worktree` to record the intent on the manifest entry; the cwd-driven flow is what actually runs codex.

## Why pipe through codex-json-filter.sh

The raw `codex exec --json` stream is JSONL with verbose event types and full payloads. Piping through the filter:
- Compresses each event into one human-readable line.
- Hides noise (full stdout of `pnpm install`, full file_change diffs).
- Keeps the Monitor notification volume manageable.

The raw stream is captured to disk via `tee` for post-mortem; `codex-json-filter.sh --level verbose` can replay it later if needed.

### Setting verbosity (`minimal` | `normal` | `verbose`)

There are **two independent filter pipelines**, each with its own verbosity. They are decoupled — setting one does NOT set the other:

1. **Runner-side filter** (the pipe inside `run-single.sh`, where the codex stdout goes through `codex-json-filter.sh` before being captured). The runner reads `FILTER_LEVEL` from its own env (default `normal`). The dispatcher (`handleSingle` in `scripts/run-codex-2.mjs`) does NOT expose a `--filter-level` flag, but `spawnRunnerDetached` inherits `process.env`, so an env var set on the dispatcher invocation propagates to the spawned runner:

   ```bash
   FILTER_LEVEL=verbose node run-codex-2.mjs single \
       --prompt-file ./prompt.md --cwd "$PWD"
   ```

2. **Monitor-pipe filter** (the `tail -F <jsonl> | bash codex-json-filter.sh` command the dispatcher emits in `singleMonitorCommand`). This pipe runs at the filter's default `normal` regardless of the dispatcher's `FILTER_LEVEL` env. To change the Monitor-pipe verbosity for an active run, edit the emitted Monitor command before arming Monitor, or replay the captured JSONL after the run with `codex-json-filter.sh --level <level> < <jsonl>`.

So: the dispatcher's `FILTER_LEVEL` env reaches the runner; it does NOT reach the Monitor's filter. Set runner-side via env at dispatch time; control Monitor-side by replaying the on-disk JSONL.

## Aborting a running mission

When the operator wants to stop a single-mode mission mid-flight (the agent is going down a wrong path, the user changed their mind, the work is no longer needed), single mode does not provide a built-in cancel command. Compose the existing primitives:

1. **Capture `runner_pid` from the dispatcher envelope.** When `node run-codex-2.mjs single` returned, its envelope's `result.runner_pid` is the bash runner's PID. If you no longer have the envelope, `pgrep -f 'run-single.sh.*<entry-id>'` or `pgrep -f 'codex exec.*<cwd>'` will find it.
2. **Send SIGTERM first:** `kill -TERM <runner_pid>`. The runner has no SIGTERM trap (no `trap 'kill 0' SIGTERM SIGINT`), so the codex grandchild process under it may orphan rather than terminate cleanly.
3. **Clean up the codex grandchild explicitly:** `pkill -f 'codex exec'` scoped to the cwd the dispatcher used (e.g. `pkill -f "codex exec.*$(realpath /path/to/single-cwd)"`). Verify with `pgrep -f 'codex exec'` — confirm zero residual processes before doing anything else.
4. **The manifest entry will be left in `running` state** (the runner did not get to write a terminal status row). Run `node run-codex-2.mjs rescue --manifest <path>` to surface the orphan; rescue's classifier reports it as `in_flight` with a dead pid (i.e. effectively `unknown`) and offers `--apply` to reclassify and redispatch (or you can flip the entry to `failed` with `manifest-update.py entry --set status=failed --set last_error=aborted_by_operator` if you do NOT want to resume).

Same recipe applies to a hung mission once the operator decides termination is the right call (see Failure-mode #2 in `references/universal/failure-modes.md`). The only difference is a hung mission may already be unresponsive on SIGTERM and need `kill -KILL` after the grace window.

## Recovery

| Symptom | Mitigation |
|---|---|
| Stream ends with no terminal event | Worker crashed mid-turn. Check `pgrep` for the codex PID. If alive, wait 5 min; if not, mark `failed`. |
| `-o` file empty but `turn.completed` seen | Codex thought there was nothing to say. Either the task was already done OR the prompt was malformed. Inspect; surface for user. |
| 503 mid-stream | Wait 15 min, then rescue. Single-mode rescue redispatch is wired end-to-end: `handleRescue` (`run-codex-2.mjs:2198-2218`) flips the entry to `queued`, builds runner args including `--resume-thread <id>` (from `entry.codex_thread_id`) or falls back to `--resume-last`, and `run-single.sh` translates these into `codex exec resume <id>` / `codex exec resume --last`. The thread context is preserved, not re-run from scratch. If `codex_thread_id` was never captured (rare — runner crashed before the JSONL `thread.started` event), the fallback `--resume-last` resumes the most recent thread on disk; if that's wrong, manually `cd <single-mode cwd>` and run `codex exec resume <correct-id>`. |
| MCP-active JSON drop | `-o` file is the truth. Mark `done` with advisory `last_error="json_event_dropped"` if the file is non-empty. |

Full taxonomy: `references/universal/failure-modes.md`.

## Cleanup

After single mode finishes successfully:
1. If you manually created a worktree before invoking, remove it via `python3 cleanup-worktrees.py --execute` after the user merges. Single mode never auto-creates a worktree, so there is nothing for the dispatcher itself to clean up.
2. Manifest deleted (one-entry manifest after the entry is `done`).
3. JSONL log + answer file are preserved at the user's discretion (under `monitor_root/`).

## Anti-patterns

- Treating single mode as "lighter discipline." It's not — same prompt template, same Monitor, same manifest. The simplification is one entry instead of N.
- Skipping the success-output assertion. `-o` file non-empty is the gate (per the success-gate table). "Codex exited 0" alone isn't enough.
- Reusing a manually-created worktree across multiple single-mission runs. State contaminates across missions. One run, one cwd; if you need a fresh sandbox, build a new worktree before invoking.
- Piping JSONL through grep without `--line-buffered`. Events delayed by minutes; Monitor sees nothing.
