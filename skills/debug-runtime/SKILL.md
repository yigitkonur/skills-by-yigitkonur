---
name: debug-runtime
description: "Use if chasing a reproducible runtime bug or repeated failed fixes with a 4-phase root-cause pass."
---

# Do Debug

Language-agnostic systematic debugging. Four mandatory phases before any fix: **Investigation → Pattern analysis → Hypothesis testing → Implementation**. Works on any runtime, any language. Hands off to a structured user-driven reframe pause after three failed fixes.

## When to use this skill

Use when one of these is true:

- *staring at a stack trace, panic, or assertion and asking "why is this failing"*
- *a fix you already tried did not stick — symptom persists, regressed, or moved*
- *the failure is intermittent ("works on my machine", "only in CI", "sometimes")*
- *the obvious layer was checked and the bug persists across multiple layers*
- *a senior engineer or another agent already diagnosed it and you are about to apply their fix*
- *you feel pulled toward "let me just try X" without naming a mechanism*
- *a reproducible runtime bug exists but the causal mechanism is unknown*

Do NOT use this skill when:

- *the task is design, architecture, or refactor with no reproducible runtime bug* → a structured reframe pause
- *the user explicitly wants user-in-the-loop brainstorm or co-authored reasoning* → a structured user-driven reframe pause
- *a specialised diagnostic tool is already loaded* (Chrome DevTools, language profiler, native debugger session) → drive that tool's skill
- *only "confirm what's actually done" on already-fixed items is needed* → `audit-completion`
- *the failure is an external-service outage the agent cannot inspect* → out of scope; surface and stop
- *no environment exists to run code yet* → Phase 1 cannot complete; ask user for a repro or exit

Boundary with a structured reframe pause: three failed fixes routes here to a structured user-driven reframe pause with the handoff template. After a structured reframe pause returns, re-enter `debug-runtime` at **Phase 2** with the new framing — never Phase 1.

## The Iron Law

> **NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

An untested fix is a guess dressed as work. A guess that *appears* to succeed is the worst case — it masks the real mechanism, which returns later as a different symptom.

## Non-negotiable rules

1. **Iron Law.** No fix before root cause. Untested-mechanism fixes are forbidden.
2. **Diagnosis and repair are separate steps.** Phases 1–3 allow only *diagnostic* edits (temporary logs, probes, repro tests, instrumentation). No edits to product logic until Phase 4.
3. **Evidence per claim.** Every hypothesis cites a trace, log, diff, test run, or config value.
4. **One hypothesis at a time.** Two simultaneous fixes destroy the falsification signal of both.
5. **Escalate at 3.** Three failed fixes triggers the a user-driven reframe pause handoff (Escalation gate, below).
6. **Verify before declaring fixed.** The same Phase 1 repro that failed must now pass with evidence captured.
7. **Regression-proof before commit.** The fix lands with a test, guard, or assertion that proves the mechanism stays dead.
8. **Keep the diagnosis trace.** Phase 1 → Phase 4 reasoning attaches to the fix (commit body, issue, or plan file).

## The four phases

| Phase | Goal | Exit gate |
|---|---|---|
| 1 — Investigation | Define and reproduce the failure | Symptom card + 10/10 repro + copy-pasteable evidence |
| 2 — Pattern analysis | Identify candidate mechanisms | 1–3 ranked candidates with evidence per row |
| 3 — Hypothesis testing | Confirm one mechanism by falsification | One candidate confirmed by an experiment that *could have failed* |
| 4 — Implementation | Apply the narrowest fix and verify | Phase 1 repro passes 10/10 + regression guard committed |

### Phase 1 — Investigation

Goal: state the failure precisely, reproduce it deterministically, capture evidence a stranger could read.

1. **State the symptom precisely** — where (file/line/frame), when (input/action), expected vs. actual, first-seen commit/version if known.
2. **Reproduce 10/10** — the smallest repro that fails every time. If intermittent, route to `references/bisection-strategies.md` for input-space bisection before continuing.
3. **Capture evidence** — stack trace, log excerpt, diff vs. last-known-good, relevant config/env values. All copy-pasteable.
4. **Write the symptom card** — one paragraph a stranger could use to reproduce the bug with no extra context. If unable, the work is still storytelling, not investigating.

Red flags → restart this phase: "it happens sometimes" (repro not 10/10); "some config mismatch" (no concrete values); "the code looks wrong" (guessing, not observing).

### Phase 2 — Pattern analysis

Goal: 1–3 candidate mechanisms, each evidence-backed.

1. **Trace backward** with `references/root-cause-tracing.md` — walk from the symptom frame to the earliest frame where state was still correct.
2. **Map to pattern families** — test pollution, race condition, error swallowing, serialization boundary, off-by-one, null propagation, config drift, ACL/permission, resource leak.
3. **Produce 1–3 candidates** — each is one sentence: *"X caused Y because Z."* Evidence attached.
4. **Rank by disprovability** — the cheapest disprovable candidate is tested first.

Red flags → back to Phase 1: evidence gap appears (missing log/trace/value); only one candidate is possible (force a second — single-candidate is over-commitment).

### Phase 3 — Hypothesis testing

Goal: prove or disprove one candidate with an experiment designed to fail *if the hypothesis is wrong*.

1. **Design a falsifiable experiment** — write the predicted result if true AND the predicted result if false. If unable to state the false-case prediction, the experiment is cover for a pre-decided fix.
2. **Run the cheapest experiment first** — log, print, unit test, bisect step, feature flag. Patterns: `references/instrumentation.md`, `references/bisection-strategies.md`.
3. **Read the result honestly** — even when it invalidates the preferred candidate. Especially then.
4. **All candidates falsified** → route to a structured reframe pause to re-form the candidate space, then re-enter Phase 2.

Red flags → back to Phase 2: the "confirmation" also fits a different mechanism (experiment was not falsifying); product code changed mid-experiment; partial confirmation accepted "because it kind of matched."

### Phase 4 — Implementation

Goal: narrowest fix that restores the broken assumption, verified, with a regression guard.

1. **Write the narrowest fix** — restore one assumption, no unrelated cleanup. Use `references/defense-in-depth.md` to pick the layer (entry / logic / env guard / instrumentation).
2. **Add the regression guard** — a test, assertion, or invariant that fails if the mechanism reappears. Non-optional. Replace `sleep(n)` patterns using `references/condition-based-waiting.md`.
3. **Run the Phase 1 repro** — must now pass 10/10 under the same conditions.
4. **Remove temporary diagnosis code** — structural instrumentation stays; temporary prints come out.
5. **Hand off to `audit-completion`** — verify nothing else in scope was broken. See `references/integration.md` for the handoff format.

Red flags → back to Phase 3: the repro still fails (hypothesis was wrong, not just the fix); the regression guard passes without the fix (guard does not test the mechanism); new symptoms appear (blast radius widened).

## Integration decision matrix

First-class routing table — consult when a phase goes sideways.

| Situation | Stay or route | Destination | Why |
|---|---|---|---|
| Phase 1: repro is not 10/10, need wider frame | Stay | `references/bisection-strategies.md` (input-space bisection) | Inline technique |
| Phase 2: only "it feels like X" as evidence | Route | a structured reframe pause (`workflows/bug-tracing.md`) | Stronger reasoning loop re-grounds the investigation |
| Phase 3: 2–3 candidates look equally plausible | Route | a structured reframe pause foundations / evidence-and-falsification | Stronger evidence framework before the experiment |
| Phase 3: "confirmation" also fits a different mechanism | Stay | Back to Phase 2; design the distinguishing test | Do not hand off |
| Fail #1 (first fix didn't stick) | Stay | Re-open Phase 2 inline | Pattern was wrong |
| Fail #2 (second fix didn't stick) | Stay | Re-open Phase 1 inline | Symptom or repro was incomplete |
| Fail #3 — **stop fixing** | Route | a structured user-driven reframe pause; template in `references/integration.md` | Architecture-shaped; re-enter Phase 2 after return |
| Phase 4: fix applied, verification passed | Route | `audit-completion` | Audit for related-but-forgotten scope |
| "Bug" is a design disagreement, not a bug | Don't start | a structured reframe pause | Not a runtime failure |
| No way to run code (env/repo missing) | Don't start | Ask user for a repro, or exit | Phase 1 cannot complete |

Full decision tree with edge cases: `references/integration.md`.

## Escalation gate — the 3-fails rule

A "failed fix" = a hypothesis-driven change that did not make Phase 1's repro pass, OR made it pass but introduced a regression. Compilation errors unrelated to the hypothesis do not count.

- **Fail 1** → re-open Phase 2. The pattern family was likely wrong.
- **Fail 2** → re-open Phase 1. The symptom definition or repro was probably incomplete.
- **Fail 3** → **Stop fixing.** Route to a structured user-driven reframe pause. Three failures means the problem is architecture-shaped, not a bug. Handoff format: `references/escalation.md` and `references/integration.md`. After a structured reframe pause returns, re-enter at Phase 2 with the new framing.

The rule is load-bearing under pressure. Verbatim excuses agents generate to skip it: `references/rationalizations.md`.

## Rationalizations to counter (short form)

Full set + pressure-scenario sidebars: `references/rationalizations.md`.

| Rationalization | Counter |
|---|---|
| "Just try this fix and see." | "See" = evidence. Write the falsification prediction before editing. |
| "The senior engineer already diagnosed it." | Their Phase 1 is not yours. Reproduce and read the evidence yourself. |
| "Sunk cost — 4 hours in, can't restart." | The 4 hours are evidence the current path is dead. Restart Phase 1. |
| "We don't have time for root cause — production is down." | Cost of a blind fix that regresses = cost of the outage × 2. |
| "The tests pass now, so it's fixed." | Passing tests without a regression guard prove nothing durable. Add the guard. |
| "I see the issue." (no mechanism stated) | Say the mechanism out loud, or the mechanism has not been seen. |
| "This is an emergency — rules off." | Rules are *especially* on under pressure. Emergencies multiply the cost of skipping. |

## Voice discipline (short form)

Full list: `references/voice.md`.

**Forbidden phrases**: *"probably just a quick fix"* / *"let me just try"* / *"I know what this is"* (without a named mechanism) / *"this feels like last time"*.

**Required forms**: *"Phase 1 symptom card: …"* / *"Phase 2 candidates: …"* / *"Phase 3 falsification prediction: …"* / *"Verification result: …"*.

## Reference routing

### Scripts

| File | Read when |
|---|---|
| `scripts/find-polluter.md` | Test-pollution bisection — documents `scripts/find-polluter.sh` usage, runner selectors, caveats, expected output |

### Top-level deep dives

| File | Read when |
|---|---|
| `references/workflow-deep.md` | The phase block here is too thin — need long worked examples (Node test pollution, Python race, Rust lifetime) |
| `references/root-cause-tracing.md` | Phase 2 — walk backward from symptom frame to earliest-correct-state frame |
| `references/condition-based-waiting.md` | Replace `sleep(n)` with polling-with-timeout; routes to `references/waiting/<lang>.md` |
| `references/defense-in-depth.md` | Phase 4 — choose which layer (entry / logic / env guard / instrumentation) the fix belongs at |
| `references/bisection-strategies.md` | "Fails in CI only" / "worked last week" / "only with feature X" / intermittent without code change |
| `references/instrumentation.md` | Phase 2–3 — print/log/stack-trace patterns per language |
| `references/escalation.md` | Any failed fix — 3-fails protocol, pressure sidebars, handoff format |
| `references/integration.md` | Unsure whether to stay in-skill or route to a structured reframe pause / `audit-completion` |
| `references/rationalizations.md` | The urge to skip Phase 1 or Phase 3 — counter table + 5 pressure scenarios |
| `references/voice.md` | Writing progress updates — forbidden phrases and required forms |
| `references/cross-runtime.md` | Running on a non-Claude runtime — ask-user-tool lookup for the 3-fails handoff |

### Language-specific condition-based-waiting

| File | Language / framework |
|---|---|
| `references/waiting/typescript.md` | Jest / Vitest |
| `references/waiting/python.md` | pytest + asyncio |
| `references/waiting/rust.md` | tokio + cancellation tokens |
| `references/waiting/go.md` | stdlib `testing.T` polling |
| `references/waiting/swift.md` | XCTest + async/await |
| `references/waiting/ruby.md` | RSpec + timeout gems |
| `references/waiting/java.md` | JUnit 5 + awaitility |

### Pressure scenarios

| File | Scenario |
|---|---|
| `references/pressure-tests/academic.md` | Calm baseline — method works without pressure |
| `references/pressure-tests/pressure-financial.md` | $15k/min outage — time pressure vs. Iron Law |
| `references/pressure-tests/pressure-sunk-cost.md` | 4 hours in — restart vs. one-more-try |
| `references/pressure-tests/pressure-authority.md` | Senior engineer says X — verify independently or defer |

## Output contract

Before declaring a bug fixed, produce these artifacts in order. Do not batch them to the end — each must be visible in the session transcript.

1. **Symptom card** (Phase 1) — one paragraph, reproducible by a stranger
2. **Ranked candidate mechanisms** (Phase 2) — 1–3 one-sentence hypotheses with evidence
3. **Experiment design + result** (Phase 3) — falsification prediction + observed result
4. **Root-cause statement** (Phase 3 → Phase 4):
   ```
   Root cause: <frame / boundary / layer> — <violated assumption>
   Mechanism: <X caused Y because Z>
   Narrowest fix location: <file/function/layer>
   ```
5. **Fix + regression guard** (Phase 4) — narrow fix, test/assertion that fails without it
6. **Verification** (Phase 4) — Phase 1 repro now passes 10/10, evidence captured
7. **Next-step pointer** — `audit-completion` handoff, or "close and ship"

## Do this, not that

| Do this | Not that |
|---|---|
| Reproduce 10/10 before theorizing | Form a hypothesis, then try to reproduce |
| Phases 1–3 are read-only on product code | Edit product code while "investigating" |
| Write the false-case prediction before running the experiment | Decide what "confirms" the hypothesis after running |
| Cite a trace/log/diff/test/config for every claim | "It seems like…" / "I think it's…" |
| Fail #1–#2 → re-open prior phases; Fail #3 → route to a structured reframe pause (Interactive) | Try fix #4, #5, #6 |
| Add a regression guard before declaring done | "The tests pass, shipping" |
| Treat the senior's diagnosis as a candidate, not a verdict | Skip Phase 1 because "they already figured it out" |

## Guardrails and recovery

- Do not edit product code during Phases 1–3.
- Do not declare "fixed" without a passing Phase 1 repro + regression guard.
- Do not recommend `debug-runtime` as the next step (no infinite regress). State which phase to re-enter.
- Do not skip the 3-fails handoff "just this once."
- Do not consume a structured reframe pause as a substitute for Phase 1. It is a handoff, not a shortcut.

Recovery moves:

- **Phase 1 repro not 10/10** → input-space bisection (`references/bisection-strategies.md`); do not proceed with a flaky repro.
- **Phase 3 experiment ambiguous** → design a distinguishing test; two mechanisms fitting the same evidence means the experiment was not falsifying.
- **3 fails hit** → hand off to a structured user-driven reframe pause using the template in `references/integration.md`; do not retry.
- **Post-fix regression detected** → Phase 1 on the new symptom; do not paper over with a second fix on top of the first.

## Final checks

Before declaring done, confirm:

- [ ] Phase 1 produced a symptom card + 10/10 repro
- [ ] Phase 2 produced 1–3 ranked candidates with evidence per row
- [ ] Phase 3 experiment stated its false-case prediction *before* running
- [ ] Phase 3 confirmed one mechanism (not "partially matched")
- [ ] Root-cause statement written before any Phase 4 product-code edit
- [ ] Phase 4 fix is narrow (no unrelated cleanup, no unrelated files)
- [ ] Regression guard exists and fails without the fix
- [ ] Phase 1 repro now passes 10/10 with evidence captured
- [ ] Diagnosis trace attached to commit body / issue / plan file
- [ ] Zero forbidden rationalizations in the session output
- [ ] Next-step pointer to `audit-completion` (or explicit "close and ship")
