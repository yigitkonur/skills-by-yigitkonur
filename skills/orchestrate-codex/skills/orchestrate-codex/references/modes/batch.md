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

`manifest.json` lives under `resolveStateDir(cwd)/orchestrate-codex/`, not in the workdir.

The dispatcher's runner stdout/stderr are redirected to `${monitor_root}/logs/<run_id>/_runner.log` (see `spawnRunnerDetached` in `scripts/orchestrate-codex.mjs`); that file lives under the state dir, **not** the workdir. Per-job artifacts (`logs/<slug>.log`, manifest entry rows) are the primary observability path; the Monitor tail target is the manifest, not a runner log.

Two input formats:

| Format | Shape | Slug derivation | Use when |
|---|---|---|---|
| Tab-delimited | `name<TAB>content` per line | `name` becomes the slug | URL lists where you derive deterministic slugs upstream |
| Plain lines | one line per input | line becomes both slug and content (sanitized) | short ID lists |

### Two slug spaces

Batch mode has **two intentional slug naming conventions** that operators must keep straight:

- **Bare slug** — what `bash render-prompts.sh inputs.txt template.md prompts/` produces. The first field of each input is sanitized (`tr -c 'a-zA-Z0-9._-' '-'`) and used directly as `prompts/<slug>.md`. No prefix, no index. Use this path when you're driving `run-batch.sh` standalone (env-var invocation; see "Standalone runner" below).
- **`NNN-` prefixed slug** — what the dispatcher's `buildBatchEntries` generates. Each entry is keyed by `<NNN>-<sanitized-first-field>` (e.g. `001-acme-corp`, `002-globex`); the dispatcher's own `renderBatchPromptFiles` writes prompt files under that NNN-prefix. Use this path when you're invoking `node orchestrate-codex.mjs batch ...`.

The two paths are not interchangeable. If you pre-render with `render-prompts.sh` and then invoke the dispatcher, the dispatcher will overwrite your bare-slug prompts with NNN-prefixed ones (different filenames). Pick one slug space per workflow and stick to it.

## Pre-flight

1. `inputs.txt` exists and is non-empty.
2. `template.md` exists and contains the literal `XXXXXXXXXXXXX` placeholder.
3. `render-prompts.sh inputs.txt template.md prompts/` runs cleanly. If it warns about slug collisions, **resolve before launching** — the second collider gets silently dropped otherwise.
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
python3 manifest-update.py --manifest "$MANIFEST" --entry "$slug" \
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
    # Note: mode_state.answer_size_bytes / mode_state.below_floor are
    # **Planned — not yet wired** in run-batch.sh; the runner only writes
    # status / finished_at / exit_code today. For size-flag flow, run
    # `bash audit-sizes.sh` after `--- all jobs finished ---` (see Audit
    # section below).
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

```bash
bash audit-sizes.sh answers/ "${MIN_BYTES:-10000}"
```

(Earlier drafts of this doc referenced a `logs/_runner.log` argument; that file does not exist — the runner's stdout is discarded by `spawnRunnerDetached`. Read `audit-sizes.sh --help` for current arguments.)

`audit-sizes.sh` prints:
- Total `DONE / FAIL / SKIP` counts derived from the `answers/` and `logs/` dirs.
- Per-answer byte size, sorted ascending.
- Bottom decile flagged for review.
- Any answer below `MIN_BYTES` flagged.

**Size is a probabilistic quality signal, not a deterministic one.** A small answer can be high-quality if the input was thin (parked domain, niche product, deleted resource). Always read the head of any flagged answer before deciding to retry. Read `references/universal/output-size-signals.md` for the heuristics.

## Concurrency

Default `JOBS=10`. Tuned for codex-cli current TPM/RPM caps with gpt-5.5 + xhigh; raise via env var, not a flag (the runner parses no flags — see "Standalone runner" below):

```bash
JOBS=15 PROMPTS=./prompts ANSWERS=./answers LOGS=./logs \
    bash run-batch.sh
```

Above 20, the soft gate kicks in via the **dispatcher** (`--i-have-measured` flag on `node orchestrate-codex.mjs batch`). The standalone runner just warns and proceeds. The recommended approach is to measure single-job latency first (one entry, see how long it takes), then divide your TPM budget by per-job token consumption to find the sustainable rate.

## Standalone runner

`run-batch.sh` parses **no command-line flags** — it reads everything from environment variables:

| Env var | Default | Meaning |
|---|---|---|
| `JOBS` | `10` | parallelism |
| `PROMPTS` | `./prompts` | input prompts dir |
| `ANSWERS` | `./answers` | output answers dir |
| `LOGS` | `./logs` | per-job log dir |
| `DRY_RUN` | `0` | `1` → print planned commands, no codex spawn |
| `ORCHESTRATE_MANIFEST` | unset | optional path to manifest.json for status writes |

There is no `--only <slug>`, no `--manifest`, no `--prompts-dir` — earlier drafts of this doc named flags that don't exist. Single-entry retry happens via the skip-existing guard plus filesystem manipulation:

```bash
# Force one slug to retry: remove its answer + log, then re-run with JOBS=1.
rm -f answers/<slug>.md logs/<slug>.log
JOBS=1 PROMPTS=./prompts ANSWERS=./answers LOGS=./logs \
    bash run-batch.sh
```

Flag-style invocation (`bash run-batch.sh --manifest ... --prompts-dir ...`) is **Planned — not yet wired**. Use the env-var form above.

## Retry / rescue

A batch retry of all FAILed entries:

```bash
node orchestrate-codex.mjs rescue --manifest <path>
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

## Anti-patterns

- Auto-retry-by-size. Codex output varies; surface and inspect, never auto-retry.
- Two runners on the same workdir. Race on the skip-existing guard. The dispatcher refuses concurrent runs.
- Naming-collision drop without resolving. Two inputs render to the same slug → second is silently skipped at render time. Always resolve before launching.
- `tail -F` outliving the runner. The Monitor's tail process keeps tailing the manifest path (or a per-job log) after the runner exits. The file stays static, no events fire, but the process lingers. Always `TaskStop` the Monitor once every entry reaches a terminal status. (There is no `_runner.log` to tail — see workdir layout above.)
- `MIN_BYTES` set so high that every entry flags. The threshold should match prompt-shape expectations. Recalibrate per template.
- One template doing N research types. If your inputs are heterogeneous (some URLs, some IDs, some product names), they probably want N templates. Render and run separately.

Full failure-mode taxonomy: `references/universal/failure-modes.md`.
