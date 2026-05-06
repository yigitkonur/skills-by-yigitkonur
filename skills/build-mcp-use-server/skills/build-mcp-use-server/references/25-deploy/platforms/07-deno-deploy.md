# Deno Deploy

Native TypeScript runtime, no build step, edge-distributed. Good fit for stateless tool servers and Deno-first teams.

---

## 1. Setup

```bash
deno install -Arf jsr:@deno/deployctl
```

---

## 2. Server code

```typescript
// main.ts
import { MCPServer, text } from "npm:mcp-use/server";
import { z } from "npm:zod";

const server = new MCPServer({
  name: "deno-mcp",
  version: "1.0.0",
});

server.tool(
  { name: "greet", description: "Greet", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`),
);

Deno.serve(server.getHandler());
```

`server.getHandler()` returns a Web-standard `Request → Response` handler. `Deno.serve()` accepts it directly.

Avoid `server.listen()` on Deno Deploy — Deploy expects you to export the handler or pass it to `Deno.serve()`. (`server.listen()` does work locally on Deno via the auto-detect path; on Deploy, use `Deno.serve()` for explicit clarity.)

---

## 3. `deno.json` — pin Zod

```json
{
  "imports": {
    "mcp-use/": "npm:mcp-use@latest/",
    "zod": "npm:zod@^4.2.0"
  },
  "tasks": {
    "dev": "deno run --allow-net --allow-env --watch main.ts"
  }
}
```

The Zod pin avoids the `e.custom is not a function` conflict — see `27-troubleshooting/01-error-catalog.md`.

---

## 4. Deploy

```bash
deployctl deploy --project=my-mcp-project main.ts
```

Or link a GitHub repo via the Deno Deploy dashboard for auto-deploys on push.

After deploy:

```
View at: https://my-mcp-project.deno.dev
```

The MCP endpoint is at `/mcp`.

---

## 5. Env vars

Set via dashboard or CLI:

```bash
deployctl env set API_KEY=value --project=my-mcp-project
```

Read with `Deno.env.get("API_KEY")`.

---

## 6. Limitations

Deno Deploy runs on V8 isolates similar to Workers:

- No persistent disk (`Deno.writeFile` to `/tmp` only).
- No long-running background tasks across invocations.
- `Deno.serve()` request handling is per-isolate; sessions don't persist between requests.
- 50ms CPU per request on the free tier.

For stateful MCP features (notifications, sampling, elicitation), use Manufact Cloud, Cloud Run, or Fly.io. Deno Deploy is best for stateless tool servers.

---

## 7. Sessions

Like Workers, the default in-process session store does not work. Options:

- **Stateless tool-only mode** — works as-is.
- **Deno KV** — write a custom `SessionStore` against `Deno.openKv()`. Globally distributed, eventually consistent.
- **External Redis** via `npm:redis` and `RedisSessionStore`.

---

## 8. Verify

```bash
curl -i https://my-mcp-project.deno.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{}}'
```

Logs are visible in the Deno Deploy dashboard or via `deployctl logs --project=my-mcp-project`.

---

## 9. When to pick Deno Deploy

- TypeScript-first team that prefers Deno's tooling (no `tsc`, no `package.json`).
- Stateless tool servers.
- Want global distribution without paying for an org plan.

For full Node compatibility, native modules, or stateful sessions, prefer Cloud Run or Fly.io.
