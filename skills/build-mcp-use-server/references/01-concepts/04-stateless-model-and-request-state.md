# Stateless Model and Request State

*Read this when you need to understand v2's stateless architecture and how multi-round flows work.*

## v2 is stateless by design

Each HTTP request is independent; the server builds a fresh MCP context per exchange.

**No:**
- Session IDs (SDK handles these internally per the MCP protocol)
- Per-client state stored on server
- Post-response notifications to named clients
- Server-side sampling

**Implications:**
- Multi-round flows (elicitation, forms) use a **request-state codec** to round-trip integrity
- Notifications travel on the originating request stream only
- Application owns client state (database, cache, etc.)
- Scales horizontally without affinity

## Request state for multi-round flows

When a tool must re-run after user input (elicitation, form entry), use `createRequestStateCodec()`:

```typescript
import { MCPServer, createRequestStateCodec } from "mcp-use";

const requestState = createRequestStateCodec({
  secret: process.env.REQUEST_STATE_SECRET, // e.g., 32-char key
});

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  requestState: requestState.verify, // codec verifier
});

// In tool callback:
server.tool(
  { name: "book", inputSchema: z.object({ date: z.string() }) },
  async (params, ctx) => {
    if (!params.date) {
      // Round 1: ask for date
      return await ctx.elicit("date", "When?", z.object({ date: z.string() }));
    }
    // Round 2: use params.date; requestState ensures integrity
  }
);
```

The codec signs state; if a client tampers with it, verification fails. Use when input state affects authorization, business logic, or resource access.

## Notifications (request-scoped)

Notifications travel on the originating request stream:

```typescript
await ctx.sendNotification("resource-updated", { uri: "db://item/123" });
```

Use `server.notifyToolsChanged()` etc. between requests for cross-session invalidations (subscriptions only).

See `14-notifications/01-overview.md` for failure modes in stateless model.

## Sessions shipped later

Documentation mentions `InMemorySessionStore`, `RedisSessionStore`, etc., but **not shipped in beta.66**. Current v2 is stateless-only; session stores are planned post-beta.

See `10-sessions/01-overview-stateless-truth.md` for current reality.
