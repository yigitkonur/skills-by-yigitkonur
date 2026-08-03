# Stateless model and request state

*Read this when handling `input_required` rounds or managing state across retries.*

## Stateless request model

Every HTTP request to `/mcp` is **independent**. The server builds a fresh MCP handler for each request; there is no persistent session object, no server-side state dictionary, and no carry-over between requests.

**Why:** Stateless servers scale horizontally without session affinity; cloud platforms can kill instances at any time without data loss.

## RequestState codec for round-trip integrity

When a tool returns an `input_required` elicitation result (`inputRequired.elicit`), the client retries the entire handler with client-provided input. To validate that the state you set on round 1 matches what you receive on round 2, use `createRequestStateCodec`:

```typescript
import { MCPServer, createRequestStateCodec, inputRequired, inputResponse, acceptedContent } from "mcp-use";
import { z } from "zod";

const requestStateSecret = process.env.REQUEST_STATE_SECRET;
if (!requestStateSecret) {
  throw new Error("REQUEST_STATE_SECRET is required");
}

const stateCodec = createRequestStateCodec<{ booking_id: string }>({
  key: requestStateSecret,
  ttlSeconds: 600,
});

const server = new MCPServer({
  name: "hotel-server",
  version: "1.0.0",
  requestState: { verify: stateCodec.verify },
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
    const response = inputResponse(ctx.inputResponses, "confirm");
    if (response.kind === "elicit" && response.action !== "accept") {
      return {
        content: [{ type: "text", text: `Booking ${response.action}` }],
        isError: true,
      };
    }

    const confirmed = acceptedContent(
      ctx.inputResponses,
      "confirm",
      z.object({ confirmed: z.boolean() })
    );

    if (confirmed === undefined) {
      return inputRequired({
        inputRequests: {
          confirm: inputRequired.elicit({
            message: "Confirm booking?",
            requestedSchema: z.object({ confirmed: z.boolean() }),
          }),
        },
        requestState: await stateCodec.mint({ booking_id }),
      });
    }

    const state = ctx.requestState<{ booking_id: string }>();
    if (!state || state.booking_id !== booking_id) {
      return {
        content: [{ type: "text", text: "Booking state is missing or does not match" }],
        isError: true,
      };
    }

    if (confirmed.confirmed) {
      await bookingService.confirm(state.booking_id);
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

The codec:
1. `stateCodec.mint(data)` encodes signed state into the `requestState` field of the `inputRequired(...)` result.
2. `ServerConfig.requestState.verify` (wired from `stateCodec.verify`) validates that state on the client's retry request before the handler re-runs; a tampered or expired value fails verification.
3. `ctx.requestState` (type `RequestStateAccessor`, called as `ctx.requestState<T>()`) exposes the verified data inside the handler on the retry round. Fail closed if it is absent or conflicts with retry arguments, and perform side effects with the verified value rather than the client-resubmitted value.

Never ship a fallback signing key. Require `REQUEST_STATE_SECRET` at startup and keep it consistent across every instance that can receive a retry.

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