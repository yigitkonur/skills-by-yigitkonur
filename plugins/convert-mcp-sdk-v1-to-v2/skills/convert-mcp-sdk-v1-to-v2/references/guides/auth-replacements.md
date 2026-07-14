# Auth Replacements

v2 removes server-side OAuth from the SDK. This is the highest-risk part of any v1→v2 migration that uses `mcpAuthRouter`. There are current paths, one conditional future path, and one path to avoid.

## What v2 removes

```typescript
// All of these are gone in v2 direct packages:
import { mcpAuthRouter } from "@modelcontextprotocol/sdk/server/auth/router.js";
import { requireBearerAuth } from "@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js";
import {
  OAuthServerProvider,
  OAuthRegisteredClientsStore,
} from "@modelcontextprotocol/sdk/server/auth/provider.js";
// ... and 17 OAuth error classes
```

The protocol still supports OAuth 2.1; v2 just stops shipping a server-side implementation. Authorization server responsibilities (issue tokens, validate tokens, manage clients, expose metadata endpoints) move out of the SDK.

## What v2 keeps for handlers

`ctx.http?.authInfo` is still populated by the HTTP transport from upstream middleware. The SDK reads `req.auth` (or equivalent) on the incoming request and surfaces it on the context — same pattern as v1, just driven by middleware you control.

```typescript
// Express middleware sets req.auth
app.use((req, _res, next) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  // verify token, set req.auth = { subject, scopes, ... }
  req.auth = verified;
  next();
});

// SDK propagates it to the handler context
server.registerTool("private", schema, async (args, ctx) => {
  if (!ctx.http?.authInfo) throw new ProtocolError(...);
  const userId = ctx.http.authInfo.subject;
});
```

## Path 1 — stay on v1 until auth is separated (OAuth-heavy servers)

As of npm verification on 2026-05-09, `@modelcontextprotocol/server-auth-legacy` is not published. OAuth-router-heavy servers should stay on v1 until auth can move to an HTTP-layer implementation, unless a later target alpha publishes a verified transition package.

```typescript
// v1
import { mcpAuthRouter } from "@modelcontextprotocol/sdk/server/auth/router.js";

// Conditional future v2 transition, only if the package is published for the target alpha
import { mcpAuthRouter } from "@modelcontextprotocol/server-auth-legacy";

// Same options, same behavior, same OAuthServerProvider interface.
const authRouter = mcpAuthRouter({ provider, baseUrl, ... });
app.use(authRouter);
```

Treat any future transition package as a bridge, not a destination. Plan a follow-up migration to a dedicated AS once v2 reaches stable.

When to use this path:

- Existing `mcpAuthRouter` is in production with live customers.
- Custom `OAuthServerProvider` implementation has business logic you can't easily replicate.
- The migration window doesn't have budget to also rewrite auth.

## Path 2 — HTTP-layer auth (recommended for v2 work)

Run a standard token verifier as Express/Hono middleware and forward the verified identity to the SDK. This is what most production v2 servers should do.

### With jose (lightweight Bearer-only)

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

Pair with an external authorization server (Auth0, Okta, Keycloak, Authentik, custom) that handles token issuance, refresh, and client management. The SDK only needs the verified token.

### With Passport (multi-strategy)

```typescript
import passport from "passport";
import { Strategy as BearerStrategy } from "passport-http-bearer";

passport.use(new BearerStrategy(async (token, done) => {
  // verify, look up user
  done(null, { subject: userId, scopes });
}));

app.use(passport.authenticate("bearer", { session: false }));
// Passport sets req.user; map to req.auth if your code reads req.auth.
app.use((req, _res, next) => {
  if (req.user) req.auth = req.user;
  next();
});
```

## Path 3 — DIY token store (small servers, internal-only)

For internal servers with a fixed token list, an env-var Bearer check is sufficient and audit-friendly:

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

This is not OAuth-compliant; clients won't auto-refresh. Only acceptable for internal servers where the operator controls every client.

## What to avoid: `better-auth` MCP plugin

`better-auth` ships an MCP plugin (`better-auth/plugins/mcp`) that wraps server-side OAuth. As of 2026-05-08:

- The plugin **targets v1 import paths only** (`@modelcontextprotocol/sdk/server/mcp.js`, `/server/streamableHttp.js`). It does not yet support v2 packages.
- The plugin documentation says it **"will soon be deprecated in favor of the OAuth Provider Plugin"**.

Do not adopt it as a new dependency in a v2 migration. If you already use it on v1, evaluate the OAuth Provider Plugin (better-auth's successor) when it stabilizes; otherwise plan a migration to one of the paths above.

## Migration sequence for OAuth servers

1. Inventory every `OAuthServerProvider` method and `mcpAuthRouter` mount point.
2. Decide: stay on v1, a verified transition package, or HTTP-layer rewrite.
3. If a transition package is published for the target alpha: swap the import line, run integration tests against the existing OAuth flow, deploy.
4. If HTTP-layer rewrite: stand up the new auth middleware in parallel, run shadow validation (verify both v1 router and new middleware accept the same tokens), cut over, remove the v1 router.
5. Confirm `ctx.http?.authInfo` populates correctly in handlers — this is the load-bearing assertion.
6. Test refresh flows, expiry, revocation, scope mismatch — full OAuth happy and unhappy paths.

## Pre-flight checklist for this rewrite

- [ ] Path chosen: stay on v1 / verified transition package / HTTP-layer / DIY.
- [ ] All `requireBearerAuth` / `mcpAuthRouter` / `OAuthServerProvider` references inventoried.
- [ ] Replacement middleware sets `req.auth` (or equivalent) before the MCP route.
- [ ] `ctx.http?.authInfo` confirmed populated in at least one handler under test.
- [ ] OAuth metadata endpoints (`/.well-known/oauth-authorization-server`) exposed by the new auth path.
- [ ] Token expiry, refresh, and revocation flows tested.
- [ ] Scope checks performed in handlers, not relied on solely from middleware.
- [ ] `better-auth/plugins/mcp` not introduced as a new dependency.
