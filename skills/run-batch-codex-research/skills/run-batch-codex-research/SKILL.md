---
name: run-batch-codex-research
description: Use skill if you are fanning out codex or another LLM CLI over a list of inputs in parallel with bounded concurrency, idempotent skip-existing, and per-input retry.
---

# run-batch-codex-research

Fan out one prompt template across N inputs through an LLM CLI (codex, claude, gemini, ollama, …), running with bounded concurrency, writing one answer file per input, skipping inputs whose answer already exists, and retrying only the failed ones. The unit of work is `(template, input) → answers/<slug>.md`.

This skill stays small on purpose. It is the generic, CLI-agnostic batch fanout pattern. If the run is codex-only and needs worktrees, manifests, monitor events, or one of the other codex modes (exec / single / review / rescue), reach for `use-codex` instead.

## When to reach for this skill

Use it if any of these phrases describe the task — *italicized so the agent matches them at trigger time*:

- *"run codex over each URL in `urls.txt`"*, *"for each input in this list, run the prompt"*, *"fan out the template across N IDs"*
- *"batch this prompt over a CSV of items"*, *"one answer file per row"*
- *"parallel research across many topics"*, *"do this for every entry and save the output"*
- *"resume the batch — retry just the ones that failed"*, *"idempotent, skip already-done inputs"*
- *"swap codex for claude / gemini / ollama and re-run the same batch"*
- *"limit to N concurrent CLI processes"*, *"don't melt my machine, cap at 8 jobs"*

Do **NOT** use this skill when:

| Situation | Use instead |
|---|---|
| One discrete codex invocation, no list. | `run-codex-exec` (deprecated compat shim → `use-codex` exec mode) |
| One technical research question, web search, single Markdown synthesis. | `run-research` |
| 5+ entities × multiple axes, multi-file evidence corpus, per-entity packs, cross-entity comparisons. | `run-corpus-research` (or `run-industry-research`) |
| Codex-only fleet with worktrees, manifests, Monitor events, or rescue mode. | `use-codex` |

The trigger shape: **a list of inputs + a prompt template + an LLM CLI on PATH**. If any of the three is missing, this is not the right skill.

## Load-bearing rules (read before drafting any command)

| # | Rule | Why |
|---|---|---|
| 1 | One answer file per input. Path: `<workdir>/answers/<slug>.md`. Slug = deterministic from input. | Idempotent skip-existing depends on a stable filename map. |
| 2 | **Skip-existing is the default retry strategy.** Re-running the batch never overwrites a non-empty answer file. | Resume after partial failure costs zero, by construction. |
| 3 | The template **must** contain a single placeholder token; never inline the input by string concat. | Prevents quoting bugs and shell injection across CLIs. |
| 4 | Concurrency is bounded — never naked `&` fanout, never `xargs -P 0`. Default cap: 8. | Unbounded fan-out exhausts API quotas and OS file handles. |
| 5 | Every CLI process gets its own rendered prompt file under `<workdir>/prompts/<slug>.md`. | Stable on-disk artifact for debugging, reruns, and audit. |
| 6 | Per-job log → `<workdir>/logs/<slug>.log`. STDERR redirected. Never piped into the answer file. | Keeps the answer file clean and machine-parseable downstream. |
| 7 | Retry policy is **only over `failed` and `never-started`**. `done` inputs are never retried automatically. | "Done" must mean done; otherwise idempotency lies. |
| 8 | An empty (0-byte) or whitespace-only answer file is **not** done — it is `failed`. | Prevents silent truncation from reading as success. |
| 9 | The CLI command is parameterized once and reused for every input. Override only via env var, never per-input flags. | Per-input flag drift defeats reproducibility. |
| 10 | A run is identified by a `run_id` (UTC compact + short hash). Workdir defaults to `./batch-runs/<run_id>/`. | Multiple runs in the same repo never collide. |

If any rule is violated, the run is no longer idempotent and the rest of this skill stops applying.

## CLI surface

This skill is CLI-agnostic. The same workflow drives any LLM CLI that reads a prompt and prints an answer to stdout. Pick one before starting.

| CLI | Read prompt from | Where the answer ends up | Notes |
|---|---|---|---|
| `codex exec` | positional arg or stdin | stdout (use `-o <file>` for JSON-MCP fallback) | Pass `--skip-git-repo-check` and a sandbox flag if running outside a git repo. |
| `claude -p` | stdin (`echo "$prompt" \| claude -p`) | stdout | Headless mode; no interactive harness. |
| `gemini` / `gemini-cli` | stdin or `--prompt-file` | stdout | Confirm flag with `--help`; vendor flags drift. |
| `ollama run <model>` | stdin | stdout | Local model; concurrency cap is bound by GPU/RAM, not API quota. |
| Other (`mistral`, `cohere`, custom wrapper) | varies | stdout | Verify the CLI is non-interactive in headless mode before fanning out. |

The decisive choice: pick the CLI **once**, before drafting the runner. Mid-run CLI swap means a new `run_id` and a new workdir.

## Workdir layout

Every batch run produces this exact tree. Treat it as a contract — downstream tools (audit, retry, archive) depend on the names.

```
<workdir>/
├── run.json              # run_id, cli, template_path, concurrency, started_at, finished_at
├── inputs.txt            # canonical input list (one per line, deduped, slugged)
├── template.md           # the prompt template, copied at run start (frozen)
├── prompts/<slug>.md     # rendered prompt per input
├── answers/<slug>.md     # final answer per input — the only file that matters downstream
├── logs/<slug>.log       # per-job stdout/stderr (clipped if > 1 MB)
├── status/<slug>.status  # one of: queued | running | done | failed | skipped
└── audit.txt             # post-run report: counts, sizes, outliers
```

Why this layout: every job has four siblings under the same slug — prompt, answer, log, status. A reviewer can walk `answers/`, hit a suspicious entry, and pivot to `logs/<slug>.log` and `prompts/<slug>.md` without searching.

## The seven steps

Every batch run follows this exact sequence. Skip a step only if its artifact already exists from a prior run with the same `run_id`.

### 1. Resolve inputs

Inputs come from a file (`inputs.txt`, `urls.txt`, `*.csv`) or from a list the user pastes inline. Normalize:

- One input per line.
- Trim whitespace; drop blank lines and `#`-prefixed comments.
- Deduplicate — duplicate inputs render to the same slug and clobber each other.
- Generate a stable slug per input: lowercase, alphanumerics + dashes, max 64 chars, suffix with `-<6-hex>` of the original string when the natural slug collides.

Write the canonical list to `<workdir>/inputs.txt`. If the source was a CSV, the canonical list contains *just the input column*; the CSV itself is preserved alongside as `inputs.csv` for traceability.

### 2. Freeze the template

Copy the template to `<workdir>/template.md`. The placeholder token is one of:

- `{{INPUT}}` — preferred default
- `XXXXXXXXXXXXX` — legacy, accepted
- A user-named token surfaced once at run start

If the template contains zero placeholders or more than one distinct placeholder, **stop and surface** before fanning out. Render time is the wrong place to discover a malformed template.

### 3. Render prompts

For each input, write `<workdir>/prompts/<slug>.md` by string-substituting the placeholder with the input. No shell quoting tricks; render in-process and write to disk. The renderer is idempotent — re-running it overwrites prompt files but never the answer files.

### 4. Plan concurrency

| Default cap | Override | Hard ceiling |
|---|---|---|
| 8 | env `BATCH_CONCURRENCY=N` or `--concurrency N` | 32 |

Above 32, refuse and ask. Concurrency this high is almost always a misconfigured retry loop, not a real workload.

The runner is a bounded worker pool. The two acceptable shapes:

- `xargs -n1 -P "$N"` reading slugs from stdin
- A small Python/Node script with a semaphore of size `N`

Forbidden: naked `&` fanout, `parallel --jobs 0`, recursive `xargs -P` from inside a job.

### 5. Run with skip-existing

For each slug, the worker function is exactly this contract:

```
worker(slug):
  if exists(answers/<slug>.md) and size(answers/<slug>.md) > 0:
      write status/<slug>.status = "skipped"
      log one line and return
  write status/<slug>.status = "running"
  run CLI with prompts/<slug>.md, capture stdout to answers/<slug>.md.tmp,
      stderr to logs/<slug>.log
  if CLI exited non-zero OR answers/<slug>.md.tmp is empty:
      write status/<slug>.status = "failed"; keep .tmp for forensics; return
  atomic rename .tmp -> answers/<slug>.md
  write status/<slug>.status = "done"
```

Atomic rename is non-negotiable. Without it, a crashed CLI can leave a partial answer file that future runs will skip.

### 6. Audit before declaring done

After the runner exits, walk `answers/` and emit `<workdir>/audit.txt`:

| Section | What it shows |
|---|---|
| Counts | `done`, `failed`, `skipped`, `never-started` (status file missing) |
| Size distribution | min, p10, p50, p90, max bytes |
| Below-floor list | answer files smaller than `MIN_BYTES` (default 200) — flagged, not auto-failed |
| Empty-status list | inputs whose `status/<slug>.status` is missing entirely |

A run is **complete** only when `failed + never-started == 0`. Below-floor entries are surfaced for human review; they do not auto-retry, because "small" sometimes means "the right answer is short".

### 7. Retry only failures and never-started

Re-running the batch with the same `run_id` and `<workdir>` is the canonical retry. Skip-existing means `done` and `skipped` entries are no-ops; `failed` and missing-status entries re-render their prompt and re-run the CLI.

To force-retry a specific slug, archive its answer first:

```
mv answers/<slug>.md answers/.prev/<slug>.md.<timestamp>
rm status/<slug>.status
```

Never delete an answer file in place. Archive-before-overwrite preserves forensics.

## Single-CLI command shape

Every CLI invocation is wrapped in the same shell:

```
timeout "${BATCH_TIMEOUT:-1500}" \
  "$CLI_BIN" $CLI_FLAGS \
  < prompts/<slug>.md \
  > answers/<slug>.md.tmp \
  2> logs/<slug>.log
```

Defaults:

- `BATCH_TIMEOUT=1500` (25 min). Hung CLIs land in `failed` instead of stalling the pool.
- `CLI_BIN` and `CLI_FLAGS` are exported once at run start, sourced from `<workdir>/run.json`.
- The `< prompt > answer 2> log` redirection shape is identical across CLIs; only `CLI_BIN` and `CLI_FLAGS` change.

If a CLI does not accept stdin (rare), wrap it: write the prompt to a tempfile in `prompts/`, pass `--prompt-file prompts/<slug>.md`, route stdout the same way.

## Failure-mode taxonomy

Every observed failure maps to one of these. If the symptom does not match a row, **stop and diagnose** before retrying — blind retry on an unknown failure mode amplifies damage.

| # | Failure | Signal | First-line response |
|---|---|---|---|
| 1 | Quota / rate-limit (HTTP 429, 503) | log says rate-limit, exit code non-zero | Wait, then re-run; skip-existing protects done entries. |
| 2 | Hung process | wall-clock hits `BATCH_TIMEOUT` | Worker kills via `timeout`, marks `failed`. Investigate one log before mass retry. |
| 3 | Empty answer | `.tmp` is 0 bytes after exit 0 | Marked `failed`. Read the log; the CLI usually printed an error to stderr. |
| 4 | Truncated answer | size below `MIN_BYTES` | Surfaced in audit, not auto-retried — human inspects. |
| 5 | CLI not found | `command not found` in worker startup | Stop entire run; `CLI_BIN` is wrong, retry will not help. |
| 6 | Workdir clash | second run picks the same `run_id` | Refuse to start; pick a new `run_id`. |
| 7 | Template malformed | zero or multiple distinct placeholders | Stop at render step, before fanout. |
| 8 | Disk full | render or rename fails with ENOSPC | Stop; clear space; resume — skip-existing makes resume free. |

## Anti-patterns

- Never overwrite an answer file in place. Archive to `answers/.prev/<slug>.md.<timestamp>`, then re-run.
- Never `cat prompt | cli | tee answer` — `tee` swallows the exit code; failures look like successes.
- Never inline the input via shell substitution (`$(echo "$INPUT")`). Render in-process, write a prompt file, redirect stdin.
- Never run the CLI without `timeout`. One hung process stalls the entire pool's slot until you notice manually.
- Never raise `BATCH_CONCURRENCY` past 32 without a measured reason. The bottleneck is almost never CPU.
- Never mix two LLM CLIs in one `run_id`. The audit row's `cli` field becomes meaningless.
- Never auto-retry below-floor entries. "Short" and "wrong" are different failure modes.
- Never read `logs/*.log` as the source of truth. The answer file is canonical; logs are forensics.
- Never edit `inputs.txt` mid-run. Append-only changes belong in a new run, not the active one.
- Never collapse `prompts/`, `answers/`, `logs/` into one directory to "save space". The four-files-per-slug invariant is what makes audit and retry tractable.

## Differentiation cheat sheet

| Skill | Trigger | Why not this skill |
|---|---|---|
| `run-codex-exec` | one codex task in the current repo | single invocation, no list, no fanout |
| `run-research` | one technical question + web search | single-question synthesis, not template×inputs |
| `run-corpus-research` | 5+ entities, multi-axis evidence corpus | corpus orchestration via subagents, not a CLI fanout |
| `use-codex` | codex-only fleet, worktrees, Monitor events, manifest, rescue mode | full codex runtime contract; this skill is the lighter CLI-agnostic cousin |

If the request says "codex" plus "worktree" or "manifest" or "Monitor", route to `use-codex`. If it just says "run this prompt over each item in the list," stay here.

## Bottom line

Resolve inputs → freeze template → render prompts → plan concurrency → run with skip-existing → audit → retry only failures. Every step writes a stable artifact under `<workdir>/`. Idempotency is a side effect of the layout, not a feature you have to remember to enable.
