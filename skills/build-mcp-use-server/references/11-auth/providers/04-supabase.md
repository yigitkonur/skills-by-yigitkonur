# OAuth Provider: Supabase

*Read this when integrating Supabase Auth and Postgres Row Level Security (RLS).*

## Import & Factory

```typescript
import { oauthSupabaseProvider } from "mcp-use/oauth/supabase";

const oauth = oauthSupabaseProvider({
  projectId: "example-project",
});
```

## Required Options (exactly one of these two)

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `projectId` | `string` | `"example-project"` | Must match `/^[a-z0-9-]+$/i`; expands to `https://<projectId>.supabase.co`. Ignored if `supabaseUrl` is also set. |
| `supabaseUrl` | `string \| URL` | `"https://example.supabase.co"` | Full project URL — required for self-hosted or local Supabase. Takes precedence over `projectId`. |

Omitting both throws `TypeError`. The issuer is derived as `<supabaseUrl>/auth/v1`.

## Optional Options

```typescript
oauthSupabaseProvider({
  projectId: "...", // or supabaseUrl
  jwtSecret?: string,                   // Legacy HS256 secret; must be >= 32 bytes or TypeError. Omit for ES256/JWKS verification.
  audience?: string,                    // Expected access-token audience (default: "authenticated")
  resource?: string | URL,              // Full MCP endpoint URL (overrides host header inference)
  requiredScopes?: readonly string[],   // Scopes required by bearer gate (default: none enforced)
  scopesSupported?: readonly string[],  // Scopes advertised to clients (no factory default)
  resourceName?: string,                // Human-readable name for OAuth metadata
  serviceDocumentationUrl?: URL,        // Documentation link in OAuth metadata
})
```

## User Type

```typescript
type SupabaseOAuthUser = {
  id: string;              // sub claim, falls back to user_id claim
  email?: string;
  name?: string;           // user_metadata.name
  fullName?: string;       // user_metadata.full_name
  username?: string;       // user_metadata.username
  avatarUrl?: string;      // user_metadata.avatar_url
  role?: string;           // Postgres role claim (use for RLS policies)
  aal?: string;            // Authenticator assurance level
  amr: SupabaseAmr[];      // Authentication methods used, non-nil, may be empty
  sessionId?: string;      // session_id claim
};

type SupabaseAmr = {
  method: string;          // e.g. "password", "otp", "oauth"
  timestamp?: number;      // Unix timestamp the method completed
};
```

`aal` also maps to a top-level permission string `aal:<level>` in `ctx.auth.permissions` when present (e.g. `aal:aal2`).

## Environment Variables

The provider does not read any environment variables itself — `projectId`/`supabaseUrl`, `jwtSecret`, and `audience` are plain function arguments. Names below are application convention:

```bash
SUPABASE_PROJECT_ID=your-project-ref
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_JWT_SECRET=your-secret-key  # Only for HS256 legacy projects; 32+ bytes
```

```typescript
const projectId = process.env.SUPABASE_PROJECT_ID;
if (!projectId) throw new Error("SUPABASE_PROJECT_ID is required");

const oauth = oauthSupabaseProvider({ projectId });
```

## Configure Supabase

In the Supabase Dashboard, before wiring the provider:

1. Enable the OAuth 2.1 server and Dynamic OAuth Apps.
2. Configure a consent-screen route implemented by your application.
3. Enable at least one user sign-in method.
4. Copy the project ID and publishable key.

## Row Level Security

Create the Supabase client per request with the verified access token, so Postgres RLS policies evaluate against the calling user:

```typescript
import { createClient } from "@supabase/supabase-js";

server.tool(
  { name: "list_notes", description: "Return notes visible under Supabase RLS." },
  async (_args, ctx) => {
    const supabase = createClient(
      process.env.SUPABASE_URL ?? `https://${process.env.SUPABASE_PROJECT_ID}.supabase.co`,
      process.env.SUPABASE_PUBLISHABLE_KEY!,
      {
        auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
        global: { headers: { Authorization: `Bearer ${ctx.auth.accessToken}` } },
      },
    );
    const { data, error } = await supabase.from("notes").select();
    if (error) return { isError: true, content: [{ type: "text", text: error.message }] };
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  },
);
```

Use this token-forwarding pattern only for user-scoped operations. Server-owned operations should use a separate credential and explicit authorization, not the forwarded user token.

## Gotchas

1. Default verifies ES256 tokens against project JWKS; pass `jwtSecret` to switch to HS256 legacy verification — `jwtSecret` must be at least 32 bytes or the factory throws `TypeError`
2. `role` field contains the Postgres role claim (use for RLS policies), distinct from `user.roles` seen on other providers — Supabase's user type has no `roles` array
3. `amr` array shows authentication methods (password, otp, oauth, ...); always an array, may be empty
4. Default `audience` is `"authenticated"`; override only if your project issues a different audience
5. `id` resolves from `sub`, falling back to `user_id` if `sub` is absent
