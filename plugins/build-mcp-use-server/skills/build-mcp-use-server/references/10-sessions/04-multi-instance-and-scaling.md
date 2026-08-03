# Multi-instance and scaling

*Read this when deploying to multiple servers or serverless runtimes.*

v2 stateless servers scale horizontally by default: every request is independent, so any instance can handle it.

## Stateless multi-instance

No sticky sessions, no session store syncing required:

```
┌─────────────────────────────────────────┐
│ Load Balancer / Edge Router              │
└────────┬────────────────────────┬────────┘
         │                        │
    ┌────▼──────┐         ┌──────▼─────┐
    │ Instance 1│         │ Instance 2  │
    │ MCP v2    │         │ MCP v2      │
    └────┬──────┘         └──────┬──────┘
         │                       │
         └───────┬───────────────┘
                 │
           ┌─────▼──────┐
           │ Redis (opt)│
           │ User state │
           └────────────┘
```

Each request:
1. Router sends to any instance
2. Instance fetches user state from Redis (if any)
3. Request completes; no server-held state
4. Next request may hit different instance — same result

**Cold starts:** Every request starts fresh. No warm closures or request-scoped caches.

**State placement:** Queries, external APIs, and verified identity (`ctx.auth`) are per-request; shared state lives in Redis/DB only.

## Example: multi-instance workflow

```typescript
import { MCPServer } from "mcp-use";
import { Redis } from "@upstash/redis";

const redis = new Redis({ url: process.env.REDIS_URL });

export const getRoomBookings = server.tool(
  { name: "get_room_bookings" },
  async ({ hotel_id }, ctx) => {
    const cacheKey = `bookings:${hotel_id}`;
    
    // Any instance can serve this; all read from same Redis
    let bookings = await redis.get(cacheKey);
    if (!bookings) {
      bookings = await hotelDb.getBookings(hotel_id);
      await redis.setex(cacheKey, 300, JSON.stringify(bookings)); // 5min TTL
    }
    
    return {
      content: [{ type: "text", text: JSON.stringify(bookings) }],
      structuredContent: bookings,
    };
  }
);
```

Instance 1 caches to Redis. Instance 2's first request hits Redis; cold start is only 1 DB query, not repeated per instance.

## Shutdown (Node.js)

`server.close()` aborts active MCP exchanges; it does not wait for them to finish. Use it directly when an aborting shutdown is acceptable:

```typescript
const { url } = await server.listen(3000);
console.log(`Listening at ${url}`);

process.on("SIGTERM", async () => {
  console.log("Aborting active exchanges and closing the listener");
  await server.close();
  process.exit(0);
});
```

For graceful draining, first make the instance unready and have the load balancer stop routing new traffic, then wait for request tracking outside `MCPServer` to reach zero (or a drain deadline) before calling `server.close()`. Calling `close()` immediately after setting an `isShuttingDown` flag still aborts in-flight work.

Platforms such as Railway send `SIGTERM` before killing the container. Fit any external drain within the platform's termination window.

## Serverless / edge (no graceful shutdown needed)

Cloudflare Workers, Deno Deploy, Vercel Functions are stateless by design; no cleanup hooks needed.

```typescript
export default {
  fetch: server.fetch,
};
```

Each invocation is isolated; nothing to clean up.

## Rate limiting without sessions

v1 could rate-limit per session (e.g., `ctx.session?.sessionId`). v2 has no sessions, so rate-limit by verified user:

```typescript
import { Ratelimit } from "@upstash/ratelimit";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, "1 h"),
});

export const expensiveTool = server.tool(
  { name: "expensive_op" },
  async (params, ctx) => {
    const userId = ctx.auth.user.id;
    const { success } = await ratelimit.limit(userId);
    
    if (!success) {
      return {
        isError: true,
        content: [{ type: "text", text: "Rate limit exceeded" }],
      };
    }
    
    // Proceed
  }
);
```

Ratelimit uses Redis key `{userId}` + sliding window; syncs across instances automatically.

## Cross-instance coordination

For workflows that span multiple requests (e.g., "start a batch job, check status"):

```typescript
export const startBatchJob = server.tool(
  { name: "start_batch" },
  async (params, ctx) => {
    const jobId = crypto.randomUUID();
    const userId = ctx.auth.user.id;
    
    // Write to shared store
    await redis.hset(`job:${jobId}`, {
      userId,
      status: "running",
      createdAt: Date.now(),
    });
    
    // Enqueue worker (outside MCP server)
    await queue.enqueue({ jobId });
    
    return {
      content: [{ type: "text", text: `Job ${jobId} started` }],
      structuredContent: { job_id: jobId },
    };
  }
);

export const getBatchStatus = server.tool(
  { name: "get_batch_status" },
  async ({ job_id }, ctx) => {
    const job = await redis.hgetall(`job:${job_id}`);
    if (!job) {
      return {
        isError: true,
        content: [{ type: "text", text: "Job not found" }],
      };
    }
    
    return {
      content: [{ type: "text", text: JSON.stringify(job) }],
      structuredContent: job,
    };
  }
);
```

Both tools read/write to Redis. Any instance can handle either request.

## Avoiding common pitfalls

| ❌ Don't | ✅ Do |
|----------|-------|
| Store state in closures (lost per-request) | Store in Redis/DB |
| Use timers/setInterval (lost on instance death) | Use cron job or queue |
| Trust user-provided IDs without OAuth | Always verify `ctx.auth` |
| Assume sticky sessions (stateful) | Assume any instance, any request |
| Open unclosed connections | Close DB/Redis on graceful shutdown |

See `03-state-patterns-without-sessions.md` for state patterns and `../09-transports/04-runtime-adapters-node-next-fetch.md` for lifecycle.