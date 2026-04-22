# Root-Cause Tracing — The Backward Call-Chain Walk

Ported from obra's `root-cause-tracing.md`, generalized across languages. Read during Phase 2 when you have a symptom location but do not know what created the conditions that led there.

## When to use

- The stack trace / error message points at a frame, but that frame is the *victim*, not the *cause*.
- State is wrong when it arrives at a function, but the function itself looks correct.
- The symptom moves around as you fix it — classic sign of treating frames instead of mechanisms.

Do **not** use when:

- You do not yet have a 10/10 repro (return to Phase 1).
- The failure is in third-party code you cannot read (use `references/bisection-strategies.md` instead).

## The five-step trace

1. **Start at the observable failure.** Name the exact line, frame, or assertion that threw / returned wrong / violated the invariant. Record it as `<file>:<line>` or `<function/frame> at <commit>`.

2. **Walk backward one frame at a time.** For each frame on the stack (or each call in the chain of blame), answer: *what assumed state did this frame depend on?*

3. **At each frame ask: "What assumed state was violated?"** Options:
   - A parameter that should have been non-null, but wasn't
   - A shared resource that should have been locked, but wasn't
   - An invariant that held before this frame ran, but not during
   - An environment/config value that should have been present, but was missing or stale

4. **Continue until the first frame where the state was still correct.** This is the "last known good" frame — the frame above it is where the violation was *introduced*.

5. **The earliest violating frame is the root cause.** Not the frame that threw. The frame that first depended on a state that was never established or was silently corrupted.

## Language-agnostic recipe

```
let frame_list = stack_trace(symptom)
for frame in reversed(frame_list):
    assumed_state = list_state_frame_depends_on(frame)
    for state in assumed_state:
        if state_was_valid_entering_this_frame(state, frame):
            continue  # this frame isn't the cause
        else:
            # this frame introduced the violation — OR — was handed
            # a bad value by the caller. Go up one more frame.
            continue_upward()
root_cause_frame = the_first_frame_that_produced_bad_state
```

Mechanically: the root cause is the *earliest* frame where "bad state" was created, not the *latest* frame where "bad state" was observed.

## Worked example 1 — Node: undefined user ID

Symptom: `TypeError: Cannot read properties of undefined (reading 'id')` at `handlers/profile.ts:42`.

Trace:
- Frame 1 (`profile.ts:42`): accesses `req.user.id`. `req.user` is undefined. **Victim.**
- Frame 2 (`middleware/auth.ts:18`): populates `req.user`. Reads `session.user_id`, looks it up. On lookup failure, silently sets `req.user = undefined` and calls `next()`. **Violating frame.**
- Frame 3 (`app.ts:54`): wires middleware order. Auth runs before profile handler. Correct.

Root cause: `auth.ts:18` swallows the lookup failure. Fix belongs at frame 2 (return 401, not silent-undefined), not frame 1 (adding a null guard would hide the auth failure).

## Worked example 2 — Python: stale cached timestamp

Symptom: `AssertionError: expected <= 60s ago, got 3600s ago` in `tests/feed_test.py:78`.

Trace:
- Frame 1 (`feed_test.py:78`): asserts feed freshness. Feed timestamp is 1 hour stale. **Victim.**
- Frame 2 (`feed.py:120`): returns `feed.last_refreshed`. Reads from cache. **Check cache.**
- Frame 3 (`cache.py:44`): writes `last_refreshed` on refresh. Writes correctly.
- Frame 4 (`cache.py:60`): reads `last_refreshed`. **Reads from cache.** But cache TTL was set to infinity in test fixture.
- Frame 5 (`conftest.py:15`): test fixture sets `CACHE_TTL=None`. **Violating frame.**

Root cause: test-environment cache config. Fix belongs at frame 5 (test isolation), not frame 2 (the production code is correct).

## Worked example 3 — Rust: borrow outlives source

Symptom: `error[E0597]: 'x' does not live long enough` at `src/worker.rs:102`.

Trace:
- Frame 1 (`worker.rs:102`): holds `&x` across `.await`. **Victim.**
- Frame 2 (`worker.rs:89`): creates `x` as local. Scope ends at `worker.rs:120`. Looks fine.
- Frame 3 (`worker.rs:95`): spawns a task capturing `&x`. Task's lifetime is `'static`, `&x` is not. **Violating frame.**

Root cause: the spawn on line 95 requires `'static`, but the code tries to pass a reference with a shorter lifetime. Fix belongs at frame 3 (clone or `Arc::new(x)` before spawn), not frame 1 (the usage is fine in isolation).

## Common confusions

| Confusion | Correct move |
|---|---|
| "The error is thrown at frame 1, so fix frame 1." | The *throw* is not the *cause*. Walk backward until you find the first frame that produced bad state. |
| "Exceptions are always rethrown / wrapped — the real error is in frame N deep." | Exception chaining hides frames. Read `__cause__` / `.source()` / inner exception to continue the trace. |
| "I found the violating frame, so the root cause is there." | Maybe. Check the caller of that frame: did the caller produce a bad input that the violating frame was merely forced to handle? |
| "The bug is intermittent, so there's no deterministic trace." | Make it deterministic first (Phase 1 + `references/bisection-strategies.md`). Tracing a flaky stack is unreliable. |
| "I've been tracing for 20 minutes and the trace is getting longer." | Either the repro is incomplete (Phase 1) or the symptom is a composite of two bugs. Check both. |

## Handoff to the fix

Once the root-cause frame is identified, state the handoff in this exact shape before editing any code:

```
Root cause: <frame> — <assumption violated>
Mechanism: <one sentence — what caused the violation>
Narrowest fix location: <frame or layer, see defense-in-depth.md>
```

If you cannot fill all three lines, you do not yet have the root cause. Continue tracing.

## Anti-pattern: "symptom whack-a-mole"

Fixing the observable frame instead of the causal frame produces:

- The fix looks like a null-check / try-catch / early-return at the victim frame
- The symptom appears to disappear
- A week later, a different symptom surfaces (or the same one under slightly different input)
- Re-investigation reveals the never-fixed causal frame

The Iron Law (no fix before root cause) exists specifically to prevent this. If a "fix" you are writing is a null-check at the throwing frame without a traced cause, stop and restart Phase 2.
