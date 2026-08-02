# OAuth Provider: Supabase

*Read this when integrating Supabase authentication and PostgreSQL RLS.*

## Import & Factory

```typescript
import { oauthSupabaseProvider } from "mcp-use/oauth/supabase";

const oauth = oauthSupabaseProvider({
  projectId: "example-project",
});
```

## Required Options (choose one)

| Option | Type | Example |
|--------|------|---------|
| `projectId` | `string` | `"example-project"` |
| `supabaseUrl` | `string \| URL` | `"https://example.supabase.co"` |

## User Type

```typescript
type SupabaseOAuthUser = {
  id: string;
  email?: string;
  name?: string;
  fullName?: string;
  username?: string;
  avatarUrl?: string;
  role?: string;
  aal?: string;
  amr: SupabaseAmr[];
  sessionId?: string;
};
```

## Environment Variables

```bash
SUPABASE_PROJECT_ID=example-project
SUPABASE_JWT_SECRET=your-secret-key  # For HS256 (legacy)
```

## Gotchas

1. Default verifies ES256 tokens against JWKS; pass `jwtSecret` for HS256 legacy tokens
2. `role` field contains Postgres role (use for RLS policies)
3. `amr` array shows authentication methods (password, otp, oauth)
