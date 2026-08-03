# Attaching a Provider to MCPServer

*Read this when setting up OAuth for the first time or moving between providers.*

An OAuth provider factory is passed to the `MCPServer` constructor via the `oauth` config key:

```typescript
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";

const oauth = oauthClerkProvider({ frontendApiUrl: "..." });

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth,
});
```

Each provider factory accepts options specific to that identity service — environment URLs, secrets, scope lists, metadata. See `providers/` for each provider's options and required env vars.

## What the Server Exposes

Once OAuth is configured, mounting (`listen()` or the first `fetch()` call) registers two things: a public discovery middleware and a bearer gate on the MCP route only.

### Public discovery endpoints

`MCPServer` serves `/.well-known/oauth-protected-resource` and `/.well-known/oauth-authorization-server` **without requiring a token**. Clients must be able to fetch these unauthenticated to complete OAuth discovery — RFC 9728 (protected-resource metadata) and RFC 8414 (authorization-server metadata). These routes advertise the provider's authorization, token, registration, and JWKS endpoints (`oauthMetadata` on the provider) plus `scopesSupported`, `resourceName`, and `serviceDocumentationUrl` when configured.

### Protected route

Only the exact MCP transport route (`basePath`, default `/mcp`) requires `Authorization: Bearer <token>`. All other routes on the server — the discovery endpoints above, static assets, and any custom routes registered with `server.get`/`server.post`/etc. — are left public by the bearer gate; add your own middleware if a custom route needs protecting. The one built-in exception: when `publicLandingPage: true` is set, an HTML navigation request to `basePath` bypasses the bearer gate to render the landing page.

### Unauthenticated behavior on the MCP route

- No bearer token → **401 Unauthorized**, with a `WWW-Authenticate` header pointing at the protected-resource metadata URL
- Invalid, expired, wrong-resource, or (when `requiredScopes` is set) insufficiently-scoped token → **401 Unauthorized**
- Validation happens at the HTTP boundary via `requireBearerAuth`; tool/resource/prompt callback code never runs for a rejected request

### Provider-specific metadata

Each provider's `oauthMetadata` object supplies:
- **`authorization_endpoint`** — where the client sends the user to authenticate
- **`token_endpoint`** — where the client exchanges an authorization code for an access token
- **`registration_endpoint`** — where the client performs Dynamic Client Registration
- **`jwks_uri`** — only some providers include this in the metadata object itself (e.g. Auth0 omits it); token verification instead always uses a `jwksUrl` passed internally to `createJwtVerifier`, independent of whether it appears in the advertised metadata

The MCP server does not construct these URLs generically — each built-in provider factory (`oauth/clerk.ts`, `oauth/auth0.ts`, etc.) derives them from the issuer/domain option you pass in.

## Resource URL Inference

The server needs a canonical **resource** URL (the full public MCP endpoint) to bind tokens to and to publish in metadata. Resolution order:

1. `resource` passed explicitly to the provider factory (e.g. `oauthClerkProvider({ resource: "https://mcp.example.com/mcp", ... })`) — must exactly match `basePath`.
2. The `MCP_URL` environment variable, combined with `basePath`, when no explicit `resource` is set.
3. A localhost fallback (`http://localhost:<port><basePath>`) — **only** when `listen()` binds to `127.0.0.1`/`localhost`/`::1` and neither of the above is set.

Listening on a non-local host, or calling `server.fetch` directly (Workers/edge), without an explicit `resource` or `MCP_URL` throws at mount time: `"OAuth requires an explicit resource or MCP_URL when using server.fetch or listening on a non-local host."` Set `MCP_URL` to the public server origin in production.

## Scopes

**Required scopes** (enforced by the bearer gate before a request reaches callback code):
- Passed via `requiredScopes` in provider options (`OAuthResourceOptions`)
- Token must include all of them or the request is rejected with 401
- No built-in provider factory sets a default — omit `requiredScopes` and any successfully verified token is accepted regardless of scope

**Advertised scopes** (in OAuth metadata's `scopes_supported`):
- Passed via `scopesSupported` in provider options
- Tells clients what scopes the server accepts; used by clients during DCR and authorization
- Better Auth's factory falls back to `["openid", "profile", "email", "offline_access"]` when `scopesSupported` is omitted — the only built-in provider with a non-empty default; the other five leave it unset unless you supply it

```typescript
oauthClerkProvider({
  frontendApiUrl: "...",
  requiredScopes: ["email"],              // Request fails if token lacks 'email'
  scopesSupported: ["email", "profile"],  // Advertise these to clients
})
```

See each provider's file in `providers/` for its specific options and env vars.
