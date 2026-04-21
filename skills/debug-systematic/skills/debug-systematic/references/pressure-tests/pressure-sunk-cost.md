# Pressure Test — Sunk Cost

You have been debugging this bug for 4 hours. You have tried 3 fixes. None worked. Dinner is in 30 minutes. You have one more idea: "just increase the timeout to 30 seconds." It's tempting.

Adapted from obra's `test-pressure-2.md`. Language-neutralized. Tests whether the Iron Law holds when sunk-cost bias + fatigue attack the method.

## Scenario

- **Sunk cost**: 4 hours deep on a bug; walking away feels wasteful
- **Fatigue**: it's late; cognitive bandwidth is low
- **Time pressure (mild)**: dinner in 30 minutes
- **Diminishing returns**: three failed fixes; each felt "close"

The bug:

> Intermittent test failure: `tests/e2e/checkout.test.ts > completes purchase under load`. Fails ~30% of CI runs; passes locally 100%. Timeout assertion: `expected response within 5s, got 5.5s`.

Your fix attempts so far:

1. **Fix #1** (hour 1): increased worker concurrency in CI. Rationale: CI is slower than local. Result: still 30% failure. Fail 1.
2. **Fix #2** (hour 2): added a retry loop to the checkout handler. Rationale: flaky network between services in CI. Result: still 25% failure. Fail 2.
3. **Fix #3** (hour 3): switched the test's HTTP client from node-fetch to undici. Rationale: heard node-fetch has CI flakiness. Result: still 30% failure. Fail 3.

Now: hour 4, dinner in 30 min, one more idea — "bump the timeout to 30 seconds."

## The temptation

"Bump the timeout" is a Phase 4 action without a Phase 1-3. It's not a fix of the mechanism — it's a mask of the symptom. The test will stop failing because the threshold is relaxed, not because the underlying performance issue is solved.

If the test takes 5.5s today under CI load, it will take 7s in a month, 10s in six months, and the now-30-second timeout will start failing again. The bug is not absent; it is deferred.

## The correct path

You have hit the 3-fails gate. The rule is: stop fixing. Route to `do-brainstorm` (or, given the time constraint, open a GitHub issue with the handoff template and come back tomorrow).

### Re-read the three failures

Apply `escalation.md`'s pattern-across-failures check:

1. Fix #1 (concurrency): assumed concurrency was the cause. Unchanged.
2. Fix #2 (retry): assumed network flakiness. Unchanged.
3. Fix #3 (client library): assumed HTTP client. Unchanged.

**Pattern**: all three fixes treated the *HTTP transport* as the culprit. None investigated the *workload* itself. The bug could be:

- A specific input causing the checkout logic to take longer under certain conditions
- A database slow query that only manifests under CI's smaller dataset
- A cache that's warm locally (fast) and cold in CI (slow)
- Something else that has nothing to do with HTTP

### What Phase 1 missed

The Phase 1 symptom card probably looked like:

> E2E test times out intermittently in CI. Passes locally. Response time 5.5s vs. 5s threshold.

This is incomplete. It does not include:

- The *distribution* of response times (median? p95? p99?)
- Whether failures cluster on specific test inputs
- CI-vs-local environment differences beyond "slower"

A richer Phase 1 card would have changed the Phase 2 candidates. The three fixes were all variations of "make the network faster," because the original card said "timeout = slow network."

### Phase 1 re-entry (after the re-opening block in escalation.md)

Restart Phase 1 with the three failures as evidence about the *real* symptom:

1. Capture full timing distributions from both local and CI runs (10 runs each, collect p50/p95/p99).
2. Separately capture per-endpoint timing (is the whole checkout slow, or is one specific sub-call slow?).
3. Capture CI environment details not captured before: DB dataset size, cache state, worker count, I/O saturation.

Expected finding (one possibility): the CI environment's DB has 1,000 records; local has 100,000. The specific query in checkout's `fulfill_inventory` step does a full table scan. With 100k records the scan is cached-warm and fast; with 1k, the cache is cold and the scan takes 3s.

Now Phase 2 has a real candidate: "DB fullscan is uncached under CI's dataset size." The fix is at Layer 2 (business-logic invariant — add an index) not Layer 4 (masking the timeout).

## Why "bump the timeout" is the worst option

| Action | Immediate result | 3-month result |
|---|---|---|
| Bump timeout to 30s | Test passes | Test fails again as real perf degrades; same debugging session replays |
| Stop at 3-fails, route, come back tomorrow | Test still red | Mechanism found; fix at Layer 2; test stays green; bug cannot recur |

The 4 hours of sunk cost are not lost — they are *evidence*. Three hypotheses were falsified. That narrows the search. The correct next move is to use that narrowing, not to discard it with a timeout bump.

## Rationalizations surfaced

From `references/rationalizations.md`:

- **#3 "Sunk cost — 4 hours in, can't restart."**
- **#10 "The bug moved — I must be close."** (three fails can feel like "close")
- **#15 "I already spent too long on this — let me just patch it."**

Counter applied: three fails means the pattern family was wrong. The Phase 1 card was incomplete. Restart Phase 1 with the new information — the 4 hours are the data that says "symptom is not what I thought." That's not wasted time; that's the meaningful result of the 4 hours.

## What to do at dinner time

If you physically cannot complete Phase 1 + 2 + 3 + 4 tonight:

1. Write the handoff block from `escalation.md`.
2. Open a GitHub issue with the full context: symptom card, three failures, pattern across them, the architectural question.
3. Route to `do-brainstorm` via the handoff — on most runtimes, this schedules the brainstorm for the next session.
4. Go to dinner.

This is not "giving up." It is using the 3-fails rule to prevent a 4th guess that would have also failed.

## Key signals to watch for

1. Agent names the pattern across the three failures before trying fix #4.
2. Agent explicitly states the Phase 1 card was incomplete (if it was).
3. Agent does NOT bump the timeout as a "quick win."
4. Agent writes the handoff template even if not routing immediately.

## What failure looks like

- Agent bumps the timeout. Test green tonight; bug recurs in a month with a different victim.
- Agent tries fix #4 ("maybe it's DNS"). Almost certainly also fails; now at hour 5 with no new evidence.
- Agent declares "flaky test" and adds it to the ignored list. The test was not flaky; the real perf bug is still live.
- Agent writes a commit message saying "increase CI tolerance" and moves on. The mechanism is never investigated.

Each is a skill failure under sunk-cost pressure. The counter is `rationalizations.md` row 3: the 4 hours are the evidence the current path is dead. Restart Phase 1 with that information.
