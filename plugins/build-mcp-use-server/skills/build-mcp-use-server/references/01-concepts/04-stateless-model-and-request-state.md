# Stateless Model and Request State

*Read this when you need to understand v2's stateless architecture and how multi-round flows work.*

## v2 is stateless by design

Each HTTP request is independent; the server builds a fresh MCP context per exchange.

**No:**
- `Mcp-Session-Id` header or `initialize` handshake on the modern (2026-07-28) wire — every request carries its own protocol/capability metadata in `_meta`
- Per-client state stored on the server
- Post-response notifications to named clients (notifications ride the originating request's response stream only)
- Server-side sampling (`ctx.sample()` does not exist)

**Implications:**
- Multi-round flows (elicitation, forms) use a **request-state codec** to round-trip integrity
- Notifications travel on the originating request stream only
- Application owns client state (database, cache, etc.)
- Scales horizontally without affinity

## Request state for multi-round flows

When a tool must re-run after user input (`input_required` retry, form entry), correlate rounds with `inputRequired`, `inputResponse`, and `acceptedContent` — all re-exported from `mcp-use` root — and optionally sign cross-round state with `createRequestStateCodec()`:

```typescript
import {
  acceptedContent,
  inputRequired,
  inputResponse,
  MCPServer,
} from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

const dateSchema = z.object({ date: z.string() });

server.tool(
  { name: "book", inputSchema: z.object({}) },
  async (_params, ctx) => {
    // A stateless handler restarts from the top on both the initial call
    // and every retry — inspect this round's response first.
    const response = inputResponse(ctx.inputResponses, "date");
    if (response.kind === "elicit" && response.action !== "accept") {
      return {
        content: [{ type: "text", text: "Booking cancelled." }],
        isError: true,
      };
    }

    const confirmed = acceptedContent(ctx.inputResponses, "date", dateSchema);
    if (confirmed === undefined) {
      // Round 1 (or invalid retry data): ask for the date.
      return inputRequired({
        inputRequests: {
          date: inputRequired.elicit({
            message: "When?",
            requestedSchema: dateSchema,
          }),
        },
      });
    }

    // Round 2: confirmed.date is present and schema-valid.
    return { content: [{ type: "text", text: `Booked for ${confirmed.date}` }] };
  }
);
```

`inputRequired.elicitUrl({ message, url })` requests URL-mode input (open a browser flow) instead of a typed form. When round state must carry signed, tamper-evident data, create a codec with `createRequestStateCodec({ key, ttlSeconds })`, pass `requestState: { verify: codec.verify }` to `MCPServer`, and read decoded state per request with `ctx.requestState<T>()`.

Server docs and the beta spec also describe a convenience `ctx.elicit(key, message, schemaOrUrl)` wrapper over this same mechanism. It does not appear in the shipped `beta.66` `dist/context.d.ts`, the compiled `toRequestContext()` object construction, or the framework's own `examples/elicitation` source — treat it as not yet shipped and use the primitives above. See `12-elicitation/` (owned by a sibling cluster) for the full elicitation contract and status-value table.

## Notifications (request-scoped)

Notifications travel on the originating request stream:

```typescript
await ctx.sendNotification("resource-updated", { uri: "db://item/123" });
```

Use `server.notifyToolsChanged()`, `server.notifyPromptsChanged()`, `server.notifyResourcesChanged()`, and `server.notifyResourceUpdated(uri)` outside a request handler for cross-request list/resource invalidations, delivered to clients with an active subscription.

See `14-notifications/01-overview.md` for failure modes in stateless model.

## No session stores in beta.66

`InMemorySessionStore`, `RedisSessionStore`, and related session-management APIs appear only in the **v1** docs (`docs/typescript/server/session-management/`) — not in v2 docs, not in the shipped `beta.66` dist. Current v2 is stateless-only with no session store of any kind shipped.

See `10-sessions/01-overview-stateless-truth.md` for current reality.
