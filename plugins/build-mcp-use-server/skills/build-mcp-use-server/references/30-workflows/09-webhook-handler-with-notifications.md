# Workflow: Webhook Handler with Server-Side Notifications

**Goal:** receive POST webhooks (Stripe, GitHub, anything) on a Hono route mounted alongside MCP, store them, and broadcast each event as an MCP notification to all connected clients.

## Prerequisites

- Streamable HTTP transport.
- A webhook source you can point at the local server (use `ngrok` or `cloudflared` for testing).
- mcp-use ≥ 1.21.5.

## Layout

```
webhook-mcp/
├── package.json
└── index.ts
```

## `index.ts`

```typescript
import { MCPServer, text, object } from "mcp-use/server";
import { z } from "zod";

interface WebhookEvent {
  id: string;
  source: string;
  receivedAt: string;
  payload: unknown;
}

const recent: WebhookEvent[] = [];
const MAX_BUFFER = 50;

const server = new MCPServer({
  name: "webhook-mcp",
  version: "1.0.0",
  description: "Receive webhooks and broadcast them as MCP notifications",
});

// ── Hono POST route — anything posted to /webhooks/<source> is captured ─────

server.post("/webhooks/:source", async (c) => {
  const source = c.req.param("source");

  let payload: unknown;
  try {
    payload = await c.req.json();
  } catch {
    return c.json({ error: "Body must be JSON" }, 400);
  }

  // Optional: verify a shared secret. Stripe / GitHub use signed headers.
  const expected = process.env.WEBHOOK_SECRET;
  if (expected) {
    const got = c.req.header("X-Webhook-Secret");
    if (got !== expected) return c.json({ error: "Unauthorized" }, 401);
  }

  const event: WebhookEvent = {
    id: crypto.randomUUID(),
    source,
    receivedAt: new Date().toISOString(),
    payload,
  };

  recent.unshift(event);
  if (recent.length > MAX_BUFFER) recent.length = MAX_BUFFER;

  // Broadcast to every connected MCP client. Notification name is custom.
  server.sendNotification("webhook/received", {
    message: `Webhook received from ${source}`,
    event,
  });

  return c.json({ status: "received", id: event.id });
});

// ── MCP tools to inspect what arrived ───────────────────────────────────────

server.tool(
  {
    name: "list-webhooks",
    description: "List recently received webhooks (newest first)",
    schema: z.object({
      limit: z.number().int().min(1).max(MAX_BUFFER).default(10),
      source: z.string().optional().describe("Filter by source path segment"),
    }),
  },
  async ({ limit, source }) => {
    const filtered = source ? recent.filter((e) => e.source === source) : recent;
    return object({
      total: recent.length,
      events: filtered.slice(0, limit),
    });
  }
);

server.tool(
  {
    name: "get-webhook",
    description: "Fetch a webhook event by id",
    schema: z.object({ id: z.string() }),
  },
  async ({ id }) => {
    const found = recent.find((e) => e.id === id);
    return found ? object(found) : text(`Not found: ${id}`);
  }
);

await server.listen(parseInt(process.env.PORT || "3000", 10));
```

## Run

```bash
WEBHOOK_SECRET=devsecret npm run dev
```

## Test (post a webhook)

```bash
curl -X POST http://localhost:3000/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: devsecret" \
  -d '{"event":"charge.succeeded","amount":2999}'
# {"status":"received","id":"..."}

curl -X POST http://localhost:3000/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: devsecret" \
  -d '{"action":"opened","number":42}'
```

## Test (observe notification on the SSE stream)

In one shell, hold an SSE stream open against an MCP session:

```bash
SID=$(curl -sN -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}' \
  -D - | awk -F': ' '/^Mcp-Session-Id/ {print $2}' | tr -d '\r')

curl -N "http://localhost:3000/mcp" \
  -H "Mcp-Session-Id: $SID" \
  -H "Accept: text/event-stream"
```

In another shell, post a webhook. The first shell receives a `notifications/webhook/received` event immediately.

## Production notes

- **Verify signatures, not shared secrets.** Stripe, GitHub, and others sign webhook bodies with HMAC. Replace the simple shared-secret check with a per-vendor signature verifier.
- **Buffer is in-memory.** Survives only as long as the process. For durability, write to Postgres / Redis stream and persist there.
- **Broadcast volume.** `sendNotification` fans out to every session. If you have thousands of sessions, batch / rate-limit before broadcasting.
- **Reverse proxy.** Disable buffering for SSE (`proxy_buffering off`).

## See also

- Per-session push (instead of broadcast): `08-real-time-stock-ticker.md`
- Notifications reference: `../14-notifications/`
- Custom routes alongside MCP: `../17-advanced/` and `../29-templates/06-side-car-existing-app.md`
