# Iterative Self-Verification — Write → Test → Fix Loop

Operation: **Iterative Self-Verification** (`Op: SelfVerify`).

Closed-loop self-correction with a **deterministic oracle**. Write code, run it, read what broke, fix, run again, until green.

This operation is **largely unique to coding** because most non-dev tasks lack a cheap, fast, deterministic oracle. A demand letter has no compiler. A research summary has no test suite. But code has compilers, type-checkers, test runners, linters — they form a free, sub-second feedback loop that lets the agent iterate against ground truth.

When the operation applies, it changes everything: the agent gets *free supervision* instead of needing human review per step. This is why coding agents have leapt ahead of non-dev agents.

## Triggers

- "Make this code pass these tests"
- "Implement to spec" (when the spec is a test suite)
- "Fix until green"
- "Iterate until it works" (with a defined "works" oracle)
- Sub-operation embedded in Composition ("build me feature X" → write tests → make code pass)

## Required precondition: the oracle

Self-Verification is only valid when a **deterministic oracle** exists:

- Compiler / type-checker (does it parse / type-check?)
- Test runner (does the test pass?)
- Linter (no rule violations?)
- Runtime (no exceptions on the happy path?)
- Comparison-against-known-output (does the output match the expected?)

**Without an oracle, "iterate to green" becomes "iterate until you decide it's green," which is just Composition with extra steps.** If you're tempted to use Self-Verification without an oracle, switch to `generative-composition.md`.

## Phase A — Frame

- **A1** (Cynefin): Complicated (the spec is clear, the path isn't) or Complex (novel implementation, expected to probe).
- **A2** (Op): SelfVerify.
- **A3** (Reframe): the user's "make this work" may have been ambiguous about what "work" means — pin down the oracle BEFORE iterating.

## Phase B — Calibrate

- **B1** (Tier): driven by **blast radius of the resulting code**.
  - Low: throwaway script, prototype
  - Medium: production code with tests as the main safety net
  - High: production code with downstream consumers, irreversibility, or security implications
- **B2** (Grounding) — SelfVerify-specific:
  1. **Oracle definition** — exactly what passes / fails (the test names, the type-check command, the linter config). Write this down before iterating.
  2. **Iteration budget** — how many loop iterations before escalating? (typical: 3-5 iterations on the same hypothesis; if all fail, the hypothesis is wrong, not the code)
  3. **Convergence criterion** — what "done" looks like (all tests green? type-check clean? no linter warnings? specific behavioral check?)

## Phase C — Compare

### C1. First attempt + first oracle reading

NOT 3 options. The pattern is:

1. **Write the first attempt** based on the spec and your understanding.
2. **Run the oracle immediately**.
3. **Read the result honestly** — what passed, what failed, what's the failure mode (compile error, test failure, type mismatch, runtime exception)?

If everything passes on attempt 1, that's the green-on-first-try outcome — verify the oracle is meaningful (not "the test trivially passes regardless of code"), then commit.

### C2. Stress-test (SelfVerify-specific — NOT the Sense-Making trio)

Three checks **before declaring done**:

- **Loop bound check** — did you stay within the iteration budget? If you went over, the underlying hypothesis was wrong — escalate, don't keep iterating.
- **Oracle accuracy** — did the oracle test what the spec actually wanted? Common failure: the test passes but doesn't exercise the real behavior. Adversarial check: would the test still pass if you broke the code in the way that matters?
- **Escape condition** — is there a path where the loop never converges? (Tests passing for the wrong reason; oracle gameable; test-tweaking until green). If yes, the oracle is broken — fix the oracle, not the code.

**Phase C exit criterion**: oracle reports green AND the 3 checks pass.

## Phase D — Commit

- **D1**: ship the code (the oracle has approved).
- **D2**: verification check — does the *actual* behavior the spec intended now hold? (The oracle is a proxy for behavior; the verification check is the real test.) Often this is "deploy to staging, manually exercise the user-facing path, confirm."

## The write-test cycle

The core loop, expanded:

```
1. Write code
2. Run oracle
3. Read result:
   - Green → go to D1 (verify oracle was meaningful first)
   - Red → diagnose: was it the code, the test, or the hypothesis?
4. If code wrong → fix narrowly, return to step 2
5. If test wrong → fix the test, return to step 2 (BUT: be honest — are you fixing the test, or tweaking it to pass?)
6. If hypothesis wrong → STOP. Re-enter Phase A. Don't iterate on a dead hypothesis.
```

**Iteration budget enforcement**: most "stuck in loop" failures are budget violations. After 3-5 iterations on the same hypothesis with no progress, the hypothesis is wrong. Escalate to Sense-Making (`workflows/bug-tracing.md`) or do-debug.

## Adversarial self-test (optional but recommended)

After green:

> "Write a test that would have caught the bug you're most worried about *if it were in this code*."

If you can't think of one, your tests are too shallow. If the new test passes, you have stronger confidence. If it fails, you found the real bug your suite missed.

## Output contract

Distinct from Sense-Making. The output is **final state + convergence path + oracle log**:

```
Final state: <code shipped>

Oracle: <test command / type-check / linter — what was the ground truth>

Convergence:
- Iteration 1: <what was tried + oracle result>
- Iteration 2: <what was tried + oracle result>
- Iteration 3 (final): <what was tried + green>

Stress-test passes:
- Loop bound: ✓ (3 iterations, within budget of 5)
- Oracle accuracy: <how the oracle was confirmed to test the real behavior>
- Escape condition: <none — oracle could only pass via correct behavior>

Verification: <real-world / staging behavior check planned or done>
```

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Iterating without an oracle ("I'll know it when I see it") | That's Composition, not Self-Verification. Without a deterministic oracle, switch workflows. |
| Test-tweaking until green (changing the test's assertion to match the code's behavior) | Forbidden. The test encodes the spec; if it's wrong, fix the spec, not the assertion. Honest fix: realize the test's assertion is right and the code is wrong. |
| Ignoring iteration budget ("just one more try") | After 3-5 iterations on the same hypothesis, the hypothesis is wrong. Escalate to bug-tracing or do-debug. More iterations on a dead hypothesis don't converge. |
| Declaring done when the oracle is green but the real behavior isn't tested | Run the adversarial self-test: "what bug would slip past my tests?" If you can't answer, the tests are shallow. |
| Skipping the post-green real-world verification | The oracle is a proxy. The real check is staging / manual exercise / production-like environment. Tier Medium/High requires the real check. |
| Using Self-Verification on tasks without code (or without an oracle) | Wrong operation. If the task is "draft a doc," it's Composition; iterating doesn't converge against truth, it converges against your taste. |
| Treating any green CI as proof of correctness | Green CI = "the tests we wrote passed." It's not proof; it's evidence. The strength of evidence depends on how good the tests are. |
