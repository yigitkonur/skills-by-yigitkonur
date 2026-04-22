# MCP Auth and Identity (2025-11-25 Spec)

Protocol-level authorization patterns for remote MCP servers. This file covers the **2025-11-25 authorization profile** and is a direct continuation of the generic advice in `security.md` (which covers prompt injection, tool hijacking, PII, SSRF, and generic OAuth2 scope tiers). Assume OAuth 2.1, RFC 9728 PRM, RFC 8707 resource indicators, RFC 8414 AS metadata, OIDC Discovery 1.0, and the Client ID Metadata Documents (CIMD) draft.

MCP moved from "auth optional, good luck" (2025-03-26) to a hardened OAuth 2.1 profile (2025-11-25) in three revisions. Three invariants now drive every pattern here: **every token has an audience**, **every client has verifiable identity**, and **MCP servers never forward user tokens upstream**.

---

## 1. Know The Spec Diff Before You Touch Auth Code

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

Only one requirement was **relaxed**: DCR dropped from SHOULD to MAY. Everything else is additive hardening.

**Source:** [spec 2025-11-25 authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization); [spec 2025-06-18 authorization](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization); [2025-11-25 changelog](https://modelcontextprotocol.io/specification/2025-11-25/changelog); [SEP-985 Final (2025-07-16)](https://modelcontextprotocol.io/seps/985-align-oauth-20-protected-resource-metadata-with-rf); [WorkOS — MCP 2025-11-25 spec update](https://workos.com/blog/mcp-2025-11-25-spec-update) (2025-11).

---

## 2. Map Every MCP Behavior To The RFC That Governs It

When reviewing a server, tick off the RFC compliance table before touching anything else. Non-compliance almost always comes from missing one of these, not from implementing something exotic.

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

**Source:** [RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728); [RFC 8707](https://datatracker.ietf.org/doc/html/rfc8707); [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414); [RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591); [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693); [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749); [Auth0 — MCP specs update (June 2025)](https://auth0.com/blog/mcp-specs-update-all-about-auth/).

---

## 3. Flow Walkthrough — First Connection (2025-11-25)

This is the reference sequence. Any deviation means your server is either pre-spec or non-compliant.

1. **Unauthenticated request.** Client POSTs to `https://mcp.example.com/mcp` without `Authorization`.
2. **Server challenges.** Response: `401` with `WWW-Authenticate: Bearer resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource", scope="files:read"`.
3. **PRM fetch.** Client GETs the PRM doc. Required fields: `resource`, `authorization_servers[...]`, `scopes_supported`, `bearer_methods_supported`.
4. **AS metadata fetch.** Using `authorization_servers[0]`:
   - Try RFC 8414 first: `/.well-known/oauth-authorization-server` and the path-appended form.
   - Fallback to OIDC Discovery: `/.well-known/openid-configuration` and its path-appended form.
   - **Abort if `code_challenge_methods_supported` is absent** — the AS cannot be trusted to enforce PKCE.
5. **Obtain `client_id`.** Three acceptable paths:
   - Pre-registered static `client_id` (traditional).
   - **CIMD**: use an HTTPS URL that serves the client's JSON manifest as the `client_id`.
   - DCR via `/register` as a last resort (2025-11-25 reduced from SHOULD to MAY).
6. **PKCE.** `code_verifier` = 43–128 random chars; `code_challenge = BASE64URL(SHA256(code_verifier))`.
7. **Authorize.** Browser `GET /authorize?response_type=code&client_id=<id>&redirect_uri=<exact>&code_challenge=<...>&code_challenge_method=S256&state=<csrf>&scope=files:read&resource=https://mcp.example.com`.
8. **User consent.** AS authenticates the user and shows consent; redirects to the exact-match `redirect_uri` with `code` and `state`.
9. **Token exchange.** Client POSTs `/token` with `grant_type=authorization_code`, `code`, `code_verifier`, `redirect_uri`, `client_id`, and **`resource=https://mcp.example.com`** (MUST). AS returns an access token with `aud="https://mcp.example.com"` plus (optionally) a rotating refresh token.
10. **Authenticated retry.** Client retries the original MCP call with `Authorization: Bearer <token>`. Server validates signature, `iss`, `exp`, `nbf`, `aud` exactly equal to its canonical URI, and scope — then dispatches.

**Source:** [spec 2025-11-25 authorization — §§ discovery, authorization flow, token validation](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization); [Stytch — Cloudflare Workers OAuth walkthrough](https://stytch.com/blog/building-an-mcp-server-oauth-cloudflare-workers/) (2025-04-19); [Christian Posta — MCP Auth step-by-step](https://github.com/christian-posta/mcp-auth-step-by-step) (2025).

---

## 4. Flow Walkthrough — Step-Up / Incremental Scope

Static `scopes_supported` is no longer sufficient. When a tool call needs more scope than the current token carries, the server drives the client through a new consent round.

1. Client holds a token with `scope="files:read"` and calls a tool that needs `files:write`.
2. Server returns `403 Forbidden` with `WWW-Authenticate: Bearer error="insufficient_scope", scope="files:write", resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource"`.
3. Client **MUST** treat the challenged `scope` as authoritative (ignore the PRM's static `scopes_supported`).
4. Client starts a fresh `/authorize` round with `scope=files:write` and redoes PKCE, obtaining a new token.
5. Client retries the tool call with the new token.

**Edge cases:**
- `client_credentials` clients (machine-to-machine) that cannot run a consent UI MAY abort and surface the error.
- Servers returning `403` without `scope=` in the header are spec-violating — clients must not attempt to guess scopes.
- When step-up is frequent, reconsider scope granularity — over-narrow scopes create noisy consent loops.

**Source:** [spec 2025-11-25 — incremental authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization); [WorkOS — MCP 2025-11-25 spec update](https://workos.com/blog/mcp-2025-11-25-spec-update) (2025-11).

---

## 5. Flow Walkthrough — On-Behalf-Of (OBO) For Upstream APIs

The MCP spec does not yet standardize OBO. Three patterns are in production today. Pick one; never fall back to forwarding the user's MCP token to upstream APIs.

**Option A — RFC 8693 Token Exchange (strongest).** MCP server holds its own client credential with an internal STS. It exchanges `subject_token = user's MCP access token`, `actor_token = MCP server's own token`, `resource = upstream API`, `scope = <narrow>`. The STS returns a fresh token audienced for the upstream API with the real user as `sub`. Upstream RBAC applies to the user, not the MCP service account.

**Option B — Identity Assertion Authorization Grant (`id-jag`) / Cross-App Access (XAA).** Enterprise IdP issues a signed assertion tying the MCP client and the upstream app so tokens can be swapped without a second consent screen. WorkOS treats this as the 2025-11-25 default for enterprise MCP. Requires both apps connected to the same IdP with XAA enabled.

**Option C — URL-mode elicitation (2025-11-25, lightest).** Server returns an elicitation that points the client to an upstream OAuth URL. **Critically, the callback goes to the MCP server, not the client.** The server stores the upstream refresh token keyed by the MCP identity's `sub` and refreshes on demand. Upstream tokens never leave the trusted server. Tradeoff: an extra consent screen.

| Pattern | Best for | Key cost |
|---|---|---|
| RFC 8693 | Single enterprise, tight STS | STS infrastructure |
| `id-jag` / XAA | Multi-app enterprise SSO | Both apps on same IdP |
| URL elicitation | Consumer / indie MCP | Extra consent UI |

**Source:** [MCP Issue #214 — OBO request, closed](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/214); [MCP Issue #1036 — URL-mode elicitation](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1036); [Solo.io — MCP authorization patterns for upstream API calls](https://www.solo.io/blog/mcp-authorization-patterns-for-upstream-api-calls) (2025-09-17); [WorkOS — DCR, MCP, and OAuth](https://workos.com/blog/dynamic-client-registration-dcr-mcp-oauth) (2025-12-09).

---

## 6. Always Validate `aud` — And Never Pass Tokens Through

An MCP server that forwards its own bearer token to an upstream API is indistinguishable from an attacker that replays it. Spec-level MUSTs here are non-negotiable.

```python
from jose import jwt

async def verify_mcp_token(raw_token: str) -> dict:
    payload = jwt.decode(
        raw_token,
        KEY,
        algorithms=["RS256"],
        audience="https://mcp.example.com",   # exact canonical URI
        issuer=EXPECTED_ISSUER,
        options={"require": ["aud", "iss", "exp", "sub"]},
    )
    if payload["aud"] != "https://mcp.example.com":
        raise Unauthorized("aud mismatch")
    return payload
```

**Rules:**
- Audience is the MCP server's canonical URI, byte-for-byte.
- If `aud` is an array, at least one element must equal the canonical URI **and** no other element may be treated as proof.
- Never re-use a received token as `Authorization` on an outbound call — use OBO (Pattern 5).
- Reject tokens whose `typ` or `alg` is weaker than expected (`typ != "JWT"` or unsigned `alg=none`).

**Source:** [spec 2025-11-25 — token validation](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization); [ForgeCode — MCP spec updates](https://forgecode.dev/blog/mcp-spec-updates) (2025-07-01).

---

## 7. Attack Primitive — Confused Deputy (MCP-As-Faux-AS)

An MCP server that also acts as an AS, accepts unauthenticated `/register`, and honors persistent IdP consent cookies can be weaponized into issuing sessions to attacker clients that impersonate the victim.

**Mechanics.** Attacker registers a client dynamically, crafts an `/authorize` link to the MCP server's AS, victim clicks, victim's IdP cookie auto-consents, MCP server redirects a code back to the attacker's `redirect_uri`, attacker completes PKCE, gets a session.

**Defenses:**
- Keep MCP server and AS separate — the 2025-06-18 split exists for this reason.
- If unavoidable, require a separate consent-cookie step that cannot be silently replayed.
- **CIMD** anchors client identity to a public HTTPS URL, so the `redirect_uris` are tied to DNS — attackers can't forge them.
- AS **MUST exact-match** `redirect_uri` against the fetched CIMD document.
- Use `__Host-` prefix cookies and `SameSite=Lax` at minimum.

**Source:** [den.dev — MCP confused deputy](https://den.dev/blog/mcp-confused-deputy-api-management/) (2025-05-25); [Obsidian Security — one-click account takeover](https://obsidiansecurity.com/blog/when-mcp-meets-oauth-common-pitfalls-leading-to-one-click-account-takeover) (2026-01-29); [Cloudflare workers-oauth-provider PR #99](https://github.com/cloudflare/ai).

---

## 8. Attack Primitive — Token Audience Confusion And Passthrough

Attacker coerces the MCP server into replaying its bearer token against an upstream API; upstream observes the original user's `sub` and authorizes the call.

**Defenses:**
- MCP server MUST reject any token whose `aud` does not equal its own canonical URI.
- Upstream APIs MUST reject tokens whose `aud` is another service.
- Mint a fresh upstream-audienced token via RFC 8693 (Pattern 5A) or XAA (5B) — never reuse.
- Treat "bearer token with matching `sub` but wrong `aud`" as a security incident, not a bug.

**Source:** [spec 2025-06-18 and 2025-11-25 — §§ token passthrough and audience](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization); [ForgeCode — MCP spec updates](https://forgecode.dev/blog/mcp-spec-updates) (2025-07-01).

---

## 9. Attack Primitive — DCR Rug Pull And Tool Squatting

With DCR open and unlimited, attackers register thousands of client records with plausible names, publish MCP servers whose tool descriptions change after approval, or poison a shared registry. Cursor publicly observed creating hundreds of thousands of DCR clients without rate limits.

**Defenses:**
- Constrain DCR registrations: force `grant_types=["authorization_code"]`, `response_types=["code"]`, `token_endpoint_auth_method="none"` for public clients, reject unknown fields, drop requests outside an allowlisted domain.
- Rate-limit `/register` per IP and per tenant.
- Emit an admin-visible audit record for every registration and expose a revocation API.
- **Prefer CIMD over DCR for new deployments** — CIMD anchors trust in DNS + HTTPS rather than a free-for-all endpoint.
- For tool definitions themselves, adopt ETDI-style signed, immutable tool schemas (see `security.md` Pattern 6 for the signing mechanics; ETDI extends that with versioned tool IDs).

**Source:** [ETDI paper (arXiv:2506.01333)](https://arxiv.org/abs/2506.01333) (2025-06-02); [Trail of Bits — security layer MCP always needed](https://blog.trailofbits.com/2025/07/28/we-built-the-security-layer-mcp-always-needed/) (2025-07-28); [WorkOS — DCR, MCP, and OAuth](https://workos.com/blog/dynamic-client-registration-dcr-mcp-oauth) (2025-12-09).

---

## 10. Attack Primitive — Session Hijacking Via Unscoped Endpoints (CVE-2025-6514)

`mcp-remote` 0.0.5 through 0.1.15 interpolated a server-supplied `authorization_endpoint` into a shell → remote code execution on the client. 437,000+ downloads affected, CVSS 8.2. Same class: unauthenticated `/status`, `/health`, `/metrics` endpoints leaked session IDs and tenant names.

**Defenses:**
- Treat every HTTP endpoint of an MCP server as scope-protected unless it is an explicit unauth OAuth endpoint (PRM, AS metadata, `/register` if enabled, `/authorize`, `/token`, redirect endpoints).
- Bind session IDs to authenticated principals; validate on every request.
- **Never interpolate server-supplied URLs into shells, argv, or filesystem paths** on the client side.
- Disable unauthenticated metrics. Gate `/health` behind a narrow allowlist or a signed probe token.

**Source:** [CVE-2025-6514 — mcp-remote](https://modelcontextprotocol-security.io/known-vulnerabilities/cve-2025-6514/); [JFrog advisory (2025)](https://modelcontextprotocol-security.io/known-vulnerabilities/cve-2025-6514/).

---

## 11. Attack Primitive — Indirect Prompt Injection To Confused Agent

Invariant Labs' `ukend0464/pacman` PoC: a malicious GitHub Issue instructs the agent (via an MCP GitHub server) to pull a private repo and leak it via a PR to a public repo. No OAuth flaw — the token is valid and scoped correctly. The defect is that the agent bridges two trust domains in one session.

**Defenses (auth-layer):**
- Scope tokens narrowly per repo / per tenant — don't issue "all repos" tokens for convenience.
- Prefer separate agent sessions per trust domain; keep cross-domain writes explicit and confirmed.
- Add a runtime policy engine (OPA, Cedar, Oso) that evaluates each tool call's `{subject, tool, resource, origin}` and denies cross-domain writes by default.
- Require user confirmation before the agent writes outside the trust domain that originated the instruction.

**Source:** [Invariant Labs — MCP GitHub vulnerability](https://invariantlabs.ai/blog/mcp-github-vulnerability) (2025-05-26); [OWASP MCP Top 10 — MCP02-2025](https://owasp.org/www-project-mcp-top-10/2025/MCP02-2025).

---

## 12. Attack Primitive — Cross-Tenant Data Leak Via Missing Per-Agent Identity

Asana's MCP integration leaked cross-tenant projects and files; the bug was live 34 days. Supabase + Cursor: the MCP agent ran with the full `service_role` key, and a prompt-injected support ticket exfiltrated data via SQL, bypassing RLS because RLS was never evaluated — the agent had bypass privileges.

**Defenses:**
- Agents MUST run with a **per-user upstream token**, obtained via OBO (Pattern 5A/B) or URL elicitation (Pattern 5C). Service-role keys are never acceptable.
- Enforce tenant scope **at the MCP server**, not trusted to upstream — bind the tenant to the session at auth time.
- Evaluate a PDP (policy decision point) on every tool call. Allowlists like `{tenant_id ∈ user.tenants}` reject the entire class of cross-tenant bugs structurally.
- Separate read and write PDP rules; log all denials with `{sub, tool, resource}`.

**Source:** [Raza Shariff — cross-tenant MCP exposures](https://dev.to/razashariff) (2026-03); [Solo.io — upstream API patterns](https://www.solo.io/blog/mcp-authorization-patterns-for-upstream-api-calls) (2025-09-17).

---

## 13. Attack Primitive — Supply-Chain Backdoor In Published Servers

`postmark-mcp` (fake npm package) silently BCC'd outbound email. Backdoor injected at v1.0.16 after 15 clean releases — typical supply-chain pattern. No OAuth flow would have stopped it.

**Defenses:**
- Require signed, versioned tool definitions (ETDI) so a changed tool description triggers re-approval.
- Pin server instructions and tool descriptions on first trusted use (TOFU) — Trail of Bits' `mcp-context-protector` implements this as a transparent proxy.
- Verify publisher identity via the npm/OCI registry signature, not the package name.
- Pair CIMD (client identity anchored in DNS) with registry-side anchoring for servers.

**Source:** [Trail of Bits — mcp-context-protector beta](https://blog.trailofbits.com/2025/07/28/we-built-the-security-layer-mcp-always-needed/) (2025-07-28); [ETDI paper (arXiv:2506.01333)](https://arxiv.org/abs/2506.01333) (2025-06-02).

---

## 14. Multi-Tenant SaaS Reference Pattern A — Separate AS With Token Exchange

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
    │                                            ▼  mints aud=api.upstream.com, sub=user@co
    ▼
[Upstream SaaS API]  ← RBAC on real user subject, not service account
```

**Scope design:**
```
mcp:tools               # present to MCP server
mcp:read, mcp:write     # enforced at MCP server
upstream:leads.read     # only on the exchanged token, aud=api.upstream.com
upstream:leads.write    # only on the exchanged token
```

**Config sketch (FastAPI + internal STS):**
```python
@tool
async def list_leads(ctx: Context) -> dict:
    mcp_token = ctx.session.raw_token            # aud=mcp.saas.com
    upstream = await sts.exchange(
        subject_token=mcp_token,
        actor_token=service_actor_token,
        audience="https://api.upstream.com",
        scope="upstream:leads.read",
    )
    return await upstream_client.list_leads(token=upstream.access_token)
```

**Source:** [Solo.io — MCP authorization patterns for upstream API calls](https://www.solo.io/blog/mcp-authorization-patterns-for-upstream-api-calls) (2025-09-17); [Christian Posta — MCP auth step-by-step](https://github.com/christian-posta/mcp-auth-step-by-step).

---

## 15. Multi-Tenant SaaS Reference Pattern B — URL-Mode Elicitation

Lighter pattern for consumer and indie MCP, or when the SaaS does not operate an STS. Upstream OAuth is completed inside the MCP server's trust boundary; upstream tokens never touch the client.

```
[User] ──Bearer(aud=mcp.saas.com)──▶ [MCP Server]
                                          │
                   tool call needs upstream (no upstream creds yet)
                                          │
                                          ▼
            Server returns elicitation { kind: "url", url: "https://mcp.saas.com/connect/github?state=..." }
                                          │
                User browser opens URL; upstream OAuth completes
                                          │
                 Callback → https://mcp.saas.com/connect/github/callback
                                          │
             Server stores upstream refresh token in KV keyed by MCP `sub`
                                          │
                          Retry tool call — now succeeds
```

**Config sketch (Cloudflare Workers KV):**
```ts
// On callback:
await env.UPSTREAM_TOKENS.put(
  `github:${mcpSub}`,
  JSON.stringify({ refresh_token, aud: "api.github.com", scopes }),
  { metadata: { createdAt: Date.now() } }
);

// On subsequent tool calls:
const stored = JSON.parse(await env.UPSTREAM_TOKENS.get(`github:${mcpSub}`));
const access = await refreshUpstream(stored.refresh_token);
return fetchGithub(access.access_token, ...);
```

**Trade-offs:** one extra consent screen; simpler than an STS; upstream tokens never leave the server. Preferred for indie / consumer MCP.

**Source:** [MCP Issue #1036 — URL-mode elicitation](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1036); [Upstash Context7 OAuth implementation](https://upstash.com/blog/mcp-oauth-implementation) (2026-01-15).

---

## 16. Reference Implementations To Study

Read one of these before writing your own auth layer. Every entry is production or reference-quality as of the cited date.

- **Stytch + Cloudflare Workers** — `github.com/stytchauth/mcp-stytch-consumer-todo-list` (2025-04-19). Clean AS separation, DCR, PKCE `S256`, PRM, per-user KV keying, `jwtVerify({ audience, issuer, typ: "JWT", algorithms: ['RS256'] })`. [Blog walkthrough](https://stytch.com/blog/building-an-mcp-server-oauth-cloudflare-workers/).
- **Cloudflare `workers-oauth-provider`** — `developers.cloudflare.com/agents/guides/remote-mcp-server/` plus `cloudflare/ai` PR #99. First public fix to the 2025-03-26 confused-deputy class; reference for the consent-cookie interrupt.
- **WorkOS mcp.shop + AuthKit** — `github.com/workos/mcp.shop` with `workos.com/docs/authkit/mcp`. FastMCP's `AuthKitProvider` auto-discovers AS endpoints and validates JWT audience. XAA / `id-jag` support for enterprise.
- **Clerk mcp-nextjs-example** — `github.com/clerk/mcp-nextjs-example` with the `mcp-handler` and `@clerk/mcp-tools` packages. PRM exposed at `/.well-known/oauth-protected-resource/mcp`; `withMcpAuth` + `verifyClerkToken`; explicit CORS on metadata endpoints; DCR opt-in from the dashboard.
- **Upstash Context7** — `@upstash/context7-mcp` (2026-01-15). End-to-end DCR + PKCE `S256`, opaque-token validation via `/oauth/userinfo`, project-selection consent step, 3-hour access token TTL.
- **Christian Posta / Solo.io "hard way"** — `github.com/christian-posta/mcp-auth-step-by-step`. Annotated Python FastAPI walkthrough of RFC 9728 + 8414 + 8707, plus scope-check dispatch.
- **localden APIM sample** — `github.com/localden/remote-auth-mcp-apim-py`. Azure API Management policies for `/register`, `/authorize`, `/token` including the consent-cookie interrupt.
- **AWS AgentCore Gateway** — policy-per-tool fine-grained access for multi-tenant MCP, Cedar-based PDP; see AWS docs for the 2025 preview.
- **Trail of Bits `mcp-context-protector`** — companion to the ETDI paper. Beta 2025-07-28. TOFU pinning of server instructions and tool descriptions, ANSI sanitization, prompt-injection guardrail. [Blog](https://blog.trailofbits.com/2025/07/28/we-built-the-security-layer-mcp-always-needed/).

**Source:** see inline links above; cross-referenced from [blog.modelcontextprotocol.io — first MCP anniversary (2025-11-25)](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/).

---

## 17. Audit Checklist Before Shipping

Run every one of these. Failing any single item is a spec violation or a known attack vector.

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
- [ ] Tool schemas signed and verified on load (see `security.md` Pattern 6).
- [ ] Streamable HTTP returns `403` for invalid `Origin`.

**Source:** composite of the 2025-11-25 spec and the attack primitives in Patterns 7–13; validated against [OWASP MCP Top 10 — 2025](https://owasp.org/www-project-mcp-top-10/2025/MCP02-2025).
