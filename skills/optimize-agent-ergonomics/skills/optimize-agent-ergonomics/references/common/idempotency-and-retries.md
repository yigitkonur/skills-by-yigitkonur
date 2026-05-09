# idempotency-and-retries — operations with side effects must be safe to retry

Operations with side effects must be safe to retry. The agent's harness retries; the user's harness retries; the platform retries; the pipeline retries. Verbs carry semantics; idempotency keys make those semantics enforceable.

## The 5 verbs and their semantics

Pick the verb deliberately. Each carries a contract about behavior on repeat calls.

| Verb | Absent target | Present target | Retry-safe? |
|---|---|---|---|
| `create` | Create | Fail (conflict) | With idempotency key only |
| `apply` | Create | Update / patch to desired state | After conflict resolution |
| `ensure` | Create | No-op or update if needed | Yes (always) |
| `delete` | Success (already absent = done) | Delete | Yes (always) |
| `update` | Fail (not found) | Update | Yes (idempotent on same input) |

Pick by intent:

- **`create`** when "this should be a new thing, fail if it already exists." Force the agent to choose between alternate name, fetch existing, or use force flag on conflict.
- **`apply`** when "make the current state match this spec." Declarative; ideal for config-as-code, infrastructure, deployments.
- **`ensure`** when "this thing should exist; do whatever it takes." Often used for setup tasks, side-effect-light operations.
- **`delete`** when "this thing should not exist after this call." Idempotent by design — already gone is success.
- **`update`** when "modify an existing thing; don't create one." Requires explicit identifier; fails fast on absence.

## Verb-by-verb worked examples

### `create-issue` — fails on duplicate

```json
{
  "ok": false,
  "error": {
    "class": "conflict",
    "code": "ISSUE_EXISTS",
    "message": "Issue 'fix-login-bug' already exists at /issues/143.",
    "existing_id": "143",
    "retryable": false,
    "next_action": { "tool": "get_issue", "args": { "issue_id": "143" } }
  }
}
```

Agent's options:
- Fetch the existing issue and update it instead.
- Pick a different title.
- Use a force / overwrite flag (if exposed; `--force-create` or similar).

`create` is the right verb when duplicates are user-meaningful. Don't make `create` silently re-create — that's the worst-of-both pattern (confuses humans, creates duplicates).

### `apply-config` — converges to desired state

```bash
$ myco apply --file deploy.yaml --json
```

```json
{
  "ok": true,
  "result": {
    "changes": [
      { "action": "update", "resource": "deployment/web", "field": "replicas", "old": 2, "new": 3 },
      { "action": "noop",   "resource": "service/web" },
      { "action": "create", "resource": "configmap/api-keys" }
    ]
  },
  "schema_version": "1"
}
```

Re-running with the same `deploy.yaml`:

```json
{ "ok": true, "result": { "changes": [{ "action": "noop", "...": "all" }] }, "schema_version": "1" }
```

Apply is idempotent: same input → same end state. Always returns the change set so the agent can verify.

### `ensure-deployment` — alias for apply, idempotent by design

```typescript
server.tool("ensure_deployment", {
  description: "Ensure a deployment with the given spec exists and matches. Idempotent: re-running with the same input is safe and produces the same end state.",
  inputSchema: z.object({
    name: z.string(),
    image: z.string(),
    replicas: z.number().min(1),
  }),
}, async ({ name, image, replicas }) => {
  const existing = await getDeployment(name);
  if (!existing) {
    await createDeployment({ name, image, replicas });
    return { content: [{ type: "text", text: `Created ${name}` }], structuredContent: { action: "created" } };
  }
  if (existing.image === image && existing.replicas === replicas) {
    return { content: [{ type: "text", text: `${name} already matches` }], structuredContent: { action: "noop" } };
  }
  await updateDeployment(name, { image, replicas });
  return { content: [{ type: "text", text: `Updated ${name}` }], structuredContent: { action: "updated" } };
});
```

`ensure` is `apply`'s simpler cousin — when the surface area is small enough that you don't need the full apply diff machinery.

### `delete-namespace` — succeeds on already-absent

```bash
$ myco delete-namespace prod --json
```

First call:
```json
{ "ok": true, "result": { "deleted": "prod", "resources_removed": 12 }, "schema_version": "1" }
```

Second call (already deleted):
```json
{ "ok": true, "result": { "deleted": "prod", "already_absent": true }, "schema_version": "1" }
```

`delete` returns success when the target is already gone. The agent doesn't have to pre-check existence; it just calls delete and the call is correct either way.

Anti-pattern: returning `not_found` when the resource is already deleted. That makes the agent guess: was this an error worth surfacing, or just a stale state? Idempotent delete removes the ambiguity.

### `update-issue` — fails on not-exists

```json
{
  "ok": false,
  "error": {
    "class": "not_found",
    "code": "ISSUE_NOT_FOUND",
    "message": "Issue '143' not found.",
    "retryable": false,
    "next_action": { "tool": "create_issue", "args": { "title": "..." } }
  }
}
```

`update` requires the resource to exist. Agent chooses: create instead, search for the right ID, or surface to user. Don't conflate update with apply — they have different contracts.

## Idempotency keys

For operations where retry-safety matters but the verb doesn't make it automatic (`create`, `update`, side-effect-heavy operations), expose an idempotency key.

### Designing the key

- **Client-supplied** — the agent generates and passes. The server caches `key → result` for some TTL.
- **Format** — opaque string up to ~256 chars. UUIDs are common; descriptive keys (`deploy-2026-05-08-abc`) are debuggable.
- **TTL** — 24 hours is the common choice. Long enough to cover retry cycles; short enough to avoid storage bloat.
- **Cache key** — `(client_id, key)` — one tenant's keys don't collide with another's.
- **Cache content** — the full success response. Re-serving it produces a deterministic re-invocation.

### When to require keys

| Workload | Key requirement |
|---|---|
| `create` of a billable / external-facing resource (subscription, payment, invoice, deploy) | **Required**. Without it, retries duplicate the side effect. |
| `create` of an internal-only resource | Optional; describe in description. |
| `update` of a resource | Optional; usually idempotent on same input anyway. |
| `apply` / `ensure` | Optional; usually idempotent by design. |
| `delete` | Not needed; verb is idempotent by design. |

### Surface mapping

CLI:
```bash
myco create-subscription --plan pro --customer cust_123 --idempotency-key sub-2026-05-08-cust_123 --json
```

Re-running with the same key returns the cached result, not a new subscription:
```json
{ "ok": true, "result": { "subscription_id": "sub_abc123", "cached": true }, "schema_version": "1" }
```

MCP:
```typescript
server.tool("create_subscription", {
  description: "Create a subscription. Required: plan, customer. Highly recommended: idempotency_key (UUID-like; safe re-tries within 24h).",
  inputSchema: z.object({
    plan: z.enum(["pro", "enterprise"]),
    customer: z.string(),
    idempotency_key: z.string().optional()
      .describe("Client-generated key. Same key within 24h returns the same result; safe to retry."),
  }),
}, async ({ plan, customer, idempotency_key }) => {
  if (idempotency_key) {
    const cached = await idempotencyCache.get(idempotency_key);
    if (cached) return cached;
  }
  const result = await createSubscription({ plan, customer });
  if (idempotency_key) await idempotencyCache.set(idempotency_key, result, 86400);
  return result;
});
```

## Retry semantics

When a transient error returns, the agent's harness retries. Make the retry behavior predictable.

### Exponential backoff with jitter

The standard formula:

```
delay = min(initial * (factor ^ attempt), max) + jitter
jitter = delay * jitter_fraction * random(-1, 1)
```

Reasonable defaults:

| Param | Value | Rationale |
|---|---|---|
| `initial` | 100ms | Fast retry on real-time-ish operations. |
| `factor` | 2.0 | Doubles each attempt — standard exponential. |
| `max` | 30s | Cap per-attempt delay; longer is the user's problem, not the harness's. |
| `jitter` | 0.2 | ±20% randomization to avoid thundering herd. |
| `max_attempts` | 5 | Most transient issues resolve within 4–5 attempts; beyond that, escalate. |

### Honoring `retry_after`

If the error envelope includes `retry_after` (or `retry_after_ms`), use it instead of computed backoff:

```python
delay = error.get("retry_after", computed_backoff)
```

`retry_after` is the server's explicit guidance — typically present on rate-limit errors. Ignoring it produces 429-loop disasters.

### What's safe vs. what isn't

| Class | Retry behavior |
|---|---|
| `transient` (rate_limit, timeout, network, dependency_failed) | Yes — exponential backoff + jitter. |
| `validation` | No — repair input; resubmit is not retry. |
| `auth` | No — escalate to user / refresh token, then retry. |
| `not_found` | No — disambiguate or surface. |
| `conflict` | Maybe — re-read state; force flag if appropriate; otherwise no. |
| `internal` (unexpected) | Maybe (once) — the agent's harness can retry once; persistent crashes need a human. |

The error envelope's `retryable` flag is the canonical signal. The class table above is the rationale; the flag is the contract.

## Surface mappings

### CLI — flags and behavior

```
--idempotency-key <key>    client-supplied idempotency key (24h TTL on server)
--max-retries <n>          override default retry count (default: 5)
--retry-base-ms <ms>        override exponential base (default: 100)
--no-retry                  disable automatic retry; surface first error
--timeout <secs>            per-request timeout (default: 30s)
```

Auto-retry inside the CLI is optional but useful for hooks like `ssh`, `curl`-style operations where the user expects "just work" semantics. Document the retry behavior in `--help` so the agent and the user both know what to expect.

For long-running async operations, prefer the job-ID pattern over in-CLI retry:

```bash
myco deploy start --json    # returns { "job_id": "j_123" }
myco deploy follow j_123 --json --stream    # JSONL events
```

### MCP — idempotency in the description

Hint at idempotency in the tool description so the model knows whether retry is safe:

```typescript
server.tool("apply_config", {
  description: "Apply a desired-state config. **Idempotent**: re-running with the same input is safe and produces the same end state.",
  // ...
});

server.tool("send_email", {
  description: "Send an email to the customer. **Not idempotent**: every call sends a new email. Use idempotency_key to make retries safe.",
  // ...
});
```

The description is what the model reads at decision time. State the idempotency contract there. Then enforce it server-side.

### Server-side dedup

Beyond client-supplied keys, servers can implement automatic dedup based on input hash within a short window:

```typescript
const CALL_DEDUP_TTL_MS = 5000;
const recentCalls = new Map<string, Promise<Result>>();

async function dedupedCall(input: Input) {
  const key = sha256(JSON.stringify(input));
  if (recentCalls.has(key)) return recentCalls.get(key)!;
  const promise = doActualCall(input);
  recentCalls.set(key, promise);
  setTimeout(() => recentCalls.delete(key), CALL_DEDUP_TTL_MS);
  return promise;
}
```

Useful for catching agents that double-fire on retry within a few seconds. Doesn't replace explicit keys; complements them.

## Anti-patterns to refuse

**`create` that silently re-creates.**
```bash
myco create user --name alice
{ "result": { "user_id": "u_001" } }
myco create user --name alice
{ "result": { "user_id": "u_002" } }   # ANTI-PATTERN: created a duplicate
```
Either fail on duplicate (use `create`) or converge (use `apply` / `ensure`). Don't silently spawn duplicates — the user / agent has no way to know.

**`delete` that fails on already-absent.**
```bash
myco delete user u_001
{ "ok": true }
myco delete user u_001
{ "error": { "class": "not_found" } }   # ANTI-PATTERN: not idempotent
```
`delete` must succeed on already-gone. The agent shouldn't have to pre-check.

**`update` that creates on missing.**
```bash
myco update user u_999 --name bob
{ "result": { "user_id": "u_999" } }   # ANTI-PATTERN: silently created u_999
```
That's not update — that's apply. Pick the right verb.

**Idempotency key with no TTL or with eternal TTL.**
Eternal TTL bloats storage and turns "same key" into "same result forever" — when the user actually wanted to retry an operation an hour later, they get the cached old result. 24h is the sweet spot.

**Per-call retry inside the tool when the agent is already retrying.**
The agent's harness retries. The MCP client retries. The CLI shouldn't independently retry on top — that produces multiplicative attempts (3 × 5 × 5 = 75 attempts). Either retry once and surface, or document explicitly that the tool retries internally.

**Ignoring `retry_after`.**
The server told the agent to wait 60s. The agent retried in 1s. The server returned 429 again. Cycle repeats. Honor `retry_after`.

**Mixing idempotency-key with retryable=false.**
"Use this key for safe retries" + "retryable: false" — the contract is contradictory. If the operation is permanent on failure, the key isn't doing work. If the key is doing work, the operation is retryable.

**No `idempotency_key` on a side-effect-heavy operation.**
`charge-card` without an idempotency key is a billing incident waiting to happen. Required for mutations to external systems with charge / send / commit semantics.

## Decision matrix: which verb, which pattern

| Use case | Verb | Idempotency key | Retry behavior |
|---|---|---|---|
| Create a new GitHub issue | `create` | Recommended | Conflict on duplicate; agent picks recovery. |
| Apply a Kubernetes manifest | `apply` | Optional | Idempotent by spec; safe to retry. |
| Ensure a feature flag is enabled | `ensure` | Not needed | Always safe. |
| Delete a deploy | `delete` | Not needed | Idempotent on already-absent. |
| Update an issue's status | `update` | Optional | Idempotent on same input. |
| Charge a customer | `create` (or `apply` if an order ID exists) | **Required** | Conflict on duplicate; never silently retry. |
| Send a transactional email | `create` | **Required** | Otherwise retries spam users. |
| Schedule a meeting | `create` | Recommended | Conflict on overlap; agent handles. |
| Cancel an order | `delete` (or `update status=cancelled`) | Not needed (delete) / optional (update) | Idempotent. |

## Cross-references

- For error envelopes that surface retry guidance, read `error-strategy.md`.
- For exit-code mapping that signals retry-safety, read `../cli/exit-codes.md`.
- For multi-step workflows where each step has its own idempotency story, read `iterative-loops.md`.
- For surface-specific verb idioms, read `../cli/architect-new.md` (CLI verb conventions) or `../mcp/patterns/tools.md` (MCP tool design).
