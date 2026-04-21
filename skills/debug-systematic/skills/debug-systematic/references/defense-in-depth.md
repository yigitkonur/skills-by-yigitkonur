# Defense in Depth — Four-Layer Validation

Ported from obra's `defense-in-depth.md`, generalized across languages. Read during Phase 4 when you've found the root cause and are about to write the fix — this file decides *which layer* the fix belongs at, and which other layers to add guards at so the bug cannot re-appear.

## The principle

A single-layer fix ("add a null check here") treats the symptom. A defense-in-depth fix restores the broken assumption *at the layer where it belongs* AND adds guards at adjacent layers so the invariant is checked multiple times along the call path. The bug becomes structurally impossible, not just operationally unreachable.

## The four layers

| Layer | Role | What belongs here | What does NOT belong here |
|---|---|---|---|
| **1. Entry-point validation** | Reject malformed input at the boundary | Schema check, type assertion, auth/permission check at the request/CLI/event entrance | Business-logic decisions, expensive lookups |
| **2. Business-logic invariants** | Assert the core domain rules hold | Pre/post-conditions on operations, invariants on data structures, state-machine edge checks | Input parsing, external I/O |
| **3. Environment guards** | Catch environmental drift | Env-var presence checks, feature-flag gating, runtime preconditions (DB up, cache reachable, clock sane) | Per-request validation |
| **4. Debug instrumentation** | Surface anomalies that pass other layers | Structured log at anomaly, metric on rare branch, assertion in test build | User-visible error handling |

## Layer 1 — Entry-point validation

**Role**: fail at the boundary with caller context, not deep in the call stack where context is lost.

**Pattern**: every public entrypoint (HTTP handler, CLI command, event consumer, public library function) validates its inputs against a precise type / schema, and returns a boundary-appropriate error (HTTP 400, non-zero exit, NACK, typed Result-Err) on violation.

**Micro-examples**:

- TypeScript: `const parsed = RequestSchema.safeParse(req.body); if (!parsed.success) return res.status(400).json(parsed.error);`
- Python: `raise ValueError(f"user_id must be a positive int, got {user_id!r}")` at function entry
- Rust: `fn handle(req: Request) -> Result<Response, Error> { req.validate()?; ... }` — `validate` is a single-pass schema check

**Signals to add Layer 1 guard**: the bug's symptom arrived via `req.body.field` being the wrong shape, the function was called with an argument of the wrong type, or a CLI flag was parsed but never checked.

## Layer 2 — Business-logic invariants

**Role**: encode the domain rules the code relies on, and check them at the points those rules could be violated.

**Pattern**: assertions + invariant checks scattered through business logic — not external validation (that's Layer 1), but internal "this code assumes X" made explicit.

**Micro-examples**:

- TypeScript: `invariant(balance >= 0, 'balance cannot be negative after debit');`
- Python: `assert len(rows) == len(ids), "ids and rows must be 1:1 after join"`
- Rust: `debug_assert!(self.state != State::Closed, "closed channel cannot send");`

**Signals to add Layer 2 guard**: the bug was caused by a domain invariant silently drifting (negative balance, duplicate IDs, out-of-range index, state machine skipped a transition). Layer 2 assertions fail fast with a named invariant; Layer 1 validation does not catch these because inputs were technically well-formed.

**When to throw vs. return-error**: invariants that should never be violated under any correct input → throw / panic / assert. Invariants that could be violated by legitimate-but-unexpected input → return a typed error.

## Layer 3 — Environment guards

**Role**: catch drift between what the code assumes about its environment and what the environment actually provides.

**Pattern**: at startup (or first-use of a subsystem), probe the environment and fail loudly if assumptions are violated.

**Micro-examples**:

- TypeScript: `if (!process.env.DATABASE_URL) throw new Error('DATABASE_URL required');` — at module load
- Python: `if not os.path.exists(CONFIG_PATH): raise EnvironmentError(f"{CONFIG_PATH} not found")` — at service startup
- Rust: `env::var("API_KEY").expect("API_KEY must be set")` — at initialization

**Signals to add Layer 3 guard**: the bug was caused by a missing env var, a feature flag defaulting to a stale value, a disk/cache/DB not reachable at runtime, or a clock-drift / time-zone mismatch. These bugs often manifest as "works on my machine."

## Layer 4 — Debug instrumentation that survives the fix

**Role**: if all three layers above are already correct but the bug still slipped through, add instrumentation that would have caught it.

**Pattern**: a log line, metric, or test-build assertion at the anomaly point — not for users, for the next debugging session.

**Micro-examples**:

- TypeScript: `logger.warn({ userId, reason: 'token-refresh-fell-back-to-credentials' })`
- Python: `logging.info("cache.miss: %s, age=%ss", key, age)` on rare-path
- Rust: `tracing::warn!(user_id = %uid, "session rotated after privilege elevation")`

**Signals to add Layer 4**: the bug was invisible during Phase 2 because no log existed for the rare path. Without Layer 4, Phase 2 would have guessed. Add a log/metric/assertion that would have made Phase 2 cheaper next time.

**What stays vs. what comes out in Phase 4**:

- Stays: structured logs at anomaly points, metrics on rare branches, assertions in test builds
- Comes out: `println!`, `console.log`, dbg!, commented-out debug code, temporary variable renames

## When to pick which layer — matrix

| Symptom type | Primary layer | Also guard at |
|---|---|---|
| Malformed external input | Layer 1 | Layer 2 if it bypasses normal entry |
| Internal state drift (negative balance, inconsistent caches) | Layer 2 | Layer 4 log on transition |
| Missing/stale env var or config | Layer 3 | Layer 1 for request-time overrides |
| Silently-swallowed error returned as success | Layer 4 log + Layer 2 assertion | — |
| Race condition | Layer 2 (invariant on shared state) | Layer 4 metric on retry/backoff |
| Auth/permission boundary violation | Layer 1 (reject at boundary) | Layer 2 (assert in protected code) |

## Anti-pattern: the single-layer fix

Most tempting failure: adding a null-check or try-catch at the symptom frame and declaring victory.

Example: symptom is `TypeError: cannot read 'id' of undefined` at `handlers/profile.ts:42`. The tempting "fix" is `if (!req.user) return res.status(401).end();` at line 42. This:

1. Does not say *why* `req.user` is undefined (the auth middleware swallowed a lookup failure)
2. Silently turns a middleware bug into a user-visible 401
3. Leaves the auth middleware bug in place for the next endpoint to hit

The defense-in-depth fix: Layer 1 at the auth middleware (return 401 with context on lookup failure) + Layer 4 log (why did the lookup fail? stale session? corrupt cookie?). Phase 2 should have identified the middleware as the causal frame; Phase 4 picks the layer.

## Handoff from Phase 3 to Phase 4

Once Phase 3 has confirmed a mechanism, answer three questions before writing the fix:

1. **Which layer did the violation originate at?** (This is where the primary fix goes.)
2. **Which adjacent layer, if guarded, would have made the bug structurally impossible?** (Add a guard there.)
3. **Which layer, if instrumented, would have made this bug cheaper to detect next time?** (Add instrumentation there.)

Fill these in before editing. If you cannot, you do not yet have the mechanism — return to Phase 3.
