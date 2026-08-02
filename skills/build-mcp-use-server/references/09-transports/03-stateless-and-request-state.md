# Stateless model and request state

*Read this when handling `input_required` rounds or managing state across retries.*

## Stateless request model

Every HTTP request to `/mcp` is **independent**. The server builds a fresh MCP handler for each request; there is no persistent session object, no server-side state dictionary, and no carry-over between requests.

**Why:** Stateless servers scale horizontally without session affinity; cloud platforms can kill instances at any time without data loss.

## RequestState codec for round-trip integrity

When a tool calls `ctx.elicit()` (client input required), the client retries the entire handler with client-provided input. To validate that the state you set on round 1 matches what you receive on round 2, use `createRequestStateCodec`:

```typescript
import { MCPServer, createRequestStateCodec } from "mcp-use";
import { z } from "zod";

const stateCodec = createRequestStateCodec({
  booking_id: z.string(),
  user_id: z.string(),
});

const server = new MCPServer({
  name: "hotel-server",
  version: "1.0.0",
  requestState: stateCodec.verify,  // <-- Enable verification
});

export const confirmBooking = server.tool(
  {
    name: "confirm_booking",
    description: "Confirm a hotel booking (requires user input)",
    inputSchema: z.object({
      booking_id: z.string(),
    }),
    outputSchema: z.object({
      status: z.enum(["confirmed", "cancelled"]),
    }),
  },
  async ({ booking_id }, ctx) => {
    // Round 1: Set state for validation on retry
    if (!ctx.inputResponses) {
      // First run: ask for confirmation
      return await ctx.elicit("confirm", "Confirm booking?", z.object({
        confirmed: z.boolean(),
      }));
    }
    
    // Round 2: Client retried with `confirmed` answer
    // requestState automatically verified by codec; use ctx.inputResponses
    const { confirmed } = ctx.inputResponses!;
    
    if (confirmed) {
      // Safe: requestState was validated; booking_id is trusted
      await bookingService.confirm(booking_id);
      return {
        content: [{ type: "text", text: "Booking confirmed" }],
        structuredContent: { status: "confirmed" },
      };
    } else {
      return {
        content: [{ type: "text", text: "Booking cancelled" }],
        structuredContent: { status: "cancelled" },
      };
    }
  }
);
```

The codec automatically:
1. Encodes state on the elicit response.
2. Verifies state on the retry request (rejects if tampered).
3. Exposes verified data via `ctx.requestState`.

## External state patterns

For state that lives across multiple independent HTTP requests (user session, tenant context), store in an external database keyed by verified identity:

```typescript
export const getUserProfile = server.tool(
  { name: "get_user_profile", /* ... */ },
  async (params, ctx) => {
    // User ID is verified by OAuth
    const userId = ctx.auth.user.id;
    
    // Fetch from external store (Redis, DB, etc.)
    const profile = await userDb.get(userId);
    
    return {
      content: [{ type: "text", text: JSON.stringify(profile) }],
      structuredContent: profile,
    };
  }
);
```

Never trust `requestState` as an authorization boundary; it can be inspected (not encrypted) and is meant only for integrity during client retries.

## No session affinity

Multiple requests from the same client do not share variables. Each handler invocation is a clean function call; you cannot rely on closure or global state persisting across requests.

Statefulness (e.g., tracking a multi-turn workflow) belongs in the client or an external store, not the server.

See `../10-sessions/03-state-patterns-without-sessions.md` for advanced external storage patterns.