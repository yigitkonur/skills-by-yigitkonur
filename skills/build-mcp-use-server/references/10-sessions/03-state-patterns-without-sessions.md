# State patterns without sessions

*Read this when managing state across independent HTTP requests.*

v2 is stateless; each request is independent. Build state management using verified identity + external storage.

## Pattern 1: RequestState codec (round-trip validation)

For client retries within a single elicitation flow, use `createRequestStateCodec` with the raw `input_required` helpers:

```typescript
import { acceptedContent, createRequestStateCodec, inputRequired, MCPServer } from "mcp-use";
import { z } from "zod";

const stateCodec = createRequestStateCodec<{ booking_id: string }>({
  key: process.env.REQUEST_STATE_SECRET!,
  ttlSeconds: 600,
});

const seatsSchema = z.object({ count: z.number() });
const server = new MCPServer({
  name: "flight-booker",
  version: "1.0.0",
  requestState: { verify: stateCodec.verify },
});

export const selectSeats = server.tool(
  { name: "select_seats", /* ... */ },
  async (params, ctx) => {
    const seats = acceptedContent(ctx.inputResponses, "seats", seatsSchema);
    if (seats === undefined) {
      return inputRequired({
        inputRequests: {
          seats: inputRequired.elicit({
            message: "How many seats?",
            requestedSchema: seatsSchema,
          }),
        },
        requestState: await stateCodec.mint({ booking_id: params.booking_id }),
      });
    }

    // The configured verifier ran before re-entry; `seats` is schema-validated.
    const { count } = seats;
    // Process count
  }
);
```

The codec's `mint()` produces the opaque state string and `ServerConfig.requestState.verify` (wired from `stateCodec.verify`) checks it before handler re-entry. Read decoded state with `ctx.requestState<T>()` (the generic is a type assertion only, not runtime validation) when the handler needs it on the retry round. Use when state is small and round-trip is synchronous.

## Pattern 2: External database (cross-request state)

For workflow state that spans multiple independent HTTP requests, store in Redis/database keyed by verified user:

```typescript
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { Redis } from "@upstash/redis";

const redis = new Redis({ url: process.env.REDIS_URL });

const server = new MCPServer({
  name: "form-builder",
  version: "1.0.0",
  oauth: oauthClerkProvider({ frontendApiUrl: process.env.CLERK_FRONTEND_API_URL! }), // Enable ctx.auth.user.id
});

export const saveFormStep = server.tool(
  { name: "save_form_step", /* ... */ },
  async (params, ctx) => {
    const userId = ctx.auth.user.id;
    const formId = params.form_id;
    
    // Fetch current form state from Redis
    const key = `form:${userId}:${formId}`;
    const form = await redis.hgetall(key) || {};
    
    // Update with current step
    form.step = params.step;
    form.answers = { ...form.answers, ...params.answers };
    form.updatedAt = Date.now();
    
    // Persist
    await redis.hset(key, form);
    
    return {
      content: [{ type: "text", text: "Step saved" }],
      structuredContent: { saved: true },
    };
  }
);
```

Use when state is large, long-lived, or shared across multiple requests. External store is the source of truth; each request fetches fresh data.

## Pattern 3: Batch client-held input with elicitation

`ctx.inputResponses` contains responses for the current retried `input_required` round; it does not accumulate accepted values from earlier rounds. When the fields can be collected together, request them in one batch:

```typescript
const collectedSchema = z.object({
  firstAnswer: schema1,
  secondAnswer: schema2,
});

export const collectData = server.tool(
  { name: "collect_data", /* ... */ },
  async (params, ctx) => {
    const collected = acceptedContent(
      ctx.inputResponses,
      "answers",
      collectedSchema,
    );

    if (collected === undefined) {
      return inputRequired({
        inputRequests: {
          answers: inputRequired.elicit({
            message: "Complete both questions",
            requestedSchema: collectedSchema,
          }),
        },
      });
    }

    const result = await processResponses(collected);
    return {
      content: [{ type: "text", text: "Completed" }],
      structuredContent: result,
    };
  }
);
```

For truly sequential rounds, carry a phase and accepted values in verified request state, then branch on `ctx.requestState<T>()` before reading the current round's responses. Do not expect the client to resend earlier elicitation responses automatically.

## Pattern 4: Tenant/multi-user scoping

Use verified OAuth identity to scope tool access and results:

```typescript
export const getOrgData = server.tool(
  { name: "get_org_data", /* ... */ },
  async (params, ctx) => {
    const userId = ctx.auth.user.id; // Verified by OAuth
    const orgId = ctx.auth.payload.org_id; // From token
    
    // Query always filtered by org
    const data = await db.query(
      "SELECT * FROM data WHERE org_id = ? AND accessed_by = ?",
      [orgId, userId]
    );
    
    return {
      content: [{ type: "text", text: JSON.stringify(data) }],
      structuredContent: data,
    };
  }
);
```

Never trust user-provided IDs; always filter by verified `ctx.auth` fields. Use `ctx.auth.user` (provider-specific shape) and `ctx.auth.payload` (verified token claims).

## Scaling considerations

1. **No session affinity:** Requests can route to any instance. All state must be accessible from any server.
2. **Cold starts:** Fetch state fresh on every request (no warm caches per instance).
3. **Consistency:** Use transactions in external DB for multi-step operations (e.g., booking + confirm).
4. **TTL:** External state stores (Redis, DB) handle cleanup; v2 server has no TTL mechanism.

See `04-multi-instance-and-scaling.md` for deployment patterns.