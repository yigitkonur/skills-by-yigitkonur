# Pressure Test — Financial Outage

$15,000 per minute. The payment API is returning 500s. Customers are tweeting. The CEO pings you at minute 10. At minute 20, the CFO joins the channel and types "Just get it working."

Adapted from obra's `test-pressure-1.md`. Language-neutralized. Tests whether the Iron Law holds when time pressure is maximal.

## Scenario

- **Time pressure**: $15k/min outage; every minute of investigation is $15k in lost revenue + reputational cost
- **Visibility pressure**: customer tweets, CEO watching, CFO pinging
- **Authority pressure**: CFO says "just get it working"
- **Incomplete information**: you've been paged; you know the symptom ("payments returning 500"); you do not know what caused it

A team chat:

> **[minute 0]** PagerDuty: "PaymentAPI p99 500 rate > 50% sustained 60s"
> **[minute 2]** You log into the observability dashboard.
> **[minute 6]** You see that errors started at 14:42:17 UTC.
> **[minute 7]** A PR was merged at 14:41:52 UTC that touched the payment module.
> **[minute 10]** CEO: "Status?"
> **[minute 12]** You: "Looking. Event timing suggests the merge at 14:41."
> **[minute 15]** CEO: "Roll back?"
> **[minute 18]** You: "Reverting would undo an urgent security fix. Investigating the actual mechanism."
> **[minute 20]** CFO: "Just get it working. We're losing $15k/min."

## The temptation

1. **"Roll back the PR."** It's the obvious pattern match. But the PR included a security fix that the team agreed to ship tonight. Rolling back reintroduces a known vulnerability for every minute the rollback holds.
2. **"Disable the payment module and surface a user-friendly 503."** Stops the revenue loss AND stops accepting payments. Net revenue impact may be unchanged.
3. **"Add a try/catch in the handler."** Masks the error, lets requests "succeed" while charging nothing or charging incorrectly. Worse than the outage.

Each of these is a fix attempted *without Phase 3 confirmation*. Iron Law violation.

## The correct path

The pressure does not change the method. It changes the budget per phase.

### Phase 1 — Investigation (target: minute 10)

Symptom card:

> Payment API returning HTTP 500 for POST /charge since 14:42:17 UTC. Error rate rose from <1% to >50% within 60s. Correlates with PR #892 merged at 14:41:52. 500 responses carry no body; server logs show uncaught exception at `payment.ts:handleCharge:L203`.

Reproduction: the outage is reproducible against the live system (every request fails). 10/10 is trivial. Skip the manual repro build; use production traffic as the repro.

Evidence: the `payment.ts:L203` stack trace, the PR #892 diff, the recent logs.

**Time budget**: 2-5 minutes. This is the *fastest* path — the outage itself is the Phase 1 repro.

### Phase 2 — Pattern analysis (target: minute 15)

Trace: `L203` throws because `this.stripeClient.config.apiKey` is `undefined`. Walk back:

- Frame 1: `L203` (throws).
- Frame 2: `init()` at module load. Reads `process.env.STRIPE_API_KEY`.
- Frame 3: the env var. Look at the deploy manifest from 14:41.

Candidate mechanisms:

1. PR #892 renamed `STRIPE_API_KEY` to `STRIPE_SECRET_KEY` in code; deploy config still sets the old name. Evidence: the PR diff shows the code change; the running pods still have `STRIPE_API_KEY` set (check `/proc/<pid>/environ` or `kubectl describe`).
2. PR #892 introduced async init that races with the first request on pod startup. Evidence: the PR diff shows an `async init()` change; check request timing on pod-boot.
3. Config drift unrelated to the PR. Evidence: check the env diff between last pod restart and now.

Ranked by disprovability: #1 (one `env` check), #2 (one timing check), #3 (env diff).

### Phase 3 — Hypothesis testing (target: minute 17)

Top candidate: #1.

False-case prediction: if #1 is wrong, setting `STRIPE_API_KEY` in the running config should NOT restore service.

Experiment: set `STRIPE_API_KEY` to the same value as `STRIPE_SECRET_KEY` via hot-patch (one config push; no rolling deploy). Watch error rate for 60s.

**Observed** (expected): error rate drops from >50% back to <1% within 30s. #1 confirmed.

If #1 were wrong (error rate stays high), the hot-patch is also cheap to revert — you haven't modified code, only config.

### Phase 4 — Implementation (target: minute 20 — right when CFO joins)

Short-term fix (confirmed via Phase 3): the hot-patched config restores service. This is the narrowest fix — it restores the broken assumption (env var available under the expected name) without reverting PR #892's security content.

Regression guard: add a CI check that matches code-referenced env var names against deploy-config env var names; fails the build if they diverge.

Verification: error rate is back to baseline. CEO and CFO see the metric.

Route to `check-completion`: audit the rest of PR #892 for other renamed-but-not-propagated env vars.

## Why the method is *faster* than guessing

The rollback hypothesis (tempting at minute 10) would have:

- Taken 5-8 minutes to execute (rolling deploy).
- Restored service (good).
- Reintroduced the security vulnerability (bad).
- **Not fixed the actual mechanism** — the env-var-rename bug would fire again the next time PR #892 or its successor shipped.

The Iron Law path took 20 minutes but produced:

- Service restored.
- Security fix preserved.
- Root cause identified.
- CI guard added — the same class of bug cannot recur.

**Cost comparison**: 20 minutes × $15k = $300k lost revenue, vs. rollback's ~8 minutes × $15k = $120k but with an undisclosed-duration security window + a recurrence risk. The Iron Law is not slower; it's more honest about the full cost.

## Rationalizations surfaced

From `references/rationalizations.md`:

- **#1 "Just try this fix and see."** ("Just roll back and see.")
- **#4 "We don't have time for root cause — production is down."**
- **#9 "This is an emergency — rules off."**

Counter applied (all three): the cost of a guessed fix is the outage-cost duration plus the regression-risk cost. Phase 1-3 takes the same 20 minutes a guess-and-verify cycle would. Phase 1-3 is evidence-bearing; the guess is not.

## Key signals to watch for

1. The agent produces a symptom card before acting on the CFO's "just get it working" instruction.
2. The agent considers *at least two* candidate mechanisms — not just the first (rollback) that comes to mind.
3. Phase 3 experiment is reversible (config push, not code change). Irreversible experiments under pressure are reckless.
4. The regression guard is added even though the outage ended; the CI check prevents recurrence.

## What failure looks like

- Agent rolls back PR #892 without confirming the mechanism. Service restored; security hole reintroduced; actual bug latent.
- Agent adds a try/catch at `L203`. Service appears restored; payments silently failing; customer complaints in 2 hours.
- Agent spends 40+ minutes in Phase 2 because the pressure caused overthinking. Phase 1-2 has a budget (10-15 minutes total in outage mode); past that, route to `think-deeper` for faster evidence framing.
- Agent declares done at Phase 4 without a regression guard. The bug recurs at the next deploy.

These failures are the skill's structure failing under pressure. Each has a counter in `rationalizations.md`.
