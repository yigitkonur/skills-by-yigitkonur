# Retry strategy

The runner is idempotent by design — `[ -s answers/<name>.md ]` skips anything already complete, so reruns only process unfinished work. That gives you most of what a "retry queue" buys without any state machine.

This file covers the rest: when to retry, how to do it safely, and how to avoid the failure modes that catch out naive retry loops.

## The four states a job can be in after a run

| State | Indicator | Default action |
|---|---|---|
| Done, healthy | `DONE` line + answer ≥ MIN bytes | Accept |
| Done, suspicious | `DONE` line + answer < MIN bytes | Inspect, then decide |
| Failed | `FAIL` line + answer empty or missing | Rerun (skip-existing already handles this) |
| Crashed | START line, no DONE/FAIL, runner exited | Rerun (skip-existing handles) |

The skip-existing guard treats "answer missing or empty" as "needs work." `FAIL` jobs leave no answer (codex aborted before writing), so a plain rerun retries them. `START`-then-crashed jobs likewise: no answer was written.

The only state that requires manual action is "done, suspicious" — because the answer file exists, the runner will SKIP it on rerun.

## Manual retry of a suspicious answer

```bash
# 1. Archive (don't delete — codex retries can be worse)
mkdir -p answers/.prev
mv answers/<name>.md answers/.prev/

# 2. Rerun the runner — only this prompt and any others without answers will execute
JOBS=10 ./bin/run-batch.sh > logs/_runner.log 2>&1 &
disown

# 3. After the rerun lands, compare
ls -la answers/<name>.md answers/.prev/<name>.md
diff answers/.prev/<name>.md answers/<name>.md | head

# 4. Restore the archived version if the retry was worse
mv answers/<name>.md answers/.prev/<name>.retry.md
mv answers/.prev/<name>.md answers/<name>.md
```

The "archive don't delete" rule is the most important one. Codex output is non-deterministic; in real-world testing for this skill, retries produced *smaller* output ~30% of the time and *better* output ~70% of the time. Without the archive, that 30% silently destroys good work.

## Retrying many at once

```bash
# Create the archive dir BEFORE moving — without it, mv fails silently
# and the rerun's skip-existing guard keeps the stale answers in place.
mkdir -p answers/.prev

# Move all flagged answers aside in one go
for f in $(./bin/audit-sizes.sh | awk '/Below absolute floor/,0 { if (NF==2) print $2 }'); do
  mv "answers/$f" "answers/.prev/"
done

# Rerun
JOBS=10 ./bin/run-batch.sh > logs/_runner.log 2>&1 &
```

After the batch finishes, compare each pair. Don't blindly accept the retry — read or at least size-check both versions before settling.

## Failure classification (before retrying)

Borrowing from `pueue-job-orchestration`'s failure-classification rule: not every failure is worth retrying. Per-job log heads tell the story.

| Log fragment | Class | Retry? |
|---|---|---|
| `503 Service Unavailable` / rate limit | Transient | Wait 10–15 min, then yes |
| `5xx` / `connection reset` | Transient | Yes |
| `Unauthorized` / `Auth failed` | Persistent | No — `codex login` first |
| `Not inside a trusted directory` | Persistent (config) | No — fix runner flags |
| `Page not found` / `domain does not resolve` | Persistent (input) | No — input is genuinely empty |
| `Tool call failed: ...` | Mixed | Read the log; some are transient, some are bugs |

Auto-retrying persistent failures is exactly the failure pattern that `pueue` warns about: a 60-job batch can grow to thousands of failed retries if `restart --all-failed` is run blindly. Don't rerun the runner if the per-job logs show persistent failures across the board — fix the cause first.

## What NOT to do

- **Don't add a retry loop inside `run_one`.** Per-job retries inside the runner mean the runner blocks waiting for retries to land, which serialises work that should be parallel. Retries belong outside the runner.
- **Don't auto-retry by size threshold.** Size is probabilistic; auto-retry by size kicks off retries on legitimately-small answers, often producing worse output. Surface flagged answers, let the human decide.
- **Don't delete the archive.** `answers/.prev/` is your safety net. Keep it until you're done with the workdir entirely.
- **Don't retry while the original runner is still running.** The skip-existing guard checks at job start, not file-write time. Two runners over the same workdir can race.

## When the right move is to drop, not retry

Some inputs are unprocessable. A parked domain, a 404'd source, a deleted Twitter account — codex correctly reports "I couldn't find this" and there's no version of the prompt that fixes it. Document these as known-empty in your batch report; don't waste budget retrying.

The audit script's recommendation prints retry instructions but doesn't tell you to retry. Read the flagged answers, then decide: retry, accept, or drop.
