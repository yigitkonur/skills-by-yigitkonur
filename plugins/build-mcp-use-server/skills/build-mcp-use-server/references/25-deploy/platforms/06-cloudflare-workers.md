# Cloudflare Workers

Global edge deploy with zero cold starts. V8 isolates, not Node — audit deps before committing.

---

## 1. Limitations

Workers run in V8 isolates with a Web-standard runtime, **not** Node:

- No `fs`, `child_process`, `net`, `dns`. Cloudflare's Node compat (`compatibility_flags = ["nodejs_compat"]`) covers a subset; native modules don't work.
- Single request CPU limit: 50ms for Free tier, 30s for Paid (configurable).
- Memory cap: 128 MB.
- No persistent in-memory state across requests — sessions need Workers KV, Durable Objects, or external Redis.

If your MCP uses notifications, sampling, or elicitation, prefer Manufact Cloud or Fly.io. Workers can host stateless tool-only servers cleanly.

---

## 2. Setup

```bash
npm create cloudflare@latest my-mcp
cd my-mcp
npm install mcp-use zod
npm install -D wrangler
```

---

## 3. Worker entry

```typescript
// src/worker.ts
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "cf-worker",
  version: "1.0.0",
});

server.tool(
  { name: "geo", description: "Where am I?", schema: z.object({}) },
  async (_, ctx) => {
    const cf = (ctx.request as any).cf;
    return text(`Hello from ${cf?.city ?? "Unknown"}`);
  },
);

export default {
  fetch: server.getHandler(),
};
```

`server.getHandler()` returns a Web-standard `(request) => Response` handler — exactly what Workers expect.

---

## 4. `wrangler.toml`

```toml
name = "mcp-worker"
main = "src/worker.ts"
compatibility_date = "2024-09-23"
compatibility_flags = ["nodejs_compat"]

[vars]
ENVIRONMENT = "production"

# Optional: Workers KV for session-like storage
# [[kv_namespaces]]
# binding = "SESSIONS"
# id = "..."
```

`compatibility_flags = ["nodejs_compat"]` enables Node compat for things like `Buffer`. Audit your dep tree — packages that import `fs` or native modules will still fail.

---

## 5. Secrets

```bash
npx wrangler secret put API_KEY
# paste value at the prompt
```

Secrets are encrypted and exposed as env vars at runtime.

---

## 6. Deploy

```bash
npx wrangler deploy
```

Output gives you a URL like `https://mcp-worker.your-account.workers.dev`. The MCP endpoint is at `/mcp`.

---

## 7. Custom domain

```bash
npx wrangler routes add mcp.example.com/*
```

Or via dashboard: Workers → your worker → Triggers → Custom Domains.

---

## 8. Sessions on Workers

The default in-memory session store is per-isolate and per-request — sessions break immediately. Options:

- **Stateless mode**: tool-only servers without notifications/sampling/elicit work fine without sessions.
- **Workers KV**: write a custom `SessionStore` that reads/writes the KV namespace. Eventually consistent, ~1s latency on writes — fine for low-frequency state.
- **Durable Objects**: a single object instance per session id gives strong consistency. Best for stateful MCP on Workers.
- **External Redis** via `RedisSessionStore` over the Worker's `fetch`-compatible Redis client.

---

## 9. Verify

```bash
curl -i https://mcp-worker.your-account.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{}}'
```

Logs:

```bash
npx wrangler tail
```

---

## 10. When to pick Workers

- Lowest-latency global edge.
- Stateless tool servers.
- Already on Cloudflare.

For stateful MCP, Cloud Run + Redis or Fly.io are simpler and avoid the runtime mismatch.
