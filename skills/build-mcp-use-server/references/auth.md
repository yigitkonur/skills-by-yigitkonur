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
- WorkOS: `import { oauthWorkOSProvider } from "mcp-use/oauth/workos"`
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
  // Declaring requiredScopes sets baseline requirement for protected tools, prompts, and resources
  oauth: oauthAuth0Provider({
    domain: process.env.AUTH0_DOMAIN!,
    requiredScopes: ["read:data"],
  }),
  mixedAuth: true, // Enables public capabilities negotiation and tools/list discovery
});

// 1. Public tool (No authentication required)
export const searchProducts = server.tool(
  {
    name: "search-products",
    inputSchema: z.object({ query: z.string() }),
    securitySchemes: [{ type: "noauth" }],
  },
  async ({ query }, ctx) => {
    // ctx.auth is undefined when called without a token.
    // NOTE: If a client sends an invalid or expired token, the server strictly returns HTTP 401.
    // A token that is sent is ALWAYS cryptographically verified, even on noauth tools.
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

### ChatGPT HTTP 200 Authentication Challenge

In standard OAuth protected resource flows, unauthenticated requests to protected endpoints return `HTTP 401 Unauthorized` with a `WWW-Authenticate: Bearer ...` header. However, when ChatGPT (`User-Agent: ChatGPT/1.0`) invokes a protected tool without a bearer token on a `mixedAuth` server, receiving an HTTP 401 causes ChatGPT to abruptly abort the conversation and report a fatal error.

To ensure seamless conversational user authorization, `mcp-use` detects ChatGPT requests and automatically intercepts missing-token invocations on protected tools, returning `HTTP 200 OK` with an error `CallToolResult` envelope:
- `isError: true`
- `content: [{ type: "text", text: "Please sign in to continue." }]`
- `_meta: { "mcp/www_authenticate": "Bearer scope=\"...\"" }`

This allows ChatGPT to render its inline interactive OAuth sign-in card directly in the chat interface without breaking the active chat session. Once the user authenticates, ChatGPT retries the tool invocation with a valid bearer token.

> [!NOTE]
> On a `mixedAuth` server:
> - Tools that omit `securitySchemes` require the provider's `requiredScopes`.
> - Resources, resource templates, and prompts **always require sign-in** with `requiredScopes`.
> - Tool views load signed out by default so ChatGPT can preview the UI during connector creation.
> - A token that is sent is always verified; an invalid or expired token yields HTTP 401, even on `noauth` tools.

---

## 3. Verified Request Identity (`ctx.auth`) vs Client Hints (`ctx.client.user()`)

### Verified Identity (`ctx.auth`)
When OAuth is configured and verified, callbacks receive `OAuthAuth<TUser>`:
- `ctx.auth.user`: Provider-normalized identity. Built-in users always have `id`.
- `ctx.auth.scopes`: Array of granted scopes.
- `ctx.auth.permissions`: Array of mapped application permissions.
- `ctx.auth.payload`: Verified token claims (raw decoded JWT claims).
- `ctx.auth.accessToken`: Bearer token (for intentional downstream API delegation only).
- `ctx.auth.clientId`: Client ID claim from `azp` or `client_id`.
- `ctx.auth.expiresAt`: Unix expiration in seconds.
- `ctx.auth.resource`: Protected resource identity URL.

Authorize specific permissions rather than checking only that a user exists:
```ts
if (!ctx.auth.permissions.includes("documents:delete")) {
  return { isError: true, content: [{ type: "text", text: "Forbidden: documents:delete required" }] };
}
```

### Unverified Client Hints (`ctx.client.user()`)
`ctx.client.user()` returns client-reported, unverified metadata (`locale`, `location`, `userAgent`, `conversationId`, `subject`, `organizationId`).

> [!CAUTION]
> **Security Mandate:** Never treat `ctx.client.user()` or `ctx.client.info()` as authenticated identity. It is self-reported by the client, unverified, and trivial to spoof. Always use `ctx.auth.user` and `ctx.auth.permissions` for authentication, authorization, and tenant isolation.

---

## 4. Custom Provider (`oauthCustomProvider`)

Custom OAuth providers must implement the strict v2 provider interfaces:
- `createTokenVerifier`: Receives canonical MCP protected resource `resource: URL` and returns `OAuthTokenVerifier`.
- `mapAuthInfo`: Receives `OAuthAuthInfo` and returns `OAuthExtra<TUser>`. Must return `{ user, payload, permissions }`.

```ts
import { oauthCustomProvider, type OAuthAuthInfo, type OAuthExtra } from "mcp-use/oauth";

interface CustomUser {
  id: string;
  email?: string;
}

const customProvider = oauthCustomProvider<CustomUser>({
  oauthMetadata: {
    issuer: "https://auth.example.com",
    authorization_endpoint: "https://auth.example.com/oauth/authorize",
    token_endpoint: "https://auth.example.com/oauth/token",
  },
  // Receives the canonical MCP protected resource URL
  createTokenVerifier: (resource: URL) => {
    return async (token: string): Promise<OAuthAuthInfo> => {
      // Verify token signature, expiry, and audience matching resource.origin
      const claims = await verifyJwt(token, { audience: resource.origin });
      return {
        token,
        claims,
        scopes: typeof claims.scope === "string" ? claims.scope.split(" ") : [],
      };
    };
  },
  // Maps verified auth info to OAuthExtra<CustomUser> (user, payload, and permissions are required)
  mapAuthInfo: (authInfo: OAuthAuthInfo): OAuthExtra<CustomUser> => {
    const claims = authInfo.claims as Record<string, unknown>;
    const scopes = authInfo.scopes ?? [];
    return {
      user: {
        id: String(claims.sub),
        email: claims.email as string | undefined,
      },
      payload: claims,
      permissions: scopes.map((scope) => `perm:${scope}`),
    };
  },
  // Optional mount hook introduced in v2.7.0
  setup: (host) => {
    // host.mixedAuth reports whether mixedAuth is active
  },
});
```

---

## 5. Security Invariants
- Never treat `ctx.client.user()`, locale, conversation ID, or other client-sent metadata as authenticated identity.
- Keep authorization next to sensitive operations or in narrowly scoped MCP middleware (`server.use("mcp:tools/call", ...)`).
- Never log, echo, or store raw bearer tokens or client secrets.
- Multi-request state belongs in an external database, not in module globals or in-memory session registries.
