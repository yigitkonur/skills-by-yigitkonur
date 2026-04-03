# Review Dimensions Checklist

This checklist is ordered by priority. Apply each dimension to every file cluster during the cluster review phase. Not every dimension applies to every file — use judgment to skip irrelevant checks.

---

## 1. Security (Priority: CRITICAL)

Security issues are always worth flagging. A single missed vulnerability can compromise an entire system. Apply this dimension to every cluster, but focus especially on API endpoints, authentication flows, and any code that handles user input.

### Input validation

- [ ] Are all user inputs validated before use? (query params, body, headers, path params)
- [ ] Are SQL queries parameterized? (no string concatenation in queries)
- [ ] Are file paths validated against traversal? (no `../` in user-supplied paths)
- [ ] Are redirects validated against open redirect? (whitelist allowed domains)
- [ ] Is deserialization safe? (no `eval()`, `pickle.loads()` on user input, no `JSON.parse` without try/catch)

Watch for subtle variants: template literals that interpolate user input into queries, ORM `.raw()` or `.query()` methods that bypass parameterization, and `new RegExp(userInput)` which enables ReDoS.

### Authentication and authorization

- [ ] Are new endpoints protected by authentication middleware?
- [ ] Are authorization checks in place? (user can only access their own resources)
- [ ] Are admin/elevated-privilege endpoints properly guarded?
- [ ] Are JWT/session tokens validated correctly? (expiry, signature, issuer)
- [ ] Is there RBAC/permission checking where needed?

The most common auth bug in PRs is a new endpoint that simply forgets to apply the auth middleware. Check route definitions and middleware chains, not just handler logic.

### Secrets and sensitive data

- [ ] Are secrets, API keys, or passwords hardcoded? (check for string literals that look like secrets)
- [ ] Are sensitive fields excluded from logs and error messages?
- [ ] Is PII handled according to data protection requirements?
- [ ] Are cryptographic operations using strong algorithms? (no MD5, SHA1 for security)

Look for: long base64 strings, anything assigned to variables named `key`, `secret`, `token`, `password`, or `credential`. Check `.env.example` files for real values accidentally committed.

### Common vulnerabilities

- [ ] XSS: Is user input escaped before rendering in HTML?
- [ ] CSRF: Are state-changing requests protected by CSRF tokens?
- [ ] SSRF: Are URLs from user input validated before server-side requests?
- [ ] Mass assignment: Are only expected fields accepted in request bodies?
- [ ] Rate limiting: Are public endpoints rate-limited?

For XSS: check `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, `{!! !!}` (Blade), and any template rendering that bypasses auto-escaping. For mass assignment: check if request bodies are spread directly into database queries or model constructors without allowlisting fields.

---

## 2. Correctness (Priority: CRITICAL)

Correctness bugs ship silently and break in production. These are the hardest to catch and the most valuable to flag. Read the code as if you are the runtime executing it.

### Logic errors

- [ ] Are boolean conditions correct? (no inverted logic, no missing `!`)
- [ ] Are comparison operators correct? (`==` vs `===`, `<` vs `<=`)
- [ ] Are loop bounds correct? (off-by-one errors)
- [ ] Are switch/match statements exhaustive? (missing default/else case)
- [ ] Are early returns correct? (not skipping necessary cleanup)

Trace each conditional branch mentally. Ask: "Is there an input that would take the wrong branch?" Pay special attention to negated conditions and De Morgan's law transformations — these are where logic inversions hide.

### Null/undefined handling

- [ ] Are nullable values checked before access?
- [ ] Are optional chaining and nullish coalescing used correctly?
- [ ] Are array/object operations safe on empty/null inputs?
- [ ] Are type narrowing checks complete?

Common patterns that crash: `.length` on a potentially null array, `.map()` on an API response that might be `undefined`, destructuring an object that might not exist. Check every variable that crosses a trust boundary (API response, database result, function parameter).

### Error handling

- [ ] Are errors caught at appropriate boundaries?
- [ ] Do catch blocks handle errors meaningfully? (not empty catch blocks)
- [ ] Are errors propagated with sufficient context?
- [ ] Are async errors handled? (missing `await`, unhandled promise rejections)
- [ ] Are error responses appropriate for the consumer? (don't leak stack traces to users)

The most dangerous pattern is a missing `await` — the function appears to work in testing but silently drops errors in production. Check every `async` function call to ensure it is awaited or its promise is handled.

### Concurrency and race conditions

- [ ] Are shared resources protected? (locks, atomic operations, transactions)
- [ ] Are concurrent requests to the same resource handled safely?
- [ ] Is there a TOCTOU (time-of-check-time-of-use) vulnerability?
- [ ] Are database transactions used where multiple writes must be atomic?

Classic TOCTOU: checking if a username is available, then inserting it — another request can insert the same username between the check and the insert. The fix is a unique constraint at the database level or a serialized transaction.

### Edge cases

- [ ] What happens with empty input? (empty string, empty array, null)
- [ ] What happens with very large input? (memory, timeouts)
- [ ] What happens with malformed input? (invalid JSON, bad encoding)
- [ ] What happens with concurrent access? (two users editing the same resource)

Don't just ask "is this handled?" — ask "what *specifically* happens?" Trace the code path for each edge case. An unhandled edge case that returns a 500 is still a bug even if it doesn't crash the server.

---

## 3. Data Integrity (Priority: HIGH)

For deprecation PRs, also check: deprecated APIs still function (backwards compatibility), emit runtime warnings, and all call sites in the diff have been migrated to the new API.


Data corruption is worse than downtime. Downtime ends; corrupted data persists. Apply this dimension rigorously to any PR that touches database schemas, migrations, or state management.

### Database migrations

- [ ] Is the migration reversible? (down/rollback migration exists)
- [ ] Is the migration backward compatible? (can the old code still work during deployment?)
- [ ] Are there data loss risks? (dropping columns, truncating tables)
- [ ] Are indexes added for new query patterns?
- [ ] Are foreign key constraints correct?
- [ ] Is the migration idempotent? (can it run twice without breaking?)

The backward compatibility check is critical for zero-downtime deployments. During a rolling deploy, old and new code run simultaneously. If the migration drops a column that old code reads, the old instances crash. Sequence: (1) deploy code that stops using the column, (2) deploy migration that drops it.

### API contracts

- [ ] Are breaking changes to API responses documented and versioned?
- [ ] Are new required fields added only to request bodies, not response bodies?
- [ ] Are enum values backward compatible? (new values OK, removing values breaks consumers)
- [ ] Are default values sensible for new optional fields?

A breaking change to a response body is removing a field or changing its type. Adding a new field to a response is generally safe. Adding a new *required* field to a request body breaks existing clients. When in doubt, make new request fields optional with sensible defaults.

### State management

- [ ] Is state updated atomically where needed?
- [ ] Are state transitions valid? (can you go from state A to state C directly?)
- [ ] Is cached data invalidated when the source of truth changes?
- [ ] Are optimistic updates rolled back on failure?

Check state machines explicitly: draw out the valid transitions and verify the code enforces them. For caching, trace every write to the source of truth and verify the cache is invalidated or updated in each case.

---

## 4. Performance (Priority: MEDIUM)

Performance issues rarely cause outages on day one, but they accumulate. Flag patterns that will degrade as data grows, but don't bikeshed micro-optimizations.

### Database queries

- [ ] Are there N+1 query patterns? (loop with a query inside)
- [ ] Are queries using indexes? (check WHERE clauses against schema)
- [ ] Are large result sets paginated?
- [ ] Are expensive queries cached where appropriate?
- [ ] Are database connections properly pooled and released?

The N+1 pattern is the single most common performance bug in PRs. Look for: a query that returns a list, followed by a loop that queries for related data per item. The fix is usually a JOIN, a batch query (`WHERE id IN (...)`), or an ORM eager-loading directive.

### Memory and compute

- [ ] Are there unbounded collections? (arrays that grow without limit)
- [ ] Are large files/blobs streamed instead of loaded into memory?
- [ ] Are expensive computations cached or debounced?
- [ ] Are there unnecessary allocations in hot paths?

Look for patterns like: reading an entire file into a string when streaming line-by-line would work, accumulating all database rows in memory before processing, or computing the same derived value repeatedly in a loop.

### Network and I/O

- [ ] Are external API calls retried with backoff?
- [ ] Are timeouts set for external requests?
- [ ] Are responses compressed where appropriate?
- [ ] Are unnecessary data fetches eliminated? (over-fetching from APIs)

Missing timeouts on external calls are a silent killer — one slow downstream service can exhaust your connection pool and bring down your entire application. Every outbound HTTP request should have an explicit timeout.

---

## 5. API Design (Priority: MEDIUM)

API design issues are cheaper to fix before merge than after consumers depend on the interface. Focus on correctness and consistency rather than philosophical debates.

- [ ] Are HTTP methods correct? (GET for reads, POST for creates, PUT/PATCH for updates, DELETE for deletes)
- [ ] Are status codes correct? (201 for created, 404 for not found, 400 for bad request, etc.)
- [ ] Are error response formats consistent with the rest of the API?
- [ ] Is input validation returning helpful error messages?
- [ ] Are new endpoints following existing naming conventions?

Check the existing API surface for conventions before flagging inconsistencies. If the codebase uses `snake_case` for JSON fields, a new endpoint using `camelCase` is worth flagging. If there is no consistent convention, don't invent one in a review comment.

---

## 6. Maintainability (Priority: LOW — only flag egregious issues)

Maintainability comments are the leading cause of review fatigue and blocked PRs. Only flag issues that would genuinely confuse the *next* developer who reads this code.

- [ ] Is there dead code introduced? (unused imports, unreachable branches)
- [ ] Are function/variable names clear and consistent with codebase conventions?
- [ ] Is complexity manageable? (deeply nested conditionals, functions >50 lines)
- [ ] Is code duplicated where it could be shared?
- [ ] Are magic numbers/strings extracted to named constants?

**Calibration note:** Only flag maintainability issues that would confuse the NEXT developer reading this code. Do not flag style preferences or minor naming choices. A function named `processData` is vague but not worth blocking a PR over. A function named `processData` that actually deletes records is worth flagging.

---

## 7. Testing (Priority: MEDIUM)

Test coverage comments should be specific. "Add tests" is not actionable. "This new error path on line 42 is not tested and could silently swallow database errors" is actionable.

### Coverage

- [ ] Are new code paths covered by tests?
- [ ] Are error paths tested? (not just happy path)
- [ ] Are edge cases tested? (empty input, boundary values)
- [ ] Are integration points tested? (API endpoints, database queries)

### Quality

- [ ] Do tests actually assert meaningful behavior? (not just "no error thrown")
- [ ] Are test names descriptive? (can you understand what's tested from the name?)
- [ ] Are tests isolated? (no dependency on execution order or external state)
- [ ] Are test fixtures/mocks appropriate? (not mocking the thing under test)

### Missing tests

- [ ] If source files changed, did corresponding test files change?
- [ ] If a bug was fixed, is there a regression test?
- [ ] If a new feature was added, are there feature tests?

A missing regression test for a bug fix is always worth flagging — it is the single highest-value test you can write, because it prevents a known failure mode from recurring.

---

## Applying the Checklist

Do NOT run through every checkbox mechanically. Instead:

1. **Look at the cluster type** and determine which dimensions are most relevant
2. **For a Data/Migration cluster:** focus on dimensions 3, 2, 1
3. **For an API cluster:** focus on dimensions 1, 2, 5, 4, 7
4. **For a Frontend cluster:** focus on dimensions 2, 1 (XSS), 4, 7
5. **For a Config/Infra cluster:** focus on dimensions 1 (secrets), 3 (breaking changes)
6. **For Tests:** focus on dimension 7

### When you find an issue

1. Note the file and line number
2. Note which dimension it falls under
3. Assess severity using the severity guide
4. Apply the actionability filter (7 checks from SKILL.md)
5. If it passes all filters, record the finding

### Severity quick-reference

| Severity | Criteria | Examples |
|----------|----------|---------|
| **must-fix** | Would cause data loss, security breach, or outage | SQL injection, missing auth, dropped migration column |
| **should-fix** | Bug or degradation likely under normal usage | Off-by-one in pagination, missing error handling on API call |
| **nit** | Improvement that doesn't affect correctness | Naming clarity, minor duplication, missing edge case test |

### Common false positives to avoid

- Flagging style preferences as correctness issues
- Flagging theoretical performance issues without evidence they matter at current scale
- Flagging missing tests for trivial getters/setters
- Flagging "potential" null issues that the type system already prevents
- Suggesting architectural refactors that are out of scope for the PR

The goal is a review that the author respects and acts on — not a comprehensive audit of every possible improvement. Prioritize ruthlessly.

## Steering notes

> These notes capture real mistakes observed during derailment testing.

1. **Security and correctness are always dimensions 1-2.** Do not reorder the dimensions based on PR type. Even in a "refactor-only" PR, check security and correctness first -- refactors can inadvertently change auth boundaries or error handling.
2. **For deprecation PRs, dimension 3 (Data Integrity) expands to include backwards compatibility and migration completeness.** Check: are all callers updated? Is there a deprecation warning for callers that were not updated? Is the migration path documented?
3. **Dimension 7 (Maintainability) is the most over-reported dimension.** Only flag maintainability when it materially affects safety, comprehension of critical paths, or onboarding difficulty. "This could be more readable" is not a review finding unless the current code is actively misleading.
4. **Each dimension should produce at most 2-3 findings per cluster.** If you are generating more, you are likely being too granular. Batch related issues within a dimension into a single finding.

> **Cross-reference:** See `references/severity-guide.md` for how to calibrate finding severity within each dimension.
