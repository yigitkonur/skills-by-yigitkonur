# Workflow: Supabase OAuth and Deploy

*Read this for an end-to-end workflow: scaffold, add Supabase OAuth, deploy with env vars.*

## Prerequisites

- Node.js >= 22
- Supabase account (https://supabase.com)
- Supabase project created
- GitHub repo (for Vercel deploy)

## Steps

### 1. Scaffold

```bash
npx create-mcp-use-app@2.0.0-beta.14 my-supabase-mcp --template mcp-server --npm --install
cd my-supabase-mcp
```

**Verify:** Basic server scaffolded.

### 2. Get Supabase Project ID

In Supabase dashboard:
1. Go to **Project Settings** → **General**.
2. Copy **Project ID** (e.g., `abcdefghijklmnop`).

### 3. Configure Server with Supabase OAuth

Edit `index.ts`:

```typescript
import { MCPServer, oauthSupabaseProvider } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "supabase-server",
  version: "1.0.0",
  oauth: oauthSupabaseProvider({
    projectId: process.env.SUPABASE_PROJECT_ID || "your-project-id",
    // Optional: jwtSecret for HS256 (legacy). Omit for ES256 JWKS verification (recommended).
  }),
});

export const getUser = server.tool(
  {
    name: "get-user",
    description: "Get current authenticated user from Supabase",
    inputSchema: z.object({}),
    outputSchema: z.object({
      id: z.string(),
      email: z.string().optional(),
      appMetadata: z.record(z.unknown()).optional(),
    }),
  },
  async (args, ctx) => {
    if (!ctx.auth) {
      return { isError: true, content: [{ type: "text", text: "Not authenticated" }] };
    }

    return {
      content: [{ type: "text", text: `User: ${ctx.auth.user.email || ctx.auth.user.id}` }],
      structuredContent: {
        id: ctx.auth.user.id,
        email: ctx.auth.user.email,
        appMetadata: ctx.auth.user.id ? { provider: "supabase" } : undefined,
      },
    };
  }
);

export const queryDatabase = server.tool(
  {
    name: "query-database",
    description: "Query Supabase database (authenticated users only)",
    inputSchema: z.object({
      table: z.string().describe("Table name"),
    }),
    outputSchema: z.object({
      rows: z.array(z.record(z.unknown())),
      count: z.number(),
    }),
  },
  async ({ table }, ctx) => {
    if (!ctx.auth) {
      return { isError: true, content: [{ type: "text", text: "Authentication required" }] };
    }

    // In reality, use @supabase/supabase-js client
    // const { data, count } = await supabase
    //   .from(table)
    //   .select("*")
    //   .limit(10);

    return {
      content: [{ type: "text", text: `Queried ${table} (mock)` }],
      structuredContent: { rows: [], count: 0 },
    };
  }
);

export default server;
server.listen();
```

**Verify:** `npm run typecheck` passes.

### 4. Set Environment Variables

Create `.env.local`:

```bash
SUPABASE_PROJECT_ID=your-project-id-here
```

Create `.env.production`:

```bash
SUPABASE_PROJECT_ID=your-project-id-here
```

**Verify:** `npm run dev` starts without errors.

### 5. Test Locally

```bash
npm run dev
```

In Inspector:
1. Click **Tools** → **get-user**.
2. Click **Call**.

**Expected:** First time: 401 or OAuth redirect. Inspector should guide you through Supabase login.

**Verify:** After login, response includes your Supabase user ID and email.

### 6. Build

```bash
npm run build
# Output: .mcp-use/build/
```

**Verify:** No errors; build directory populated.

### 7. Deploy

**Option A: Via GitHub (automatic)**

```bash
git add .
git commit -m "feat: supabase-protected server"
git push origin main

mcp-use deploy --env SUPABASE_PROJECT_ID=your-project-id-here
# Auto-detects GitHub repo; creates Vercel project
```

**Option B: Via env file**

```bash
mcp-use deploy --env-file .env.production
```

**Verify:** Deployment succeeds; URL shown: `https://my-supabase-mcp.vercel.app/mcp`.

## Understanding Supabase OAuth in v2

1. **DCR (Dynamic Client Registration)** — MCP client registers with Supabase (not your server).
2. **Supabase token** — Client receives JWT from Supabase authorization endpoint.
3. **Token verification** — Your server verifies JWT against Supabase's public JWKS endpoint.
4. **ctx.auth.user** — Populated with Supabase user data from token payload.

No proxy involved; direct OAuth flow.

## Common Issues

| Issue | Solution |
|-------|----------|
| 401 on deploy | Check `SUPABASE_PROJECT_ID` is set in Vercel env vars |
| JWT verification fails | Ensure Supabase JWKS is reachable; check token issuer claim |
| User data is empty | Check Supabase JWT claims; ensure `aud` matches expectation |
| DCR fails in Inspector | Supabase may not have registered your client yet; wait a few seconds and retry |

## Adding Supabase Client

For database access, install Supabase client:

```bash
npm install @supabase/supabase-js
```

Then in tool callback:

```typescript
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  `https://${process.env.SUPABASE_PROJECT_ID}.supabase.co`,
  process.env.SUPABASE_ANON_KEY
);

// Within tool:
const { data, error } = await supabase
  .from("users")
  .select("*")
  .eq("id", ctx.auth.user.id)
  .single();
```

## Next

- Read `../11-auth/providers/04-supabase.md` for Supabase-specific config (scopes, audience).
- Read `../25-deploy/01-decision-matrix.md` for platform alternatives.
- See `../11-auth/06-debugging-checklist.md` for auth troubleshooting.
