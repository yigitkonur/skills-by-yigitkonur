# OAuth Provider: Supabase

*Read this when integrating Supabase authentication and PostgreSQL row-level security.*

## Import & Factory

```typescript
import { oauthSupabaseProvider } from "mcp-use/oauth/supabase";

const oauth = oauthSupabaseProvider({
  projectId: "example-project",
});
```

## Required Options (choose one)

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `projectId` | `string` | `"example-project"` | Auto-derives `supabaseUrl = https://<projectId>.supabase.co` |
| `supabaseUrl` | `string \| URL` | `"https://example.supabase.co"` | Full project URL; takes precedence over `projectId` |

## Optional Options

```typescript
oauthSupabaseProvider({
  projectId: "...",
  jwtSecret?: string,                   // HS256 secret; omit to verify ES256 tokens against JWKS
  audience?: string,                    // Expected token audience (default: "authenticated")
  resource?: string \| URL,             // Full MCP endpoint URL
  requiredScopes?: readonly string[],   // Required by bearer gate
  scopesSupported?: readonly string[],  // Advertised to clients
  resourceName?: string,                // Display name
  serviceDocumentationUrl?: URL,        // Documentation link
})
```

## User Type

```typescript
type SupabaseOAuthUser = {
  id: string;                 // Supabase user ID
  email?: string;
  name?: string;
  fullName?: string;
  username?: string;
  avatarUrl?: string;
  role?: string;              // Postgres database role
  aal?: string;               // Authenticator assurance level
  amr: SupabaseAmr[];         // Auth methods used (non-nil)
  sessionId?: string;         // Session ID
};

type SupabaseAmr = {
  method: string;             // e.g., "password", "otp", "oauth"
  timestamp?: number;         // Milliseconds
};
```

Access in tools:

```typescript
async (input, ctx) => {
  const userId = ctx.auth.user.id;
  const dbRole = ctx.auth.user.role;
  const email = ctx.auth.user.email;
}
```

## Environment Variables

```bash
# .env
SUPABASE_PROJECT_ID=example-project
# OR
SUPABASE_URL=https://example.supabase.co

# For HS256 tokens (legacy):
SUPABASE_JWT_SECRET=your-secret-key
```

```typescript
const oauth = oauthSupabaseProvider({
  projectId: process.env.SUPABASE_PROJECT_ID,
  jwtSecret: process.env.SUPABASE_JWT_SECRET,
});
```

## Gotchas

1. **JWT verification method**: By default, verifies ES256 tokens against Supabase's JWKS endpoint. If your tokens are HS256, pass `jwtSecret: process.env.SUPABASE_JWT_SECRET`.

2. **Database role**: The `role` field contains the Postgres role. Use it for row-level security (RLS) policies:
   ```sql
   CREATE POLICY "Users can view own records" ON public.records
     FOR SELECT USING (user_id = auth.uid());
   ```

3. **amr array**: Always present. Contains authentication methods (e.g., `[{ method: "password" }]`). Check method type if you care about how the user was authenticated.

4. **Session affinity**: Supabase sessions are short-lived. For long-running operations, use the access token to fetch fresh credentials or rely on MCP's stateless request model.

## Typical Setup

```typescript
import { MCPServer, oauthSupabaseProvider } from "mcp-use";
import { createClient } from "@supabase/supabase-js";
import { z } from "zod";

const server = new MCPServer({
  name: "supabase-server",
  oauth: oauthSupabaseProvider({
    projectId: process.env.SUPABASE_PROJECT_ID!,
  }),
});

server.tool({
  name: "get-user-data",
  description: "Fetch authenticated user's data",
  inputSchema: z.object({}),
  async (input, ctx) => {
    const supabase = createClient(
      `https://${process.env.SUPABASE_PROJECT_ID}.supabase.co`,
      process.env.SUPABASE_ANON_KEY!,
      { global: { headers: { Authorization: `Bearer ${ctx.auth.accessToken}` } } },
    );
    const { data } = await supabase.from("users").select("*").eq("id", ctx.auth.user.id);
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  },
});

await server.listen(3000);
```
