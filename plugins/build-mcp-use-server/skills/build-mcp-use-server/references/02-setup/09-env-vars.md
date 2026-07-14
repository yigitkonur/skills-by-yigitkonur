# Server Environment Variables

Every env var the running `mcp-use` server reads. CLI-only env vars (auth tokens, debug levels for the build tool) live in `03-cli/14-environment-variables.md`.

## Core runtime

| Variable | Effect | Default |
|---|---|---|
| `PORT` | HTTP listen port | `3000` |
| `HOST` | Bind hostname | `localhost` |
| `NODE_ENV` | Disables dev-only features (Inspector, type generation) when set to `production` | `development` |
| `MCP_URL` | Full public base URL. **Fallback only** — used when the `MCPServer({ baseUrl })` constructor option is unset. The constructor option always wins (per `mcp-use@1.26.0` `getServerBaseUrl()`). Used to rewrite widget asset paths behind reverse proxies and CDNs. | `http://{HOST}:{PORT}` |
| `MCP_BASE_URL` | Alias accepted by some integrations; prefer `MCP_URL` | — |
| `MCP_SERVER_URL` | Build-time public URL for widget asset paths (read by `mcp-use build`, baked into the manifest) | — |

`MCP_URL` is read at runtime; `MCP_SERVER_URL` is read at build time. Set both to the same value when deploying.

## CSP / asset domains

| Variable | Effect | Default |
|---|---|---|
| `CSP_URLS` | Comma-separated list of extra origins added to widget CSP `resource_domains` | — |

Use when widgets fetch from third-party CDNs.

## Logging

| Variable | Effect | Default |
|---|---|---|
| `DEBUG` | Enables verbose framework logging when truthy | — |
| `MCP_DEBUG_LEVEL` | Log level — `info`, `debug`, `trace` | `info` |

## Sessions and streams

| Variable | Effect | Default |
|---|---|---|
| `REDIS_URL` | Connection string consumed by `RedisSessionStore` and `RedisStreamManager` (only when you instantiate those stores) | — |

`REDIS_URL` is not magic — `mcp-use` only reads it if you wire it into a Redis store yourself. Example wiring lives in `08-server-config/` and `10-sessions/`.

## OAuth

The bundled OAuth providers (`oauthAuth0Provider`, `oauthSupabaseProvider`, `oauthKeycloakProvider`, `oauthCustomProvider`) read provider-specific env vars. Common patterns:

| Variable | Read by | Purpose |
|---|---|---|
| `MCP_AUTH_ISSUER` | Custom / Keycloak provider | OIDC issuer URL |
| `MCP_AUTH_CLIENT_ID` | Most providers | OAuth client id |
| `MCP_AUTH_CLIENT_SECRET` | Confidential clients | OAuth client secret |
| `MCP_AUTH_AUDIENCE` | Auth0 | Token audience |
| `MCP_AUTH_REDIRECT_URI` | All providers | Post-login redirect |
| `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET` | `oauthAuth0Provider` | Auth0-specific |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET` | `oauthSupabaseProvider` | Supabase-specific |
| `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID` | `oauthKeycloakProvider` | Keycloak-specific |

Exact names depend on the provider wrapper you use; the wrappers expose explicit constructor args, so prefer those over env-only configuration. See `11-auth/` for full provider configs.

## Behavior matrix

| You want to | Set |
|---|---|
| Run on port 8080 locally | `PORT=8080` |
| Bind to all interfaces | `HOST=0.0.0.0` |
| Disable Inspector and type-gen for prod | `NODE_ENV=production` |
| Serve widgets behind a reverse proxy | `MCP_URL=https://your-domain.com` (runtime) + `MCP_SERVER_URL=https://your-domain.com` (build) |
| Allow widget to fetch from extra CDNs | `CSP_URLS=https://cdn.example.com,https://images.example.com` |
| Crank up logs | `MCP_DEBUG_LEVEL=debug` (or `trace`) |
| Use Redis for sessions | `REDIS_URL=redis://...` plus wiring in code |

## Where these come from

| Source file | Notes |
|---|---|
| `package.json scripts` | Inherited at process start. |
| `.env.local`, `.env`, `.env.production` | Loaded by `dotenv` if you `import "dotenv/config"`. `mcp-use` does not auto-load dotenv. |
| Cloud platform env panel | Production values; do not check secrets into git. |

For deploy-time secret upload, see `25-deploy/`.

## See also

- `03-cli/14-environment-variables.md` — env vars the CLI itself reads.
- `08-server-config/` — `MCPServer` constructor options (which often read these vars).
- `11-auth/` — OAuth provider env requirements.
