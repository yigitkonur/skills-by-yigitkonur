# Auth and identity

Protocol-level authorization for remote MCP servers under the 2025-11-25 OAuth 2.1 profile. Five patterns the auditor must recognize: OAuth 2.1, RFC 9728 PRM (Protected Resource Metadata), CIMD (Client-Initiated MCP Delegation), OBO (On-Behalf-Of), and step-up consent. Cross-link to `security.md` for prompt injection / PII / SSRF, and `threat-catalog.md` for the named OAuth attack primitives. Sourced from `optimize-agentic-mcp/.../patterns/auth-identity.md`.

MCP moved from "auth optional, good luck" (2025-03-26) to a hardened OAuth 2.1 profile (2025-11-25) in three revisions. Three invariants now drive every pattern:

1. **Every token has an audience** — `aud` claim must match the MCP server's canonical URI byte-for-byte.
2. **Every client has verifiable identity** — pre-registered, CIMD URL-as-`client_id`, or DCR fallback.
3. **MCP servers never forward user tokens upstream** — always exchange via OBO.

---

## The 2025-11-25 spec diff

If your server or client was written against `2025-06-18` or earlier, assume it is wrong on at least one of: AS discovery, PRM location, DCR assumptions, step-up scope, or CIMD. Audit against the diff first, then code.

| Area | 2025-06-18 | 2025-11-25 |
|---|---|---|
| AS metadata discovery | RFC 8414 only | RFC 8414 **OR** OIDC Discovery 1.0 — AS MUST implement at least one; clients MUST support **both** |
| PRM discovery | `WWW-Authenticate` challenge required on 401 | Either the header OR `/.well-known/oauth-protected-resource` (SEP-985 Final, 2025-07-16) |
| DCR (RFC 7591) | SHOULD support | **MAY** support (compat only) |
| Client registration (new) | — | **CIMD (SEP-991)** recommended default — HTTPS URL as `client_id`, JSON manifest with `client_id`, `client_name`, `redirect_uris`, optional `jwks`/`jwks_uri` for `private_key_jwt` |
| PKCE | MUST per OAuth 2.1 §7.5.2 | MUST + MUST verify AS advertises support + MUST use `S256` when capable + MUST refuse if `code_challenge_methods_supported` is absent |
| Scopes / consent | Static `scopes_supported` | **Incremental / step-up** via `WWW-Authenticate scope=`; clients MUST treat challenged scope as authoritative; runtime escalation returns **403 `error="insufficient_scope"`** |
| Resource indicator (RFC 8707) | MUST | Unchanged — still MUST |
| Audience validation | Server MUST reject tokens not audienced for itself | Unchanged |
| Token passthrough | Forbidden (MUST NOT) | Unchanged |
| Redirect URIs | HTTPS or `localhost`; exact-match pre-registered | Same + under CIMD AS MUST validate against the fetched metadata doc |
| Invalid Origin on Streamable HTTP | — | Clarified: HTTP **403** |
| Governance | — | SDK tiering, Working Groups, formal SEP process |

Only one requirement was **relaxed**: DCR dropped from SHOULD to MAY. Everything else is additive hardening. Source: spec 2025-11-25 authorization (modelcontextprotocol.io/specification/2025-11-25/basic/authorization); SEP-985 Final (2025-07-16); WorkOS — MCP 2025-11-25 spec update (2025-11).

---

## RFC compliance map

When reviewing a server, tick off each row before touching anything else. Non-compliance almost always comes from missing one of these, not from implementing something exotic.

| RFC / Spec | Role in MCP | Who must implement |
|---|---|---|
| RFC 6749 OAuth 2.0 | Baseline — superseded within MCP by OAuth 2.1 | AS + clients |
| OAuth 2.1 (draft) | Auth-code + PKCE only — **no implicit, no ROPC**; short-lived access tokens; rotating refresh tokens for public clients | AS + clients |
| RFC 7591 DCR | Runtime client registration — **MAY** as of 2025-11-25 | AS (optional) + clients (fallback) |
| RFC 7592 DCR Management | Update/delete registrations | AS |
| RFC 8414 AS Metadata | `/.well-known/oauth-authorization-server[/path]` | AS (MUST offer this or OIDC) + clients (MUST support) |
| OIDC Discovery 1.0 | `/.well-known/openid-configuration[/path]` — alternate AS discovery | AS (MUST offer this or 8414) + clients (MUST support both) |
| RFC 9728 Protected Resource Metadata | `/.well-known/oauth-protected-resource` at the MCP server; declares `authorization_servers`, `scopes_supported`, `bearer_methods_supported` | MCP server (MUST) + clients (MUST consume) |
| RFC 8707 Resource Indicators | `resource=` on `/authorize` and `/token` — canonical URI of MCP server; binds the `aud` claim | Client (MUST send) + AS (SHOULD audience-restrict) + MCP server (MUST reject non-matching `aud`) |
| RFC 6750 Bearer Tokens | `Authorization: Bearer <token>`; `WWW-Authenticate` challenge with `error=`, `scope=`, `resource_metadata=` | Client + MCP server |
| RFC 8693 Token Exchange | OBO pattern — `subject_token` + `actor_token` → upstream-audienced token. Not in MCP spec, but commonly used by servers | MCP server + internal STS |
| CIMD I-D (SEP-991) | URL-as-`client_id`; JSON manifest hosted by the client at an HTTPS URL; optional `jwks` for `private_key_jwt` | Clients (SHOULD host) + AS (SHOULD fetch, MUST validate redirects against it) |

---

## OAuth 2.1 — first-connection flow

This is the reference sequence. Any deviation means your server is either pre-spec or non-compliant.

1. **Unauthenticated request.** Client POSTs to `https://mcp.example.com/mcp` without `Authorization`.
2. **Server challenges.** Response: `401` with `WWW-Authenticate: Bearer resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource", scope="files:read"`.
3. **PRM fetch.** Client GETs the PRM doc. Required fields: `resource`, `authorization_servers[...]`, `scopes_supported`, `bearer_methods_supported`.
4. **AS metadata fetch.** Using `authorization_servers[0]`:
   - Try RFC 8414 first: `/.well-known/oauth-authorization-server` and the path-appended form.
   - Fallback to OIDC Discovery: `/.well-known/openid-configuration` and its path-appended form.
   - Abort if `code_challenge_methods_supported` is absent — the AS cannot be trusted to enforce PKCE.
5. **Obtain `client_id`.** Three acceptable paths:
   - Pre-registered static `client_id` (traditional).
   - **CIMD**: use an HTTPS URL that serves the client's JSON manifest as the `client_id`.
   - DCR via `/register` as a last resort.
6. **PKCE.** `code_verifier` = 43–128 random chars; `code_challenge = BASE64URL(SHA256(code_verifier))`.
7. **Authorize.** Browser `GET /authorize?response_type=code&client_id=<id>&redirect_uri=<exact>&code_challenge=<...>&code_challenge_method=S256&state=<csrf>&scope=files:read&resource=https://mcp.example.com`.
8. **User consent.** AS authenticates the user and shows consent; redirects to the exact-match `redirect_uri` with `code` and `state`.
9. **Token exchange.** Client POSTs `/token` with `grant_type=authorization_code`, `code`, `code_verifier`, `redirect_uri`, `client_id`, and **`resource=https://mcp.example.com`** (MUST). AS returns an access token with `aud="https://mcp.example.com"` plus (optionally) a rotating refresh token.
10. **Authenticated retry.** Client retries the original MCP call with `Authorization: Bearer <token>`. Server validates signature, `iss`, `exp`, `nbf`, `aud` exactly equal to its canonical URI, and scope — then dispatches.

Source: spec 2025-11-25 authorization; Stytch — Cloudflare Workers OAuth walkthrough (2025-04-19); Christian Posta — MCP Auth step-by-step (2025).

---

## RFC 9728 PRM — Protected Resource Metadata

The PRM document is what makes MCP discoverable as an OAuth 2.0 Resource Server. It tells clients which Authorization Servers can issue tokens for this MCP server, what scopes exist, and how the bearer should be presented.

```json
GET https://mcp.example.com/.well-known/oauth-protected-resource

{
  "resource": "https://mcp.example.com",
  "authorization_servers": [
    "https://auth.example.com"
  ],
  "scopes_supported": [
    "files:read",
    "files:write",
    "billing:read"
  ],
  "bearer_methods_supported": ["header"],
  "resource_documentation": "https://docs.example.com/mcp"
}
```

Implementation in FastAPI:

```python
@app.get("/.well-known/oauth-protected-resource")
def prm():
    return {
        "resource": "https://mcp.example.com",
        "authorization_servers": ["https://auth.example.com"],
        "scopes_supported": ["files:read", "files:write", "billing:read"],
        "bearer_methods_supported": ["header"],
    }
```

Two ways the client discovers PRM (the spec accepts either, 2025-11-25):

1. The 401 response carries `WWW-Authenticate: Bearer resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource"`.
2. The client probes `/.well-known/oauth-protected-resource` directly (SEP-985 fallback).

Servers that implement only the header (and 404 on the `.well-known` path) break clients that probe directly. Implement both.

---

## CIMD — Client-Initiated MCP Delegation

CIMD (SEP-991) replaces DCR for new deployments. The client identity is anchored in DNS + HTTPS instead of a free-for-all `/register` endpoint. The `client_id` is an HTTPS URL that serves a JSON manifest:

```
GET https://client.example.com/.well-known/oauth-client

{
  "client_id": "https://client.example.com/.well-known/oauth-client",
  "client_name": "Example MCP Client",
  "redirect_uris": [
    "https://client.example.com/oauth/callback"
  ],
  "token_endpoint_auth_method": "none",
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "jwks_uri": "https://client.example.com/.well-known/jwks.json"
}
```

The Authorization Server fetches that document on every authorize request and exact-matches the `redirect_uri` parameter against the manifest's `redirect_uris`. Attackers cannot register a fake `redirect_uri` because they don't control the DNS for `client.example.com`.

When to choose CIMD over DCR:

| Constraint | Choose |
|---|---|
| New deployment, indie or enterprise | CIMD |
| Need anonymous client registration with no DNS | DCR (rate-limited) |
| Localhost-only desktop client | Pre-registered + software statement |
| Multi-app enterprise SSO | CIMD + identity assertion grants |

Source: MCP Blog — DCR vs CIMD (2025-08-22); SEP-991 draft; WorkOS — DCR, MCP, and OAuth (2025-12-09).

---

## Step-up consent — incremental scope

Static `scopes_supported` is no longer sufficient. When a tool call needs more scope than the current token carries, the server drives the client through a new consent round.

1. Client holds a token with `scope="files:read"` and calls a tool that needs `files:write`.
2. Server returns `403 Forbidden` with `WWW-Authenticate: Bearer error="insufficient_scope", scope="files:write", resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource"`.
3. Client **MUST** treat the challenged `scope` as authoritative (ignore the PRM's static `scopes_supported`).
4. Client starts a fresh `/authorize` round with `scope=files:write` and redoes PKCE, obtaining a new token.
5. Client retries the tool call with the new token.

Implementation sketch in FastAPI:

```python
from fastapi import Request, Response, HTTPException, Depends

@app.post("/mcp")
async def mcp_endpoint(req: Request, token = Depends(verify_token)):
    payload = jwt.decode(token, KEY, algorithms=["RS256"], audience=CANONICAL)
    needed_scope = scope_for_method(req.method)
    if needed_scope not in payload.get("scope", "").split():
        return Response(
            status_code=403,
            headers={
                "WWW-Authenticate": (
                    f'Bearer error="insufficient_scope", scope="{needed_scope}", '
                    f'resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource"'
                ),
            },
        )
    return await handle(req)
```

Edge cases:

- `client_credentials` clients (machine-to-machine) that cannot run a consent UI MAY abort and surface the error.
- Servers returning `403` without `scope=` in the header are spec-violating — clients must not attempt to guess scopes.
- When step-up is frequent, reconsider scope granularity — over-narrow scopes create noisy consent loops.

Source: spec 2025-11-25 — incremental authorization; WorkOS — MCP 2025-11-25 spec update (2025-11).

---

## OBO — On-Behalf-Of for upstream APIs

The MCP spec does not yet standardize OBO. Three patterns are in production today. Pick one; never fall back to forwarding the user's MCP token to upstream APIs (token passthrough is a spec MUST-NOT and a CWE-class vulnerability).

### Option A — RFC 8693 Token Exchange (strongest)

The MCP server holds its own client credential with an internal STS. It exchanges:

- `subject_token` = user's MCP access token (`aud="mcp.example.com"`)
- `actor_token` = MCP server's own token
- `resource` = upstream API canonical URI
- `scope` = narrow upstream scope

The STS returns a fresh token audienced for the upstream API with the real user as `sub`. Upstream RBAC applies to the user, not the MCP service account.

```python
@tool
async def list_leads(ctx: Context) -> dict:
    mcp_token = ctx.session.raw_token  # aud="mcp.example.com"
    upstream = await sts.exchange(
        subject_token=mcp_token,
        actor_token=service_actor_token,
        audience="https://api.upstream.com",
        scope="upstream:leads.read",
    )
    return await upstream_client.list_leads(token=upstream.access_token)
```

### Option B — Identity Assertion / Cross-App Access (XAA, `id-jag`)

Enterprise IdP issues a signed assertion tying the MCP client and the upstream app so tokens can be swapped without a second consent screen. WorkOS treats this as the 2025-11-25 default for enterprise MCP. Requires both apps connected to the same IdP with XAA enabled.

### Option C — URL-mode elicitation (lightest)

Server returns an elicitation that points the client to an upstream OAuth URL. **Critically, the callback goes to the MCP server, not the client.** The server stores the upstream refresh token keyed by the MCP identity's `sub` and refreshes on demand. Upstream tokens never leave the trusted server. Tradeoff: an extra consent screen.

```ts
// On callback (Cloudflare Workers KV):
await env.UPSTREAM_TOKENS.put(
  `github:${mcpSub}`,
  JSON.stringify({ refresh_token, aud: "api.github.com", scopes }),
  { metadata: { createdAt: Date.now() } },
);

// On subsequent tool calls:
const stored = JSON.parse(await env.UPSTREAM_TOKENS.get(`github:${mcpSub}`));
const access = await refreshUpstream(stored.refresh_token);
return fetchGithub(access.access_token, ...);
```

| Pattern | Best for | Key cost |
|---|---|---|
| RFC 8693 | Single enterprise, tight STS | STS infrastructure |
| `id-jag` / XAA | Multi-app enterprise SSO | Both apps on same IdP |
| URL elicitation | Consumer / indie MCP | Extra consent UI |

Source: MCP Issue #214 — OBO request, closed; MCP Issue #1036 — URL-mode elicitation; Solo.io — MCP authorization patterns for upstream API calls (2025-09-17); WorkOS — DCR, MCP, and OAuth (2025-12-09).

---

## Bearer tokens, validation, and never passing through

An MCP server that forwards its own bearer token to an upstream API is indistinguishable from an attacker that replays it. Spec-level MUSTs here are non-negotiable.

```python
from jose import jwt

CANONICAL = "https://mcp.example.com"

async def verify_mcp_token(raw_token: str) -> dict:
    payload = jwt.decode(
        raw_token,
        KEY,
        algorithms=["RS256"],
        audience=CANONICAL,
        issuer=EXPECTED_ISSUER,
        options={"require": ["aud", "iss", "exp", "sub"]},
    )
    if payload["aud"] != CANONICAL:
        raise Unauthorized("aud mismatch")
    return payload
```

Rules:

- Audience is the MCP server's canonical URI, byte-for-byte.
- If `aud` is an array, at least one element must equal the canonical URI **and** no other element may be treated as proof of authorization.
- Never re-use a received token as `Authorization` on an outbound call — use OBO (Pattern OBO).
- Reject tokens whose `typ` or `alg` is weaker than expected (`typ != "JWT"` or unsigned `alg=none`).

---

## Token rotation and leak handling

Refresh tokens for public clients (single-page apps, desktop clients without a backend secret) MUST rotate on every use. The pattern:

1. Client presents `refresh_token=R1` at `/token`.
2. AS issues fresh `access_token=A2` and **new** `refresh_token=R2`. AS invalidates `R1` on the next use.
3. If the AS later receives `R1` again, it treats this as a replay attempt — revokes the entire chain (`R1`, `R2`, any descendants).

Server-side token leak handling:

- Maintain a revocation list (or a `jti`-cache against issuance) so a leaked token can be killed immediately.
- Bind tokens to client fingerprint when feasible (DPoP RFC 9449); requires AS support.
- Short access-token TTL (≤ 1 hour for read scopes, ≤ 15 min for elevated scopes).
- Audit log every `aud` mismatch as a security incident — see `security.md` § Audit logging.

---

## Confused-deputy attack and defense

An MCP server that also acts as an AS, accepts unauthenticated `/register`, and honors persistent IdP consent cookies can be weaponized into issuing sessions to attacker clients that impersonate the victim.

Mechanics:

1. Attacker registers a client dynamically.
2. Attacker crafts an `/authorize` link to the MCP server's AS.
3. Victim clicks; victim's IdP cookie auto-consents.
4. MCP server redirects a code back to the attacker's `redirect_uri`.
5. Attacker completes PKCE, gets a session.

Defenses:

- Keep MCP server and AS separate — the 2025-06-18 split exists for this reason.
- If unavoidable, require a separate consent-cookie step that cannot be silently replayed.
- **CIMD** anchors client identity to a public HTTPS URL, so the `redirect_uris` are tied to DNS — attackers can't forge them.
- AS **MUST exact-match** `redirect_uri` against the fetched CIMD document.
- Use `__Host-` prefix cookies and `SameSite=Lax` at minimum.

Source: den.dev/blog/mcp-confused-deputy-api-management/ (2025-05-25); Obsidian Security — one-click account takeover (2026-01-29); Cloudflare workers-oauth-provider PR #99.

---

## Multi-tenant SaaS reference patterns

### Pattern A — separate AS with token exchange

Recommended default for SaaS offering MCP to enterprise customers. Clear separation of roles; upstream RBAC uses real user identity.

```
[User] ──SSO──▶ [IdP]
    │
    ▼
[MCP Client]
    │  Bearer(aud=mcp.saas.com, sub=user@co)
    ▼
[MCP Server] ── RFC 8693 token exchange ──▶ [Internal STS]
    │                                            │
    │                                            ▼ mints aud=api.upstream.com, sub=user@co
    ▼
[Upstream SaaS API]  ← RBAC on real user subject, not service account
```

Scope design:

```
mcp:tools             # presented to MCP server
mcp:read, mcp:write   # enforced at MCP server
upstream:leads.read   # only on the exchanged token, aud=api.upstream.com
upstream:leads.write  # only on the exchanged token
```

### Pattern B — URL-mode elicitation

Lighter pattern for consumer and indie MCP, or when the SaaS does not operate an STS. Upstream OAuth is completed inside the MCP server's trust boundary; upstream tokens never touch the client. See Option C above.

---

## DCR rug pull and tool squatting

With DCR open and unlimited, attackers register thousands of client records with plausible names, publish MCP servers whose tool descriptions change after approval, or poison a shared registry. Cursor publicly observed creating hundreds of thousands of DCR clients without rate limits.

Defenses:

- Constrain DCR registrations: force `grant_types=["authorization_code"]`, `response_types=["code"]`, `token_endpoint_auth_method="none"` for public clients, reject unknown fields, drop requests outside an allowlisted domain.
- Rate-limit `/register` per IP and per tenant.
- Emit an admin-visible audit record for every registration and expose a revocation API.
- **Prefer CIMD over DCR for new deployments.**
- For tool definitions themselves, adopt ETDI-style signed, immutable tool schemas (see `security.md` and `threat-catalog.md`; ETDI extends signing with versioned tool IDs).

Source: ETDI paper (arXiv:2506.01333) (2025-06-02); Trail of Bits — security layer MCP always needed (2025-07-28); WorkOS — DCR, MCP, and OAuth (2025-12-09).

---

## Cross-tenant data leak — per-agent identity

Asana's MCP integration leaked cross-tenant projects and files; the bug was live 34 days. Supabase + Cursor: the MCP agent ran with the full `service_role` key, and a prompt-injected support ticket exfiltrated data via SQL, bypassing RLS because RLS was never evaluated — the agent had bypass privileges.

Defenses:

- Agents MUST run with a **per-user upstream token**, obtained via OBO (Pattern A/B) or URL elicitation (Pattern C). Service-role keys are never acceptable.
- Enforce tenant scope **at the MCP server**, not trusted to upstream — bind the tenant to the session at auth time.
- Evaluate a PDP (policy decision point) on every tool call. Allowlists like `{tenant_id ∈ user.tenants}` reject the entire class of cross-tenant bugs structurally.
- Separate read and write PDP rules; log all denials with `{sub, tool, resource}`.

---

## Reference implementations to study

Read one of these before writing your own auth layer.

- **Stytch + Cloudflare Workers** — github.com/stytchauth/mcp-stytch-consumer-todo-list (2025-04-19). Clean AS separation, DCR, PKCE `S256`, PRM, per-user KV keying, `jwtVerify({ audience, issuer, typ: "JWT", algorithms: ['RS256'] })`.
- **Cloudflare `workers-oauth-provider`** — developers.cloudflare.com/agents/guides/remote-mcp-server/ plus `cloudflare/ai` PR #99. First public fix to the 2025-03-26 confused-deputy class.
- **WorkOS mcp.shop + AuthKit** — github.com/workos/mcp.shop with workos.com/docs/authkit/mcp. FastMCP's `AuthKitProvider` auto-discovers AS endpoints and validates JWT audience. XAA / `id-jag` support for enterprise.
- **Clerk mcp-nextjs-example** — github.com/clerk/mcp-nextjs-example with `mcp-handler` and `@clerk/mcp-tools`. PRM exposed at `/.well-known/oauth-protected-resource/mcp`; `withMcpAuth` + `verifyClerkToken`; explicit CORS on metadata endpoints; DCR opt-in from the dashboard.
- **Upstash Context7** — `@upstash/context7-mcp` (2026-01-15). End-to-end DCR + PKCE `S256`, opaque-token validation via `/oauth/userinfo`, project-selection consent step, 3-hour access token TTL.
- **Christian Posta / Solo.io "hard way"** — github.com/christian-posta/mcp-auth-step-by-step. Annotated Python FastAPI walkthrough of RFC 9728 + 8414 + 8707, plus scope-check dispatch.
- **localden APIM sample** — github.com/localden/remote-auth-mcp-apim-py. Azure API Management policies for `/register`, `/authorize`, `/token` including the consent-cookie interrupt.
- **Trail of Bits `mcp-context-protector`** — companion to the ETDI paper. Beta 2025-07-28. TOFU pinning of server instructions and tool descriptions, ANSI sanitization, prompt-injection guardrail.

---

## Audit checklist before shipping

Run every item. Failing any single one is a spec violation or a known attack vector.

- [ ] PRM served at `/.well-known/oauth-protected-resource` with `resource`, `authorization_servers[]`, `scopes_supported`, `bearer_methods_supported`.
- [ ] `WWW-Authenticate` challenge on 401 includes `resource_metadata=` and `scope=`.
- [ ] AS advertises either RFC 8414 or OIDC Discovery metadata; `code_challenge_methods_supported` includes `S256`.
- [ ] Client uses PKCE `S256` and aborts if the AS does not advertise it.
- [ ] Client sends `resource=<canonical MCP URI>` on both `/authorize` and `/token`.
- [ ] Server validates `aud`, `iss`, `exp`, `nbf` and the signature on every request; exact-match `aud` against canonical URI.
- [ ] Server never forwards incoming tokens upstream — uses RFC 8693, `id-jag`, or URL elicitation for OBO.
- [ ] Step-up path returns `403` with `error="insufficient_scope"` and the required `scope=`.
- [ ] If DCR enabled: rate-limited, constrained grant/response types, allowlisted `redirect_uris` domains, admin audit log.
- [ ] If CIMD adopted: AS validates `redirect_uris` against the fetched CIMD doc on every authorize.
- [ ] No unauthenticated `/status`, `/health`, `/metrics` leaking session or tenant data.
- [ ] Tenant binding enforced at the MCP server, not trusted to upstream.
- [ ] Tool schemas signed and verified on load (see `security.md`).
- [ ] Streamable HTTP returns `403` for invalid `Origin`.

---

## Cross-references

- `security.md` — content sanitization, PII tokenization, sandbox, audit logging
- `threat-catalog.md` — named OAuth attack primitives and CVEs
- `../decision-trees/security-posture.md` — diagnostic tree from threat profile to controls
- `transport-and-ops.md` — auth at transport vs auth at tool
- `advanced-protocol.md` — URL-mode elicitation mechanics
- `session-and-state.md` — session ID generation and lifecycle
