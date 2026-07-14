# Canonical Anchor — `mcp-use/mcp-progress-demo`

Reference repository for production-grade progress notification patterns:

**https://github.com/mcp-use/mcp-progress-demo**

## What it demonstrates

| Pattern | Where to look |
|---|---|
| `ctx.reportProgress?.(...)` for in-tool progress events | `index.ts` |
| Custom `/api/progress/:jobId` Hono endpoint for polling | `index.ts` |
| Polling fallback when client lacks push progress | `resources/progress-view/widget.tsx` |
| Client-side correlation by `jobId` | `resources/progress-view/widget.tsx` |
| Widget prop contract for `jobId` / `totalSteps` | `resources/progress-view/types.ts` |

## Patterns worth copying

### 1. Job ID + polling endpoint

The demo creates a `jobId` in the tool, kicks off async work, and exposes a Hono `GET /api/progress/:jobId` endpoint that returns the current state. Widgets poll this endpoint when push notifications aren't available (stateless clients).

```typescript
const jobId = crypto.randomUUID();
runJobInBackground(jobId);
return widget({ props: { jobId }, message: "Started." });

// In a separate route:
server.get("/api/progress/:jobId", (c) => {
  const job = jobs.get(c.req.param("jobId"));
  return c.json(job ?? { error: "not found" }, job ? 200 : 404);
});
```

### 2. Push + poll hybrid

The demo reports MCP progress with `ctx.reportProgress?.(...)` and also exposes the polling endpoint. The widget polls `GET /api/progress/:jobId` using `mcp_url` and `props.jobId`.

### 3. Throttled progress

Progress events fire on a time-throttled interval, not per inner loop iteration. See `03-progress-tokens.md` for the pattern.

## How to use this anchor

When teaching or implementing progress reporting:

1. Explain the API surface from `03-progress-tokens.md`.
2. Show the canonical layout from `mcp-progress-demo`.
3. Adapt to the user's transport mode — push only for stateful, push+poll for environments mixing both.

The demo is the closest thing to a "shape of a real progress-aware mcp-use server" — copy from it, don't reinvent.
