# Workflow: OAuth-Protected Server with Supabase Auth

**Goal:** require Supabase OAuth on every tool call, then use `ctx.auth.user.userId` and `ctx.auth.accessToken` to scope Supabase queries to the caller. Each user sees only their own data.

## Prerequisites

- Supabase project with OAuth Server enabled and Dynamic OAuth Apps allowed.
- A `notes` table with an `owner_id uuid` column and Row Level Security enabled.
- mcp-use 1.26.0 or newer.

## Layout

```
oauth-supabase-mcp/
├── package.json
├── tsconfig.json
├── .env.example
└── src/
    ├── server.ts
    ├── config.ts
    └── tools/notes.ts
```

## `.env.example`

```env
PORT=3000
MCP_USE_OAUTH_SUPABASE_PROJECT_ID=your-project-id
MCP_USE_OAUTH_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
MCP_USE_OAUTH_SUPABASE_JWT_SECRET=...  # optional for legacy HS256 projects
```

## `src/config.ts`

```typescript
import "dotenv/config";

function need(key: string) {
  const v = process.env[key];
  if (!v) throw new Error(`Missing env: ${key}`);
  return v;
}

export const config = {
  port: parseInt(process.env.PORT || "3000", 10),
  supabase: {
    projectId: need("MCP_USE_OAUTH_SUPABASE_PROJECT_ID"),
    publishableKey: need("MCP_USE_OAUTH_SUPABASE_PUBLISHABLE_KEY"),
    jwtSecret: process.env.MCP_USE_OAUTH_SUPABASE_JWT_SECRET,
  },
};
```

## `src/tools/notes.ts`

```typescript
import { object, error } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";
import { createClient } from "@supabase/supabase-js";
import { config } from "../config.js";

function supabaseForRequest(accessToken: string) {
  return createClient(
    `https://${config.supabase.projectId}.supabase.co`,
    config.supabase.publishableKey,
    {
      auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
      global: { headers: { Authorization: `Bearer ${accessToken}` } },
    }
  );
}

export function registerNoteTools(server: MCPServer) {
  server.tool(
    {
      name: "list-notes",
      description: "List notes owned by the authenticated user",
      schema: z.object({
        limit: z.number().int().min(1).max(100).default(20),
      }),
    },
    async ({ limit }, ctx) => {
      const userId = ctx.auth?.user.userId;
      if (!userId) return error("Authentication required");
      const supabase = supabaseForRequest(ctx.auth.accessToken);

      const { data, error: dbErr } = await supabase
        .from("notes")
        .select("id, title, body, created_at")
        .eq("owner_id", userId)
        .order("created_at", { ascending: false })
        .limit(limit);

      if (dbErr) return error(`Query failed: ${dbErr.message}`);
      return object({ notes: data, count: data.length });
    }
  );

  server.tool(
    {
      name: "create-note",
      description: "Create a note for the authenticated user",
      schema: z.object({
        title: z.string().min(1).max(200),
        body: z.string().max(10_000),
      }),
    },
    async ({ title, body }, ctx) => {
      const userId = ctx.auth?.user.userId;
      if (!userId) return error("Authentication required");
      const supabase = supabaseForRequest(ctx.auth.accessToken);

      const { data, error: dbErr } = await supabase
        .from("notes")
        .insert({ owner_id: userId, title, body })
        .select("id, title, body, created_at")
        .single();

      if (dbErr) return error(`Insert failed: ${dbErr.message}`);
      return object({ note: data });
    }
  );

  server.tool(
    {
      name: "whoami",
      description: "Return the authenticated user's claims",
      schema: z.object({}),
    },
    async (_, ctx) => {
      if (!ctx.auth) return error("Authentication required");
      return object({
        userId: ctx.auth.user.userId,
        email: ctx.auth.user.email ?? null,
        scopes: ctx.auth.scopes,
        permissions: ctx.auth.permissions ?? [],
      });
    }
  );
}
```

## `src/server.ts`

```typescript
import { MCPServer, oauthSupabaseProvider } from "mcp-use/server";
import { config } from "./config.js";
import { registerNoteTools } from "./tools/notes.js";

const server = new MCPServer({
  name: "supabase-mcp",
  version: "1.0.0",
  description: "Per-user notes with Supabase Auth",
  oauth: oauthSupabaseProvider({
    projectId: config.supabase.projectId,
    jwtSecret: config.supabase.jwtSecret,
  }),
});

registerNoteTools(server);

await server.listen(config.port);
```

## SQL: notes table with RLS

Run once in the Supabase SQL editor:

```sql
create table if not exists public.notes (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  body text not null,
  created_at timestamptz not null default now()
);

alter table public.notes enable row level security;

create policy "owners read" on public.notes
  for select using (auth.uid() = owner_id);
create policy "owners write" on public.notes
  for insert with check (auth.uid() = owner_id);
```

The server uses the caller's bearer token when creating the Supabase client, so RLS policies run as the authenticated user. The explicit `eq("owner_id", userId)` filter is an extra guard.

## Test

Get a Supabase access token (from your client app, or from `supabase auth get-jwt`), then:

```bash
TOKEN=eyJhbGc...
curl -N -X POST http://localhost:3000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list-notes","arguments":{"limit":5}}}'
```

Without the `Authorization` header, the server returns 401 before the tool runs.

## Notes

- `ctx.auth.user.userId` is the Supabase user id exposed by mcp-use. Use it as the foreign key everywhere.
- `ctx.auth.accessToken` lets Supabase RLS evaluate requests as the caller.
- Still re-validate authorization in the tool body. Middleware authentication does not imply per-record authorization.
- Never accept a `userId` argument from the model — read it only from `ctx.auth`.

## See also

- Provider matrix (Auth0 / Supabase / WorkOS / custom): `../11-auth/`
- Auth0 variant: see `../29-templates/03-production-http.md` and swap the provider.
- Per-user widget data: `../30-workflows/13-resource-watcher-with-subscriptions.md`
