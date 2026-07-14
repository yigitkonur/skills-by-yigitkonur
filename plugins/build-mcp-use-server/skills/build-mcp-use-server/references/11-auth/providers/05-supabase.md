# Supabase

Current mcp-use uses Supabase as a DCR-direct OAuth 2.1 authorization server. Supabase handles OAuth and issues tokens; your MCP server verifies them and hosts the consent page. Older Supabase proxy-mode workarounds had significant pitfalls — see the migration cross-reference at the bottom.

## Prerequisites

In the [Supabase Dashboard](https://app.supabase.com/):

1. **Authentication → Sign In / Providers → OAuth Server** — toggle on. Toggle **Allow Dynamic OAuth Apps** so MCP clients can self-register.
2. **Authentication → URL Configuration → Consent Screen URL** — point at your MCP server's consent route (e.g. `http://localhost:3000/auth/consent`). Supabase redirects to this URL with `?authorization_id=<uuid>`.
3. **Authentication → Sign In / Providers** — enable at least one sign-in method:
   - **Anonymous sign-ins** for demos
   - **Email + password**, **magic links**, or social providers for real apps
4. Copy from **Project Settings**:
   - **Project ID**
   - **Publishable key** (`sb_publishable_...`) — used by your consent UI and tools, not by mcp-use itself

## Environment variables

```bash
MCP_USE_OAUTH_SUPABASE_PROJECT_ID=your-project-id
MCP_USE_OAUTH_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...   # for tools and consent UI
# Legacy HS256 projects only:
# MCP_USE_OAUTH_SUPABASE_JWT_SECRET=...
```

New Supabase projects sign with **ES256** and expose JWKS — the provider auto-detects. Only legacy HS256 projects need the secret.

## Server config

```ts
import { MCPServer, oauthSupabaseProvider } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  oauth: oauthSupabaseProvider(), // reads MCP_USE_OAUTH_SUPABASE_PROJECT_ID
})

await server.listen(3000)
```

Explicit config:

```ts
oauth: oauthSupabaseProvider({
  projectId: 'your-project-id',
  verifyJwt: process.env.NODE_ENV === 'production',
  scopesSupported: ['openid', 'profile', 'email'],
})
```

## Hosting the consent UI

Supabase redirects browsers to your consent screen URL with `?authorization_id=<uuid>`. Your route must:

1. Sign the user in (anonymous, email/password, or social).
2. Load authorization details with the Supabase JS SDK (`auth.oauth.getAuthorizationDetails`).
3. Render approve/deny.
4. Submit decision back to Supabase (`auth.oauth.approveAuthorization` / `auth.oauth.denyAuthorization`).

mcp-use is **not involved** in this step. Use the [`mcp-oauth-supabase-template`](https://github.com/mcp-use/mcp-oauth-supabase-template) starter, or follow Supabase's [OAuth Server — Getting Started](https://supabase.com/docs/guides/auth/oauth-server/getting-started).

## Calling Supabase from a tool

Use the user's access token so RLS policies see them as authenticated:

```ts
import { createClient } from '@supabase/supabase-js'

server.tool(
  { name: 'list-notes' },
  async (_args, ctx) => {
    const supabase = createClient(
      `https://${process.env.MCP_USE_OAUTH_SUPABASE_PROJECT_ID}.supabase.co`,
      process.env.MCP_USE_OAUTH_SUPABASE_PUBLISHABLE_KEY!,
      {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
          detectSessionInUrl: false,
        },
        global: {
          headers: { Authorization: `Bearer ${ctx.auth.accessToken}` },
        },
      }
    )
    const { data } = await supabase.from('notes').select('*')
    return { content: [{ type: 'text', text: JSON.stringify(data) }] }
  }
)
```

## Pitfalls (legacy proxy-mode users)

If you are still carrying a legacy Supabase proxy-mode workaround, expect these failures:

- `Incompatible auth server` — Supabase metadata had no `registration_endpoint`. Fixed by enabling DCR + Allow Dynamic OAuth Apps.
- `Unsupported provider` — old proxy required `provider=google` injected manually into authorize URL.
- `bad_json` on token exchange — old Supabase token endpoint required `Content-Type: application/json` + `apikey` header; mcp-use's proxy sent form-urlencoded.
- `redirect_uri_mismatch` — localhost wildcard not in Supabase **Redirect URLs**. Add `http://localhost:*/**` for dev.

The new DCR-direct flow eliminates all of these. Migrate by enabling Supabase's OAuth 2.1 server and removing custom authorize/token middleware. See `../../28-migration/05-dcr-vs-proxy-mode-shift.md` for the full migration.

Do not keep historical custom authorize/token/register handlers or Hono middleware overrides once Supabase DCR is enabled.

## Common issues table

For the full troubleshooting matrix (parameter mapping, content-type gotchas, dashboard URL config), see `../../27-troubleshooting/03-oauth-and-supabase-issues.md`.

## Cross-references

- Decision matrix: `../01-overview-decision-matrix.md`
- Migration from proxy to DCR: `../../28-migration/05-dcr-vs-proxy-mode-shift.md`
- Troubleshooting: `../../27-troubleshooting/03-oauth-and-supabase-issues.md`
- Canonical: https://manufact.com/docs/typescript/server/authentication/providers/supabase
- Template: https://github.com/mcp-use/mcp-oauth-supabase-template
