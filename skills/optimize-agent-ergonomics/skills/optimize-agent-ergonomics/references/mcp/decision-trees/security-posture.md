# Decision tree — security posture

Pick the threat model from the deployment context. Local stdio has near-zero network surface; remote multi-tenant HTTP has the full attack surface (OAuth 2.1, RFC 9728 PRM, audit logs, per-call authorization). Threat model selection is not optional — guessing here means an audit-time finding instead of a design-time decision. Source: `optimize-agentic-mcp/references/decision-trees/security-posture.md`.

## Decision branches

```
START: How is the server deployed?
|
+-- Local stdio (one user, one process, user's machine)
|   +-- Trust boundary = the user's machine
|   +-- Threats: human confirmation gaps on destructive ops; supply-chain
|   +-- Apply:
|   |   - human confirmation for delete/send/modify
|   |   - read-only tools auto-approved (search_, list_, get_)
|   |   - server-side input validation regardless
|   --> ../patterns/security.md
|
+-- Local HTTP (loopback port on user's machine)
|   +-- Trust boundary = same machine, but a port is listening
|   +-- Additional threats:
|   |   - CSRF from a malicious page in the user's browser
|   |   - Other processes on the same machine port-scanning
|   +-- Apply:
|   |   - bind to 127.0.0.1 only (NOT 0.0.0.0)
|   |   - Origin/Referer header check on all requests
|   |   - per-session secret bound to the launching client
|   --> ../patterns/security.md, ../patterns/transport-and-ops.md
|
+-- Remote HTTP, single tenant (one organization, OAuth)
|   +-- Trust boundary = the public internet
|   +-- Apply the full remote threat model:
|   |   - OAuth 2.1 + PKCE (no implicit, no resource-owner password)
|   |   - RFC 9728 Protected Resource Metadata (PRM) endpoint
|   |   - audience-restricted tokens (your server is the audience)
|   |   - SSRF defenses (block 10/8, 172.16/12, 192.168/16, 127/8)
|   |   - HTTPS only; HSTS; structured audit log per call
|   |   - rate limiting at transport (per-token bucket)
|   --> ../patterns/auth-identity.md, ../patterns/security.md
|
+-- Remote HTTP, multi-tenant (B2B SaaS, marketplace)
|   +-- Trust boundary = the public internet, hostile co-tenants
|   +-- Add to single-tenant baseline:
|   |   - per-tenant key isolation; per-call tenant check
|   |   - delegated permissions (caller's scope, not superuser)
|   |   - OBO (on-behalf-of) for upstream calls; audience claim required
|   |   - CIMD / Dynamic Client Registration if public marketplace
|   |   - per-tenant rate limit + per-tenant audit log
|   |   - row-level isolation in any shared cache
|   --> ../patterns/auth-identity.md, ../patterns/security.md, ../patterns/threat-catalog.md
|
+-- Step-up consent required (high-stakes operations within an authorized session)
    +-- delete user data; transfer money; change auth config; admin ops
    +-- Apply: separate scope (mcp:admin); short TTL (15min); re-auth UI
    --> ../patterns/auth-identity.md, ../patterns/prompt-gates.md
```

## Threat-model selection routine

Run this in order; first match wins.

1. **Is the server reachable from the network at all?** If no → local stdio model.
2. **Is the listener on a loopback interface only?** If yes → local HTTP model.
3. **Is there exactly one tenant (one organization, fixed customer base)?** If yes → single-tenant remote.
4. **Does the server serve more than one tenant?** Multi-tenant remote.
5. **Are any operations high-stakes within an already-authorized session?** Add step-up consent.

The model is cumulative: multi-tenant inherits everything from single-tenant; single-tenant inherits everything from local HTTP. **Skipping a level is a finding.**

## Local stdio — what to apply

Even with a near-zero network surface:

- Human confirmation for **every** state-changing tool (`delete_*`, `send_*`, `modify_*`, `transfer_*`).
- Read-only tools (`search_*`, `list_*`, `get_*`, `describe_*`) auto-approved.
- Server-side input validation. Never trust LLM-generated input.
- Treat tool descriptions as data the LLM will read at runtime — sanitize anything that originates from upstream APIs.
- Supply-chain hygiene: pin SDK versions; monitor advisories.

## Local HTTP — additional defenses

When the server listens on a loopback port:

- Bind to `127.0.0.1`, not `0.0.0.0`.
- Reject requests without `Origin: chrome-extension://...` or the expected MCP client origin.
- Generate a per-session shared secret and require it in the `Authorization` header.
- Log the launching PID; reject when the secret is reused from a different PID family.

## Remote HTTP — the full threat model

### OAuth 2.1 profile

- Use `code` flow with PKCE (S256).
- No implicit. No resource-owner password credentials.
- Refresh tokens rotated.
- Discovery via RFC 9728 PRM (`/.well-known/oauth-protected-resource`).
- Token audience must include your server's identifier; reject tokens audienced elsewhere.

### Per-call authorization

- Validate the bearer token on every tool call, not just on session establishment.
- Scope check the operation: `mcp:read`, `mcp:write`, `mcp:delete`, `mcp:admin`.
- Use the caller's scoped permissions for upstream calls — never a superuser key.

### SSRF defenses

If the server makes outbound HTTP calls:

- Resolve the hostname server-side; reject private IP ranges before fetching.
- Block `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `::1`, `fc00::/7`.
- Disallow URL schemes other than `https://` (and `http://` only on explicit, audited allowlists).
- Time out outbound calls; cap response size.

### Audit log

Per call: timestamp, tenant, user, tool name, params (with PII redacted), result success/fail, duration, IP.

Stream to an append-only sink. Never `console.log` to stdout (corrupts the protocol channel).

### Rate limiting

Per-tenant token buckets, separated by tool category:

| Category | Capacity | Refill |
|---|---|---|
| `read` | 120 | 10/s |
| `write` | 30 | 2/s |
| `ai` (expensive) | 10 | 0.5/s |
| `external_api` | 20 | 1/s (or upstream's limit) |

Return `retry_after_ms` in rate-limit errors; the agent backs off correctly.

### CORS

Only when browser clients exist. Allow specific origins; never `*` with credentials. Pre-flight `OPTIONS` is mandatory.

## Multi-tenant — additional defenses

- **Per-tenant isolation**: tenant id resolved server-side from the token; never trusted from input.
- **OBO for upstream**: when calling another API on behalf of the user, mint a fresh token with the upstream service as audience and the user's scoped permissions; never forward the user's MCP token.
- **Per-tenant cache rows**: cache keys include the tenant id so a co-tenant cannot poll into another tenant's data.
- **Cross-tool injection defenses**: a malicious tool description in one connected MCP can influence another via shared context — see `../patterns/threat-catalog.md` for the named attack catalog (TPA, line jumping, FSP, ATPA, shadowing). Mitigations: separate high-trust from low-trust contexts, sanitize external tool descriptions, signed manifests.
- **PII tokenization**: replace emails / phones / SSNs with `[EMAIL_1]`, `[PHONE_1]` before the LLM sees them; un-tokenize in the response path before showing to the user.

## When to require step-up consent

Step-up means: even though the session is already authorized, a specific operation requires a fresh consent prompt with a higher scope.

Triggers:
- **Destructive at scale**: deleting >N records, terminating production resources.
- **Money movement**: transferring funds, refunding > threshold.
- **Auth config**: rotating secrets, adding admins.
- **Cross-tenant or admin ops**: operations that touch tenants other than the caller's.

Implementation:
- Separate scope (`mcp:admin`) requested only when needed.
- TTL of 15 minutes for elevated scope; drop back to base scope after.
- Re-auth UI surfaced via OAuth's `prompt=consent`.

Deep dive: `../patterns/auth-identity.md` (CIMD + step-up consent), `../patterns/prompt-gates.md`.

## Anti-patterns

- **No auth on remote.** Single biggest finding in the wild.
- **Forwarding the user's token upstream.** Use OBO with audience checks.
- **Trusting tenant id from input.** Always resolve from the token.
- **`Authorization: Bearer ${userToken}` in cache keys.** Token lifetime ≠ cache lifetime; key off the user id, not the token.
- **`*` CORS with credentials.** Catastrophic.
- **SSE for new remote deployments.** Deprecated; use Streamable HTTP. Source: `optimize-agentic-mcp/SKILL.md` pitfall #9.
- **Logging tokens or PII.** Redact at the log boundary; logs leak.
- **Skipping the audit log.** Without it, a breach has no forensics.
- **One global rate limit.** A 10 r/s cap on `read` and `ai` together starves both. Per-category buckets.

## Cross-references

- Generic defenses (input validation, sandboxing, prompt-injection): `../patterns/security.md`.
- Named MCP attacks, CVEs, defense tooling: `../patterns/threat-catalog.md`.
- 2025-11-25 OAuth profile (PKCE, PRM, CIMD, OBO, step-up): `../patterns/auth-identity.md`.
- Prompt gates and approval workflows: `../patterns/prompt-gates.md`.
- Transport and ops (TLS, reverse proxy, rate limiting infra): `../patterns/transport-and-ops.md`.
- Production-readiness gating before deploy: `production-readiness.md`.

## When to re-evaluate

- Moving from local dev to remote deployment — apply the full remote threat model.
- Adding a third-party MCP server to the agent's environment — context-isolation review.
- Tool starts processing user-generated content — sanitization + PII tokenization.
- Handling regulated data — PII tokenization becomes mandatory.
- Single-user scope grows to multi-tenant — per-tenant isolation, OBO, audit per tenant.
- Trust incident or new CVE — re-read `../patterns/threat-catalog.md`.
