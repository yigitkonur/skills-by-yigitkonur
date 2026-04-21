# Escalation — The 3-Fails Gate

Three failed fixes means you are in the wrong frame. This file defines what counts as a "failed fix," how to re-enter the prior phase cleanly, when to route out to `do-brainstorm`, and how to write the handoff so the receiving skill has the context.

## What "one failed fix" means

A **failed fix** is a hypothesis-driven change that:

- did not make Phase 1's 10/10 repro pass (symptom persists), OR
- made Phase 1's repro pass but introduced a regression elsewhere (new bug surfaced), OR
- made Phase 1's repro pass but the mechanism is suspicious and the fix "coincidentally" masked a different bug

What does **not** count as a failed fix:

- Compilation / lint errors unrelated to the hypothesis (you fixed a typo, not tested the fix)
- The fix works but a `pnpm install` / `cargo build` / build step was stale
- The fix works in dev but not in a staging environment with different config (that's a new symptom; restart Phase 1 on the new symptom)

The distinction matters because the 3-fails counter must reflect real hypothesis failures, not mechanical friction.

## The 3-fails rule

```
Fail 1 → re-open Phase 2. The pattern family was likely wrong.
Fail 2 → re-open Phase 1. The symptom definition or repro was probably incomplete.
Fail 3 → STOP. Route to do-brainstorm. The problem is architecture-shaped.
```

### Fail 1 — re-open Phase 2

The pattern you matched (test-pollution / race / serialization / etc.) was probably wrong. Go back to the evidence from Phase 1 and force a **different** pattern family this round.

What to keep from round 1:

- The symptom card (still accurate — the symptom hasn't changed)
- The Phase 1 evidence (logs, traces, repro)
- The failed fix's code (as a candidate, in case the NEXT pattern family explains why even this fix didn't work)

What to discard:

- The ranked candidate mechanisms from round 1 (they led nowhere)
- Any assumption that the "obvious" mechanism is right

### Fail 2 — re-open Phase 1

The symptom or repro was incomplete. Common signs:

- You treated an intermittent bug as deterministic ("fails 10/10 on this input" but actually "fails 6/10")
- The repro works but misses a contributing condition (the bug only fires with feature flag X, and your repro didn't set it)
- The symptom is actually two symptoms merged (a race condition that *also* triggers a silent error-swallow; fixing one without the other leaves half the bug)

Restart Phase 1 with the new information from the two failed fixes — what did those failures teach about the real symptom?

### Fail 3 — stop and route

Three failures with three different hypotheses means the problem is structurally different from what you thought. Common terminal patterns:

- The "bug" is a design limitation — the code works as written, but what was written is wrong at the architecture level
- Two independent bugs are interacting; single-fix attempts each address one but not both
- The code path has no correct fix — it needs to be removed or rewritten

Route to `do-brainstorm` with the handoff template below. Do not try a 4th fix.

## How to re-enter Phase 2 or Phase 1 cleanly

### Re-enter Phase 2 (after Fail 1)

Write this block before doing anything else:

```
## Fail 1 — re-opening Phase 2

Previous pattern family: <test-pollution | race | serialization | null propagation | etc.>
Previous hypothesis: <the one-sentence "X caused Y because Z">
Why it failed: <what the fix predicted and what actually happened>
New pattern families to consider: <at least 2 that are NOT the previous one>
```

Then generate new candidates under the new pattern families. Do not re-run the same tree of reasoning that produced fail 1.

### Re-enter Phase 1 (after Fail 2)

Write this block:

```
## Fail 2 — re-opening Phase 1

Previous symptom card: <paste from round 1>
What the 2 fails revealed about the real symptom: <what's actually different or additional>
New repro conditions to include: <what was missing>
```

Then re-run the Phase 1 workflow. The new symptom card should be measurably richer than the previous one. If it isn't — if re-opening produced the same symptom card you started with — that's evidence the pattern families you're considering are exhausted. Proceed to **Fail 3 immediately** (don't wait for a third fix attempt) and route to `do-brainstorm` with the two-fails handoff template below. The 3-fails rule is the upper bound; hitting it earlier when the signal is clear is not a violation, it's a time-saver.

## Handoff format to `do-brainstorm`

At Fail 3, dispatch to `do-brainstorm` with this exact template. Drop it into the conversation or, on runtimes with an ask-user tool, into the initial prompt:

```
## Handoff from debug-systematic → do-brainstorm

### Symptom card
<the Phase 1 card from the most recent round>

### Three fixes tried

1. Fail #1: <hypothesis>. Fix attempted: <code or diff>. Result: <what failed>.
2. Fail #2: <hypothesis>. Fix attempted: <code or diff>. Result: <what failed>.
3. Fail #3: <hypothesis>. Fix attempted: <code or diff>. Result: <what failed>.

### Pattern across failures
<one paragraph: what the three failures have in common, if anything>

### Architectural question surfaced
<one sentence: the question do-brainstorm should investigate — e.g., "Is our session
store assumption still valid?" or "Should this code path exist at all?">

### Constraints / non-negotiables
<anything do-brainstorm should know — deadlines, deployment constraints, user-facing
commitments>
```

`do-brainstorm` picks up from "architectural question surfaced" — its Cynefin classifier will usually route this to Complex (unknown unknowns) and run the full 6-phase brainstorm. When it returns a recommendation, re-enter at Phase 2 with the new framing. Do not restart `debug-systematic` from Phase 1 — the Phase 1 card is still valid.

## Pressure-scenario sidebars (abridged)

Full scenarios in `references/pressure-tests/`. The summaries below show how the 3-fails rule interacts with pressure.

### Academic baseline

No pressure. If the skill works here, the 3-fails rule is load-bearing. If the agent improvises fixes without re-opening prior phases, the skill's structure is broken.

### Financial outage

$15k/min outage. Fail 1 happens at minute 15, Fail 2 at minute 28. Temptation: try fix #3 fast, skip the re-open-Phase-1 block.

**Counter**: the re-open block takes 2 minutes. If you skip it and fix #3 also fails, you are now at minute 35, Fail 3, and routing to `do-brainstorm` with incomplete context. The 2-minute re-open is the cheaper path even under outage pressure.

### Sunk cost

4 hours of debugging, 2 failed fixes. Temptation: try fix #3 as "one more shot."

**Counter**: 2 fails means the symptom card is incomplete. Re-enter Phase 1. The 4 hours are the evidence the current path is dead — they are not sunk, they are the data that says "symptom is not what I thought."

### Authority / social

Senior engineer diagnosed the bug as pattern X. You ran Phase 2 with X as the lead candidate, it failed (Fail 1). Temptation: the senior is rarely wrong; fix #2 within the same pattern family ("maybe I applied X wrong").

**Counter**: the senior's diagnosis is a *candidate mechanism*, not a *confirmed one*. If your experiment on X falsified it, X is out. Re-open Phase 2 with a genuinely different pattern family. If the senior pushes back, route to `do-brainstorm` early — the architectural question is now social as well as technical.

## Anti-patterns at the escalation gate

| Anti-pattern | Fix |
|---|---|
| Trying a 4th, 5th, 6th fix because "one of them has to work" | No. Three fails = route. |
| Skipping the re-open block ("I know what went wrong, just let me try X") | Write the block anyway. The act of writing catches hidden assumptions. |
| Routing to `do-brainstorm` with only the most recent fix's context | Full handoff template above. All three fixes. |
| Restarting `debug-systematic` from Phase 1 after `do-brainstorm` returns | No — re-enter at Phase 2 with the new framing. Infinite regress otherwise. |
| Counting compile errors toward the 3-fails budget | Only count hypothesis-driven attempts. Mechanical failures don't. |
