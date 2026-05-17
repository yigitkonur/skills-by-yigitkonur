# Workflow: Real-Time Stock Ticker (Per-Session SSE Push)

**Goal:** push live updates to specific MCP clients on a `setInterval` timer. Each client subscribes to one or more symbols; the server tracks `symbol -> Set<sessionId>` and pushes to each subscriber via `sendNotificationToSession`.

## Prerequisites

- Streamable HTTP transport (SSE).
- mcp-use ≥ 1.21.5.

## Layout

```
ticker-mcp/
├── package.json
└── index.ts
```

## `index.ts`

```typescript
import { MCPServer, text, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "ticker-mcp",
  version: "1.0.0",
  description: "Real-time price push per session",
});

// symbol -> Set<sessionId>
const subs = new Map<string, Set<string>>();

// Replace with a real price feed. The simulated feed runs while subs is non-empty.
const interval = setInterval(() => {
  if (subs.size === 0) return;
  for (const [symbol, sessions] of subs) {
    const price = Number((Math.random() * 1000).toFixed(2));
    const payload = { symbol, price, ts: Date.now() };
    for (const sessionId of sessions) {
      // Notification name is custom — clients listen for "price/update".
      server.sendNotificationToSession(sessionId, "price/update", payload);
    }
  }
}, 1000);

server.tool(
  {
    name: "subscribe",
    description: "Subscribe the current session to live price updates for a symbol",
    schema: z.object({
      symbol: z.string().min(1).max(8).describe("Ticker symbol, e.g. AAPL"),
    }),
  },
  async ({ symbol }, ctx) => {
    const sid = ctx.session?.sessionId;
    if (!sid) return error("This tool requires a session-bound transport (HTTP)");

    const upper = symbol.toUpperCase();
    if (!subs.has(upper)) subs.set(upper, new Set());
    subs.get(upper)!.add(sid);

    return text(
      `Subscribed to ${upper}. Listen on the 'price/update' notification.`
    );
  }
);

server.tool(
  {
    name: "unsubscribe",
    description: "Unsubscribe the current session from a symbol",
    schema: z.object({
      symbol: z.string().min(1),
    }),
  },
  async ({ symbol }, ctx) => {
    const sid = ctx.session?.sessionId;
    if (!sid) return error("No session");

    const upper = symbol.toUpperCase();
    subs.get(upper)?.delete(sid);
    if (subs.get(upper)?.size === 0) subs.delete(upper);

    return text(`Unsubscribed from ${upper}.`);
  }
);

server.tool(
  {
    name: "list-subscriptions",
    description: "Show what the current session is subscribed to",
    schema: z.object({}),
  },
  async (_, ctx) => {
    const sid = ctx.session?.sessionId;
    if (!sid) return error("No session");
    const mine: string[] = [];
    for (const [symbol, sessions] of subs) {
      if (sessions.has(sid)) mine.push(symbol);
    }
    return text(mine.length ? mine.join(", ") : "(none)");
  }
);

// Clean up subscriptions when a session ends.
server.onSessionEnd?.((sessionId) => {
  for (const [symbol, sessions] of subs) {
    sessions.delete(sessionId);
    if (sessions.size === 0) subs.delete(symbol);
  }
});

process.on("SIGINT", () => {
  clearInterval(interval);
  process.exit(0);
});

await server.listen();
```

## Run

```bash
npm install && npm run dev
```

## Test (manual)

```bash
# Open a session and subscribe
SID=$(curl -sN -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}' \
  -D - | awk -F': ' '/^Mcp-Session-Id/ {print $2}' | tr -d '\r')

curl -N -X POST http://localhost:3000/mcp \
  -H "Mcp-Session-Id: $SID" \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"subscribe","arguments":{"symbol":"AAPL"}}}'

# Listen on the same session for notifications:
curl -N "http://localhost:3000/mcp" \
  -H "Mcp-Session-Id: $SID" \
  -H "Accept: text/event-stream"
# You'll see notifications/price/update events arriving every second.
```

## Test (in the Inspector)

1. `mcp-use dev` → http://localhost:3000/inspector.
2. Connect. Call `subscribe` with `{ "symbol": "AAPL" }`.
3. The Inspector's notifications panel will start receiving `price/update` events.

## Notes

- `sendNotificationToSession(sessionId, name, payload)` is the per-session push primitive. `sendNotification(name, payload)` (without the session arg) broadcasts to every active session.
- The interval fires forever — gate it on `subs.size === 0` to avoid wasted CPU when no one is listening.
- Sessions disappear when clients drop. Handle in `server.onSessionEnd?.(sid => ...)` (optional in older versions; safe with `?.`).
- For a fan-out across replicas, swap the in-memory `Map` for Redis pub/sub keyed by session id. See `02-stateful-redis-streaming-server.md`.

## See also

- Notifications reference: `../14-notifications/`
- Sessions reference: `../10-sessions/`
- Webhook -> notification fan-out: `09-webhook-handler-with-notifications.md`
