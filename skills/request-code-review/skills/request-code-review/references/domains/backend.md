# Backend Service / API Review

Author-side checklist for PRs that touch server routes, API handlers, SQL, auth, sessions, background jobs, or infrastructure. Use when classifying the diff's domain as **backend** in SKILL.md Step 4.

## What backend reviewers care about

| Concern | Why it matters | Evidence they want |
|---|---|---|
| **Correctness under concurrency** | Races, deadlocks, and lost writes only show up at scale | Locking strategy, isolation level, idempotency keys, retry semantics |
| **Data integrity** | Migrations that backfill / drop constraints can lose production data | Migration is reversible; constraints validated against real data shape |
| **Contract compatibility** | Callers break silently on removed fields or changed types | Explicit API version bump, or documented additive-only change |
| **Auth + authz boundaries** | Privilege elevation bugs are the highest-cost class of backend bug | Which roles can hit the route; what the authz check is and where |
| **Observability** | Prod debugging without logs/metrics is a scramble | Structured logs on boundaries; metric for new code paths |
| **Error shapes** | Callers depend on error codes/types as much as happy path | Consistent error envelope; no stack traces leaked to clients |
| **Resource limits** | One unbounded query kills the service | Timeouts, pagination limits, rate limits on the new path |

## Weaknesses the author should pre-empt

Surface these in the "Weaknesses and open questions" section before the reviewer finds them:

- **N+1 queries.** Did you add a loop that calls the DB inside it? Measure queries per request on the new path.
- **Transaction boundaries.** Where does the transaction start and end? Is anything outside it that assumes atomicity?
- **Migration safety.** If you added a NOT NULL column to a large table, what's the backfill plan? What's the rollback if it fails halfway?
- **Retry safety.** If the client retries this request, does it double-charge / double-create / double-send? Idempotency key present?
- **Background-job failure mode.** If the worker dies partway through, what's the state? Retriable? Poison-pill handling?
- **Cache invalidation.** If you read from a cache here, what invalidates it on the write path?
- **Secret leakage in logs.** Did you add a `logger.info(request)` that includes tokens or PII?
- **Timezone + DST.** Every time-based bug is eventually a timezone bug. What timezone is stored? What's displayed?

## Questions to ask the reviewer explicitly

Pick the ones that match your uncertainty:

- "The isolation level on this transaction is `READ COMMITTED` — confirm this is tight enough for the double-write scenario in `worker.ts:42`."
- "Migration `0042_add_user_token_rotation.sql` adds a NOT NULL column with a backfill default. Under concurrent writes, I believe the backfill is safe because [X]. Please verify — this is the scenario I'm least sure about."
- "Rate-limit window is 10 requests / 60 seconds. Please sanity-check against the expected traffic pattern for this route."
- "I did not add a metric for this code path because [reason]. Is that acceptable or should I add one?"
- "The authz check uses `session.role === 'admin'` rather than a policy object. I picked this because [reason] — push back if the policy-object pattern is preferred."

## What to verify before opening the PR

- [ ] All tests pass (unit + integration if touching DB)
- [ ] Migration runs forward AND backward in a dev DB
- [ ] If the route is authenticated: tried it with wrong role, expired token, missing token
- [ ] No secrets / tokens in log output of the happy path
- [ ] `curl` or equivalent hits the new route and returns the expected shape
- [ ] N+1 check: log the DB queries for one request, count them

State exactly what you ran in the **Verification** section. "Tests pass" is not enough — which tests.

## Signals the review is off-track

If you catch yourself thinking any of these while writing the body, slow down:

- "The migration is probably fine, the reviewer can check." → Verify locally first.
- "I didn't test the error path, but it's just a 500." → Test it. 500s become user-facing when the frontend doesn't handle them.
- "The authz is the same as the other route." → Link the other route in the body so the reviewer can compare.
- "I'll add the metric in a follow-up." → Fine, but list it under Follow-ups.
- "Rate limit is guessed." → Say so in the weaknesses section.

## When to split the PR

Backend PRs exceed review budget fast. Consider splitting if:

- Diff crosses two distinct capabilities (new route + unrelated migration)
- Schema change + code change + background-job change are all in one PR
- >30 files touched
- The Summary section feels like it needs 6+ sentences to explain the intent
