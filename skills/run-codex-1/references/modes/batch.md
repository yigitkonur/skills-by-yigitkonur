# Batch mode — template × N inputs, no worktrees

Run one prompt template over N input rows in parallel, with bounded concurrency, idempotent skip-existing, and an output-size audit at the end. The work is research, summarization, generation — not coding inside a repo.

## Contents

- When to pick batch mode
- Inputs
- Render contract
- Runner behavior
- Output-size audit
- Retry and rescue

## When to pick batch mode

- ≥ 5 input rows (under that, just loop).
- The same prompt template applies to every input with one substitution.
- Each input is independent (no cross-input dependencies).
- The work is research / summary / generation — not git-bound.

When to skip:
- < 5 inputs → loop directly.
- Coding inside a repo → exec mode (worktrees + auto-commit).
- One research question → `run-research` skill.

## Inputs

A workdir laid out:

```
<workdir>/
├── inputs.txt          # tab-delimited (name<TAB>content) OR plain lines
├── template.md         # the prompt template, with placeholder XXXXXXXXXXXXX
├── prompts/            # generated under the run state dir by render-prompts.sh
│   └── <slug>.md
├── answers/            # codex output, one per input
│   └── <slug>.md
└── logs/               # per-job stdout+stderr captured here
    ├── <slug>.log      # codex stdout (combined w/ stderr) — one per input
    └── <slug>.jsonl    # parallel JSONL stream when codex was invoked with --json
```

`manifest.json` lives under `resolveStateDir(cwd)/run-codex-1/`, not in the workdir.

The dispatcher's runner stdout/stderr are redirected to `${monitor_root}/logs/<run_id>/_runner.log` (see `spawnRunnerDetached` in `scripts/run-codex-1.mjs`); that file lives under the state dir, **not** the workdir. Per-job artifacts (`logs/<slug>.log`, manifest entry rows) are the primary observability path; the Monitor tail target is the manifest, not a runner log.

Two input formats:

| Format | Shape | Slug derivation | Use when |
|---|---|---|---|
| Tab-delimited | `name<TAB>content` per line | `name` becomes the slug | URL lists where you derive deterministic slugs upstream |
| Plain lines | one line per input | line becomes both slug and content (sanitized) | short ID lists |

### Dispatcher flags

`node run-codex-1.mjs batch` accepts the following flags (`handleBatch` in `scripts/run-codex-1.mjs:1413`). Value options: `inputs`, `template`, `concurrency`, `cwd`, `monitor-root`, `run-id`, `answers-dir`, `i-have-measured`, `force-redo`. Boolean options: `force-redo-all`, `force-new-run`, `dry-run`.

| Flag | Default | When to set it |
|---|---|---|
| `--inputs <file>` | required | path to `inputs.txt` (relative to `--cwd`) |
| `--template <file>` | required | path to `template.md` (relative to `--cwd`) |
| `--cwd <dir>` | `process.cwd()` | workspace root; affects relative-path resolution and the manifest's `state` directory |
| `--answers-dir <dir>` | `<cwd>/answers` | where to write `answers/<slug>.md`. Override when you want outputs alongside your workdir instead of nested under `<cwd>/answers/` — e.g. `--answers-dir /Users/me/research/parked-domain-survey/out` keeps the deliverables in your project tree while the manifest lives under `<state>/run-codex-1/`. |
| `--concurrency N` | `10` | parallelism (above 20 requires `--i-have-measured`; hard cap 100) |
| `--i-have-measured "<text>"` | unset | required when `--concurrency > 20`; the text is recorded on the manifest |
| `--monitor-root <dir>` | `<state>/run-codex-1/<run_id>` | where prompts/, logs/ and the runner log land |
| `--run-id <id>` | auto-generated | reuse to resume / inspect a prior run |
| `--force-new-run` | off | requires `--run-id <custom>`; writes to a per-run manifest path instead of the shared one |
| `--force-redo <slug,…>` | unset | archive `answers/<slug>.md` to `.prev/`, flip the entry to `queued`, re-spawn |
| `--force-redo-all` | off | same as above, every entry |
| `--dry-run` | off | runner prints planned commands and writes stub artifacts; no codex spawn |

### Two slug spaces

Batch mode has **two intentional slug naming conventions** that operators must keep straight:

- **Bare slug** (default) — what both `bash render-prompts.sh inputs.txt template.md prompts/` and the dispatcher's `buildBatchEntries` produce. The first field of each input is sanitized (`slugify(firstField)` in `scripts/run-codex-1.mjs:589`; `tr`-equivalent in `render-prompts.sh:64`) and used directly as the entry id and `prompts/<slug>.md` filename. No prefix, no index — `acme-corp`, `globex`, etc.
- **`row-NNN` fallback** — only when the first-field slug is empty after sanitization (e.g. an all-symbols input). The dispatcher falls back to `row-001`, `row-002`, …; `render-prompts.sh` hard-fails on empty slugs instead. The fallback is a safety net, not the default shape.

Both code paths agree on the bare-slug naming, so pre-rendering with `render-prompts.sh` and then invoking the dispatcher produces consistent filenames — provided your inputs sanitize to non-empty slugs.

## Pre-flight

1. `inputs.txt` exists and is non-empty.
2. `template.md` exists and contains the literal `XXXXXXXXXXXXX` placeholder.
3. `render-prompts.sh inputs.txt template.md prompts/` runs cleanly. **Slug collisions are a hard fail** — `render-prompts.sh:71-74` exits 1 the moment the second input would write the same `<slug>.md`. The dispatcher's `buildBatchEntries` likewise rejects duplicate rendered slugs with `bad_inputs_file`. Disambiguate the input (add a discriminator) before dispatching.
4. `answers/` and `logs/` directories exist (created by render).
5. `codex login status` — warn unless `~/.codex/config.toml` declares no `model_provider`. Some setups (vendored OpenAI key, ChatGPT subscription, custom auth shim) leave login-status non-zero even when `codex exec` works. Soft warning, not a hard fail.

## Per-input spawn flow

`run-batch.sh` fans out via `xargs -P "$JOBS" -n 1` over `prompts/*.md`. Each invocation:

```bash
# 1. Skip-existing guard.
if [ -s "answers/$slug.md" ]; then
    echo "SKIP $slug (already done)"
    exit 0
fi

# 2. Mark entry running.
python3 manifest-update.py entry --manifest "$MANIFEST" --entry "$slug" \
    --set 'status=running' --set "started_at=$(date -u ...)"

# 3. Spawn codex with the universal flag set + per-spawn additions.
. codex-flags.sh
tmp="$(mktemp -t answers-$slug.XXXXXX)"
echo "START $slug"

codex exec "${CODEX_FLAGS[@]}" \
    --json \
    -o "$tmp" \
    < "$prompt_file" \
    > "logs/$slug.jsonl" 2>&1
CODEX_EXIT=$?

# 4. Atomic answer move (only after codex returns 0 AND tmp is non-empty).
if [ "$CODEX_EXIT" = "0" ] && [ -s "$tmp" ]; then
    mv -f "$tmp" "answers/$slug.md"
    bytes=$(wc -c < "answers/$slug.md")
    echo "DONE $slug ($bytes bytes)$([ $bytes -lt $MIN_BYTES ] && echo ' [SMALL]')"
    # mode_state.answer_size_bytes (the byte count) and mode_state.below_floor
    # (true when bytes < MIN_BYTES) are written alongside status/finished_at/
    # exit_code via manifest-update.sh entry (run-batch.sh:281-289). The
    # `audit-sizes.sh` step after `--- all jobs finished ---` is still the
    # cross-fleet bottom-decile + below-floor surface (see Audit section).
    python3 manifest-update.py ... --set 'status=done' --set "exit_code=0"
else
    rm -f "$tmp"
    echo "FAIL $slug (codex_exit=$CODEX_EXIT, see logs/$slug.log)"
    python3 manifest-update.py ... --set 'status=failed' --set "exit_code=$CODEX_EXIT" \
        --set "last_error=codex_failed_or_empty_output"
fi
```

After all entries process: `echo "--- all jobs finished ---"`.

## Why pair `--json` with `-o`

The MCP-active dropout issue ([#15451](https://github.com/openai/codex/issues/15451)) silently drops events from the `--json` stream when MCP servers are configured in the user's codex. The `-o` file is unaffected — codex always writes the final agent message there. The runner reads the `-o` file as truth for "did codex produce output." The JSONL stream is supplementary.

If the user has no MCP servers configured, the JSONL stream contains everything and `-o` is redundant insurance. The cost is one tiny file per entry.

## Atomic answer move

The `mv -f tmp answers/<slug>.md` only happens after codex exits 0 AND the tmp is non-empty. This is the idempotency anchor:

- Re-running the runner over the same workdir skips entries with non-empty `answers/<slug>.md`.
- Partial-write protection: a crashed codex never leaves a half-written `answers/<slug>.md`.
- If the temp file is empty (codex bailed without writing), the runner deletes the temp and marks failure; the answer file does not appear.

## Audit after `--- all jobs finished ---`

Prefer the manifest-aware invocation — it picks up the dispatcher's `--answers-dir <override>` automatically. The dispatcher's batch envelope surfaces the exact command in `result.post_run_audit_cmd`:

```bash
bash audit-sizes.sh --manifest <state-dir>/run-codex-1/manifest.json
```

The legacy positional form is preserved for direct/standalone use:

```bash
bash audit-sizes.sh answers/ "${MIN_BYTES:-10000}"
```

Use `--manifest` whenever the run was dispatched through `node scripts/run-codex-1.mjs batch`. The positional form defaults `<answers-dir>` to `./answers/` and silently inspects the wrong directory when the operator passed `--answers-dir <override>` to the dispatcher (D2 silent-failure path).

**Note:** `node scripts/run-codex-1.mjs audit` (the dispatcher's audit subcommand) wraps `audit-fleet-state.py`, which inspects manifest-vs-filesystem drift but does NOT read answer-file sizes beyond presence/non-emptiness. For batch fleets, run `bash scripts/audit-sizes.sh <answers-dir>` separately — a 50-byte truncated answer reports clean under `audit` but flags `[SMALL]` here. The two auditors are deliberately split; the operator must run both.

`audit-sizes.sh` prints:
- Total `DONE / FAIL / SKIP` counts derived from the `answers/` and `logs/` dirs.
- Per-answer byte size, sorted ascending.
- Bottom decile flagged for review.
- Any answer below `MIN_BYTES` flagged.

**Size is a probabilistic quality signal, not a deterministic one.** A small answer can be high-quality if the input was thin (parked domain, niche product, deleted resource). Always read the head of any flagged answer before deciding to retry. Read `references/universal/output-size-signals.md` for the heuristics.

### Calibrating MIN_BYTES per task type

The default `MIN_BYTES=10000` is calibrated for research and long summarization. Other task shapes need different floors:

| Task type | Suggested MIN_BYTES |
|---|---|
| Research / long summary | 10000 (default) |
| Code review / audit narrative | 5000 |
| Error remediation note / triage | 800–2000 |
| One-line structured output (JSON, classification) | 100–500 |

Set the env var BEFORE invoking the dispatcher: `MIN_BYTES=2000 node <skill-root>/scripts/run-codex-1.mjs batch ...`. The dispatcher forwards the value to the runner via `spawnRunnerDetached` (which inherits `process.env`). See the `1:N output` section for per-bucket `MIN_BYTES` examples.

## Concurrency

Default `JOBS=10`. Tuned for codex-cli current TPM/RPM caps with gpt-5.5 + xhigh; raise via env var or `--concurrency N` (see "Standalone runner" below):

```bash
JOBS=15 PROMPTS=./prompts ANSWERS=./answers LOGS=./logs \
    bash run-batch.sh
```

Above 20, the soft gate kicks in via the **dispatcher** (`--i-have-measured` flag on `node run-codex-1.mjs batch`). The standalone runner just warns and proceeds. The recommended approach is to measure single-job latency first (one entry, see how long it takes), then divide your TPM budget by per-job token consumption to find the sustainable rate.

## Standalone runner

`run-batch.sh` accepts **both env-style and flag-style invocation**. Flags win when both are given. The full set:

| Flag | Env var | Default | Meaning |
|---|---|---|---|
| `--concurrency N` / `--jobs N` | `JOBS` | `10` | parallel concurrency (warns above 20; hard cap 100; above 20 requires `--i-have-measured`) |
| `--prompts-dir <p>` / `--prompts <p>` | `PROMPTS` | `./prompts` | input prompts dir |
| `--answers-dir <a>` / `--answers <a>` | `ANSWERS` | `./answers` | output answers dir |
| `--logs-dir <l>` / `--logs <l>` | `LOGS` | `./logs` | per-job log dir |
| `--manifest <m>` | `ORCHESTRATE_MANIFEST` | unset | path to `manifest.json`; runner writes status / size / below_floor here |
| `--min-bytes N` | `MIN_BYTES` | `10000` | `[SMALL]` flag threshold; recorded as `mode_state.below_floor` |
| `--only id,id` | `ONLY_IDS` | unset | restrict the run to a comma-separated subset of slugs (per-job filter; non-matching prompts are skipped silently) |
| `--runner-log <file>` | `RUNNER_LOG` | unset | optional out-of-band runner-log path (the runner does NOT tee here; the dispatcher binds stdio to this fd) |
| `--audit-report <file>` | `AUDIT_REPORT` | unset | post-run, write `audit-sizes.sh` output to this file |
| `--i-have-measured "<text>"` | `ORCHESTRATE_CONCURRENCY_JUSTIFICATION` | unset | required justification when `JOBS > 20` |
| `--dry-run` | `DRY_RUN=1` | `0` | print planned commands and stub artifacts; do not invoke codex |
| `--inputs <f>` / `--template <f>` | n/a | n/a | accepted-and-ignored (these are dispatcher render-time concerns; the runner consumes already-rendered prompts) |

Single-entry retry can use either filesystem manipulation or `--only`:

```bash
# Filesystem path: drop the answer + log, then re-run.
rm -f answers/<slug>.md logs/<slug>.log
JOBS=1 bash run-batch.sh --prompts-dir ./prompts --answers-dir ./answers --logs-dir ./logs

# Flag path: restrict to one slug (skip-existing still applies, so archive first).
mkdir -p answers/.prev && mv answers/<slug>.md answers/.prev/
bash run-batch.sh --prompts-dir ./prompts --answers-dir ./answers --logs-dir ./logs \
    --only <slug> --concurrency 1
```

## Retry / rescue

A batch retry of all FAILed entries:

```bash
node run-codex-1.mjs rescue --manifest <path>
# Pick "redo failures only". (Today this is read-only classification; see
# rescue.md — manual redispatch may be required.)
```

The skip-existing guard handles the rest: `answers/<slug>.md` non-empty → `SKIP`.

To re-run an entry that's already `done` (you want a different output):

```bash
mkdir -p answers/.prev
mv answers/<slug>.md answers/.prev/
# Then re-invoke run-batch.sh (env-var form above) or rescue.
```

**Never delete `.prev/`** until you've confirmed the new answer is acceptable. Codex non-determinism means a retry can produce a smaller (or larger but worse) output than the original.

## 1:N output (multi-invoke pattern)

Batch is **1:1 by design**: one input row produces one answer file at `answers/<slug>.md`. There is no first-class flag for fan-out (e.g. one input × N output buckets). For a 1:N shape — translate 50 source strings into 4 target languages (200 outputs), generate 3 length variants per article, render each input in 5 visual styles — invoke batch **N times**, once per output bucket, each with its own `--answers-dir` and its own per-run manifest.

Each invocation gets:
- `--answers-dir <bucket>/` so the buckets do not collide on `answers/<slug>.md`.
- `--force-new-run --run-id <bucket-tag>` so each bucket gets `manifest.<run-id>.json` and an isolated audit trail. Without `--force-new-run`, all invocations share the default per-cwd manifest path and the second invocation's entries either overwrite or skip-existing the first invocation's.

Canonical 4-language translation example:

```bash
for lang in en es ja tr; do
    node run-codex-1.mjs batch \
        --inputs strings.txt \
        --template translate-${lang}.md \
        --answers-dir i18n/${lang} \
        --force-new-run --run-id translate-${lang}
done
```

Each bucket runs to completion in series (the loop is sequential); within each bucket the dispatcher's normal concurrency applies. Rendering 4 separate templates is the simplest path; if the only per-bucket variable is the language tag, build the templates from a shared base in the same script. Audit each bucket independently — the per-run manifest is what `audit-fleet-state.py` and `audit-sizes.sh` operate on.

Per-bucket `MIN_BYTES`: the dispatcher does not expose `--min-bytes`; only the standalone `run-batch.sh` does (see flag table above). To set heterogeneous size floors per bucket, prefix each dispatcher call with `MIN_BYTES=<N>` as an env var — `spawnRunnerDetached` inherits the parent env and forwards it to the runner (`run-batch.sh:94`). For example: `MIN_BYTES=200 node run-codex-1.mjs batch --run-id julia-bucket … ; MIN_BYTES=1500 node run-codex-1.mjs batch --run-id notes-bucket …`.

Do not try to encode the output dimension into the slug (`<input>-en`, `<input>-es`, …) inside one run. That makes one logical row produce N entries with N different slugs, defeats the skip-existing guard per-language, and pollutes the per-run manifest with entries that share an input but differ in a hidden axis.

## Anti-patterns

- Auto-retry-by-size. Codex output varies; surface and inspect, never auto-retry.
- Two runners on the same workdir. Race on the skip-existing guard. The dispatcher refuses concurrent runs.
- Treating slug collisions as warnings. Two inputs that sanitize to the same slug make `render-prompts.sh` exit 1 (and the dispatcher reject the inputs file). Disambiguate the input row before dispatch — there is no recovery path mid-run.
- `tail -F` outliving the runner. The Monitor's tail process keeps tailing the manifest path (or a per-job log) after the runner exits. The file stays static, no events fire, but the process lingers. Always `TaskStop` the Monitor once every entry reaches a terminal status. (There is no `_runner.log` to tail — see workdir layout above.)
- `MIN_BYTES` set so high that every entry flags. The threshold should match prompt-shape expectations. Recalibrate per template.
- One template doing N research types. If your inputs are heterogeneous (some URLs, some IDs, some product names), they probably want N templates. Render and run separately.

Full failure-mode taxonomy: `references/universal/failure-modes.md`.
