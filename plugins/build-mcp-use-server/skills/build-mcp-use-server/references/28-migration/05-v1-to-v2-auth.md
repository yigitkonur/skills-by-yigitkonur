# Authentication, OAuth, and Mixed Auth Migration

*Read this when migrating authentication, OAuth provider adapters, user identity context, or removing the OAuth Proxy in mcp-use v2.*

In `mcp-use v1`, authentication was configured as an all-or-nothing server-wide gate: attaching an OAuth provider protected every endpoint, blocking unauthenticated clients from even discovering available tools. Provider factories were imported from `mcp-use/server`, user identity was exposed as `ctx.auth.user.userId`, and fixed-client providers relied on the built-in `oauthProxy()`.

`mcp-use v2` overhauls authentication with a granular, production-ready security model:
1. **Mixed Authentication (`mixedAuth: true`)**: Allows unauthenticated discovery (`tools/list`, `resources/list`, `prompts/list`) while protecting individual tools.
2. **Tool-Level Security Schemes**: Individual tools declare `securitySchemes: [{ type: "noauth" }]` for public access or `securitySchemes: [{ type: "oauth2", scopes: [...] }]` for protected execution.
3. **Provider Subpath Modularization**: Provider adapters are imported from dedicated subpaths (`mcp-use/oauth/*`).
4. **Normalized User ID**: All providers normalize user identity under `ctx.auth.user.id` (replacing `userId`).
5. **OAuth Proxy Removal**: `oauthProxy()` is removed in favor of external standards-based authorization brokers and `oauthCustomProvider`.

---

## At a Glance: Auth Migration Diff

| Capability / Surface | Legacy v1 (`mcp-use <= 1.34.5`) | Canonical v2 (`mcp-use >= 2.8.2`) | Impact / Action |
|---|---|---|---|
| **Discovery Access** | Single-mode: All-or-nothing; 401 on `tools/list` if unauthenticated | `mixedAuth: true` enables public discovery of unauthenticated tools | Add `mixedAuth: true` to `new MCPServer(...)` to allow tool catalog inspection |
| **Tool-Level Gating** | None; all tools inherit server-wide auth requirement | `securitySchemes: [{ type: "noauth" }]` or `[{ type: "oauth2", scopes: [...] }]` | Declare explicit security requirements per tool definition |
| **Provider Imports** | Imported from `mcp-use/server` | Subpaths: `mcp-use/oauth/clerk`, `mcp-use/oauth/auth0`, etc. | Update import specifiers; root package exports zero providers |
| **User Identity** | `ctx.auth.user.userId` | `ctx.auth.user.id` | Rename `.userId` to `.id` across all tool handlers |
| **OAuth Proxy** | `oauthProxy()` helper for non-DCR providers | **Removed**; deploy external authorization broker | Use Keycloak or external broker + `oauthCustomProvider` |
| **Custom Verifier** | `verifyToken: async (token) => ...` (flat function) | `createTokenVerifier: (resource) => ({ verifyAccessToken })` | Returns an `OAuthTokenVerifier` object; reads `authInfo.extra` |
| **Audience Binding** | Bound to origin only (`https://mcp.example.com`) | Bound to origin + `basePath` (`https://mcp.example.com/mcp`) | Use dual-audience array in `createJwtVerifier` during migration |
| **Scope Checking** | Built-in helper `ctx.hasScope("read")` | Native array methods: `ctx.auth.scopes.includes("read")` | Update custom permission checks to standard JavaScript array lookups |

---

## Mixed Authentication: Public Discovery with Protected Tools

In v1, configuring OAuth prevented unauthenticated clients or LLM hosts from reading `tools/list`. The host received an HTTP 401 Unauthorized before it could determine which tools the server offered.

In `mcp-use v2`, setting `mixedAuth: true` on `MCPServer` allows public discovery:
- `tools/list`, `resources/list`, and `prompts/list` are publicly readable without a Bearer token.
- Tools declaring `securitySchemes: [{ type: "noauth" }]` can be called by anyone without authentication.
- Tools declaring `securitySchemes: [{ type: "oauth2", scopes: [...] }]` strictly enforce valid Bearer tokens and required scopes.

```typescript
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { z } from "zod";

const server = new MCPServer({
  name: "ecommerce-mcp",
  version: "2.0.0",
  basePath: "/mcp",
  mixedAuth: true, // Enables unauthenticated tool listing
  oauth: oauthClerkProvider({
    frontendApiUrl: process.env.CLERK_FRONTEND_API_URL!,
  }),
});

// 1. PUBLIC TOOL: Callable without an OAuth token
export const searchCatalog = server.tool(
  {
    name: "search-catalog",
    description: "Search public catalog items",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: z.object({ results: z.array(z.string()) }),
    securitySchemes: [{ type: "noauth" }], // Explicitly public
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Found 3 items for "${query}"` }],
    structuredContent: { results: ["Item A", "Item B", "Item C"] },
  })
);

// 2. PROTECTED TOOL: Requires valid bearer token and required scopes
export const purchaseItem = server.tool(
  {
    name: "purchase-item",
    description: "Charge account and place an order",
    inputSchema: z.object({ itemId: z.string() }),
    outputSchema: z.object({ orderId: z.string() }),
    securitySchemes: [{ type: "oauth2", scopes: ["orders:write"] }], // Strictly protected
  },
  async ({ itemId }, ctx) => {
    // Guaranteed verified user in protected tool
    const userId = ctx.auth.user.id;
    return {
      content: [{ type: "text", text: `Order created for user ${userId}` }],
      structuredContent: { orderId: "ord_12345" },
    };
  }
);
```

> **Security Invariant**: Even under `mixedAuth: true`, if a client supplies an expired, malformed, or untrusted Bearer token to a public tool, `mcp-use` will reject the request with HTTP 401. Public tools only permit requests that carry *no* credentials or *valid* credentials.

---

## Modular Provider Subpaths

In v2, all OAuth provider adapters are imported from explicit subpaths under `mcp-use/oauth/*`:

```typescript
// v1 (all from mcp-use/server)
import { oauthClerkProvider, oauthAuth0Provider } from "mcp-use/server";

// v2 (modular subpaths)
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";
import { oauthSupabaseProvider } from "mcp-use/oauth/supabase";
import { oauthKeycloakProvider } from "mcp-use/oauth/keycloak";
import { oauthWorkOSProvider } from "mcp-use/oauth/workos";
import { oauthBetterAuthProvider } from "mcp-use/oauth/better-auth";
import { oauthScalekitProvider } from "mcp-use/oauth/scalekit";
import { oauthConvexProvider } from "mcp-use/oauth/convex";
import { oauthCustomProvider, createJwtVerifier } from "mcp-use/oauth";
```

All provider factories require an explicit configuration object; there is no implicit fallback to environment variables.

---

## User Context Normalization: `userId` → `user.id`

In v1, user IDs were accessed via `ctx.auth.user.userId`. In v2, this property is **renamed to `ctx.auth.user.id`** across all built-in providers:

```typescript
// v1 (Removed)
const userId = ctx.auth.user.userId;

// v2 (Canonical)
const userId = ctx.auth.user.id;
```

### Provider-Specific User Shapes

While `ctx.auth.user.id` is standardized as the stable identifier, providers attach additional normalized claims:

```typescript
// Clerk (oauthClerkProvider)
ctx.auth.user.id                // string — Clerk user ID (e.g. "user_2...")
ctx.auth.user.email             // string | undefined
ctx.auth.user.organizationId    // string | undefined
ctx.auth.user.organizationRole  // string | undefined
ctx.auth.user.roles             // string[]

// Auth0 (oauthAuth0Provider)
ctx.auth.user.id                // string — Auth0 subject (e.g. "auth0|12345")
ctx.auth.user.email             // string | undefined
ctx.auth.user.roles             // string[]

// Supabase (oauthSupabaseProvider)
ctx.auth.user.id                // string — Supabase UUID
ctx.auth.user.email             // string | undefined
ctx.auth.user.role              // string — Postgres role (e.g. "authenticated")

// WorkOS (oauthWorkOSProvider)
ctx.auth.user.id                // string — WorkOS user ID
ctx.auth.user.organizationId    // string | undefined
```

---

## OAuth Proxy Removal & Custom Provider Migration

### Why OAuth Proxy Was Removed

In v1, `oauthProxy()` served as an intermediary for non-DCR providers (Google, GitHub, Slack) that require static, pre-registered client secrets. In v2, the runtime was decoupled from third-party proxy dependencies. 

To connect clients to a non-DCR upstream in v2, deploy an external authorization broker (such as Keycloak, Auth0, or Hydra) that:
1. Implements Dynamic Client Registration (RFC 7591) for connecting MCP clients.
2. Completes the upstream social/enterprise OAuth handshake.
3. Issues resource-bound JWT access tokens to the MCP client.

### Custom Verification via `oauthCustomProvider`

When connecting to an RFC 8414 compliant authorization server with DCR support, use `oauthCustomProvider`. In v2, `createTokenVerifier(resource)` must return an `OAuthTokenVerifier` object with a `verifyAccessToken` method (not a bare function), and `mapAuthInfo` reads from `authInfo.extra` (not `authInfo.claims`):

```typescript
import { oauthCustomProvider } from "mcp-use/oauth";
import { jwtVerify, createRemoteJWKSet } from "jose";

const JWKS = createRemoteJWKSet(new URL("https://auth.example.com/.well-known/jwks.json"));

const oauth = oauthCustomProvider({
  createTokenVerifier: (resource) => ({
    async verifyAccessToken(token) {
      // 1. Verify token signature, issuer, and audience
      const { payload } = await jwtVerify(token, JWKS, {
        issuer: "https://auth.example.com",
        audience: resource.href, // resource.href is the server's MCP endpoint
      });

      if (!payload.sub || !payload.exp) {
        throw new Error("Token payload missing required 'sub' or 'exp' claims");
      }

      // 2. Return AuthInfo structure; store verified claims in 'extra'
      return {
        token,
        clientId: typeof payload.client_id === "string" ? payload.client_id : "unknown",
        scopes: typeof payload.scope === "string" ? payload.scope.split(" ") : [],
        expiresAt: payload.exp,
        resource,
        extra: { payload }, // Read back in mapAuthInfo
      };
    },
  }),

  // RFC 8414 Authorization Server Metadata
  oauthMetadata: {
    issuer: "https://auth.example.com",
    authorization_endpoint: "https://auth.example.com/oauth/authorize",
    token_endpoint: "https://auth.example.com/oauth/token",
    registration_endpoint: "https://auth.example.com/oauth/register",
    jwks_uri: "https://auth.example.com/.well-known/jwks.json",
  },

  mapAuthInfo: (authInfo) => {
    const claims = authInfo.extra?.payload as Record<string, unknown> | undefined;
    return {
      user: {
        id: (claims?.sub as string) ?? authInfo.clientId,
        email: claims?.email as string | undefined,
      },
      payload: claims ?? {},
      permissions: (claims?.permissions as string[]) ?? [],
    };
  },
});
```

---

## Dual Audience Verification During Migration

In v1, access tokens were bound to the server's origin only (`https://mcp.example.com`). In v2, tokens are bound to origin + `basePath` (e.g. `https://mcp.example.com/mcp`). 

Existing clients with cached v1 tokens will be rejected with HTTP 401 (`Token audience does not include the protected resource`) unless both audiences are permitted during migration:

```typescript
import { createJwtVerifier } from "mcp-use/oauth";

createTokenVerifier: (resource) =>
  createJwtVerifier({
    issuer: "https://auth.example.com",
    jwksUrl: new URL("https://auth.example.com/.well-known/jwks.json"),
    // Accepts both v2 resource endpoint and legacy v1 origin tokens:
    audience: [resource.href, "https://mcp.example.com"],
    mapUser: (payload) => ({ id: String(payload.sub) }),
  });
```

---

## Runnable Before & After Code Transformation

### Before: Legacy v1 Server with Global Single-Mode Auth & `userId`

```typescript
// Legacy v1 Server: Global auth, root imports, userId property
// legacy-auth-server.ts
const { MCPServer, oauthClerkProvider, text } = require("mcp-use/server");
const { z } = require("zod");

const server = new MCPServer({
  name: "legacy-auth-server",
  version: "1.0.0",
  // Single-mode: blocks unauthenticated tools/list discovery!
  oauth: oauthClerkProvider({
    frontendApiUrl: process.env.CLERK_FRONTEND_API_URL,
  }),
});

server.tool(
  {
    name: "get-profile",
    description: "Get user profile",
    schema: z.object({}),
  },
  async (_, ctx) => {
    // Legacy userId property
    const id = ctx.auth.user.userId;
    return text(`Profile ID: ${id}`);
  }
);

server.listen(3000);
```

---

### After: Canonical mcp-use v2 Server with Mixed Auth & `securitySchemes`

```typescript
// Canonical mcp-use v2: Mixed auth, provider subpath, securitySchemes, normalized user.id
// server.ts
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { z } from "zod";

const server = new MCPServer({
  name: "canonical-auth-server",
  version: "2.0.0",
  basePath: "/mcp",
  mixedAuth: true, // Enables public discovery on tools/list
  oauth: oauthClerkProvider({
    frontendApiUrl: process.env.CLERK_FRONTEND_API_URL!,
  }),
});

// Public Discovery Tool: Callable without credentials
export const getSystemStatus = server.tool(
  {
    name: "get-system-status",
    title: "System Status",
    description: "Check system health and status",
    inputSchema: z.object({}),
    outputSchema: z.object({ status: z.string() }),
    securitySchemes: [{ type: "noauth" }], // Explicit public access
  },
  async () => ({
    content: [{ type: "text", text: "System operational" }],
    structuredContent: { status: "operational" },
  })
);

// Protected Tool: Requires valid OAuth bearer token
export const getProfile = server.tool(
  {
    name: "get-profile",
    title: "User Profile",
    description: "Get verified caller account details",
    inputSchema: z.object({}),
    outputSchema: z.object({
      id: z.string(),
      email: z.string().optional(),
    }),
    securitySchemes: [{ type: "oauth2", scopes: ["profile:read"] }], // Explicit OAuth protection
  },
  async (_, ctx) => {
    // Normalized user ID in v2
    const userId = ctx.auth.user.id;
    const email = ctx.auth.user.email;

    return {
      content: [{ type: "text", text: `Active user: ${userId} (${email ?? "no email"})` }],
      structuredContent: { id: userId, email },
    };
  }
);

export default server;
```

---

## Anti-Patterns and Common Auth Migration Traps

| Anti-Pattern | Root Mechanism & Failure Mode | Canonical v2 Fix |
|---|---|---|
| **Public Tools Returning 401 on `tools/list`** | In v2, attaching an OAuth provider defaults to rejecting unauthenticated discovery unless `mixedAuth: true` is configured. | Add `mixedAuth: true` to `new MCPServer({ ..., mixedAuth: true })`. |
| **Reading `ctx.auth.user.userId`** | In v2, `userId` was renamed to `id`. Reading `.userId` evaluates to `undefined`, silently breaking database lookups. | Update all code to use `ctx.auth.user.id`. |
| **Importing Providers from Root `mcp-use`** | Provider adapters are not exported from root. Triggers `SyntaxError: The requested module 'mcp-use' does not provide export 'oauth*Provider'`. | Import from subpaths: `mcp-use/oauth/<provider>`. |
| **Passing a Function to `createTokenVerifier`** | In v2, `createTokenVerifier(resource)` must return an object: `{ verifyAccessToken: async (token) => AuthInfo }`. Returning a bare function causes runtime verification failure. | Wrap verification function inside `{ verifyAccessToken: async (token) => ... }`. |
| **Reading `authInfo.claims` in `mapAuthInfo`** | `AuthInfo` has no `.claims` property. Verifier claims placed in `authInfo.extra` must be read via `authInfo.extra`. | Place custom claims in `extra` during verification and access `authInfo.extra` in `mapAuthInfo`. |
| **Calling Removed `oauthProxy()`** | The proxy was deleted in v2. Attempting to import or invoke it throws `export 'oauthProxy' not found`. | Deploy an external authorization server (Keycloak, Auth0) and verify tokens with `oauthCustomProvider`. |
| **Passing Stale Token to Public Tool** | Clients assuming public tools ignore Bearer tokens send expired credentials and receive 401 Unauthorized. | If a client sends an Authorization header, mcp-use strictly validates it even on public tools. Strip the header or refresh the token. |

---

## Next Steps & Cross-References

- **Master Overview**: See `02-v1-to-v2-overview.md` for the comprehensive breaking change checklist.
- **REST & Downstream Pass-Through**: See `09-openapi-and-rest-to-tools.md` for forwarding `ctx.auth.token` to upstream REST APIs.
- **Provider Reference Details**: See `references/11-auth/` for provider-specific setup guides.
