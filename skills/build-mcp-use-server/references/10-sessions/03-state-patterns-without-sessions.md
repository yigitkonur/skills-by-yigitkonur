# State patterns without sessions

*Read this when managing state across independent HTTP requests.*

v2 is stateless; each request is independent. Build state management using verified identity + external storage.

## Pattern 1: RequestState codec (round-trip validation)

For client retries within a single elicitation flow, use `createRequestStateCodec`:

```typescript
import { MCPServer, createRequestStateCodec } from "mcp-use";
import { z } from "zod";

const stateCodec = createRequestStateCodec({
  booking_id: z.string(),
  seat_count: z.number(),
});

const server = new MCPServer({
  name: "flight-booker",
  version: "1.0.0",
  requestState: stateCodec.verify,
});

export const selectSeats = server.tool(
  { name: "select_seats", /* ... */ },
  async (params, ctx) => {
    if (!ctx.inputResponses) {
      // Round 1: client hasn't provided input yet
      return await ctx.elicit("seats", "How many seats?", z.object({
        count: z.number(),
      }));
    }
    
    // Round 2: state verified by codec; safe to use
    const { count } = ctx.inputResponses;
    // Process with verified count
  }
);
```

Codec automatically encodes/verifies state on retry; you don't explicitly set or read it. Use when state is small and round-trip is synchronous.

## Pattern 2: External database (cross-request state)

For workflow state that spans multiple independent HTTP requests, store in Redis/database keyed by verified user:

```typescript
import { MCPServer } from "mcp-use";
import { Redis } from "@upstash/redis";

const redis = new Redis({ url: process.env.REDIS_URL });

const server = new MCPServer({
  name: "form-builder",
  version: "1.0.0",
  oauth: clerckProvider, // Enable ctx.auth.user.id
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

## Pattern 3: Client-held state with elicitation

For ephemeral multi-round flows, use `ctx.elicit()` + `ctx.inputResponses`:

```typescript
export const collectData = server.tool(
  { name: "collect_data", /* ... */ },
  async (params, ctx) => {
    const responses = ctx.inputResponses || {};
    
    // Accumulate responses across rounds
    if (!responses.step1) {
      return await ctx.elicit("step1", "First question?", schema1);
    }
    if (!responses.step2) {
      return await ctx.elicit("step2", "Second question?", schema2);
    }
    
    // All steps collected; process
    const result = await processResponses(responses);
    return { content: [...], structuredContent: result };
  }
);
```

Client (via MCP SDK) aggregates input across elicitation rounds and sends all together on the final retry. Server never holds state; client does. Use for short, linear workflows.

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