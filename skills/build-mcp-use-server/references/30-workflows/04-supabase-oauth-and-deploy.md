# Workflow: Supabase OAuth and Deploy

*Read this for an end-to-end workflow: scaffold, add Supabase OAuth, deploy with env vars.*

## Prerequisites

- Node.js >= 22
- Supabase account (https://supabase.com)
- Supabase project created
- GitHub repo for the default Manufact Cloud source mode, or plan to use `mcp-use deploy --no-github` for managed upload

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
import { MCPServer } from "mcp-use";
import { oauthSupabaseProvider } from "mcp-use/oauth/supabase";
import { z } from "zod";

const server = new MCPServer({
  name: "supabase-server",
  version: "1.0.0",
  oauth: oauthSupabaseProvider({
    projectId: process.env.SUPABASE_PROJECT_ID || "your-project-id",
    resource: process.env.MCP_RESOURCE_URL, // Full public MCP endpoint outside localhost
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
      claims: z.record(z.string(), z.unknown()),
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
        // ctx.auth.payload carries the raw, verified JWT claims — SupabaseOAuthUser
        // has no appMetadata field, so read app-specific claims from payload directly.
        claims: ctx.auth.payload,
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
      rows: z.array(z.record(z.string(), z.unknown())),
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
```

Never call `server.listen()` here — the CLI (`mcp-use dev`/`mcp-use start`) owns the listener.

**Verify:** `npm run typecheck` passes.

### 4. Set Environment Variables

Create `.env.local`:

```bash
SUPABASE_PROJECT_ID=your-project-id-here
```

Create `.env.production` only when the canonical public endpoint is known:

```bash
SUPABASE_PROJECT_ID=your-project-id-here
MCP_RESOURCE_URL=https://mcp.example.com/mcp
```

For a platform-generated domain, set `MCP_RESOURCE_URL` after the server is created using the exact dashboard endpoint, then redeploy. Never derive it from a slug.

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
# Resolves the GitHub repo from git origin and confirms GitHub App repo access;
# creates/updates a Manufact Cloud server — never a Vercel project.
```

**Option B: Via env file**

```bash
mcp-use deploy --env-file .env.production
```

**Verify:** Capture the deployment ID, apply the terminal-success gate in `../25-deploy/platforms/01-mcp-use-cloud.md`, and copy the exact MCP endpoint from the dashboard. If that generated endpoint was not known before the first deploy, set it with `mcp-use servers env set <server-id-or-slug> MCP_RESOURCE_URL=<dashboard-mcp-url>`, redeploy, and wait for the new deployment to succeed before testing.

## Understanding Supabase OAuth in v2

1. **DCR (Dynamic Client Registration)** — MCP client registers with Supabase (not your server).
2. **Supabase token** — Client receives JWT from Supabase authorization endpoint.
3. **Token verification** — Your server verifies JWT against Supabase's public JWKS endpoint.
4. **ctx.auth.user** — Populated with Supabase user data from token payload.

No proxy involved; direct OAuth flow.

## Common Issues

| Issue | Solution |
|-------|----------|
| 401 on deploy | Check `SUPABASE_PROJECT_ID` is set via `mcp-use deploy --env` or the deployed server's env vars |
| JWT verification fails | Ensure Supabase JWKS is reachable; check token issuer claim |
| User data is empty | Check Supabase JWT claims; ensure `aud` matches expectation |
| DCR fails in Inspector | Supabase may not have registered your client yet; wait a few seconds and retry |

## Adding Supabase Client

For database access, install Supabase client and set `SUPABASE_ANON_KEY` in every environment that runs the database tool:

```bash
npm install @supabase/supabase-js
```

Then in tool callback:

```typescript
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  `https://${process.env.SUPABASE_PROJECT_ID}.supabase.co`,
  process.env.SUPABASE_ANON_KEY!,
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
