# Decision tree — production readiness

Pre-deploy checklist for an MCP server that will face real users. Every item is a "yes / not applicable / fix before deploy" decision. Skipping items reliably surfaces as outages, not as theoretical concerns. Run this tree before announcing the server is live.

## How to use this checklist

For each check below: state the verification command, the common ways teams skip the check, and the production failure that follows when skipped. Do not deploy with red items unless the user explicitly accepts the risk in writing (a comment in the PR, an issue, a Slack note).

The checklist is **gating** — production readiness means every item is green or explicitly waived. A green test on one item does not back-door another.

## Pre-deploy checklist

### 1. Tests cover schema validation, error recovery, advanced protocol negotiation

**Verify.** Run the suite. Inspect coverage of: valid input shapes, invalid input shapes, business-error paths, transport failures, capability-negotiation drops (sampling / elicitation / roots on a non-supporting client).

**Skip patterns.** "We tested manually with the Inspector"; "the SDK validates so we don't need tests"; coverage drops below 70%.

**Failure mode.** First malformed input from a real agent crashes the tool; agents abandon the workflow.

**Pattern reference.** `../patterns/testing.md`.

### 2. Threat model documented and addressed

**Verify.** Re-read `security-posture.md`. Open the doc that records the threat model (a `SECURITY.md` or similar). Confirm every applicable defense is wired.

**Skip patterns.** "It's behind OAuth so we're fine"; no SSRF defenses on outbound calls; no audit log.

**Failure mode.** SSRF to internal cloud metadata; cross-tenant data leak; missing forensics on incident.

**Pattern reference.** `../patterns/security.md`, `../patterns/auth-identity.md`, `../patterns/threat-catalog.md`, `security-posture.md`.

### 3. Auth flow tested end-to-end

**Verify.** A non-developer account completes a full OAuth code+PKCE flow. Token includes the right audience. Refresh works. Step-up consent surfaces correctly for elevated scopes. PRM endpoint resolves.

**Skip patterns.** "It works for the dev team's accounts"; one scope tested, others assumed; refresh never run.

**Failure mode.** First non-developer user can't authenticate; refresh fails after 60 minutes; token audience mismatch with upstream rejects the call.

**Pattern reference.** `../patterns/auth-identity.md`.

### 4. Sessions clean up on disconnect

**Verify.** Kill a client mid-session. Check that the server releases the session within the configured timeout. Confirm no orphan in-memory state. Check the metric for active sessions trends back to zero.

**Skip patterns.** Session map grows unbounded; no `disconnect` handler; cleanup deferred to GC.

**Failure mode.** Memory leak; the server hits OOM after a deploy day with many flapping connections.

**Pattern reference.** `../patterns/session-and-state.md`.

### 5. Caching strategy implemented (or explicitly not needed)

**Verify.** For each high-frequency tool, confirm there is a cache layer with the right key and TTL — or document explicitly why caching is not needed (e.g., always-unique inputs).

**Skip patterns.** "We'll add caching later"; cache key includes the bearer token; no invalidation on writes.

**Failure mode.** Upstream API rate-limited by your own server's repeated reads; cost spike; user-visible latency.

**Pattern reference.** `../patterns/caching-economics.md`.

### 6. Logging structured (no PII; redact tokens)

**Verify.** Log a sample call. Inspect the log line. Confirm structured JSON to stderr (never stdout — corrupts the protocol channel). Confirm bearer tokens, API keys, emails, phones are redacted. Confirm tool name, params (sanitized), status, duration are present.

**Skip patterns.** `console.log` to stdout; logs include `Authorization` headers; PII echoed unredacted.

**Failure mode.** Audit and security reviews fail; logs are unsearchable; protocol channel breaks when stdout is shared.

**Pattern reference.** `../patterns/transport-and-ops.md`.

### 7. Telemetry — span tracing or per-call audit

**Verify.** Pick a single tool call, trace it through to upstream APIs and back. Span ids propagate. Per-call audit row written.

**Skip patterns.** Logs only, no tracing; audit row missing tenant id.

**Failure mode.** Incident response can't reconstruct a session; cross-tenant questions un-answerable.

**Pattern reference.** `../patterns/transport-and-ops.md`.

### 8. Rate limiting at the transport

**Verify.** Send N+1 requests at the per-category rate-limit cap. Confirm the (N+1)-th gets `isError: true` with `retry_after_ms`. Confirm per-tenant isolation (one tenant's burst doesn't starve another).

**Skip patterns.** No rate limit; one global bucket; burst-only without sustained refill; no `retry_after_ms` in the response.

**Failure mode.** A single agent's retry loop eats the whole server's budget; cost spikes; cascading failure.

**Pattern reference.** `../patterns/transport-and-ops.md`, `error-strategy.md`.

### 9. Healthcheck endpoint

**Verify.** `GET /health` returns per-component status (database / cache / upstreams each `healthy | degraded | unhealthy`). On Kubernetes, wire to liveness and readiness probes. Optional `?include_metrics=true` exposes throughput, latency, error rate.

**Skip patterns.** No `/health` endpoint; one-line `{"ok": true}` with no per-component detail; health "always returns 200".

**Failure mode.** Load balancer routes traffic to an unhealthy pod; rolling deploy succeeds but new pods serve errors.

**Pattern reference.** `../patterns/transport-and-ops.md`.

### 10. Deployment platform tested

**Verify.** Deploy to the chosen platform (Cloudflare Workers, Vercel, Lambda, Cloud Run, ACA, Modal, Fly, Railway, Smithery, Docker). Run a real session through it. Inspect: cold start, session affinity, transport (Streamable HTTP, NOT SSE), graceful shutdown on deploy, env vars present.

**Skip patterns.** "It works locally"; deploy untested with real client; SSE used because it was the example in the SDK docs.

**Failure mode.** Cold start drops the first request; session re-routes mid-call to a different pod with no state; SSE incompatible with the load balancer.

**Pattern reference.** `../patterns/transport-and-ops.md`.

### 11. Registry / distribution plan

**Verify.** Decide where the server lives: internal git, NPM, Smithery, Docker MCP Catalog, official Registry. Confirm versioning scheme. Confirm namespace ownership.

**Skip patterns.** Publishing to v0 of the official Registry (still unstable); namespace squatted by another MCP; version pinning unclear.

**Failure mode.** v0 registry breaks on a schema rev; users can't install; namespace dispute.

**Pattern reference.** `../patterns/registry-and-distribution.md`.

### 12. Graceful shutdown on SIGTERM

**Verify.** Send SIGTERM. Confirm the server stops accepting new requests, drains in-flight calls within the grace period, then exits cleanly. On Kubernetes, set `terminationGracePeriodSeconds` accordingly.

**Skip patterns.** Hard exit on SIGTERM; in-flight calls dropped without a final result frame.

**Failure mode.** Every deploy is a small outage for active sessions.

**Pattern reference.** `../patterns/transport-and-ops.md`.

### 13. Resource limits set

**Verify.** Container limits: 250m–1000m CPU, 256–512Mi memory (adjust to actual profile). HPA targets CPU 70% or memory 80%. RollingUpdate with `maxUnavailable: 0` and `maxSurge: 1` if multi-replica.

**Skip patterns.** No limits → noisy neighbor; no HPA → can't scale; no rolling update strategy.

**Failure mode.** OOM kills; cold-start storms; outage on deploy.

**Pattern reference.** `../patterns/transport-and-ops.md`.

### 14. Capability negotiation tested

**Verify.** Connect a client that does NOT support sampling / elicitation / roots. Call a tool that uses them. Confirm graceful fallback (text response, no silent drop).

**Skip patterns.** Tested only on Claude Code; assumed every client supports the same features.

**Failure mode.** Cursor / Windsurf / VS Code users see a blank screen or a confused agent.

**Pattern reference.** `../patterns/advanced-protocol.md`, `../patterns/client-compatibility.md`.

### 15. Loop detection (server-side)

**Verify.** Hash `tool_name + JSON.stringify(params)`. After N (default 3) identical calls within T (default 120s), respond with `isError: true` + "loop detected".

**Skip patterns.** None; agents cannot detect their own loops.

**Failure mode.** A single agent's stuck loop ticks up your bill and your upstream's quota.

**Pattern reference.** `error-strategy.md`, `../patterns/error-handling.md`.

### 16. Data hygiene — no sensitive data in tool responses

**Verify.** Sample tool responses. Confirm no API keys, no internal IDs that leak architecture, no stack traces, no email/phone unless explicitly requested.

**Skip patterns.** Returning the upstream's full response; stack traces in error content.

**Failure mode.** Sensitive data enters the LLM context; downstream prompts leak it.

**Pattern reference.** `../patterns/security.md`.

## Final go/no-go

Before announcing the server is live:

- [ ] Every checklist item above is green or explicitly waived.
- [ ] An on-call or owner is named.
- [ ] An incident-response runbook exists (logs, dashboards, rollback command).
- [ ] A rollback plan is rehearsed (last green deploy is one command away).
- [ ] First-day metrics dashboard is up: tool-call count, error rate, P95 latency, active sessions.

If any of those is blank, you are not deploying — you are launching with one foot off the ground.

## Anti-patterns

- **Cold-tested on the dev team's accounts only.** The first non-dev user finds the bugs in production.
- **`{"ok": true}` healthcheck.** The LB happily routes traffic to broken pods.
- **No graceful shutdown.** Every deploy is an outage.
- **PII or tokens in logs.** Logs leak; this is the #1 audit finding.
- **One global rate-limit bucket.** A noisy tool starves the rest.
- **Skipping capability negotiation tests.** Cursor users discover the bugs.
- **Publishing to v0 of the official Registry.** The schema is still unstable.
- **No loop detection.** The first stuck retry is a credit-card surprise.

## Cross-references

- Transport, deployment, ops specifics: `../patterns/transport-and-ops.md`.
- Registry and distribution: `../patterns/registry-and-distribution.md`.
- Testing patterns and eval-driven development: `../patterns/testing.md`.
- Auth and identity: `../patterns/auth-identity.md`.
- Caching: `../patterns/caching-economics.md`.
- Session and state lifecycle: `../patterns/session-and-state.md`.
- Threat catalog (named MCP attacks, CVEs): `../patterns/threat-catalog.md`.

## When to re-run this checklist

- Before every initial production deploy.
- Before any deploy that changes auth, transport, or state model.
- After any incident — re-run the affected items.
- After SDK or platform major version bumps.
