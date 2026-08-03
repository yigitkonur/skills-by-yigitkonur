# OAuth Provider: Keycloak

*Read this when integrating self-hosted Keycloak for fine-grained auth.*

## Import & Factory

```typescript
import { oauthKeycloakProvider } from "mcp-use/oauth/keycloak";

const oauth = oauthKeycloakProvider({
  serverUrl: "https://keycloak.example.com",
  realm: "production",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `serverUrl` | `string \| URL` | `"https://keycloak.example.com"` | Base URL of the Keycloak server |
| `realm` | `string` | `"production"` | Realm that issues accepted tokens; must not contain `/`, `?`, or `#`, or the factory throws `TypeError` |

There is no separate `audience` option — verification is bound to the resolved MCP resource, so Keycloak must issue access tokens for that exact resource.

## Optional Options

```typescript
oauthKeycloakProvider({
  serverUrl: "...",
  realm: "...",
  resource?: string | URL,              // Full MCP endpoint URL (overrides host header inference)
  requiredScopes?: readonly string[],   // Scopes required by bearer gate (default: none enforced)
  scopesSupported?: readonly string[],  // Scopes advertised to clients (no factory default)
  resourceName?: string,                // Human-readable name for OAuth metadata
  serviceDocumentationUrl?: URL,        // Documentation link in OAuth metadata
})
```

## User Type

```typescript
type KeycloakOAuthUser = {
  id: string;                                  // sub claim
  email?: string;
  name?: string;
  preferredUsername?: string;                  // preferred_username claim
  givenName?: string;                           // given_name claim
  familyName?: string;                          // family_name claim
  emailVerified?: boolean;                      // email_verified claim
  roles: string[];                              // realm_access.roles, normalized (empty if realm_access absent)
  realmAccess?: Record<string, unknown>;        // Raw realm_access claim, unmodified
  resourceAccess?: Record<string, unknown>;     // Raw resource_access claim, unmodified
};
```

Client (resource) roles from `resource_access` are flattened to top-level `ctx.auth.permissions` as `<resource>:<role>` strings — e.g. `resource_access.mcp-api.roles: ["admin"]` becomes permission `"mcp-api:admin"`.

## Environment Variables

The provider does not read any environment variables itself — `serverUrl` and `realm` are plain function arguments:

```bash
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=mcp
```

```typescript
const serverUrl = process.env.KEYCLOAK_SERVER_URL;
const realm = process.env.KEYCLOAK_REALM;
if (!serverUrl || !realm) throw new Error("KEYCLOAK_SERVER_URL and KEYCLOAK_REALM are required");

const oauth = oauthKeycloakProvider({ serverUrl, realm });
```

## Configure Keycloak

Before wiring the provider:

1. Configure Dynamic Client Registration for the hosts used by MCP clients. Keep redirect URI policies strict; add browser client origins when needed.
2. For production, only require Initial Access Tokens after confirming every intended MCP client can send one during registration — mcp-use verifies tokens, it does not perform registration on the client's behalf.
3. Configure token audience/resource claims for the canonical MCP endpoint.
4. Serve both Keycloak and the MCP server over HTTPS.

## Gotchas

1. No trailing slash needed on `serverUrl`; it's normalized internally
2. Issuer is derived as `<serverUrl>/realms/<realm>` — no separate issuer config
3. `roles` contains realm roles only (from `realm_access.roles`); check `resourceAccess`/`ctx.auth.permissions` for app-specific (client) roles
4. No built-in default scopes — the factory does not set `["openid", "profile"]` or any other value unless you pass `scopesSupported`
5. `realm` must not contain `/`, `?`, or `#`
