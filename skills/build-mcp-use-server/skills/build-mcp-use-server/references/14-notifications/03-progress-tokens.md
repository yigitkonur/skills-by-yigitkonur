# Progress Tokens

`ctx.reportProgress()` sends a `notifications/progress` event tied to the originating tool call's progress token. Clients use these events to render progress bars and to reset request timeouts.

## Signature

```typescript
ctx.reportProgress?: (progress: number, total?: number, message?: string) => Promise<void>
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `progress` | `number` | Yes | Current step or value (0 → total) |
| `total` | `number` | No | Total steps; omit for indeterminate tasks |
| `message` | `string` | No | Human-readable status |

## How progress tokens work

1. The client attaches a `progressToken` to a tool request's `_meta.progressToken`.
2. mcp-use exposes `ctx.reportProgress` only when a progress token and notification transport are present.
3. Each call emits `notifications/progress` with the same `progressToken`, the current `progress` value, optional `total`, and optional `message`.
4. The client correlates the events to the in-flight request and updates its UI / extends its timeout.

## Long-running tool example

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "progress-demo", version: "1.0.0" });

server.tool(
  {
    name: "bulk-import",
    description: "Import a batch of records with progress.",
    schema: z.object({ count: z.number().min(1).max(500) }),
  },
  async ({ count }, ctx) => {
    await ctx.reportProgress?.(0, count, "Starting import");

    for (let i = 1; i <= count; i++) {
      await doWork(i);
      if (i % 10 === 0) {
        await ctx.reportProgress?.(i, count, `Imported ${i}/${count}`);
      }
    }

    await ctx.reportProgress?.(count, count, "Complete");
    return text(`Imported ${count} records.`);
  }
);
```

## When to emit

| Situation | Recommended behavior |
|---|---|
| Token provided by client | Call `ctx.reportProgress?.(...)` periodically (every ~1-5s) |
| No token | `ctx.reportProgress` is absent; call with `ctx.reportProgress?.(...)` |
| Indeterminate duration | Emit `ctx.reportProgress?.(0, undefined, "Starting")`, then update messages only |
| Tool finishes in <1s | Skip — overhead exceeds value |

## Throttling: don't flood

Each `reportProgress` call is a network round-trip. Emit periodically, not per iteration.

```typescript
// BAD — hundreds of events
for (let i = 0; i < total; i++) {
  await ctx.reportProgress?.(i, total, `step ${i}`);
}

// GOOD — every 10th step or every ~1s
for (let i = 0; i < total; i++) {
  if (i % 10 === 0) {
    await ctx.reportProgress?.(i, total, `Processed ${i}/${total}`);
  }
}
```

For time-based throttling:

```typescript
let lastEmit = 0;
for (let i = 0; i < total; i++) {
  await doWork(i);
  if (Date.now() - lastEmit > 1000) {
    await ctx.reportProgress?.(i, total, `Processed ${i}/${total}`);
    lastEmit = Date.now();
  }
}
```

## Auto-progress during sampling

`ctx.sample()` emits progress notifications automatically every `progressIntervalMs` (default 5s). You don't need to call `ctx.reportProgress` around a sample. Details: `../13-sampling/05-progress-during-sampling.md`.

## How progress prevents client timeouts

When the client opts in with `resetTimeoutOnProgress: true`:

- Each progress notification resets the client's request timeout counter.
- A long task can run beyond the default ~60s timeout as long as progress keeps flowing.
- Both auto-progress (sampling) and manual progress reset the same counter.

If your tool exceeds 60s of silence (no progress, no completion), the client may cancel the request.

## Progress notification wire format

```typescript
{
  method: "notifications/progress",
  params: {
    progressToken: number,  // From the original request's _meta.progressToken
    progress: number,
    total?: number,
    message?: string,
  }
}
```

## Stateless caveat

Progress notifications require a stateful notification path and a request progress token. In stateless mode or when the client does not provide a token, `ctx.reportProgress` is absent. Use optional chaining and fall back to polling if progress is core UX. See `06-when-notifications-fail.md`.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Calling `ctx.reportProgress` per tight-loop iteration | Throttle by count or time |
| No progress on a >60s tool | Add at least one progress event every 30s, or the client may time out |
| Sending `progress > total` | Cap at `total` to keep client UI sane |
| Storing the progress token manually | mcp-use handles it; just call `ctx.reportProgress?.(...)` |
