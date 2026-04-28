# Integration — When to Route Out, When to Stay Inline

This skill coordinates with two siblings in the pack: `do-think` (which now covers both Solo deep-think and Interactive brainstorm modes — the former separate `do-brainstorm` skill is merged into `do-think` Interactive mode) and `check-completion` (audit-then-remediate). The inline routing matrix in SKILL.md covers the common cases; this file covers edge cases and the handoff templates.

## Overview: when to hand off

The decision is almost always between "do I have enough signal to stay in the current phase" vs. "am I stuck in a way that more debugging won't resolve."

- **Stuck on evidence** (Phase 2 pattern can't form) → route to `do-think` (Solo)
- **Stuck on architecture** (3 fixes failed) → route to `do-think` (Mode: Interactive)
- **Fix applied, want to verify nothing else broke** → route to `check-completion`

Never route to yourself (`do-debug` → `do-debug` is infinite regress). When a routed-out skill returns, re-enter at the appropriate phase of this skill; do not restart from Phase 1.

## Route to `do-think` (Solo) when...

`do-think` Solo mode is the pack's tool-agnostic solo-reasoning mode. It does not require user input and applies a stronger evidence-and-falsification loop than Phase 2/3 of this skill.

### When it helps

1. **Phase 2 candidates are weak** — you can articulate only "it feels like X" for every candidate. Evidence is thin across the board.
2. **Phase 3 candidates tied** — two candidates fit the evidence equally well and you cannot design a cheap distinguishing test.
3. **Phase 1 repro is solid but Phase 2 is blocked** — the symptom is clear; you just can't form a mechanism hypothesis worth testing.

### When it doesn't help

- Phase 1 is incomplete (no 10/10 repro). `do-think` can't fix an unreproducible bug; go back to Phase 1.
- Phase 3 experiment was falsifying and a candidate was confirmed. You have a mechanism; go to Phase 4.
- You are at the 3-fails gate. That's `do-think` Interactive mode territory, not Solo.

### Worked handoff examples

**Example A** — Phase 2 candidates all weak:

> Handing to `do-think` (Mode: Solo). Phase 1 is solid (symptom card + 10/10 repro). Phase 2 produced three candidate mechanisms, all rated "maybe": (1) race on the session store, (2) middleware order issue, (3) cache invalidation timing. None has evidence stronger than "it could be this." Need a stronger evidence frame before running Phase 3.

**Example B** — Phase 3 tied:

> Handing to `do-think` (Mode: Solo). Two candidates fit: (1) connection pool exhaustion under load, (2) DNS resolution timing out on the cold path. Both would produce the observed "intermittent slow requests + error log." Tests so far have not distinguished them. Need a design for a falsifying experiment.

### Re-entry after `do-think` Solo

Re-enter this skill at **Phase 2** with the sharper evidence frame. Do not re-run Phase 1.

## Route to `do-think` (Mode: Interactive) when...

`do-think` Interactive mode is the user-in-the-loop variant. It requires the user to participate at 5 forks (Cynefin classification, decomposition, exploration, evaluation, stress-test). Use it when the debug question becomes an architectural question and the user's context is needed.

### When it helps

1. **3-fails gate hit** — three hypothesis-driven fixes failed. The problem is architecture-shaped; pure debugging will not resolve it.
2. **Phase 2 surfaces a scope question** — the candidates are technical but each implies a different product scope / team-ownership / architectural decision. The user needs to pick.
3. **The bug crosses team boundaries** — the fix requires a decision about *who owns this*.

### When it doesn't help

- You haven't tried three fixes yet. Stay in this skill and use the re-open cycles first.
- The bug is clearly technical (no product/scope/architecture implication). Stay technical.
- You just want to "bounce ideas" but don't have the 3-fails evidence. Interactive mode expects substantive input.

### Worked handoff example

> Handing to `do-think` (Mode: Interactive). Three fixes failed (attached below). All three tried to preserve the current session-store architecture. The pattern across the fails: each fix ran into the same synchronization boundary between the auth service and the session cache. The architectural question: *should the session cache be colocated with the auth service rather than shared?* This is a design decision, not a bug.

### Handoff template (required fields)

Use this exact shape:

```
## Handoff from do-debug → do-think (Mode: Interactive)

### Symptom card (from Phase 1)
<paste>

### Three fixes tried
1. <hypothesis + fix + result>
2. <hypothesis + fix + result>
3. <hypothesis + fix + result>

### Pattern across the fails
<one paragraph>

### Architectural question
<one sentence the brainstorm should investigate>

### Constraints
<deadline, rollback window, commitments, team ownership>
```

### Re-entry after `do-think` Interactive

If `do-think` Interactive returns a recommendation that is a new architecture:

- Re-enter this skill at **Phase 2** with the new framing. The symptom card is still valid; the pattern families to consider have changed.
- Do not try to squeeze the new architecture into the old Phase 2 candidate list. Regenerate candidates under the new framing.

If `do-think` Interactive returns "this is not a bug, it's a scope decision; defer":

- Close the debug session with the scope note.
- Do not continue to Phase 4.

## Route to `check-completion` when...

`check-completion` is the pack's audit-then-remediate skill with a 22-status taxonomy. Route to it after Phase 4's fix is verified, before declaring the session done.

### When it helps

1. **Phase 4 fix applied and Phase 1 repro passes** — the bug is fixed, but you want to verify nothing else in scope was broken by the change.
2. **Multiple files / modules touched** — the fix crossed module boundaries. `check-completion` audits whether the session's full scope is still intact.
3. **Fix landed but the session started with multiple tasks** — `check-completion`'s scope-disambiguation will identify what's still outstanding.

### When it doesn't help

- Only one file changed and the regression guard is tight. Skip `check-completion`; declare done.
- Phase 4 hasn't produced a fix yet. Don't route prematurely.
- The bug was a compile error; the compiler validates the fix. No audit needed.

### Re-entry after `check-completion`

Usually `check-completion` returns a list of things to verify. Either:

- Everything is clean → declare the debug session done, commit, move on.
- Something else broke → that's a new bug. Start a new `do-debug` session on the new symptom. Do NOT treat the original bug as unresolved; it's fixed. You have a *new* bug.

## Do NOT route when...

1. **Phase 1 is incomplete.** Routing out without a 10/10 repro makes the receiving skill invent evidence. Finish Phase 1 first.
2. **You are tired and looking for a shortcut.** `do-think` (in either mode) is not a substitute for the work you should be doing in this skill. It is a genuine handoff for genuine stuck-points.
3. **The session has already routed out twice.** Three skill handoffs in one debug session means the problem is something else entirely — surface this to the user and stop.
4. **The route would be recursive** (`do-debug` → `do-debug`). Never. If more debugging is needed, re-enter at the correct phase.

## Handoff templates — copy-paste ready

### To `do-think` (Mode: Solo)

```
## Route: do-debug (Phase 2/3) → do-think (Mode: Solo)

### Why routing
<one sentence: Phase 2 candidates too weak / Phase 3 experiments not distinguishing>

### Phase 1 artifact
<symptom card + repro>

### Phase 2 artifact (if Phase 2 completed)
<ranked candidates with evidence>

### What do-think should produce
<e.g., "a sharper evidence frame that lets me distinguish between candidates A and B"
or "a design for a falsifying experiment that would kill candidate X">
```

### To `do-think` (Mode: Interactive)

```
## Route: do-debug (Fail 3) → do-think (Mode: Interactive)

### Symptom card (Phase 1)
<paste>

### Three fails
1. <...>
2. <...>
3. <...>

### Pattern across fails
<one paragraph>

### Architectural question
<one sentence>

### Constraints
<bullet list>
```

### To `check-completion`

```
## Route: do-debug (Phase 4 complete) → check-completion

### Scope
<e.g., "session-loading fix touched middlewares/load-session.ts, tests/fixtures/app.ts,
and added tests/middleware/session-missing.test.ts. Audit these and confirm no other
session-related tests regressed.">

### Specific concerns
<e.g., "login flow uses the same middleware. Audit that login's integration tests pass.">
```

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Routing to `do-think` (Solo) at Fail 1 | No — use the re-open-Phase-2 block first. Solo deep-think is for stuck evidence, not stuck hypotheses. |
| Routing to `do-think` (Interactive) at Fail 2 | Try the re-open-Phase-1 block first. Fail 3 is the gate, not Fail 2. |
| Routing to `check-completion` before Phase 4 is done | You don't have a fix yet — nothing to audit. |
| Routing to multiple skills in sequence without re-entering this one | Re-enter at the correct phase; the handoffs are not a pipeline. |
| Restarting `do-debug` from Phase 1 after any routed-out skill returns | Re-enter at Phase 2 (post-`do-think`) or declare done (post-`check-completion`). Never Phase 1 unless the symptom actually changed. |
