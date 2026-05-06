# Vercel

Vercel hosts mcp-use as either a serverless API route or an Edge Function. Stateless mode is required — sessions don't persist across invocations.

---

## 1. Limitations

Stateless serverless platforms cannot host MCP features that require a long-lived session:

- Notifications (`server.sendNotification(...)`)
- Sampling (`ctx.sample(...)`)
- Elicitation (`ctx.elicit(...)`)
- Long-running tool progress reports

If your server uses any of these, deploy to Manufact Cloud, Cloud Run + Redis, or Fly.io instead.

---

## 2. Project layout

```
.
├── api/
│   └── mcp.ts          # Serverless function entry
├── package.json
├── vercel.json
└── tsconfig.json
```

---

## 3. Serverless function

```typescript
// api/mcp.ts
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "vercel-mcp",
  version: "1.0.0",
});

server.tool(
  { name: "greet", description: "Greet someone", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`),
);

const handler = await server.getHandler();
export default { fetch: handler };
```

`getHandler()` returns the underlying Hono `fetch` handler. Vercel's Edge runtime invokes `fetch(request)` per request.

---

## 4. `vercel.json`

```json
{
  "version": 2,
  "functions": {
    "api/mcp.ts": {
      "runtime": "edge"
    }
  },
  "rewrites": [
    { "source": "/mcp", "destination": "/api/mcp" }
  ]
}
```

Without the rewrite, the URL is `https://your-project.vercel.app/api/mcp` instead of `/mcp`. Either rewrite or update client configs to use `/api/mcp`.

---

## 5. Edge runtime caveats

- The Edge runtime is **not** Node — `fs`, `child_process`, `net` are unavailable.
- Native modules don't work.
- Audit your deps with `vercel build` locally first; failures surface at build time.

If you need full Node, use the Node runtime instead:

```json
{
  "functions": {
    "api/mcp.ts": {
      "runtime": "nodejs22.x",
      "memory": 1024,
      "maxDuration": 60
    }
  }
}
```

`maxDuration` caps a single invocation; the default for Hobby is 10s, Pro is 60s. Long-running tools must finish inside this window.

---

## 6. Env vars

Set via dashboard or CLI:

```bash
vercel env add MCP_API_KEY production
vercel env add SUPABASE_ANON_KEY production
```

---

## 7. Deploy

```bash
npm install -g vercel
vercel        # preview deploy
vercel --prod # production deploy
```

After deploy, Vercel prints the URL. Test:

```bash
curl -i https://your-project.vercel.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{}}'
```

---

## 8. CORS

Configure on the `MCPServer` constructor — Vercel does not add CORS by default:

```typescript
const server = new MCPServer({
  name: "vercel-mcp",
  version: "1.0.0",
  cors: {
    origin: ["https://your-client.com"],
    allowMethods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "mcp-protocol-version", "mcp-session-id"],
    exposeHeaders: ["mcp-session-id"],
  },
});
```

---

## 9. When to pick Vercel

- Free tier viable for low-traffic, stateless tools.
- Project already on Vercel (Next.js + MCP colocated — see `19-nextjs-drop-in/`).
- Don't need `RedisSessionStore` or session-bound features.

For most production MCP servers, **prefer Manufact Cloud** — it gives you sessions, widgets, and OAuth without the stateless tradeoffs.
