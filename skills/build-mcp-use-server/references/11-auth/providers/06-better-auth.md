# OAuth Provider: Better Auth

*Read this when using Better Auth's OAuth Provider plugin as your own authorization server.*

## Import & Factory

```typescript
import { oauthBetterAuthProvider } from "mcp-use/oauth/better-auth";

const oauth = oauthBetterAuthProvider({
  authURL: "https://auth.example.com/api/auth",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `authURL` | `string \| URL` | `"https://auth.example.com/api/auth"` | Full Better Auth issuer URL, **including its base path** (`/api/auth`) |

The provider does not create or mount Better Auth. It derives Better Auth's `/oauth2/authorize`, `/oauth2/token`, `/oauth2/register`, and `/jwks` endpoints from `authURL`, then verifies JWT issuer, signature, expiration, and MCP resource audience. Better Auth itself owns registration, sign-in, consent, and token issuance.

## Optional Options

```typescript
oauthBetterAuthProvider({
  authURL: "...",
  resource?: string | URL,              // Full MCP endpoint URL (overrides host header inference)
  requiredScopes?: readonly string[],   // Scopes required by bearer gate (default: none enforced)
  scopesSupported?: readonly string[],  // Scopes advertised to clients (default: ["openid", "profile", "email", "offline_access"] — the only provider with a built-in default)
  resourceName?: string,                // Human-readable name for OAuth metadata
  serviceDocumentationUrl?: URL,        // Documentation link in OAuth metadata
})
```

## User Type

```typescript
type BetterAuthOAuthUser = {
  id: string;              // sub claim
  email?: string;
  name?: string;
  picture?: string;
  emailVerified?: boolean; // email_verified claim
  sessionId?: string;      // sid claim
  isAnonymous?: boolean;   // is_anonymous or isAnonymous claim (either spelling accepted)
  roles: string[];         // roles claim, normalized to a string array
};
```

`permissions` claim maps separately to top-level `ctx.auth.permissions`. Profile and application-specific access-token fields must be added on the Better Auth side with `customAccessTokenClaims` — the built-in mapper only recognizes `email`, `name`, `picture`, `email_verified`, `sid`, `is_anonymous`/`isAnonymous`, `roles`, and `permissions`.

## Environment Variables

The provider does not read any environment variables itself — `authURL` is a plain function argument:

```bash
BETTER_AUTH_URL=https://auth.example.com/api/auth
```

```typescript
const oauth = oauthBetterAuthProvider({
  authURL: process.env.BETTER_AUTH_URL!,
});
```

## Run Better Auth as a separate Hono app

The authorization server can be a separate application and origin. The `mcp-use` server owns `/mcp` and its protected-resource metadata; a separate Hono app mounts Better Auth, its discovery routes, and login/consent pages:

```typescript
import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { auth } from "./auth.js";

const app = new Hono();
app.on(["GET", "POST"], "/api/auth/*", (c) => auth.handler(c.req.raw));
serve({ fetch: app.fetch, port: 61843 });
```

Because the issuer contains `/api/auth`, also route Better Auth's RFC 8414 path-insertion metadata endpoint `/.well-known/oauth-authorization-server/api/auth` to `auth.handler` (or `oauthProviderAuthServerMetadata(auth)`). If browser-based MCP clients call this separate origin directly, configure Hono CORS for the MCP origin and include that origin in Better Auth's `trustedOrigins`.

## Access the verified identity

```typescript
server.tool({ name: "whoami" }, async (_params, ctx) => ({
  content: [
    {
      type: "text",
      text: JSON.stringify({
        id: ctx.auth.user.id,
        isAnonymous: ctx.auth.user.isAnonymous,
        scopes: ctx.auth.scopes,
      }),
    },
  ],
}));
```

## Gotchas

1. Include the full base path in `authURL` (`/api/auth`), not just the origin
2. Better Auth owns registration, authorization, consent, and token issuance — this provider only verifies tokens and advertises discovery metadata
3. Check `isAnonymous` before assuming an authenticated session; the maintained example uses anonymous sign-in with no Google/GitHub credentials
4. `sessionId` is provided but rarely needed in a stateless MCP context
5. Without a persistent Better Auth database, anonymous users, dynamic clients, codes, and consent reset on every process restart — fine for local dev, not for production
6. This is the only provider with a built-in `scopesSupported` default (`["openid", "profile", "email", "offline_access"]`); every other provider factory leaves it unset unless you pass it
