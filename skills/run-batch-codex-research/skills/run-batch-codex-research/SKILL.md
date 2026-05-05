---
name: run-batch-codex-research
description: Use skill if you are running codex (or another LLM CLI) over N inputs in parallel — template-driven prompts, bounded-concurrent shell runner, Monitor stream with size signal, idempotent retry.
---

# Run Batch Codex Research

You orchestrate N independent codex jobs from a single prompt template. The shape is always the same: one input list, one prompt template, one runner with bounded parallelism, one Monitor stream, one audit pass. The skill stays generic — the inputs can be URLs, IDs, file paths, product names, or arbitrary strings; the template can be any research, summarisation, or generation prompt.

## When to reach for this

Pick this skill when **all** of the following are true:

- You have a list of 10+ items to process and the work for each item is roughly independent.
- The same prompt template applies to every item with one substitution.
- You want every item's output saved as a separate file you can audit later.
- You want bounded parallelism (don't melt the API or your laptop) plus live progress.
- The work is research/summarisation/generation, not coding tasks that would benefit from worktrees.

Do **not** reach for it when:

- The list is < 5 items — just loop. The infra cost outweighs the parallelism win.
- The work is coding inside a git repo — use `run-codex-exec` (worktrees + auto-commit).
- The work is one research question — use `run-research`.
- The items have dependencies on each other — sequence them or use a real queue.

## Tool prerequisites

| Tool | Why | Failure mode |
|---|---|---|
| `codex` CLI on `$PATH`, authenticated | Runs each prompt | `codex login` if unauthenticated |
| `Monitor` tool (Claude Code v2.1.98+) | Streams runner events into the conversation | Skill still works without it; you lose live updates |
| `xargs`, `awk`, `wc`, `tail -F` | Parallel runner + watcher | Standard Unix; install GNU coreutils on minimal images |

If `codex` is invoked from a `bash` subshell (which xargs does), it does **not** inherit any zsh function wrapper. Always invoke the binary directly with explicit flags — see `references/codex-cli-flags.md`.

## The six-step workflow

This is a Sequential pattern (Pattern 1) with one Iterative refinement loop (Pattern 3) at Step 6. Show artifacts at each step boundary.

### Step 1 — Define the workspace

Create a working directory and decide on canonical paths. Defaults:

```
<workdir>/
  inputs.txt          # one item per line OR tab-delimited "name<TAB>content"
  template.md         # the prompt template, with placeholder XXXXXXXXXXXXX
  prompts/<name>.md   # generated, one per input
  answers/<name>.md   # codex output, one per input
  logs/<name>.log     # per-job stdout+stderr
  logs/_runner.log    # the runner's STREAM of START/DONE/FAIL/SKIP events
  bin/                # bundled scripts (see Step 3)
```

Confirm with the user before creating. If the workdir already has answers/, treat it as an in-progress batch and respect the skip-existing guard.

### Step 2 — Generate per-input prompt files

Use `scripts/render-prompts.sh`. It reads `inputs.txt` and `template.md`, substitutes the placeholder, and writes one prompt file per input.

Two input formats are supported:

- **Tab-delimited** (`name<TAB>content`): `name` becomes the filename, `content` replaces the placeholder. Use when you control the slug (e.g. domain-derived names from URLs).
- **Plain lines**: each line becomes both the filename slug (sanitised) and the substituted content. Use for short ID lists.

For URL lists like `[label](https://example.com/)`, pre-process to tab-delimited form first (see `references/input-formats.md` for the one-liner). Filename derivation is the user's call — the skill does not invent slugs from arbitrary text.

After this step, show: how many prompt files were written and the first generated filename so the user can verify.

### Step 3 — Stage the runner

Copy `scripts/run-batch.sh` into the workdir's `bin/`. The runner:

- Iterates every `prompts/*.md` and runs `codex exec` per file with `xargs -P $JOBS -n 1 -0`.
- Skips any prompt whose `answers/<name>.md` is already non-empty (idempotent rerun).
- Writes per-job stdout/stderr to `logs/<name>.log`.
- Emits a single line per state transition to `logs/_runner.log`: `START <name>`, `DONE <name>`, `FAIL <name> (see logs/<name>.log)`, `SKIP <name> (...)`, and a final `--- all jobs finished ---`.

Defaults: `JOBS=10`, `MODEL=gpt-5.5`, `EFFORT=medium`. Override via env vars. See `references/runner-script.md` for full anatomy.

### Step 4 — Attach the Monitor BEFORE launching

This is the load-bearing step. The Monitor must be armed before the runner starts so it captures every START event from the first batch wave.

Use `scripts/watch-runner.sh` as the Monitor command. It does `tail -F logs/_runner.log` piped through `awk` that:

- Emits one line per runner event (line-buffered — see `references/monitor-watcher.md` for why this matters).
- For DONE/SKIP events, augments the line with `wc -c` of the corresponding answer file: `DONE foo (18234 bytes)`.
- Flags any answer below `MIN` bytes with ` [SMALL]` so weak outputs surface in real time.
- Covers every terminal state (START / DONE / FAIL / SKIP / `--- all jobs finished ---`) so silence cannot mask a crash.

Invoke as a persistent monitor:

```
Monitor({
  description: "codex batch progress with output sizes",
  command: "bash <workdir>/bin/watch-runner.sh logs/_runner.log answers 10000",
  persistent: true,
  timeout_ms: 300000
})
```

`timeout_ms` is required by the schema but ignored when `persistent: true` — pass `300000` as convention. Stop the monitor explicitly with `TaskStop` when the runner finishes; do not rely on it dying on its own (`tail -F` doesn't exit when the file stops growing).

### Step 5 — Launch the runner

Launch in the background so the conversation stays interactive:

```bash
cd <workdir>
JOBS=10 ./bin/run-batch.sh > logs/_runner.log 2>&1 &
disown
```

Expected behavior:

- The first wave fires `JOBS` START events within ~200 ms — the Monitor batches them into one notification (this is normal).
- Each codex job typically takes 5–15 minutes. With 10-way parallelism, a 60-item batch lands in ~45–75 minutes.
- 2× `codex exec` processes per job (parent + child binary). 10 jobs ≈ 20 codex procs in `pgrep`. Normal.

Do not start a second runner concurrently — the skip-existing guard works at job start, not file-write time, so two runners over the same workdir would race. Wait for the first to finish.

### Step 6 — Audit, then retry the weak ones (iterative)

Once `--- all jobs finished ---` lands, run `scripts/audit-sizes.sh`. It prints:

- Total `DONE` / `FAIL` / `SKIP` counts.
- Per-answer byte size, sorted ascending.
- The bottom decile flagged for review.
- Any answer below the absolute floor (`MIN`, default 10000 bytes).

**Size is a probabilistic quality signal, not a deterministic one.** A small answer can be high-quality if the underlying source was thin (parked domain, niche product). Always read the head of any flagged answer before deciding to retry. Do not auto-retry by size alone — see `references/output-size-signals.md` for the heuristics and `references/retry-strategy.md` for the playbook.

To retry a subset:

```bash
mkdir -p answers/.prev
mv answers/<name>.md answers/.prev/   # archive, don't delete
JOBS=10 ./bin/run-batch.sh > logs/_runner.log 2>&1 &
```

The skip-existing guard auto-handles the rest. Move archived versions back if the retry produces something worse.

## Decision rules

- **Concurrency cap default 10.** Three independent sources converge on 10 (this skill's empirical run, `processing-api-batches`, `pueue` group sizing). Bump only if you've measured and your provider's TPM/RPM allows it.
- **Filename slugs are the user's responsibility.** The skill does not auto-slug arbitrary strings. For URL lists, derive slugs deterministically (domain with dots → hyphens). For ID lists, the ID is the slug.
- **Idempotency is free — use it.** The `[ -s answers/<name>.md ]` guard makes every rerun safe. Never write a runner that overwrites by default.
- **Run the Monitor before the runner, not after.** A monitor armed late misses the first wave's START events and you lose the ability to count what's actually inflight.
- **Codex CLI flags are non-negotiable in subshells.** `command codex --dangerously-bypass-approvals-and-sandbox exec --skip-git-repo-check` — anything less and xargs-spawned bash subshells fail the trusted-dir check. See `references/codex-cli-flags.md`.

## Honest gotchas

1. **Bash subshell loses your zsh codex wrapper.** If `~/.zshrc` defines `codex() { command codex --dangerously-bypass-approvals-and-sandbox "$@" }`, xargs's `bash -c` won't see it and codex aborts with "Not inside a trusted directory." The runner script invokes the binary explicitly with the flags inline. Don't strip them.

2. **`tail -F` outlives the runner.** The Monitor's watcher process keeps tailing the log even after the runner exits. The log stays static, no events fire, but the process lingers. Always `TaskStop` the monitor task when the batch is done.

3. **Output size lies sometimes.** A parked-domain product or a deliberately concise answer can produce a small file that is *correct*. Surface and inspect; don't auto-retry. Conversely, a large file can be a hallucinated wall of text — size is a screening signal, not a quality verdict.

4. **Codex non-determinism.** A retry of the same prompt can produce a smaller output than the original — codex output varies run-to-run. Archive the prior answer (`answers/.prev/`) before retrying so you can compare and revert.

5. **Naming collisions are skipped, not overwritten.** If two inputs slugify to the same name, the render script writes a stderr warning and **skips** the second one — the first file wins, the second is dropped. Disambiguate the input (add a discriminator) before re-rendering, or you'll lose work silently to the skip.

## Output contract

Show the user, in order:

1. The chosen workdir layout (Step 1) — confirm before proceeding.
2. Render summary: `Wrote N prompt files; first: prompts/<example>.md` (Step 2).
3. The Monitor `tool_hint` block they would arm (Step 4).
4. The runner launch command and PID (Step 5).
5. As Monitor events arrive: relay only meaningful ones (DONEs, FAILs, SMALL flags). Don't echo every SKIP.
6. After completion: the audit summary table — total counts, smallest 5 with sizes, recommended retries (or "all sizes look healthy").

## Reference routing

| File | Read when |
|---|---|
| `references/codex-cli-flags.md` | Why `--dangerously-bypass-approvals-and-sandbox` and `--skip-git-repo-check` are required, and what each flag does. |
| `references/runner-script.md` | Full anatomy of `run-batch.sh`, env vars, idempotency guard, exit codes, common modifications. |
| `references/monitor-watcher.md` | The awk filter explained, why `--line-buffered` and `fflush()` matter, how `wc -c` gets injected per event. |
| `references/output-size-signals.md` | When small ≠ bad, the bottom-decile rule, absolute-floor heuristic, false-positive examples. |
| `references/retry-strategy.md` | Idempotency, archive-before-retry, failure classification (transient vs persistent), pueue's "do not auto-retry-all" lesson. |
| `references/input-formats.md` | Pre-processing one-liners for URL lists, ID lists, file lists, plus filename-derivation patterns. |
| `references/anti-patterns.md` | What NOT to do: arming Monitor late, auto-retry-by-size, ignoring SKIP semantics, recursive worktree fanout, runner-without-skip-guard. |

## What's in the bundle

- `scripts/render-prompts.sh` — input list + template → per-input prompt files
- `scripts/run-batch.sh` — bounded-parallel codex runner with idempotent skip
- `scripts/watch-runner.sh` — Monitor command: tail + awk + size injection
- `scripts/audit-sizes.sh` — post-run size distribution and flagging

All scripts are self-contained — copy them into the workdir's `bin/` so the workdir is portable after the skill goes away.

## One-line summary

Template + input list → N parallel codex jobs → live Monitor stream with size-augmented events → audit pass → optional idempotent retry. Read `references/runner-script.md` for the canonical recipe.
