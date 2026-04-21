---
name: debug-systematic
description: Use skill if you are hitting repeated failed fixes, an intermittent bug, or a diagnosis you cannot explain, and need a language-agnostic four-phase root-cause method before editing code.
---

# Debug Systematic

Language-agnostic systematic debugging method. Four mandatory phases before any fix: Investigation → Pattern analysis → Hypothesis testing → Implementation. Works across any runtime and language.

## Trigger boundary

Use this skill when the task is to:

- debug a runtime bug you can reproduce but whose causal mechanism is unknown
- recover from a fix that failed — the symptom persists, regressed, or moved
- investigate an intermittent ("sometimes") failure where pattern-matching a quick fix is tempting
- stop yourself mid-diagnosis when you feel pulled toward "let me just try X"
- audit a multi-layer bug where the obvious layer has been checked but the bug persists

Prefer another skill when:

- a specific diagnostic tool is available and loaded (Tauri DevTools, Chrome DevTools, profiler) → `debug-tauri-devtools` or the tool's skill
- the task is "reason about a design tradeoff" with no bug to reproduce → `think-deeper`
- the user explicitly wants a user-in-the-loop brainstorm about architecture → `do-brainstorm` (this skill routes there at the 3-fails gate)
- only "confirm what's actually done" is needed on already-fixed items → `check-completion`
- the code is not running yet — pure design or scoping work → `think-deeper` or `do-brainstorm`
- the bug is an external-service outage the agent cannot inspect → out of scope; surface the fact and stop

## Non-negotiable rules

1. **Iron Law.** No fix before root cause. Fix attempts with unverified mechanism are forbidden.
2. **Diagnosis and repair are separate steps.** During Phases 1-3, the only edits allowed are *diagnostic* — temporary logs, probes, tests that reproduce the bug, instrumentation. No *fixes* to product logic until Phase 4, after Phase 3 has confirmed a mechanism.
3. **Evidence per claim.** Every hypothesis cites a trace, log, diff, test run, or config value.
4. **One hypothesis at a time.** Testing two fixes simultaneously discards the falsification signal of both.
5. **Escalate at 3.** Three failed fixes triggers the `do-brainstorm` handoff (see Escalation gate).
6. **Verify before declaring fixed.** The same symptom reproduction that failed must now pass with evidence captured.
7. **Regression-proof before commit.** The fix lands with a test, guard, or assertion that proves the mechanism stays dead.
8. **Keep the diagnosis trace.** Reasoning from Phase 1 → Phase 4 attaches to the fix (commit body, issue comment, or a plan file).

## The Iron Law

> **NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

An untested fix is a guess dressed as work. A guess that appears to succeed is the worst case — it masks the real mechanism, which returns later as a different symptom.

## Required workflow

### 1. Investigation

**Goal**: define the exact failing behavior, reproduce it deterministically, capture minimum evidence.

Steps:

1. **State the symptom precisely** — where (file/line/frame), when (on what input/action), expected vs. actual, first-seen commit or version if known.
2. **Reproduce deterministically** — the smallest repro that fails 10/10. If intermittent, route to `references/bisection-strategies.md` input-space bisection before continuing.
3. **Capture evidence** — stack trace, log excerpt, diff vs. last-known-good, relevant config/env values. Copy-pasteable.
4. **Write the symptom card** — one paragraph a stranger could read and reproduce the bug without additional context. If you cannot, you are still storytelling, not investigating.

**Exit criteria**: symptom card + 10/10 repro + copy-pasteable evidence.

**Red flags → back to step 1**: "it happens sometimes" (repro not 10/10); "some config mismatch" (no concrete values); "the code looks wrong" (guessing, not observing).

### 2. Pattern analysis

**Goal**: identify 1-3 candidate mechanisms by matching evidence to known failure patterns.

Steps:

1. **Trace backward** — apply `references/root-cause-tracing.md` to walk from the symptom frame back to the earliest frame where state was still correct.
2. **Map to pattern families** — test-pollution, race condition, silent error-swallowing, serialization boundary, off-by-one, null propagation, config drift, ACL/permission, resource leak.
3. **Produce 1-3 candidate mechanisms** — each a one-sentence hypothesis of the form *"X caused Y because Z."* Evidence attached.
4. **Rank by disprovability** — the candidate you can disprove cheapest is tested first.

**Exit criteria**: 1-3 ranked, evidence-backed candidate mechanisms written down.

**Red flags → back to Phase 1**: evidence gaps appear (you need a log you don't have); candidates are all "maybe the code is wrong" (pattern not identified); only one candidate is possible (force a second — absence of alternatives is over-commitment).

### 3. Hypothesis testing

**Goal**: prove or disprove each candidate with an experiment designed to fail *if the hypothesis is wrong*.

Steps:

1. **Design falsifiable experiments** — for the top candidate, write down the predicted result if the hypothesis is true AND the predicted result if false. If you cannot state the false-case prediction, the experiment is cover for a pre-decided fix.
2. **Run the cheapest experiment first** — log addition, print, unit test, bisect step, feature-flag toggle. See `references/instrumentation.md` and `references/bisection-strategies.md`.
3. **Read the result honestly** — even if it invalidates your preferred candidate. Especially then.
4. **If all candidates falsified → route to `think-deeper`** to re-form the space of mechanisms before repeating Phase 2.

**Exit criteria**: one candidate mechanism confirmed with evidence the experiment produced.

**Red flags → back to Phase 2**: your "confirmation" also fits a different mechanism (experiment was not falsifying); you changed product code mid-experiment (left Phase 3 early); you accepted a partial confirmation "because it kind of matched."

### 4. Implementation

**Goal**: apply the narrowest fix that restores the broken assumption, verify it, land it with a regression guard.

Steps:

1. **Write the narrowest fix** — one assumption restored, no unrelated cleanup. See `references/defense-in-depth.md` for *which layer* the fix belongs at.
2. **Add the regression guard** — a test, assertion, or invariant that fails if the mechanism reappears. Non-optional.
3. **Run the Phase 1 repro** — the 10/10 failing repro must now be 10/10 passing. Same conditions.
4. **Remove temporary diagnosis code** — *structural* instrumentation stays; temporary prints come out.
5. **Route to `check-completion`** — before declaring done, verify nothing else in scope was broken by the change. See `references/integration.md` for the handoff format.

**Exit criteria**: symptom gone (evidence) + regression guard (test/assertion) + `check-completion` result.

**Red flags → back to Phase 3**: the repro still fails (hypothesis was wrong, not just the fix); the regression guard passes without the fix (guard doesn't test the mechanism); new symptoms appear (you widened the blast radius).

## Integration decision matrix

This skill does not handle everything alone. The matrix below is the first-class routing table — consult it when a phase goes sideways.

| Situation | Route? | Destination | Why |
|---|---|---|---|
| Phase 1: repro is not 10/10, need wider frame | Stay | `references/bisection-strategies.md` input-space bisection | Inline technique |
| Phase 2: only "it feels like X" as evidence | Out | `think-deeper` (its `workflows/bug-tracing.md`) | Stronger reasoning loop re-grounds you |
| Phase 3: 2-3 candidates look equally plausible | Out | `think-deeper` foundations/evidence-and-falsification | Stronger evidence framework before the experiment |
| Phase 3: "confirmation" also fits a different mechanism | Stay | Back to Phase 2; write the distinguishing test | Do not hand off |
| Fail #1 (first fix didn't stick) | Stay | Re-open Phase 2 inline | Pattern was wrong |
| Fail #2 (second fix didn't stick) | Stay | Re-open Phase 1 inline | Symptom was wrong or repro was fake |
| Fail #3 (third fix didn't stick) | **Out — stop fixing** | `do-brainstorm` with handoff template in `references/integration.md` | Architecture-shaped, not a bug |
| Phase 4: fix applied, verification passed | Out | `check-completion` | Audit for related-but-forgotten scope |
| "Bug" is a design disagreement, not a bug | **Do not start** | `think-deeper` or `do-brainstorm` | Not a runtime failure |
| No way to run code (env/repo missing) | **Do not start** | Ask user for a repro, or exit | Phase 1 cannot complete |

Full decision tree with edge cases: `references/integration.md`.

## Escalation gate — the 3-fails rule

A "failed fix" = a hypothesis-driven change that did not make Phase 1's repro pass, OR made it pass but with a regression elsewhere. Compilation errors unrelated to the hypothesis do not count.

- **Fail 1** → re-open Phase 2. The pattern family was likely wrong.
- **Fail 2** → re-open Phase 1. The symptom definition or repro was probably incomplete.
- **Fail 3** → **Stop fixing.** Route to `do-brainstorm`. Three failures means the problem is architecture-shaped, not a bug. Full handoff format in `references/escalation.md` and `references/integration.md`.

The rule is load-bearing under pressure. See `references/rationalizations.md` for the verbatim excuses agents generate to skip it.

## Rationalizations to counter (short form)

Abridged table. Full set + pressure-scenario sidebars in `references/rationalizations.md`.

| Rationalization | Counter |
|---|---|
| "Just try this fix and see." | "See" = evidence. Write the falsification prediction before editing. |
| "The senior engineer already diagnosed it." | Their Phase 1 is not yours. Reproduce and read the evidence yourself. |
| "Sunk cost — 4 hours in, can't restart." | The 4 hours are the evidence the current path is dead. Restart Phase 1. |
| "We don't have time for root cause — production is down." | Cost of a blind fix that regresses = cost of the outage × 2. |
| "The tests pass now, so it's fixed." | Passing tests without a regression guard prove nothing durable. Add the guard. |
| "I see the issue." (no mechanism stated) | Say the mechanism out loud, or you have not seen it. |
| "This is an emergency — rules off." | Rules are *especially* on under pressure. Emergencies multiply the cost of skipping. |

## Voice discipline (short form)

Debugging-specific forbidden phrases (distinct from `check-completion`'s general voice rules). Full list in `references/voice.md`.

**Forbidden**: "probably just a quick fix" / "let me just try" / "I know what this is" (without a named mechanism) / "this feels like last time".

**Required forms**: "Phase 1 symptom card: …" / "Phase 2 candidates: …" / "Phase 3 falsification prediction: …" / "Verification result: …".

## Reference routing

### Top-level

| File | Read when |
|---|---|
| `references/workflow-deep.md` | SKILL.md's phase block is too thin — need long worked examples (Node test-pollution, Python race, Rust lifetime) |
| `references/root-cause-tracing.md` | Phase 2 — walk backward from symptom frame to earliest-correct-state frame |
| `references/condition-based-waiting.md` | Replace `sleep(n)` with polling-with-timeout; routes to `references/waiting/<lang>.md` for drop-in code |
| `references/defense-in-depth.md` | Phase 4 — deciding which layer (entry / logic / env guard / instrumentation) the fix belongs at |
| `references/bisection-strategies.md` | "Fails in CI only" / "worked last week" / "broken only with feature X" / intermittent without code change |
| `references/instrumentation.md` | Phase 2-3 — print/log/stack-trace patterns per language |
| `references/escalation.md` | Any failed fix — the 3-fails protocol, pressure-scenario sidebars, handoff format |
| `references/integration.md` | Unsure whether to stay in-skill or route to `think-deeper` / `do-brainstorm` / `check-completion` |
| `references/rationalizations.md` | The urge to skip Phase 1 or Phase 3 — 15-row counter table + 5 pressure scenarios |
| `references/voice.md` | Writing progress updates to the user — forbidden phrases, required forms |
| `references/cross-runtime.md` | Running on a non-Claude runtime — ask-user-tool lookup for the 3-fails handoff |

### Language-specific condition-based-waiting

| File | Language / framework |
|---|---|
| `references/waiting/typescript.md` | Jest / Vitest — port of obra's reference utilities |
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

Before declaring a bug fixed, produce these artifacts in order:

1. **Symptom card** (Phase 1) — one paragraph, reproducible by a stranger
2. **Ranked candidate mechanisms** (Phase 2) — 1-3 one-sentence hypotheses with evidence
3. **Experiment design + result** (Phase 3) — falsification prediction + observed result
4. **Fix + regression guard** (Phase 4) — narrow fix, test/assertion that fails without it
5. **Verification** (Phase 4) — the Phase 1 repro now passes, evidence captured
6. **Next-step pointer** — `check-completion` handoff, or "close and ship"

Each artifact is visible in the session transcript. Do not batch them to the end.

## Do this, not that

| Do this | Not that |
|---|---|
| Reproduce 10/10 before theorizing | Form a hypothesis, then try to reproduce |
| Separate diagnosis from repair (Phases 1-3 are read-only on product code) | Edit product code while "investigating" |
| Write the false-case prediction before running the experiment | Run the experiment, then decide what "confirms" the hypothesis |
| Cite a trace/log/diff/test/config for every claim | "It seems like…" / "I think it's…" |
| On fail #1-#2, re-open prior phases; on fail #3, route to `do-brainstorm` | Try fix #4, #5, #6 |
| Add a regression guard before declaring done | "The tests pass, shipping" |
| Treat the senior's diagnosis as a candidate, not a verdict | Skip Phase 1 because "they already figured it out" |

## Guardrails and recovery

- Do not edit product code during Phases 1-3.
- Do not declare "fixed" without a passing Phase 1 repro + regression guard.
- Do not recommend `debug-systematic` as the next-step (no infinite regress). If more debugging is needed, state which phase to re-enter.
- Do not skip the 3-fails handoff "just this once." See `references/rationalizations.md`.
- Do not consume `think-deeper` or `do-brainstorm` as substitutes for Phase 1. They are handoffs, not shortcuts.

Recovery moves:

- **Phase 1 repro not 10/10** → input-space bisection (`references/bisection-strategies.md`); do not proceed with a flaky repro
- **Phase 3 experiment ambiguous** → design a distinguishing test; two mechanisms fitting the same evidence means the experiment was not falsifying
- **3 fails hit** → hand off to `do-brainstorm` with the template in `references/integration.md`; do not retry
- **Post-fix regression detected** → Phase 1 on the new symptom; do not paper over with a second fix on top of the first

## Final checks

Before declaring done, confirm:

- [ ] Phase 1 produced a symptom card + 10/10 repro
- [ ] Phase 2 produced 1-3 ranked candidates with evidence per row
- [ ] Phase 3 experiment stated its false-case prediction before running
- [ ] Phase 3 confirmed one mechanism (not "partially matched")
- [ ] Phase 4 fix is narrow (no unrelated cleanup, no unrelated files)
- [ ] Regression guard exists and fails without the fix
- [ ] Phase 1 repro now passes 10/10 with evidence captured
- [ ] Diagnosis trace attached to commit body / issue / plan file
- [ ] Zero occurrences of forbidden rationalizations in the session output
- [ ] Next-step pointer to `check-completion` (or explicit "close and ship")
