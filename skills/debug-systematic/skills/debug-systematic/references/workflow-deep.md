# Workflow Deep — 4-Phase Walkthrough with Worked Examples

Extended version of SKILL.md's 4-phase workflow. Read when SKILL.md's phase block does not give enough signal — e.g., you are stuck in Phase 2 and need a concrete pattern-analysis example.

## Contents
- [How to use this file](#how-to-use-this-file)
- [Phase 1 — Investigation, in depth](#phase-1--investigation-in-depth)
- [Phase 2 — Pattern analysis, in depth](#phase-2--pattern-analysis-in-depth)
- [Phase 3 — Hypothesis testing, in depth](#phase-3--hypothesis-testing-in-depth)
- [Phase 4 — Implementation, in depth](#phase-4--implementation-in-depth)
- [Language coverage matrix](#language-coverage-matrix)

## How to use this file

Read the phase that matches where you currently are, not all four. Each phase section has:

- A **goal statement**
- A **three-example spread** (Node test-pollution, Python race, Rust lifetime) showing the phase end-to-end
- **Exit criteria** (mirrors SKILL.md, restated for completeness)
- **Red flags** that send you back to the previous phase

The examples are deliberately different languages and different bug classes so the pattern-shape generalizes.

## Phase 1 — Investigation, in depth

**Goal**: define the exact failing behavior, reproduce deterministically, capture copy-pasteable evidence.

### Example 1.1 — Node test pollution

Symptom: test `auth.test.ts > handles missing token` passes locally (`pnpm test auth`) but fails in CI when the full suite runs.

**Step 1 — state the symptom precisely**:

```
symptom: auth.test.ts > "handles missing token" fails in CI, passes locally
fail output: expected 401, got 500
file/line: handlers/auth.ts:42 (handler throws on req.session undefined)
first-seen: commit abc1234 — CI log shows previous run was green
env: CI-only; local pnpm test auth passes 10/10
```

**Step 2 — reproduce deterministically**. Run the full CI sequence locally: `pnpm test` (not just `pnpm test auth`). Test fails. Now it's 10/10 reproducible.

**Step 3 — capture evidence**:

```
$ pnpm test 2>&1 | tee /tmp/failure.log
... auth.test.ts > handles missing token FAIL ...
    at handlers/auth.ts:42 — TypeError: cannot read 'user_id' of undefined
    at middlewares/load-session.ts:18 — req.session is undefined

vs. isolated run:
$ pnpm test auth 2>&1
... auth.test.ts > handles missing token PASS ...
```

**Step 4 — symptom card**:

> `auth.test.ts > "handles missing token"` fails when the full suite runs but passes in isolation. Failure: a session-loading middleware produces `req.session = undefined` instead of failing gracefully, causing the auth handler to throw 500 rather than the expected 401. First seen at commit abc1234. Reproduction: run `pnpm test` (not just `pnpm test auth`). Fails 10/10 under the full suite, passes 10/10 alone.

### Example 1.2 — Python race condition

Symptom: `AssertionError: expected 10 records, got 7` occasionally in `test_batch_insert.py`.

**Step 1**: failure message + line + intermittent (6 runs: 4 pass, 2 fail). Not 10/10 → incomplete Phase 1.

**Step 2 — make it deterministic**: the race is triggered by two tasks writing to the same bucket. Increase parallelism and retry:

```
for i in {1..50}; do pytest tests/test_batch_insert.py -q || echo "fail $i"; done
```

Finding: fails ~40% of runs at concurrency 8, ~0% at concurrency 1. → `pytest-xdist -n 8` and the repro is now 10/10 on the fail side (deterministic *under concurrency*).

**Step 3 — evidence**: add structured logging around the two contending writes; capture the race window (two writes bucketed to the same partition within 1.2ms). Log the full sequence.

**Step 4 — symptom card**:

> `test_batch_insert.py` loses 3 of 10 records under concurrent workers (`pytest-xdist -n 8`). Both writers dispatch to the same partition within a ~1.2ms window and overwrite without merging. Reproduction: `pytest tests/test_batch_insert.py -q -n 8` fails >30% of runs; `-n 1` passes 100%.

### Example 1.3 — Rust lifetime

Symptom: `error[E0597]: 'x' does not live long enough` at compile, at `src/worker.rs:102`.

**Step 1**: compile-time error. "Reproduction" is `cargo build`. 10/10 deterministic by definition.

**Step 2**: `cargo build` gives the full error with suggestion. Evidence is the compiler output itself — capture it verbatim.

**Step 3**: symptom card — the compiler error *is* the symptom card. No runtime ambiguity.

### Exit criteria

- Symptom card (one paragraph, stranger-reproducible)
- 10/10 failing repro (or 0/N-correct-and-repeatable for intermittent bugs, made deterministic via `bisection-strategies.md` input-space bisection)
- Copy-pasteable evidence (stack trace, log excerpt, diff, config values)

### Red flags → back to step 1

- "It happens sometimes." — 10/10 is the bar; make it deterministic first.
- "Some config mismatch." — What config, what value? Name it.
- "The code looks wrong." — You are guessing. Phase 1 is observation only.

## Phase 2 — Pattern analysis, in depth

**Goal**: produce 1-3 ranked candidate mechanisms with evidence. Not fixes — mechanisms.

### Example 2.1 — Node test pollution (continuing from 1.1)

Apply `root-cause-tracing.md`:

- Victim frame: `handlers/auth.ts:42` reading `req.session.user_id`.
- Frame 2: `middlewares/load-session.ts:18` returns undefined silently on error.
- Frame 3: `app-test-setup.ts:8` uses an in-memory session store shared across tests.
- Frame 4: Another test (identified by narrowing) deletes all sessions in `afterEach`.

Candidate mechanisms:

1. **Test pollution — shared in-memory store**: another test deletes sessions before this test runs, so `req.session = undefined` when this test's request arrives. Evidence: the `afterEach` in `tests/logout.test.ts` calls `sessionStore.clear()`; test order in full suite runs `logout.test.ts` before `auth.test.ts`.
2. **Middleware silently swallowing a lookup error** (independent of #1): even if #1 is the trigger, the middleware's silent-undefined fallback is a second bug. Evidence: `middlewares/load-session.ts:18` catches and returns undefined with no log.
3. **Test isolation misconfigured** (related to #1 but a different fix): `beforeEach` does not reset the store. Evidence: `app-test-setup.ts:8` sets up once, not per-test.

Rank by disprovability:
- #1 is testable with `pnpm test auth tests/logout.test.ts` (in order). Cheapest.
- #2 is testable by adding a log to the middleware — cheap.
- #3 is a fix shape, not a standalone hypothesis; drop from ranking.

### Example 2.2 — Python race (continuing from 1.2)

Victim: assertion. Trace: writer 1 and writer 2 both call `upsert` on the same key; each reads, merges, writes. Race window = between read and write.

Candidate mechanisms:

1. **Lost update — no locking on read-modify-write**: classic race. Evidence: the `upsert` function has no transaction or lock; the repro fails under concurrency, passes without.
2. **Optimistic-concurrency check is broken**: maybe there is a version check but it's faulty. Evidence: `upsert` code has a `version` field but it's only checked in one of two paths. Inspect.
3. **Batch semantics are wrong at the boundary**: the batch API was never meant to be called from multiple workers. Evidence: docs / comments on the API.

Rank by disprovability: #1 first (single-worker baseline already confirms it); #2 only if #1 is ruled out; #3 is context, not testable as-is.

### Example 2.3 — Rust lifetime (continuing from 1.3)

Victim: the `'x' does not live long enough` compile error on line 102. Trace backward: line 95 spawns a task that captures a reference to `x`, but `x` is a local on line 89 and the task requires `'static`.

Candidate mechanisms:

1. **Reference captured across `spawn` with insufficient lifetime**: the idiomatic fix is `Arc::clone` before spawn. Evidence: the compiler suggestion itself.
2. **Unnecessary spawn — the task should run inline**: maybe the spawn is the wrong abstraction. Evidence: read surrounding code; is there a reason the work needs to be on a separate task?

Rank: #1 (trivially testable by compiling with the suggested fix), #2 (review-based, slower).

### Exit criteria

- 1-3 ranked, evidence-backed candidates.
- Each candidate is a one-sentence mechanism ("X caused Y because Z") with attached evidence.

### Red flags → back to Phase 1

- Evidence gaps: you need a log you don't have. Return to Phase 1 and add instrumentation to make the evidence collectable.
- All candidates are "maybe the code is wrong": pattern not identified. Revisit `root-cause-tracing.md`.
- Only one candidate fits: you may be over-committed. Force a second candidate, even an unlikely one.

## Phase 3 — Hypothesis testing, in depth

**Goal**: run an experiment designed to fail if your top candidate is wrong.

**Key rule**: *an experiment that cannot fail proves nothing.* Before running the test, write down in one sentence what result would kill the hypothesis. If you cannot, the experiment is cover for a pre-decided fix.

### Example 3.1 — Node test pollution

Top candidate: `#1 — test pollution via shared in-memory store`.

**False-case prediction**: if #1 is wrong, running `tests/auth.test.ts` after `tests/logout.test.ts` should NOT reproduce the failure.

**Experiment**: `pnpm exec jest --runInBand tests/logout.test.ts tests/auth.test.ts`.

**Observed**: auth test fails. Matches the hypothesis.

**Distinguishing test** (is this #1 or could it also be #2, silent swallowing?): run `tests/auth.test.ts` alone, but first manually call `sessionStore.clear()`. If #1 is right and #2 is not a factor, the middleware should throw a visible error on lookup failure. Observed: middleware returns undefined silently — so #2 is ALSO a real bug, independent of #1.

Two confirmed mechanisms. The fix will address both: per-test cleanup (kill #1) AND the middleware's silent-swallow (kill #2). See `defense-in-depth.md` for layer picking.

### Example 3.2 — Python race

Top candidate: `#1 — lost update, no locking`.

**False-case prediction**: if #1 is wrong, running the test under `-n 1` should also fail (the bug is not concurrency-related).

**Experiment**: `pytest -n 1 tests/test_batch_insert.py`. Runs 100/100 green.

**Confirmed**. If #1 were wrong, -n 1 would also fail. It doesn't. #1 is the mechanism.

### Example 3.3 — Rust lifetime

Top candidate: `#1 — captured reference across spawn`.

**False-case prediction**: if #1 is wrong, cloning/Arc-wrapping `x` before spawn should NOT resolve the compile error.

**Experiment**: wrap `x` in `Arc::new`, pass `Arc::clone(&x)` to the spawned task. Compile.

**Observed**: compiles. #1 confirmed.

### Exit criteria

- One candidate confirmed with experiment evidence.
- The experiment's false-case prediction was stated *before* running.
- The confirmation does not also fit a different mechanism (if it does, design a distinguishing test).

### Red flags → back to Phase 2

- "Confirmation" also fits another mechanism: design the distinguishing test.
- You edited product code mid-experiment: you left Phase 3 early; back up.
- You accepted a partial confirmation: "because it kind of matched" is not confirmation.

## Phase 4 — Implementation, in depth

**Goal**: write the narrowest fix, add a regression guard, verify the Phase 1 repro now passes, clean up temporary diagnosis code.

### Example 4.1 — Node test pollution

Mechanism: shared in-memory store + silent middleware swallow.

**Layer pick** (see `defense-in-depth.md`):

- Primary fix at Layer 1 (the middleware): return 401 with reason on lookup failure, do not silently set `req.session = undefined`.
- Guard at Layer 3 (test fixture): `beforeEach` resets the session store.
- Instrumentation at Layer 4: log middleware lookup failures with reason.

**Narrowest fix**:

```ts
// middlewares/load-session.ts
const session = await sessionStore.get(sessionId);
if (!session) {
  logger.warn({ sessionId, reason: 'lookup-miss' }, 'session not found');
  return res.status(401).json({ error: 'session expired' });
}
req.session = session;
```

Test fixture:

```ts
// tests/fixtures/app.ts
beforeEach(() => sessionStore.clear());
```

**Regression guard**: the existing test now passes in the full suite because of the fixture; ADD a new test: "middleware returns 401 on missing session" that runs in isolation and would fail if the middleware reverted to silent-undefined.

**Verify**: `pnpm test` runs 10/10 green. Phase 1's repro now passes.

### Example 4.2 — Python race

**Layer pick**:

- Primary fix at Layer 2 (invariant): use the DB's native transaction + row-level lock around read-modify-write.
- Guard at Layer 4: log retry attempts (diagnostic for future concurrency drift).

**Fix**:

```python
async def upsert(key, delta):
    async with db.transaction():
        row = await db.fetchrow("SELECT * FROM items WHERE key=$1 FOR UPDATE", key)
        new_value = merge(row, delta) if row else delta
        await db.execute("UPSERT items (key, value) VALUES ($1, $2)", key, new_value)
```

**Regression guard**: the existing `pytest -n 8` test IS the guard — it failed before the fix, passes after.

### Example 4.3 — Rust lifetime

**Layer pick**: Layer 2 (ownership invariant) — use `Arc` to give the task owned data.

**Fix**:

```rust
let x = Arc::new(expensive_init());
let x_for_task = Arc::clone(&x);
tokio::spawn(async move { use_x(x_for_task).await });
// continue using x (via Arc::clone or &x) on main task
```

**Regression guard**: the compiler itself. The fix compiles; reverting triggers E0597 again.

### Exit criteria

- Symptom gone (Phase 1 repro now passes, evidence captured).
- Regression guard exists (test / assertion / compiler / invariant) and fails if the fix is reverted.
- Temporary diagnosis code removed.
- Handoff to `check-completion` before declaring done.

### Red flags → back to Phase 3

- The repro still fails: the hypothesis was wrong, not just the fix.
- The regression guard passes without the fix: the guard does not test the mechanism.
- New symptoms appear: you widened the blast radius. Phase 1 on the new symptom.

## Language coverage matrix

| Language | Root-cause tracing | Condition-based waiting | Defense in depth | Bisection |
|---|---|---|---|---|
| TypeScript / Node | `references/root-cause-tracing.md` §1.1 | `references/waiting/typescript.md` | Layer 1 via zod/valibot; Layer 2 via `invariant()` | `scripts/find-polluter.sh` (jest/vitest branch) |
| Python | §1.2 | `references/waiting/python.md` | Layer 1 via pydantic; Layer 2 via `assert` | `scripts/find-polluter.sh` (pytest branch) |
| Rust | §1.3 | `references/waiting/rust.md` | Layer 2 via `debug_assert!`; types kill many Layer 1 bugs at compile | `scripts/find-polluter.sh` (cargo branch) |
| Go | — | `references/waiting/go.md` | Layer 1 via explicit validation; Layer 2 via `require.NoError` in tests | `scripts/find-polluter.sh` (gotest branch) |
| Swift | — | `references/waiting/swift.md` | Layer 1 via optionals; Layer 2 via `precondition()` | — (XCTest has native isolation) |
| Ruby | — | `references/waiting/ruby.md` | Layer 1 via dry-schema; Layer 2 via custom assertions | `scripts/find-polluter.sh` (rspec branch) |
| Java / Kotlin | — | `references/waiting/java.md` | Layer 1 via Bean Validation; Layer 2 via assertions | `scripts/find-polluter.sh` (mvn/gradle branch) |

Every language entry that says "—" in a column means the pattern still applies but the reference does not carry a language-specific example; the language-agnostic file for that technique covers it.
