# Template: Serverless Deno (Supabase Edge / Deno Deploy)

Run mcp-use in a Deno edge runtime — no `node_modules` to ship, npm packages resolved via `npm:` specifiers in a `deno.json` import map. `server.listen()` auto-detects edge runtimes and runs in stateless mode.

## Layout

```
serverless-mcp-server/
├── deno.json
└── supabase/functions/mcp-server/index.ts
```

## `deno.json`

The import map pins both `mcp-use` and `zod` against `npm:` specifiers. Pinning Zod here resolves duplicate-Zod conflicts that otherwise surface on Deno.

```json
{
  "imports": {
    "mcp-use/": "npm:mcp-use@latest/",
    "zod": "npm:zod@^4.2.0"
  }
}
```

## `supabase/functions/mcp-server/index.ts`

```typescript
// Resolved via deno.json import map. Equivalent: import { ... } from "npm:mcp-use/server"
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "serverless-mcp",
  version: "1.0.0",
  description: "MCP server deployed on Supabase Edge Functions",
});

server.tool(
  {
    name: "hello",
    description: "Greet user",
    schema: z.object({
      name: z.string().default("world"),
    }),
  },
  async ({ name }) => text(`Hello, ${name}! From Supabase Edge.`)
);

// listen() auto-detects Deno and runs stateless — no Node-specific server boot.
server.listen().catch(console.error);
```

## Deploy to Supabase Edge

```bash
supabase functions new mcp-server
# copy index.ts and deno.json into supabase/functions/mcp-server/
docker info                              # Docker must be running for the bundler
supabase functions deploy mcp-server --use-docker
```

## Deploy to Deno Deploy (standalone)

For Deno Deploy without Supabase, export the handler explicitly via `Deno.serve`:

```typescript
import { MCPServer, text } from "npm:mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "deno-mcp", version: "1.0.0" });

server.tool(
  { name: "hello", schema: z.object({}) },
  async () => text("Hello from Deno Deploy!")
);

Deno.serve(server.getHandler());
```

`server.getHandler()` returns a Deno-compatible `(req: Request) => Promise<Response>`.

## Test locally

```bash
supabase functions serve mcp-server --no-verify-jwt
# in another shell
curl -N -X POST http://localhost:54321/functions/v1/mcp-server/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Constraints

- Stateless only. No long-lived sessions, no Redis stream manager. For session state, use a Postgres/Supabase row keyed by request — see `../10-sessions/`.
- Cold-start sensitive. Keep imports tight and avoid heavy SDKs.
- No filesystem write. Read-only edge environment.

## See also

- Stateless tool server with Vercel Edge: `../30-workflows/01-stateless-vercel-tool-server.md`
- Per-user data via OAuth (Supabase Auth): `../30-workflows/03-oauth-protected-supabase-server.md`
- Transport details: `../09-transports/`
