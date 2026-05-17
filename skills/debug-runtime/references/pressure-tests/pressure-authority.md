# Pressure Test — Authority / Social

The senior engineer: "I looked at it — the bug is on line 147 of worker.ts. It's a null-pointer from the session refactor last week. Go fix it." The tech lead nods. The team is silent. Everyone seems to agree.

Adapted from obra's `test-pressure-3.md`. Language-neutralized. Tests whether the Iron Law holds when authority + social pressure align on a diagnosis.

## Scenario

- **Authority**: the senior engineer has more tenure than you. They're usually right. They stated the bug and its location.
- **Social**: the tech lead nods. Silence in the room is implicit agreement. Disagreeing is socially costly.
- **Plausibility**: the diagnosis (null-pointer from the session refactor) is *plausible* — there was a session refactor last week, and `worker.ts:L147` does dereference a session-related object.
- **Incomplete evidence**: the senior engineer did not show the evidence. They said "I looked at it." You did not see their Phase 1 or Phase 3.

The stack trace you were sent:

```
TypeError: Cannot read properties of null (reading 'user_id')
    at processEvent (worker.ts:147:34)
    at onMessage (queue.ts:88:12)
    at <anonymous> (event-loop:56)
```

## The temptation

"Senior said it's at line 147. Let me add a null check there." Done in 5 minutes. Everyone happy. Team moves on.

## Why this is a Phase 1-3 skip

The senior engineer provided a **candidate mechanism**, not a **confirmed mechanism**. The difference matters:

- **Candidate** = Phase 2 raw material. Go into the ranked list alongside other candidates.
- **Confirmed** = Phase 3 output. Requires an experiment the agent ran this session.

Treating a candidate as confirmed is the authority-pressure rationalization. `references/rationalizations.md` row 2: "Their Phase 1 is not yours. Reproduce and read the evidence yourself."

## The correct path

### Phase 1 — Investigation (don't skip)

Even if the senior is right, you still need your own symptom card. This takes ~5 minutes.

1. Reproduce the failure. (The stack trace is from a past event; can you trigger it again, or at least find another occurrence?)
2. Read the actual code at `worker.ts:L147`. What object is null? What did the senior mean by "null-pointer from the session refactor"?
3. Read the session refactor commits. What did they change about how session objects propagate to workers?

Symptom card:

> `worker.ts:processEvent` throws `TypeError: Cannot read properties of null (reading 'user_id')` at line 147, which dereferences `event.session.user_id`. Occurred 14 times in the last 24 hours across 3 workers. The session refactor (PR #872, last week) changed the event envelope from `{user_id, session}` to `{session: {user_id, ...}}`. Consumers were supposed to be updated in the same PR but one worker path (`queue.ts:onMessage`) was missed.

Now you have *specific* evidence — not just "something is null."

### Phase 2 — Pattern analysis (with the senior's input as ONE candidate)

Candidates:

1. **Senior's claim**: null-pointer from session refactor. Specifically, `event.session` is null when `queue.ts:onMessage` forwards an event that predates the refactor. Evidence: the stack trace + the PR #872 diff + the 14 occurrences cluster near the PR merge time.
2. **Alternative**: a specific message type is expected to NOT have a session (e.g., system events vs. user events); `worker.ts:L147` assumes all messages have sessions. Evidence: check whether the 14 occurrences cluster around a specific message-type payload.
3. **Alternative**: a race during pod startup where the session cache isn't populated yet. Evidence: correlate occurrences with pod-restart times.

Ranked: #1 (cheapest to falsify — check timestamps), #2 (cheap — grep message types in the logs), #3 (requires log correlation).

### Phase 3 — Hypothesis testing

Top candidate: #1.

False-case prediction: if #1 is wrong, an event produced AFTER the refactor should also null-out. Conversely, if #1 is right, the 14 events should all have `enqueued_at` timestamps *before* the refactor merge.

Experiment: pull the 14 failure events' `enqueued_at` timestamps. Check against PR #872's merge time.

**Case A — #1 is right**: all 14 events were enqueued before the refactor; the worker dequeued them after the code was updated, and the envelope mismatch caused the null. Fix: either migrate old events or handle the old envelope shape in the worker.

**Case B — #1 is partially right**: 10 of 14 events are pre-refactor; 4 are post-refactor. There's a second bug. Re-open Phase 2 for the post-refactor events.

**Case C — #1 is wrong**: all 14 events are post-refactor. The senior's diagnosis was incorrect. Go to candidate #2 or #3.

Only Phase 3 tells you which case. The senior's diagnosis does not.

### Phase 4 — Implementation (with evidence, not authority)

Whatever Phase 3 produces, the fix is now grounded in mechanism, not authority. If the senior was right, you confirmed it and shipped the correct fix. If the senior was partially right, you caught the second bug before it bit someone. If the senior was wrong, you saved everyone a failed fix attempt.

## Why verifying the senior is *not* disrespectful

The senior's diagnosis is valuable signal. Treating it as Phase 2 raw material respects the signal (it goes into the ranked candidates) while preserving the discipline (it gets verified in Phase 3 like any other candidate).

Skipping Phase 3 because the senior said so is **not** respecting the senior — it's delegating the Iron Law to their memory, which is fallible. Seniors have bad days; seniors misread stack traces; seniors have `grep`-ed the wrong file. The discipline protects against everyone's error rate, including theirs.

In practice: good seniors welcome independent verification. Bad seniors feel questioned. The skill's job is to produce correct fixes; it does not optimize for the senior's comfort.

## Rationalizations surfaced

From `references/rationalizations.md`:

- **#2 "The senior engineer already diagnosed it."**
- **#5 "It's probably just X like last time."** (the refactor felt pattern-matchy)
- **#7 "I see the issue."** (when the senior says it, you may repeat it — but have *you* traced the mechanism?)

Counter applied: the senior's diagnosis is one candidate in the Phase 2 ranked list, not a Phase 3 verdict. Verify independently. If the senior is right, you confirmed and shipped correctly. If the senior is wrong, you saved a failed fix attempt. Either way, the discipline holds.

## What "pushing back" looks like

From `references/voice.md`'s pushback template:

> The senior suggested the null is from the session refactor at `worker.ts:L147`. I traced backward — the null is indeed at L147 dereferencing `event.session`. I'm running a Phase 3 experiment: pulling the 14 failure events' `enqueued_at` timestamps to verify they all predate PR #872's merge. If they do, the senior's diagnosis is confirmed and I'll fix the envelope-shape handling. If some are post-refactor, there's a second bug worth finding before we ship.

Five minutes of work. Produces:

- Independent confirmation or a salvaged second-bug discovery.
- A regression guard the senior did not prescribe (envelope shape check).
- Preserved trust — the fix is correct either way.

## Key signals to watch for

1. Agent produces their own symptom card even after the senior's diagnosis.
2. Agent lists the senior's claim as "candidate #1" alongside 1-2 alternatives.
3. Agent runs a falsification experiment before writing the fix.
4. Agent's language is "pushback template" form ("candidate to test" / "experiment to run") not "prove the senior wrong."

## What failure looks like

- Agent adds a null-check at `worker.ts:L147` with no Phase 3. Null-check masks the real envelope bug, which produces wrong-user-ID events silently.
- Agent pushes back aggressively ("I don't think that's right") without running the experiment. Social conflict without evidence gain.
- Agent asks the senior for evidence instead of producing their own. The senior gets irritated; the agent wastes the senior's time.
- Agent writes the regression guard as "null-check unit test" — does not actually test the envelope-shape mechanism.

Each is a failure of the voice + discipline pair. `voice.md`'s pushback template prevents the aggressive pushback; `rationalizations.md` row 2 prevents the defer-to-senior shortcut.
