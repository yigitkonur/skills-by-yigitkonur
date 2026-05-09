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
├── logs/               # per-job stdout+stderr + the runner log
│   ├── <slug>.log
│   ├── <slug>.jsonl
│   └── _runner.log
└── manifest.json       # the orchestrate-codex manifest (under resolveStateDir(cwd))
```

Two input formats:

| Format | Shape | Slug derivation | Use when |
|---|---|---|---|
| Tab-delimited | `name<TAB>content` per line | `name` becomes the slug | URL lists where you derive deterministic slugs upstream |
| Plain lines | one line per input | line becomes both slug and content (sanitized) | short ID lists |

## Pre-flight

1. `inputs.txt` exists and is non-empty.
2. `template.md` exists and contains the literal `XXXXXXXXXXXXX` placeholder.
3. `render-prompts.sh inputs.txt template.md prompts/` runs cleanly. If it warns about slug collisions, **resolve before launching** — the second collider gets silently dropped otherwise.
4. `answers/` and `logs/` directories exist (created by render).
5. `codex login status` exits 0.

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
    python3 manifest-update.py ... --set 'status=done' --set "exit_code=0" \
        --set "mode_state.answer_size_bytes=$bytes" \
        --set "mode_state.below_floor=$( [ $bytes -lt $MIN_BYTES ] && echo true || echo false )"
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
bash audit-sizes.sh answers/ logs/_runner.log "${MIN_BYTES:-10000}"
```

`audit-sizes.sh` prints:
- Total `DONE / FAIL / SKIP` counts.
- Per-answer byte size, sorted ascending.
- Bottom decile flagged for review.
- Any answer below `MIN_BYTES` flagged.

**Size is a probabilistic quality signal, not a deterministic one.** A small answer can be high-quality if the input was thin (parked domain, niche product, deleted resource). Always read the head of any flagged answer before deciding to retry. Read `references/universal/output-size-signals.md` for the heuristics.

## Concurrency

Default `JOBS=10`. Tuned for codex-cli current TPM/RPM caps with gpt-5.5 + xhigh; adjust:

```bash
JOBS=15 ./run-batch.sh ...
```

Above 20, the soft gate kicks in: `--i-have-measured` flag required and a justification recorded in `manifest.policy.cap_override`. The recommended approach is to measure single-job latency first (one entry, see how long it takes), then divide your TPM budget by per-job token consumption to find the sustainable rate.

## Retry / rescue

A single failed entry retried in isolation:

```bash
mv answers/.prev/<slug>.md answers/.prev/<slug>.md.older 2>/dev/null
JOBS=1 ./run-batch.sh --only <slug>
```

A batch retry of all FAILed:

```bash
node orchestrate-codex.mjs rescue --manifest <path>
# Pick "redo failures only".
```

The skip-existing guard handles the rest.

To re-run an entry that's already `done` (you want a different output):

```bash
mkdir -p answers/.prev
mv answers/<slug>.md answers/.prev/
node orchestrate-codex.mjs rescue --manifest <path>
# Pick "redo failures only" — the missing answer file makes this entry classify as failed.
```

**Never delete `.prev/`** until you've confirmed the new answer is acceptable. Codex non-determinism means a retry can produce a smaller (or larger but worse) output than the original.

## Anti-patterns

- Auto-retry-by-size. Codex output varies; surface and inspect, never auto-retry.
- Two runners on the same workdir. Race on the skip-existing guard. The dispatcher refuses concurrent runs.
- Naming-collision drop without resolving. Two inputs render to the same slug → second is silently skipped at render time. Always resolve before launching.
- `tail -F` outliving the runner. The Monitor's tail process keeps tailing `_runner.log` after the runner exits. The log stays static, no events fire, but the process lingers. Always `TaskStop` the Monitor when `--- all jobs finished ---` lands.
- `MIN_BYTES` set so high that every entry flags. The threshold should match prompt-shape expectations. Recalibrate per template.
- One template doing N research types. If your inputs are heterogeneous (some URLs, some IDs, some product names), they probably want N templates. Render and run separately.

Full failure-mode taxonomy: `references/universal/failure-modes.md`.
