# Authentication

MCP servers can require authentication for HTTP transport. The SDK provides built-in OAuth 2.1 support and middleware for bearer token validation. Source-verified against `v1.x` branch.

## Authentication approaches

| Approach | Use when | Complexity |
|---|---|---|
| No auth | stdio transport, local-only servers | None |
| Bearer token (static) | Simple API key protection | Low |
| OAuth 2.1 (full) | Multi-user, token refresh, scoped access | High |
| Custom headers | Proxied behind API gateway | Low |

## Bearer token validation

### requireBearerAuth — source-verified signature

```typescript
import { requireBearerAuth } from "@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js";

type BearerAuthMiddlewareOptions = {
  verifier: OAuthTokenVerifier;   // Must implement verifyAccessToken()
  requiredScopes?: string[];      // Token must have all listed scopes
  resourceMetadataUrl?: string;   // URL for WWW-Authenticate header (RFC 9728)
};

// Returns Express RequestHandler
function requireBearerAuth(options: BearerAuthMiddlewareOptions): RequestHandler;
```

### Token verification flow (from source)

1. Extract `Authorization` header — 401 if absent
2. Check format is `Bearer <token>` (case-insensitive prefix) — 401 if malformed
3. Call `verifier.verifyAccessToken(token)` → returns `AuthInfo`
4. Check all `requiredScopes` are in `authInfo.scopes` — 403 `InsufficientScopeError` if missing
5. Validate `authInfo.expiresAt` is a number — 401 if not
6. Check token not expired (`expiresAt < Date.now() / 1000`) — 401 if expired
7. Set `req.auth = authInfo` and call `next()`

Error → HTTP status mapping:
- `InvalidTokenError` → 401 with `WWW-Authenticate: Bearer error="invalid_token"`
- `InsufficientScopeError` → 403 with `WWW-Authenticate` including required scopes
- `ServerError` → 500
- Other `OAuthError` → 400

### OAuthTokenVerifier interface

The minimal verifier interface — implement just this for bearer token validation:

```typescript
interface OAuthTokenVerifier {
  verifyAccessToken(token: string): Promise<AuthInfo>;
}
```

### Example — static API key

```typescript
import { requireBearerAuth } from "@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js";

const verifier = {
  async verifyAccessToken(token: string) {
    if (token !== process.env.MCP_API_KEY) {
      throw new Error("Invalid token");
    }
    return {
      token,
      clientId: "api-client",
      scopes: ["mcp:tools"],
      expiresAt: Math.floor(Date.now() / 1000) + 3600, // 1 hour
    };
  },
};

app.use("/mcp", requireBearerAuth({
  verifier,
  requiredScopes: ["mcp:tools"],
}));
```

### AuthInfo — source-verified type

```typescript
interface AuthInfo {
  token: string;
  clientId: string;
  scopes: string[];
  expiresAt?: number;                // Seconds since epoch (UNIX timestamp)
  resource?: URL;                    // RFC 8707 resource server identifier
  extra?: Record<string, unknown>;   // Custom claims
}
```

Access in handlers via `extra.authInfo`:

```typescript
server.registerTool("my-tool", config, async (args, extra) => {
  const { clientId, scopes } = extra.authInfo!;
  if (!scopes.includes("admin")) {
    return {
      content: [{ type: "text", text: "Insufficient permissions" }],
      isError: true,
    };
  }
  // ...
});
```

## OAuth 2.1 server

### mcpAuthRouter — source-verified signature

```typescript
import { mcpAuthRouter } from "@modelcontextprotocol/sdk/server/auth/router.js";

type AuthRouterOptions = {
  provider: OAuthServerProvider;
  issuerUrl: URL;                   // Must be HTTPS (localhost/127.0.0.1 exempt)
  baseUrl?: URL;                    // Falls back to issuerUrl
  serviceDocumentationUrl?: URL;
  scopesSupported?: string[];
  resourceName?: string;
  resourceServerUrl?: URL;          // Falls back to baseUrl then issuerUrl
  authorizationOptions?: Omit<AuthorizationHandlerOptions, 'provider'>;
  clientRegistrationOptions?: Omit<ClientRegistrationHandlerOptions, 'clientsStore'>;
  revocationOptions?: Omit<RevocationHandlerOptions, 'provider'>;
  tokenOptions?: Omit<TokenHandlerOptions, 'provider'>;
};

function mcpAuthRouter(options: AuthRouterOptions): RequestHandler;
```

### Routes mounted by mcpAuthRouter

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/authorize` | Authorization handler |
| POST | `/token` | Token exchange |
| GET | `/.well-known/oauth-protected-resource[/path]` | Protected Resource Metadata (RFC 9728) |
| GET | `/.well-known/oauth-authorization-server` | AS Metadata (RFC 8414) |
| POST | `/register` | Client registration (only if `clientsStore.registerClient` exists) |
| POST | `/revoke` | Token revocation (only if `provider.revokeToken` exists) |

### OAuthServerProvider — source-verified interface

```typescript
interface OAuthServerProvider {
  get clientsStore(): OAuthRegisteredClientsStore;

  authorize(
    client: OAuthClientInformationFull,
    params: AuthorizationParams,
    res: Response                      // Express Response — redirect the user
  ): Promise<void>;

  challengeForAuthorizationCode(
    client: OAuthClientInformationFull,
    authorizationCode: string
  ): Promise<string>;

  exchangeAuthorizationCode(
    client: OAuthClientInformationFull,
    authorizationCode: string,
    codeVerifier?: string,
    redirectUri?: string,
    resource?: URL                     // RFC 8707 resource indicator
  ): Promise<OAuthTokens>;

  exchangeRefreshToken(
    client: OAuthClientInformationFull,
    refreshToken: string,
    scopes?: string[],
    resource?: URL
  ): Promise<OAuthTokens>;

  verifyAccessToken(token: string): Promise<AuthInfo>;

  revokeToken?(
    client: OAuthClientInformationFull,
    request: OAuthTokenRevocationRequest
  ): Promise<void>;

  skipLocalPkceValidation?: boolean;   // Skip PKCE if AS handles it
}

type AuthorizationParams = {
  state?: string;
  scopes?: string[];
  codeChallenge: string;
  redirectUri: string;
  resource?: URL;
};
```

### OAuthRegisteredClientsStore — source-verified interface

```typescript
interface OAuthRegisteredClientsStore {
  getClient(clientId: string):
    OAuthClientInformationFull | undefined |
    Promise<OAuthClientInformationFull | undefined>;

  registerClient?(
    client: Omit<OAuthClientInformationFull, 'client_id' | 'client_id_issued_at'>
  ): OAuthClientInformationFull | Promise<OAuthClientInformationFull>;
}
```

Note: Do NOT delete expired client secrets in `getClient` — the middleware checks `client_secret_expires_at` automatically.

### OAuth metadata helpers

```typescript
import {
  mcpAuthMetadataRouter,
  createOAuthMetadata,
  getOAuthProtectedResourceMetadataUrl,
} from "@modelcontextprotocol/sdk/server/auth/router.js";

// Serve metadata endpoints independently
app.use(mcpAuthMetadataRouter({
  oauthMetadata: OAuthMetadata,
  resourceServerUrl: new URL("https://api.example.com"),
  serviceDocumentationUrl?: URL,
  scopesSupported?: string[],
  resourceName?: string,
}));

// Generate OAuth metadata object
const metadata = createOAuthMetadata({
  provider, issuerUrl, baseUrl?, serviceDocumentationUrl?, scopesSupported?,
});

// Get the well-known URL for a server
const url = getOAuthProtectedResourceMetadataUrl(serverUrl);
```

## OAuth error classes

The SDK provides 17 typed OAuth error classes (all extend `OAuthError`):

| Class | Error code | Standard |
|---|---|---|
| `InvalidRequestError` | `invalid_request` | RFC 6749 |
| `InvalidClientError` | `invalid_client` | RFC 6749 |
| `InvalidGrantError` | `invalid_grant` | RFC 6749 |
| `UnauthorizedClientError` | `unauthorized_client` | RFC 6749 |
| `UnsupportedGrantTypeError` | `unsupported_grant_type` | RFC 6749 |
| `InvalidScopeError` | `invalid_scope` | RFC 6749 |
| `AccessDeniedError` | `access_denied` | RFC 6749 |
| `ServerError` | `server_error` | RFC 6749 |
| `TemporarilyUnavailableError` | `temporarily_unavailable` | RFC 6749 |
| `InvalidTokenError` | `invalid_token` | RFC 6750 |
| `InsufficientScopeError` | `insufficient_scope` | RFC 6750 |
| `InvalidTargetError` | `invalid_target` | RFC 8707 |
| `InvalidClientMetadataError` | `invalid_client_metadata` | RFC 7591 |
| `UnsupportedResponseTypeError` | `unsupported_response_type` | RFC 6749 |
| `UnsupportedTokenTypeError` | `unsupported_token_type` | RFC 6749 |
| `MethodNotAllowedError` | `method_not_allowed` | Custom |
| `TooManyRequestsError` | `too_many_requests` | RFC 6585 |

All are importable from `@modelcontextprotocol/sdk/server/auth/errors.js`.

## Environment variable patterns

Never hardcode secrets. Use environment variables:

```typescript
const config = {
  apiKey: process.env.MY_API_KEY,
  dbUrl: process.env.DATABASE_URL,
};

if (!config.apiKey) {
  console.error("MY_API_KEY environment variable is required");
  process.exit(1);
}
```

For Claude Desktop configuration, secrets use `${VAR_NAME}` syntax:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["server.js"],
      "env": {
        "MY_API_KEY": "${MY_API_KEY}"
      }
    }
  }
}
```

## Security checklist

- [ ] Never hardcode tokens in source code
- [ ] Never log tokens or credentials
- [ ] Use HTTPS for all HTTP transport in production
- [ ] Validate `Host` header to prevent DNS rebinding (use `createMcpExpressApp()`)
- [ ] Set appropriate token expiration (`expiresAt` in `AuthInfo`)
- [ ] Validate scopes before performing privileged operations
- [ ] Use environment variables for all secrets
- [ ] Check `authInfo.resource` matches your server's URL (RFC 8707)
