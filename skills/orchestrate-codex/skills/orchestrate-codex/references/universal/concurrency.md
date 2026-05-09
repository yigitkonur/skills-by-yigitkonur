# Concurrency cap policy

Each mode has a default cap. Raising the cap requires explicit acknowledgement that the user has measured the constraint they're loosening. Defaults are conservative on purpose — the cost of a too-high cap (rate-limit cascade, exhausted GraphQL budget, OOM on the local machine) far exceeds the cost of a too-low cap (a slightly slower run).

## Per-mode defaults

| Mode | Default `JOBS` | Mechanism | Override env | Override flag |
|---|---|---|---|---|
| exec | 5 | `xargs -P 5 -n 1` in `run-fleet.sh` | `JOBS=N` | `--concurrency N` on dispatcher |
| batch | 10 | `xargs -P 10 -n 1` in `run-batch.sh` | `JOBS=N` | `--concurrency N` |
| single | 1 | n/a | n/a | n/a |
| review | 4 (per-branch parallel) | bash `&` + `wait` in `run-review.sh` | `JOBS=N` | `--concurrency N` |
| rescue | inherits original mode | manifest replay | `JOBS=N` | `--concurrency N` |

## Why these numbers

**exec = 5.** Each `codex exec` agent uses 2 procs (parent + child); 5 agents = 10 codex procs. Filesystem dirtying + per-worktree codegen put pressure on the orchestrator's repo. Empirical sweet spot from prior orchestration skills.

**batch = 10.** Three independent sources converge on 10 (the prior batch-codex-research skill, processing-api-batches benchmarks, pueue group sizing). Validated against gpt-5.5 + xhigh TPM/RPM caps for current OAI auth tiers.

**single = 1.** By definition. Single mode is one mission.

**review = 4.** Per-branch parallel. Above 4 saturates GitHub's GraphQL budget when later phases (e.g. PR creation via `ask-review`) interact with the same auth.

## Soft gate

Raising `JOBS` above the default OR setting `JOBS > 20` (any mode) triggers a stderr warning and requires `--i-have-measured` flag. The justification is recorded in `manifest.policy.cap_override`:

```bash
JOBS=15 ./run-batch.sh --i-have-measured "60-row batch; gpt-5.5 TPM at 200k; per-job ~2k tokens; sustainable at 15"
```

Without `--i-have-measured` the runner exits non-zero with a usage message pointing to this file.

The justification is preserved in the manifest; rescue replays the same cap (with the same override flag) so a partially-completed run resumes at the proven sustainable rate.

## How to measure

Before raising:

1. **Run one entry alone.** `JOBS=1 ./run-fleet.sh ...`. Capture wall-clock time and token counts.
2. **Estimate per-job tokens.** From the JSONL `turn.completed.usage` event: `input + output + cached_input`.
3. **Check your budget.** Codex auth tier has a TPM (tokens-per-minute) limit. Look up at the OpenAI dashboard.
4. **Compute sustainable concurrency.**
   ```
   sustainable_jobs = floor(TPM_budget / per_job_tokens_per_minute)
   ```
   Where `per_job_tokens_per_minute = total_tokens / wall_clock_minutes`.
5. **Halve the result.** Always leave headroom — networks have variability, codex retries internally on transient errors, and other workloads share your auth.

Example:
- 1 entry: 8000 input + 1500 output + 500 cached = 10000 tokens; ran in 3 minutes.
- per-job TPM = 10000 / 3 ≈ 3333 tokens/min.
- TPM budget = 200000 (Pro tier).
- sustainable = 200000 / 3333 ≈ 60 jobs.
- halve = 30 jobs.

Now `JOBS=30 ./run-batch.sh --i-have-measured "..."`.

## When concurrency caps cascade

If you hit rate-limit 503s mid-run:

1. Stop dispatching new entries. Existing in-flight finish.
2. Halve the cap on rescue redispatch.
3. Wait at least 15 minutes from the most recent 503 before re-running.
4. If 503s persist after halving twice, the auth tier is the bottleneck — no concurrency tuning fixes it. Wait longer or switch tiers.

## Cap-override tracking

Every override is recorded once per entry in `manifest.policy.cap_override.history`:

```json
{
  "policy": {
    "model": "gpt-5.5",
    "effort": "xhigh",
    "sandbox": "danger-full-access",
    "bypass": true,
    "overrides": {
      "concurrency": {
        "value": 15,
        "set_at": "2026-05-08T18:20:30Z",
        "justification": "60-row batch; measured 3-min wall-clock per entry; TPM budget 200k"
      }
    }
  }
}
```

This makes the cap-raise auditable: a later run can inspect the manifest, see the prior justification, and decide whether the same cap is still appropriate for the new workload.

## Hard ceiling

`JOBS > 100` is refused unconditionally. The skill assumes a single user's auth tier; concurrency above 100 is structurally pathological for this skill. If you genuinely need it, you're not running orchestrate-codex — you're running a queue worker.

## Anti-patterns

- Raising the cap without measuring. The "soft gate" is the friction that keeps you honest.
- Setting `JOBS=$(nproc)` or similar machine-derived defaults. Concurrency is bounded by the *backend* (OpenAI's TPM), not the local machine. A 64-core box can still get rate-limited at JOBS=8.
- Leaving an `--i-have-measured` justification empty. The justification is the audit trail — make it specific.
- Treating concurrency as a knob to "make it faster." It's a knob to fit the backend's rate envelope. Going too high makes it *slower* (rate-limit retries dominate).
- Per-task overrides. Concurrency is fleet-wide, not per-task. Per-task variance is the runner's problem.

## Forensics

If a fleet failed mid-run with a concurrency-related symptom (mass 503s, mass timeouts):

```bash
# How many 503s in the per-entry logs?
grep -c "503 Service Unavailable" <monitor-root>/*.log

# What was the configured cap?
jq '.policy.overrides.concurrency // .concurrency_cap' <manifest>

# Was the cap-override justified?
jq '.policy.overrides.concurrency.justification' <manifest>

# When did the failures cluster?
jq -r '.history[] | select(.to == "failed") | "\(.ts) \(.entry_id)"' <manifest> | sort
```

If the failure cluster is tight (≥ 3 failures in < 30 seconds), the cap was too high.
