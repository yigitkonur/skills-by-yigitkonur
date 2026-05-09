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
    (--prompt-file /abs/path/to/prompt.md | --prompt "<text>") \
    [--cwd /abs/path/to/repo] \
    [--out /abs/path/to/answer.md] \
    [--monitor-root /abs/path/to/dir] \
    [--run-id <id>]
```

The dispatcher's full `valueOptions` for single mode are: `prompt`, `prompt-file`, `out`, `cwd`, `monitor-root`, `run-id` (see `handleSingle` in `scripts/orchestrate-codex.mjs`). It declares no boolean options; any unrecognized flag is silently swallowed by the permissive parser.

If `--cwd` is omitted, the dispatcher uses `pwd`. **Single mode runs in `cwd` directly — it does NOT create a worktree, does NOT require a git repo, and does NOT touch `.gitignore`.** A non-git working directory (e.g. a research folder, a mounted notebook, a scratch dir) is fully supported; codex runs in place. If you want isolation in a real repo, create a worktree yourself first and pass it as `--cwd`.

The prompt file follows `references/templates/single.tmpl.md`.

> **`--reuse-worktree` is Planned — not yet wired.** Earlier drafts of this skill exposed `--reuse-worktree`, but `handleSingle`'s parser declares no boolean options, so the flag is silently dropped. Manual workaround for today:
>
> ```bash
> # 1. cd into the existing worktree.
> cd ../myrepo-wt-feat-auth
> # 2. Invoke single mode with --cwd "." (single mode never builds a worktree
> #    on top of cwd, so cwd-is-already-a-worktree is the same code path).
> node /path/to/orchestrate-codex.mjs single \
>     --prompt-file ./prompt.md \
>     --cwd "$PWD"
> ```

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
```

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

A single task is `failed` when ANY of:
- `codex exit code != 0` (runner exits 1).
- `codex exit 0` but `-o` answer file is empty (runner exits 2).
- The runner itself crashed before writing a terminal manifest row (rescue will see `running` with a dead pid).

## When `cwd` is already a worktree

Single mode runs in cwd unmodified — it never creates or migrates worktrees. If `pwd` is already under `../<repo>-wt-*`, codex runs in that worktree. If `pwd` is the main checkout, codex runs in main. If `pwd` is a non-git scratch dir, codex runs there.

The "reuse vs. fresh worktree" decision is the operator's, made before invoking single mode:

- **Reuse** an existing worktree (deps installed, specific branch, half-finished work): `cd ../myrepo-wt-feat-auth && node orchestrate-codex.mjs single --prompt-file ./prompt.md --cwd "$PWD"`.
- **Fresh worktree** for isolation: create it manually first via `git worktree add ../myrepo-wt-single-<slug> <branch>`, then invoke single mode with `--cwd ../myrepo-wt-single-<slug>`.
- **No git at all**: just invoke from the cwd you want; single mode doesn't care.

The `--reuse-worktree` flag is Planned (see Inputs); today the cwd-driven flow above is the working substitute.

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
| 503 mid-stream | Wait 15 min, then rescue. **Resume-thread continuation is Planned — not yet wired.** `handleRescue` (`scripts/orchestrate-codex.mjs`) classifies the manifest and emits an envelope but never invokes `codex exec resume`; today's rescue effectively re-runs from scratch. Manual workaround: `cd <single-mode cwd>` and run `codex exec resume --last` directly to pick up the most recent thread; copy the resulting deliverable into the manifest's recorded answer path so audit stays consistent. |
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
