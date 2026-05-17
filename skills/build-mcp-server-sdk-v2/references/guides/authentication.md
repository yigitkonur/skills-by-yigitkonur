# Authentication (v2)

v2 removes server-side OAuth from the SDK. The protocol still supports OAuth 2.1 — v2 just stops shipping the authorization server. Authentication for a v2 MCP server is now HTTP middleware that runs *before* the SDK and forwards verified identity to the handler context.

This guide covers server-side authentication only. For client-side auth providers (`OAuthClientProvider`, `ClientCredentialsProvider`, `PrivateKeyJwtProvider`, middleware system), see `references/guides/client-api.md`.

## How auth reaches the handler

The Express and Hono adapters propagate upstream-set request fields into `ServerContext`. Set `req.auth` (Express) or the equivalent on the Hono context, and it surfaces as `ctx.http?.authInfo` in every handler.

```typescript
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/core";

// Adapter middleware sets req.auth
app.use(async (req, res, next) => {
  const verified = await verifyToken(req.headers.authorization);
  if (!verified) return res.status(401).json({ error: "unauthorized" });
  req.auth = { subject: verified.sub, scopes: verified.scopes, raw: verified };
  next();
});

// SDK reads it on every request
server.registerTool("private", schema, async (args, ctx) => {
  if (!ctx.http?.authInfo) {
    throw new ProtocolError(ProtocolErrorCode.InvalidParams, "auth required");
  }
  const userId = ctx.http.authInfo.subject;
  // ...
});
```

`ctx.http?` is **nullable** — stdio transport has no HTTP layer. Code that reads `ctx.http?.authInfo` must handle the `undefined` case explicitly.

## Three credible paths

### Path 1 — JWT verifier (lightweight Bearer)

The minimal production-ready setup. Pair with an external authorization server (Auth0, Okta, Keycloak, Authentik, custom AS).

```typescript
import { jwtVerify, createRemoteJWKSet } from "jose";

const JWKS = createRemoteJWKSet(new URL(process.env.JWKS_URL!));

app.use(async (req, res, next) => {
  const auth = req.headers.authorization;
  if (!auth?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "missing_token" });
  }
  try {
    const { payload } = await jwtVerify(auth.slice(7), JWKS, {
      issuer: process.env.OAUTH_ISSUER,
      audience: process.env.OAUTH_AUDIENCE,
    });
    req.auth = {
      subject: payload.sub!,
      scopes: (payload.scope as string)?.split(" ") ?? [],
      raw: payload,
    };
    next();
  } catch {
    res.status(401).json({ error: "invalid_token" });
  }
});
```

Pros: no SDK lock-in, audit-friendly, works with any OAuth-compliant AS.
Cons: clients must handle token refresh themselves (the AS does, not the SDK).

### Path 2 — Passport (multi-strategy)

Use when the server needs more than Bearer tokens (session cookies, API keys, OAuth provider chains).

```typescript
import passport from "passport";
import { Strategy as BearerStrategy } from "passport-http-bearer";

passport.use(new BearerStrategy(async (token, done) => {
  const user = await verifyToken(token);
  user ? done(null, user) : done(null, false);
}));

app.use(passport.authenticate("bearer", { session: false }));
app.use((req, _res, next) => {
  if (req.user) req.auth = req.user as any;
  next();
});
```

Passport sets `req.user`; map to `req.auth` so the SDK picks it up.

### Path 3 — Static-token allow-list (internal-only)

Acceptable for internal servers where the operator controls every client. Not OAuth-compliant.

```typescript
const VALID_TOKENS = new Set(process.env.MCP_TOKENS?.split(",") ?? []);

app.use((req, res, next) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token || !VALID_TOKENS.has(token)) {
    return res.status(401).json({ error: "unauthorized" });
  }
  req.auth = { subject: `token:${token.slice(-6)}`, scopes: ["*"] };
  next();
});
```

## Main-branch Resource-Server helpers

PR #1907 restored `@modelcontextprotocol/express` Resource-Server helpers (`requireBearerAuth`, `mcpAuthMetadataRouter`) on the main branch after npm `2.0.0-alpha.2`. Treat them as post-alpha source signal unless the installed `@modelcontextprotocol/express` package exports them.

Use them only after re-checking package exports in the current release. If unavailable, keep the auth boundary as normal Express/Hono middleware that sets `req.auth` before the MCP route.

## Server-side OAuth transition: server-auth-legacy

If the server needs to issue tokens itself — multi-tenant SaaS, dynamic client registration, custom grant flows — `@modelcontextprotocol/server-auth-legacy` is the planned transitional package for the frozen v1 `mcpAuthRouter` code. As of 2026-05-09 UTC, npm returns 404 and upstream PR #1908 is open, not merged or published.

Do not recommend installing it unless fresh checks prove both:

- `npm view @modelcontextprotocol/server-auth-legacy version dist-tags --json` succeeds.
- PR #1908 is merged or release notes explicitly document the package.

Even if it becomes available, treat it as transitional. The destination for new v2 auth remains HTTP middleware plus `ctx.http?.authInfo`, backed by an external authorization server or a dedicated AS implementation.

## What to avoid: better-auth MCP plugin (current state, 2026-05-08)

`better-auth/plugins/mcp` is a server-side OAuth provider for MCP. As of 2026-05-08:

- It targets **v1 import paths only** (`@modelcontextprotocol/sdk/server/mcp.js`, `/server/streamableHttp.js`) — not yet ported to v2 packages.
- The plugin docs flag it as **"will soon be deprecated in favor of the OAuth Provider Plugin"** (better-auth's successor).

Do not adopt it as a new dependency for a v2 server. Re-evaluate after the OAuth Provider Plugin stabilizes.

## Authorization server metadata

MCP clients discover OAuth endpoints via `/.well-known/oauth-authorization-server` (RFC 8414). Make sure the metadata endpoint:

- Lives on the same origin as the MCP endpoint (or is reachable via CORS).
- Returns the issuer, authorization, token, and revocation endpoint URLs.
- Lists supported response types, grant types, code challenge methods.

For Path 1 / Path 2, the external AS handles this. For a future verified `server-auth-legacy` release, the router should expose it. For Path 3, metadata is unnecessary because it is not OAuth.

## Scope checks belong in handlers

Middleware should authenticate (verify the token, populate `req.auth`); handlers should authorize (check that the user has the right scope for the specific tool). Don't rely on middleware-level scope filtering — it makes per-tool exceptions impossible and obscures the authorization boundary.

```typescript
server.registerTool("delete-record", schema, async (args, ctx) => {
  const scopes = ctx.http?.authInfo?.scopes ?? [];
  if (!scopes.includes("records:write")) {
    return {
      content: [{ type: "text" as const, text: "Insufficient scope" }],
      isError: true,
    };
  }
  // ...
});
```

`isError: true` is preferred over throwing `ProtocolError` for missing scope — the LLM can self-correct (ask the user to upgrade) instead of treating it as a hard protocol failure.

## DNS rebinding protection

Independent of token verification: HTTP servers must validate the `Host` header. The Express/Hono adapters auto-protect localhost bindings; for production hosts, add `hostHeaderValidation`:

```typescript
import { hostHeaderValidation } from "@modelcontextprotocol/express";

app.use(hostHeaderValidation(["mcp.example.com"]));
```

Skipping this lets attackers trigger MCP tool calls from arbitrary websites by abusing DNS rebinding. See `references/guides/transports.md` for the full transport-layer security walkthrough.

## Production checklist

- [ ] Authentication middleware runs *before* the MCP route mount.
- [ ] `req.auth` (or equivalent) is set with at minimum `subject` and `scopes`.
- [ ] At least one handler reads `ctx.http?.authInfo` to confirm propagation.
- [ ] `ctx.http?` nullability handled in every handler (stdio path).
- [ ] OAuth metadata at `/.well-known/oauth-authorization-server` (if OAuth-compliant).
- [ ] Scope checks live in handler bodies, not middleware allow-lists.
- [ ] DNS rebinding protection enabled for non-localhost binds.
- [ ] Token expiry and revocation tested with a real client.
- [ ] No `better-auth/plugins/mcp` dependency introduced new.
