# Authentication & Mixed Auth

*Authoritative guide for mcp-use v2 authentication, OAuth providers, mixed auth, and verified user context.*

Official documentation:
- [Authentication Overview](https://docs.mcp-use.com/v2/typescript/server/authentication)
- [Mixed Authentication](https://docs.mcp-use.com/v2/typescript/server/authentication/mixed-auth)
- [User Context](https://docs.mcp-use.com/v2/typescript/server/authentication/user-context)

---

## 1. Provider Adapters

Import provider adapters from explicit subpaths in `mcp-use/oauth/*`:

- Clerk: `import { oauthClerkProvider } from "mcp-use/oauth/clerk"`
- Auth0: `import { oauthAuth0Provider } from "mcp-use/oauth/auth0"`
- WorkOS: `import { oauthWorkosProvider } from "mcp-use/oauth/workos"`
- Supabase: `import { oauthSupabaseProvider } from "mcp-use/oauth/supabase"`
- Keycloak: `import { oauthKeycloakProvider } from "mcp-use/oauth/keycloak"`
- Better Auth: `import { oauthBetterAuthProvider } from "mcp-use/oauth/better-auth"`
- Scalekit: `import { oauthScalekitProvider } from "mcp-use/oauth/scalekit"`
- Convex: `import { oauthConvexProvider } from "mcp-use/oauth/convex"`
- Custom: `import { oauthCustomProvider, createJwtVerifier } from "mcp-use/oauth"`

---

## 2. Mixed Authentication (`mixedAuth: true`)

`mixedAuth: true` lets unauthenticated clients connect and list tools, resources, and prompts from one OAuth-enabled endpoint in Claude and ChatGPT:

```ts
import { MCPServer } from "mcp-use";
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";
import { z } from "zod";

const server = new MCPServer({
  name: "store-server",
  version: "1.0.0",
  oauth: oauthAuth0Provider({ domain: process.env.AUTH0_DOMAIN! }),
  mixedAuth: true, // Enables public tools/list discovery
});

// 1. Public tool (No authentication required)
export const searchProducts = server.tool(
  {
    name: "search-products",
    inputSchema: z.object({ query: z.string() }),
    securitySchemes: [{ type: "noauth" }],
  },
  async ({ query }, ctx) => {
    // ctx.auth is optional (present if client sent a valid token)
    return { content: [{ type: "text", text: `Results for ${query}` }] };
  },
);

// 2. Optional authentication tool
export const getCart = server.tool(
  {
    name: "get-cart",
    inputSchema: z.object({ sessionId: z.string() }),
    securitySchemes: [
      { type: "noauth" },
      { type: "oauth2", scopes: ["cart:read"] }
    ],
  },
  async ({ sessionId }, ctx) => {
    const user = ctx.auth?.user;
    return { content: [{ type: "text", text: user ? `Cart for ${user.id}` : `Anonymous cart ${sessionId}` }] };
  },
);

// 3. Required sign-in tool with specific scopes
export const checkout = server.tool(
  {
    name: "checkout",
    inputSchema: z.object({ orderId: z.string() }),
    securitySchemes: [{ type: "oauth2", scopes: ["orders:write"] }],
  },
  async ({ orderId }, ctx) => {
    // ctx.auth is guaranteed and typed
    return { content: [{ type: "text", text: `Order ${orderId} placed for user ${ctx.auth.user.id}` }] };
  },
);

export default server;
```

> [!NOTE]
> On a `mixedAuth` server, resources, resource templates, and prompts **always require sign-in**. Tool views load signed out so ChatGPT can preview the UI during connector creation.

---

## 3. Verified Request Identity (`ctx.auth`)

When OAuth is configured and verified, callbacks receive:
- `ctx.auth.user`: Normalized identity. Built-in users always have `id`.
- `ctx.auth.scopes`: Array of granted scopes.
- `ctx.auth.permissions`: Array of mapped application permissions.
- `ctx.auth.payload`: Verified token claims.
- `ctx.auth.accessToken`: Bearer token (for intentional downstream API delegation only).
- `ctx.auth.clientId`, `expiresAt`, `resource`.

Authorize specific permissions rather than checking only that a user exists:
```ts
if (!ctx.auth.permissions.includes("documents:delete")) {
  return { isError: true, content: [{ type: "text", text: "Forbidden" }] };
}
```

---

## 4. Custom Provider (`oauthCustomProvider`)

```ts
import { oauthCustomProvider } from "mcp-use/oauth";

const customProvider = oauthCustomProvider({
  oauthMetadata: {
    issuer: "https://auth.example.com",
    authorization_endpoint: "https://auth.example.com/oauth/authorize",
    token_endpoint: "https://auth.example.com/oauth/token",
  },
  createTokenVerifier: () => {
    // Return async token verification function
    return async (token) => ({ sub: "user-123", scope: "read write" });
  },
  mapAuthInfo: (claims) => ({
    user: { id: claims.sub },
    scopes: claims.scope.split(" "),
  }),
  // Optional mount hook introduced in v2.7.0
  setup: (host) => {
    // host.mixedAuth reports whether mixedAuth is active
  },
});
```

---

## 5. Security Invariants
- Never treat `ctx.client.user()`, locale, conversation ID, or other client-sent metadata as authenticated identity.
- Keep authorization next to sensitive operations or in narrowly scoped MCP middleware.
- Never log, echo, or store raw bearer tokens or client secrets.
- Multi-request state belongs in an external database, not in module globals or in-memory session registries.
