# Rate limiting

Three places to apply limits. Pick by what you're protecting:

| Where | Limit by | Protects | Layer |
|---|---|---|---|
| HTTP middleware on `/mcp` | IP | Network-level abuse, unauthenticated flood | `server.use()` (HTTP) |
| MCP-op middleware on `mcp:tools/call` | Session ID | Per-tenant fairness across all tools | `server.use("mcp:tools/call", ...)` |
| In-tool guard | Auth scope, user ID, custom key | Expensive tools (LLM calls, image gen, exports) | Inside the tool handler |

Apply them additively. The HTTP layer handles the firehose; the MCP-op layer handles the per-tenant share; the in-tool guard handles individual hot spots.

For middleware basics, see `08-server-config/05-middleware-and-custom-routes.md`. For multi-instance deploys, the in-memory limiter below is wrong — use a Redis-backed limiter so all replicas share the same window.

## Sliding-window limiter (in-memory, single instance)

```typescript
class SlidingWindow {
  private windows = new Map<string, { count: number; resetAt: number }>();
  constructor(private max: number, private windowMs: number) {}

  check(key: string): { ok: boolean; retryAfterMs: number } {
    const now = Date.now();
    const w = this.windows.get(key);
    if (!w || now > w.resetAt) {
      this.windows.set(key, { count: 1, resetAt: now + this.windowMs });
      return { ok: true, retryAfterMs: 0 };
    }
    if (w.count >= this.max) {
      return { ok: false, retryAfterMs: w.resetAt - now };
    }
    w.count++;
    return { ok: true, retryAfterMs: 0 };
  }
}
```

The map grows until each key's window expires. For a dev server this is fine. In production with many keys, prune on a timer or use Redis (`INCR` + `PEXPIRE`).

## HTTP-layer limiting (per-IP)

Reject before the MCP handshake even runs:

```typescript
const httpLimiter = new SlidingWindow(120, 60_000); // 120 req/min/IP

server.use(async (c, next) => {
  const ip = c.req.header("x-forwarded-for")?.split(",")[0].trim()
    ?? c.req.header("x-real-ip")
    ?? "unknown";
  const { ok, retryAfterMs } = httpLimiter.check(ip);
  if (!ok) {
    return c.json(
      { error: "rate_limit_exceeded" },
      429,
      { "Retry-After": String(Math.ceil(retryAfterMs / 1000)) }
    );
  }
  await next();
});
```

Trusting `X-Forwarded-For` only works if you're behind a known proxy you control — see `26-anti-patterns/05-security-and-cors.md`.

## MCP-op layer (per-session)

Cap tool calls per session so one client can't monopolize the server:

```typescript
const sessionLimiter = new SlidingWindow(60, 60_000); // 60 tools/min/session

server.use("mcp:tools/call", async (c, next) => {
  const sessionId = c.req.header("mcp-session-id") ?? "stateless";
  const { ok, retryAfterMs } = sessionLimiter.check(sessionId);
  if (!ok) {
    throw new Error(`Rate limit exceeded. Retry in ${Math.ceil(retryAfterMs / 1000)}s.`);
  }
  await next();
});
```

In MCP-op middleware, `throw` becomes the failure mechanism — the transport surfaces it as an error response. Stateless requests share a single bucket here; promote them to per-IP at the HTTP layer instead.

## In-tool limiting (per-scope or per-user)

For the few expensive tools (LLM-backed search, image generation, exports), gate inside the handler so cheap tools aren't impacted:

```typescript
import { error } from "mcp-use/server";

const expensiveLimiter = new SlidingWindow(10, 60_000); // 10/min/user

server.tool(
  { name: "generate-image", schema: z.object({ prompt: z.string() }) },
  async ({ prompt }, ctx) => {
    const userId = ctx.auth?.userId ?? ctx.client.info().name ?? "anon";
    const { ok, retryAfterMs } = expensiveLimiter.check(userId);
    if (!ok) {
      return error(`Rate limit: 10 generations/min. Retry in ${Math.ceil(retryAfterMs / 1000)}s.`);
    }
    return await generate(prompt);
  }
);
```

Use `return error(...)`, not `throw` — this is an *expected* failure the model can recover from (back off, retry, ask the user). See `04-error-strategy.md`.

## Per-scope limiting

Different scopes get different budgets. A `pro` scope gets 600/min, a `free` scope gets 60/min:

```typescript
const limits = { pro: 600, free: 60 };

server.use("mcp:tools/call", async (c, next) => {
  const auth = c.get("auth"); // populated by your auth middleware
  const tier = auth?.scopes.includes("pro") ? "pro" : "free";
  const limiter = tier === "pro" ? proLimiter : freeLimiter;
  const { ok, retryAfterMs } = limiter.check(auth?.userId ?? "anon");
  if (!ok) throw new Error(`Rate limit (${tier}). Retry in ${Math.ceil(retryAfterMs / 1000)}s.`);
  await next();
});
```

## Multi-instance: use Redis

In-memory limiters are per-process. Two replicas behind a load balancer = double the effective limit. For accuracy, put the counter in Redis:

```typescript
async function checkRedis(key: string, max: number, windowSec: number) {
  const count = await redis.incr(key);
  if (count === 1) await redis.expire(key, windowSec);
  return count <= max;
}
```

Higher fidelity (true sliding window) requires Lua scripts or a sorted-set + `ZREMRANGEBYSCORE` pattern; the `INCR + EXPIRE` version is good enough for most cases.

## Don't

- Don't apply rate limits before authentication when authenticated users have a higher budget — you'll deny legitimate paying traffic.
- Don't use the same limiter at multiple layers without per-key namespacing — they collide.
- Don't `throw` in HTTP middleware when you could return 429 — `throw` doesn't set `Retry-After`.
- Don't omit `Retry-After` on 429 — clients with backoff logic need it.
