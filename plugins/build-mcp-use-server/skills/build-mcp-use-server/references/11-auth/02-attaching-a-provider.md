# Attaching a Provider to MCPServer

*Read this when setting up OAuth for the first time or moving between providers.*

An OAuth provider factory is passed to the `MCPServer` constructor via the `oauth` config key:

```typescript
import { MCPServer } from "mcp-use/server";
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

Once OAuth is configured:

### Protected Endpoints

1. **OAuth metadata discovery** (`/.well-known/oauth-authorization-server`): Advertises registration, authorization, token, and JWKS endpoints to clients; follows RFC 8414.
2. **MCP protocol** (`/mcp/*`): Tools, resources, prompts endpoints; all require `Authorization: Bearer <token>` header.

### Unauthenticated Behavior

- Requests without a bearer token → **401 Unauthorized** (to metadata AND MCP endpoints)
- Requests with invalid/expired token → **401 Unauthorized**
- Validation happens at the HTTP boundary; handler code never receives an unauthenticated request

### Provider-Specific Metadata

Each provider defines its own:
- **Authorization endpoint** — where clients register and authenticate users
- **Token endpoint** — where clients exchange auth codes for access tokens
- **JWKS endpoint** — public keys to verify token signatures
- **Registration endpoint** — where clients register with OAuth server (DCR)

The MCP server knows these from provider configuration; clients discover them via `/.well-known/oauth-authorization-server`.

## Resource URL Inference

Clients registering with the identity provider need the MCP server's full canonical URL to set up correct token audiences and CORS origins. The server infers this from the request:

```
https://<Host header or resource option>/<basePath>
```

If ambiguous, pass `resource: "https://mcp.example.com"` to the provider factory to override.

## Scopes

**Required scopes** (enforced by bearer gate):
- Passed via `requiredScopes` in provider options
- Token must include all of them or request is rejected
- Defaults vary per provider (Clerk uses `profile`; Keycloak uses `openid profile`)

**Advertised scopes** (in OAuth metadata):
- Passed via `scopesSupported` in provider options
- Tells clients what scopes the server accepts
- Used during client registration (DCR); clients request these when authorizing users

```typescript
oauthClerkProvider({
  frontendApiUrl: "...",
  requiredScopes: ["email"],              // Request fails if token lacks 'email'
  scopesSupported: ["email", "profile"],  // Advertise these to clients
})
```

See each provider's file for defaults and common configurations.
