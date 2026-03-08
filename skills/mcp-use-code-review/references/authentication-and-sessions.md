# Authentication and Session Management

## Authentication

### Overview

MCP supports OAuth 2.0/2.1 for server authentication. The approach differs significantly between the official SDK (manual) and mcp-use (built-in providers).

### Official TS SDK — Manual OAuth

The official SDK provides interfaces but requires manual implementation:

```typescript
// You must implement this interface
interface OAuthServerProvider {
    clientsStore: OAuthRegisteredClientsStore;
    authorize(client: OAuthClientInformationFull, params: AuthorizationParams): Promise<string>;
    challengeForAuthorizationCode(client: OAuthClientInformationFull, authorizationCode: string): Promise<string>;
    exchangeAuthorizationCode(client: OAuthClientInformationFull, authorizationCode: string, codeVerifier?: string): Promise<OAuthTokens>;
    exchangeRefreshToken(client: OAuthClientInformationFull, refreshToken: string, scopes?: string[]): Promise<OAuthTokens>;
    verifyAccessToken(token: string): Promise<AuthInfo>;
}

// Then wire up auth middleware manually
function requireBearerAuth(options) {
    return async (req, res, next) => {
        const token = req.headers.authorization?.slice('Bearer '.length);
        if (!token) { res.status(401).end(); return; }
        const authInfo = await provider.verifyAccessToken(token);
        next();
    };
}
```

### mcp-use TS — Built-in OAuth Providers

```typescript
import { MCPServer, oauthAuth0Provider } from 'mcp-use/server'

const server = new MCPServer({
    name: 'protected-server',
    oauth: oauthAuth0Provider({
        domain: 'your-tenant.auth0.com',
        audience: 'https://your-api.example.com',
    }),
})
```

### Available Providers

| Provider | Import | Key Config |
|---|---|---|
| Auth0 | `oauthAuth0Provider` | `{ domain, audience }` |
| Supabase | `oauthSupabaseProvider` | `{ projectId }` (+ `jwtSecret` only for legacy HS256 projects) |
| WorkOS | `oauthWorkOSProvider` | `{ subdomain }` (+ optional `apiKey`, `clientId`) |
| Keycloak | `oauthKeycloakProvider` | Provider-specific realm/client settings |
| Custom | `oauthCustomProvider` | Custom OAuth/OIDC endpoints + token verification |

### Auth0 Configuration

```typescript
import { oauthAuth0Provider } from 'mcp-use/server'

const oauth = oauthAuth0Provider({
    domain: 'your-tenant.auth0.com',
    audience: 'https://your-api.example.com',
})
```

### Supabase Configuration

```typescript
import { oauthSupabaseProvider } from 'mcp-use/server'

// ES256 (recommended; uses JWKS automatically)
const oauth = oauthSupabaseProvider({
    projectId: process.env.MCP_USE_OAUTH_SUPABASE_PROJECT_ID!,
})

// HS256 (legacy projects only)
const legacyOauth = oauthSupabaseProvider({
    projectId: process.env.MCP_USE_OAUTH_SUPABASE_PROJECT_ID!,
    jwtSecret: process.env.MCP_USE_OAUTH_SUPABASE_JWT_SECRET!,
})
```

### WorkOS Configuration

```typescript
import { oauthWorkOSProvider } from 'mcp-use/server'

const oauth = oauthWorkOSProvider({
    subdomain: process.env.MCP_USE_OAUTH_WORKOS_SUBDOMAIN!,
    apiKey: process.env.MCP_USE_OAUTH_WORKOS_API_KEY,      // optional
    clientId: process.env.MCP_USE_OAUTH_WORKOS_CLIENT_ID,  // optional
})
```

### Accessing Auth in Tools

```typescript
server.tool({ name: 'protected-action' }, async (_, context) => {
    const user = context.auth

    // Standard fields
    console.log(user.userId, user.email, user.name)

    // Authorization fields when present
    if (!user.permissions?.includes('documents:write')) {
        return error('Forbidden: missing documents:write permission')
    }

    return text(`Action completed for ${user.userId}`)
})
```

### User Context

```typescript
interface UserInfo {
    userId: string
    email?: string
    name?: string
    username?: string
    nickname?: string
    picture?: string
    roles?: string[]
    permissions?: string[]
    scopes?: string[]
    [key: string]: any
}

const server = new MCPServer({
    name: 'my-server',
    version: '1.0.0',
    oauth: oauthAuth0Provider({
        domain: 'your-tenant.auth0.com',
        audience: 'https://your-api.example.com',
        getUserInfo: (payload) => ({
            userId: payload.sub,
            email: payload.email,
            name: payload.name,
            roles: payload['https://myapp.com/roles'] || [],
            ...payload,
        }),
    }),
})
```

### Python Authentication

```python
from mcp_use.server.auth import BearerAuthProvider

server = MCPServer(
    name="protected-server",
    auth=BearerAuthProvider(token="your-secret-token"),
)
```

### OAuth Endpoints (Auto-configured by mcp-use)

| Endpoint | Purpose |
|---|---|
| `GET /authorize` | Start OAuth flow |
| `POST /token` | Exchange code for tokens |
| `GET /.well-known/oauth-authorization-server` | OAuth metadata |
| `GET /.well-known/openid-configuration` | OIDC metadata |

When OAuth is configured, `/mcp/*` endpoints require `Authorization: Bearer <token>`.

---

## Session Management

### Overview

MCP servers can run in **stateful** mode (sessions + SSE) or **stateless** mode (no session tracking).

### Session Lifecycle

```
Client                          Server
──────                          ──────
POST /mcp (initialize)    →    Create session + session ID
                           ←    mcp-session-id response header
POST /mcp (next calls)    →    Route by mcp-session-id
GET /mcp (SSE)            →    Open stream in stateful mode
DELETE /mcp               →    Terminate session
```

If a client sends an invalid/expired session ID in stateful mode, server returns **HTTP 404** (per MCP spec), and modern clients re-initialize automatically.

### Stateful vs Stateless Mode

- **Node.js default behavior**: per-request auto-detection via `Accept` header.
  - `application/json, text/event-stream` → stateful
  - `application/json` only → stateless
- **Deno/edge runtimes**: stateless by default.
- Force mode with `stateless: true` or `stateless: false`.

### mcp-use Session Storage

`sessionStore` controls serializable session metadata; `streamManager` controls active SSE stream routing.

#### FileSystemSessionStore (Development Default)

```typescript
import { MCPServer, FileSystemSessionStore } from 'mcp-use/server'

const server = new MCPServer({
    name: 'dev-server',
    version: '1.0.0',
    sessionStore: new FileSystemSessionStore({
        path: '.mcp-use/sessions.json',
        debounceMs: 100,
        maxAgeMs: 86400000,
    }),
})
```

- Default provider in development mode (`NODE_ENV !== 'production'`)
- Persists sessions across hot reloads
- Not recommended for production/distributed deployments

#### InMemorySessionStore (Default in Production when no custom store is set)

```typescript
import { MCPServer, InMemorySessionStore } from 'mcp-use/server'

const server = new MCPServer({
    name: 'prod-server',
    version: '1.0.0',
    sessionStore: new InMemorySessionStore(),
})
```

- Fast, no dependencies
- Sessions lost on restart

#### RedisSessionStore + RedisStreamManager (Distributed Production)

```typescript
import { MCPServer, RedisSessionStore, RedisStreamManager } from 'mcp-use/server'
import { createClient } from 'redis'

const redis = createClient({ url: process.env.REDIS_URL })
const pubSubRedis = redis.duplicate()

await redis.connect()
await pubSubRedis.connect()

const server = new MCPServer({
    name: 'prod-server',
    version: '1.0.0',
    sessionStore: new RedisSessionStore({ client: redis }),
    streamManager: new RedisStreamManager({
        client: redis,
        pubSubClient: pubSubRedis,
    }),
})
```

- Full horizontal scaling support
- Cross-instance notification delivery via Redis Pub/Sub

### Split Architecture: SessionStore vs StreamManager

```
SessionStore                          StreamManager
────────────                          ─────────────
Stores: session metadata              Manages: active SSE connections
(serializable data)                   (in-process connections)

InMemorySessionStore  ←→ InMemoryStreamManager     (single server)
FileSystemSessionStore←→ InMemoryStreamManager     (development persistence)
RedisSessionStore     ←→ RedisStreamManager        (distributed)
```

### Session Configuration

```typescript
const server = new MCPServer({
    name: 'my-server',
    version: '1.0.0',
    stateless: false,
    sessionIdleTimeoutMs: 3600000, // 1 hour
})
```

## Deployment Patterns

| Pattern | SessionStore | StreamManager | Use Case |
|---|---|---|---|
| Development | FileSystem | InMemory | Local dev with HMR persistence |
| Single instance | InMemory (or Redis) | InMemory | Small production |
| Distributed | Redis | Redis (Pub/Sub) | Scaled production |
| Stateless | None | None | Edge/serverless request-response |
