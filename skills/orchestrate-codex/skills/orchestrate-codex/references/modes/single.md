# Single mode — one big mission with live stream

Run one focused codex task with full Monitor visibility. The agent gets `[CMD>]`, `[CMD✓]`, `[THINK]`, `[SAID]` lines as they happen. Use this when the work is too big for a casual `codex exec` invocation but doesn't have N parallel siblings.

## When to pick single mode

- One task, ≥ 5 minutes of agent time, benefits from observability.
- The user wants to see codex's reasoning live (so they can intervene if it drifts).
- You need the discipline of a manifest entry (rescue + audit) without fleet overhead.
- Research / summarization / generation that doesn't fit the template-fanout shape of batch mode.

When to skip:
- N parallel tasks → exec mode.
- N parallel research jobs from one template → batch mode.
- Trivial one-shot (< 5 minutes, no observability needed) → just type `codex exec` directly.

## Inputs

The dispatcher accepts:

```
node orchestrate-codex.mjs single \
    --prompt-file /abs/path/to/prompt.md \
    [--cwd /abs/path/to/repo] \
    [--reuse-worktree]
```

Or `--prompt "<text>"` inline.

If `--cwd` is omitted, the dispatcher uses `pwd`. If cwd is already inside a worktree AND `--reuse-worktree` is passed, the spawn runs in that worktree (no new worktree). Otherwise the dispatcher creates `../<repo>-wt-single-<slug>` per worktree-contract.

The prompt file follows `references/templates/single.tmpl.md`.

## Pre-flight

1. `codex login status` exits 0.
2. `--prompt-file` exists OR `--prompt` is provided.
3. If a worktree will be created: cwd is a git repo; `.gitignore` covers `../<repo>-wt-single-*`.
4. If `--reuse-worktree` was passed: cwd is inside an existing worktree (verified via `git rev-parse --show-toplevel` matching a path under `../<repo>-wt-*`).

## Spawn flow

`run-single.sh` does one shot:

```bash
. codex-flags.sh
codex exec "${CODEX_FLAGS[@]}" \
    --json \
    -o "$ANSWER_FILE" \
    -C "$CWD" \
    < "$PROMPT_FILE" \
    2>&1 \
    | tee "$JSONL_LOG" \
    | bash codex-json-filter.sh
```

The pipe is the Monitor: `codex-json-filter.sh` emits one human-readable line per JSONL event. The `tee` keeps the raw stream on disk for post-mortem.

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
```

## Success gate

A single task is `done` when ALL of:
- `turn.completed` event observed in the JSONL stream OR `agent_message phase=final_answer` event observed.
- `-o` answer file exists and is non-empty.
- `codex exit code == 0`.

A single task is `failed` when ANY of:
- `codex exit code != 0`.
- No `turn.completed` event AND `-o` answer file empty.
- The JSONL stream ends without a terminal event (worker crashed, pipe broke).

## When `cwd` is already a worktree

The skill never creates a worktree on top of a worktree. If `pwd` is already under `../<repo>-wt-*`, the dispatcher detects this and asks:

- "Reuse this worktree? (run codex inside it)"
- "Or create a fresh worktree at `../<repo>-wt-single-<slug>`?"

Reuse is the right answer when the user has set up an environment they want to keep (deps installed, specific branch checked out, half-finished work). A fresh worktree is right when they want isolation.

If `--reuse-worktree` is set explicitly, no question is asked — reuse happens.

## Why pipe through codex-json-filter.sh

The raw `codex exec --json` stream is JSONL with verbose event types and full payloads. Piping through the filter:
- Compresses each event into one human-readable line.
- Hides noise (full stdout of `pnpm install`, full file_change diffs).
- Keeps the Monitor notification volume manageable.

The raw stream is captured to disk via `tee` for post-mortem; `codex-json-filter.sh --level verbose` can replay it later if needed.

## Recovery

| Symptom | Mitigation |
|---|---|
| Stream ends with no terminal event | Worker crashed mid-turn. Check `pgrep` for the codex PID. If alive, wait 5 min; if not, mark `failed`. |
| `-o` file empty but `turn.completed` seen | Codex thought there was nothing to say. Either the task was already done OR the prompt was malformed. Inspect; surface for user. |
| 503 mid-stream | Wait 15 min. Single mode rescue: `node orchestrate-codex.mjs rescue` picks up the most recent thread via `codex exec resume --last`. |
| MCP-active JSON drop | `-o` file is the truth. Mark `done` with advisory `last_error="json_event_dropped"` if the file is non-empty. |

Full taxonomy: `references/universal/failure-modes.md`.

## Cleanup

After single mode finishes successfully:
1. If a worktree was created: `python3 cleanup-worktrees.py --execute` removes it after the user merges (or per `--keep-worktree` flag).
2. Manifest deleted (one-entry manifest after the entry is `done`).
3. JSONL log + answer file are preserved at the user's discretion (under `monitor_root/`).

## Anti-patterns

- Treating single mode as "lighter discipline." It's not — same prompt template, same Monitor, same manifest. The simplification is one entry instead of N.
- Skipping the success-output assertion. `-o` non-empty + terminal event is the gate. "Codex exited 0" alone isn't enough.
- Reusing a worktree across multiple single-mission runs. State contaminates across missions. One run, one worktree (or one cwd if `--reuse-worktree`).
- Piping JSONL through grep without `--line-buffered`. Events delayed by minutes; Monitor sees nothing.
