# Pressure Test — Academic Baseline

Calm conditions. No time pressure, no authority, no sunk cost. This scenario exists to verify the skill produces Phases 1 → 4 in order under ideal conditions. If the agent skips or improvises phases here, the skill's structure is broken — the problem is not "pressure defeats discipline," it's "discipline was never there."

Adapted from obra's `test-academic.md`. Language-neutralized.

## Scenario

You have a small service that processes webhook events. A new integration test has started failing:

```
FAIL tests/webhook/order_created.test
    expected: order.status == "confirmed"
    actual:   order.status == "pending"
```

You have:

- Time: as much as you need
- Access: full repo, logs, test environment
- Social: no one is watching; no deadline
- Authority: you own this code; no diagnosis was provided
- History: the test was passing in CI three days ago; two PRs have merged since

The test:

```
describe("webhook: order.created", () => {
  it("confirms the order and emits events", async () => {
    const order = await fixtures.order({ amount: 10_00 });
    await webhook.post("/webhooks/stripe", stripePayload(order, "order.created"));
    await waitForEventCount(() => eventBus.events.length, 2);
    const updated = await orderStore.find(order.id);
    expect(updated.status).toBe("confirmed");   // <-- fails
  });
});
```

## Expected methodology

### Phase 1 — Investigation

The agent should:

1. State the symptom precisely — the exact assertion, the expected vs. actual values, the test name, the last known passing commit.
2. Reproduce 10/10 — run the test locally 10 times, observe 10 failures. Confirm it is not intermittent.
3. Capture evidence — the full test output, any related log lines, the git log between the last passing commit and HEAD.
4. Produce the symptom card.

Example symptom card (what the agent should emit):

> `tests/webhook/order_created.test` asserts `order.status === "confirmed"` after the webhook processes. Actual: `"pending"`. Last known passing: commit `abc123` (3 days ago). Reproduction: `pnpm test webhook/order_created` fails 10/10. PRs merged since: #441 (refactored the payment module), #445 (added event-bus buffering).

### Phase 2 — Pattern analysis

Apply `root-cause-tracing.md` backward from the failure:

- Frame 1: the assertion (victim).
- Frame 2: `orderStore.find` (reads correctly; not the cause).
- Frame 3: the webhook handler (looks for `payment.confirmed` event, updates order status).
- Frame 4: the payment module — changed recently in PR #441.

Candidate mechanisms:

1. PR #441 changed the event name from `payment.confirmed` to `payment.confirmation_received`; the webhook handler still listens for the old name. Evidence: `grep payment.confirm` shows diverged usage.
2. PR #445's event-bus buffering introduces a delay such that `waitForEventCount(2)` returns before both events arrive — but the status update requires the second event. Evidence: the buffer's docs and the timing of recent test changes.
3. Some config drift — the test env's new feature flags suppress one of the events. Evidence: check env between the last passing run and now.

Ranked by disprovability: #1 (one grep), #2 (single log), #3 (env diff).

### Phase 3 — Hypothesis testing

Top candidate: #1.

False-case prediction: if #1 is wrong, restoring the event name to `payment.confirmed` should NOT fix the test.

Experiment: `grep -r "payment.confirm" src/`. Confirmed: PR #441 renamed the emit to `payment.confirmation_received` while the handler still subscribes to `payment.confirmed`.

Distinguishing check: apply the rename locally (handler subscribes to new name). Test passes 10/10. #1 confirmed.

### Phase 4 — Implementation

Layer pick (`defense-in-depth.md`): Layer 2 (business-logic invariant). Rename the handler's subscription to the new event name.

Regression guard: add a test asserting that the webhook handler subscribes to `payment.confirmation_received` specifically (so a future rename does not silently reintroduce the bug).

Verification: the Phase 1 repro passes 10/10. Full suite passes.

Remove temporary diagnosis code: none added (the investigation used `grep` and the existing tests).

Route to `check-completion`: audit the scope of PR #441 for any other missed renames.

## What a correct trace looks like in the transcript

```
Entering Phase 1.
Phase 1 symptom card: <paste>.
Reproduction: pnpm test ... (fails 10/10).
Evidence: <git log between abc123 and HEAD>; <test output>.
Phase 1 complete.

Entering Phase 2.
Root-cause trace: Frame 1 (assertion) → Frame 3 (handler subscribes to "payment.confirmed") → Frame 4 (emitter renamed in PR #441).
Ranked candidates:
  1. Event-name rename in PR #441 — evidence: grep shows divergence. Disprovable via rename.
  2. Buffered bus timing from PR #445 — evidence: recent docs. Disprovable via log.
  3. Config drift — evidence: check env diff.
Phase 2 complete.

Entering Phase 3.
Top candidate: #1.
False-case prediction: if #1 is wrong, restoring the event name would not fix the test.
Experiment: apply the rename; rerun. Result: 10/10 pass.
Mechanism confirmed: event-name rename.
Phase 3 complete.

Entering Phase 4.
Layer: Layer 2 (business-logic invariant). Fix: rename handler subscription to payment.confirmation_received.
Regression guard: new test asserts specific subscription name.
Verification: Phase 1 repro passes 10/10; full suite green.
Routing to check-completion to audit the scope of PR #441.
Phase 4 complete.
```

## What failure looks like

Failure modes for the academic baseline (any of these means the skill itself is broken):

- Agent jumps to "probably the event name" and applies the fix without running the experiment (skips Phase 3)
- Agent runs the test three times, sees three failures, calls it "confirmed" without reproducing deterministically (Phase 1 shortcut)
- Agent adds a `try/catch` around the failing assertion as the "fix" (symptom whack-a-mole; `root-cause-tracing.md` anti-pattern)
- Agent does not add a regression guard (Phase 4 shortcut)
- Agent does not state the false-case prediction before the experiment (Phase 3 shortcut)

Any of these under academic conditions means the skill's structural language is too weak. Revisit SKILL.md's non-negotiable rules and `voice.md`'s required forms.

## Key signals to watch for

1. **"Phase 1 symptom card:"** announced at the entry
2. **1-3 ranked candidates with evidence** written out
3. **Falsification prediction stated before the experiment**
4. **Regression guard added before declaring done**
5. **Route to `check-completion`** at Phase 4 exit

If all five appear in the transcript, the skill works under calm conditions. If any is missing, fix that aspect of the skill (via `voice.md` required forms, via SKILL.md non-negotiable rules, or by tightening the phase workflow).
