# Output size signals — when bytes are a quality screen

In batch mode, `audit-sizes.sh` runs after `--- all jobs finished ---` and surfaces the bottom decile + entries below the absolute floor (`MIN_BYTES`, default 10000). Size is a probabilistic quality screen, not a deterministic verdict.

## What size correlates with

- **Source material depth.** A research prompt against a parked domain produces a thin output because there's nothing to research. That's correct, not a failure.
- **Reasoning effort.** `xhigh` produces longer outputs than `medium`. Switching effort across runs invalidates threshold comparisons.
- **Prompt-imposed length cap.** "Answer in 100 words" produces 100-word outputs. The floor must match the prompt.
- **Random variance.** Codex output is non-deterministic. The same prompt run twice can produce outputs differing by 30%.

## What size does NOT correlate with

- **Correctness.** A 50000-byte output can be a hallucinated wall of text. A 2000-byte output can be a perfectly-cited summary of a thin source.
- **Cost.** Token counts (visible in `turn.completed.usage`) are the actual cost signal. A small output can have used a large input + reasoning budget.
- **Completeness.** The output may stop at a logical end-point well below your floor; that's not truncation.

## When small ≠ bad

- Parked domain or deleted resource (web research). The output should explicitly say so.
- Niche product with thin official docs (product research). Codex extracted what's available.
- Short input that doesn't warrant a long output (transformation tasks).
- Real incident summary that's intentionally concise.

In each case, **read the head of the file before deciding to retry**.

## When small IS bad

- Median-tail anomaly. If 95% of outputs are 8000+ bytes and 5% are 1500-byte stubs with the same prompt, the 5% likely lost connection or hit a transient codex bug.
- "Cannot find" or "I cannot research" patterns. These are codex bailing rather than the underlying source being thin.
- Hallucinated single-sentence outputs ("This product appears to provide [generic feature]."). The hallmark: no specifics, no citations, no structure.
- Cut-off mid-sentence with `...` trailing.

## Default thresholds

| Threshold | Default | Override |
|---|---|---|
| `MIN_BYTES` (absolute floor) | 10000 | env `MIN_BYTES=N` |
| Bottom-decile inspection | always (10% of outputs flagged) | n/a |
| Median-tail variance | 30% below median flags | n/a |

10000 bytes ≈ 1500 words ≈ 1 page of typical research output. Adjust to your prompt's expected output:
- Research / summarization template: 10000–15000.
- Code-extraction template: 2000–5000 (less prose).
- Data-transformation template: 100 (just the transformed value).

## Inspection workflow

```bash
# 1. Run audit.
bash audit-sizes.sh answers/ logs/_runner.log "$MIN_BYTES"

# 2. For each flagged file, read the head.
for slug in $(audit-sizes.sh ... --json | jq -r '.flagged[]'); do
    echo "=== $slug ==="
    head -20 "answers/$slug.md"
    echo
done

# 3. Decide per file:
#    - Accept (small but correct → record `mode_state.below_floor=true, accepted_small=true`)
#    - Retry (small and broken → archive + redo)
#    - Drop (input was bad → mark skipped with `last_error="input_unrecoverable"`)
```

The skill never auto-retries by size. Always inspect before deciding.

## Recording acceptance

When you accept a small output as legitimately small:

```bash
python3 manifest-update.py --manifest <path> --entry <slug> \
    --set 'mode_state.below_floor=true' \
    --set 'mode_state.accepted_small=true' \
    --set 'mode_state.accept_reason="parked domain — no source material"'
```

Audit then shows the entry as flagged-but-accepted, not flagged-and-actionable. The manifest carries forward the human's decision.

## Per-input MIN

Sometimes inputs are heterogeneous and a single floor is wrong. Set `MIN_BYTES` per slug via `mode_state.min_bytes`:

```bash
# In tasks.json or the input file's render annotation:
{"id": "01-deep-research", "mode_state": {"min_bytes": 20000}}
{"id": "02-quick-lookup", "mode_state": {"min_bytes": 500}}
```

`audit-sizes.sh` reads per-entry `mode_state.min_bytes` if set, falls back to `MIN_BYTES` env, falls back to 10000.

## Anti-patterns

- Auto-retry-by-size. Codex non-determinism means a retry can produce a smaller (or larger but worse) output than the original.
- Setting `MIN_BYTES` so high every entry flags. Recalibrate; don't ignore.
- Accepting flagged outputs without reading them. Surfaced is not the same as decided.
- Using size as the only success signal. The runner's success gate combines size + codex exit code + (if applicable) terminal JSONL event.
- Comparing sizes across runs with different effort or model. The thresholds shift.

## Forensics

If audit shows wide size variance for a single template:

```bash
# Sort answers by size.
ls -laS answers/*.md | head -5     # largest
ls -laS answers/*.md | tail -5     # smallest

# Diff structure (sections, headers) between large and small samples.
diff <(grep -E '^#+ ' answers/<large>.md) <(grep -E '^#+ ' answers/<small>.md)
```

If structure is consistent (same sections, just shorter content per section), the small inputs are thinner sources — accept. If structure is missing in the small samples, the prompt isn't producing the expected shape — adjust the template.
