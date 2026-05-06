# Streaming large results

A buffered tool response goes into one JSON-RPC message. The whole payload sits in memory on both server and client, and the model sees it as one chunk *after* the handler returns. For large outputs this is wrong on three axes: memory, time-to-first-byte, and conversation-context size.

Use `stream()` (see `05-responses/06-stream-and-file.md` for the helper) when:

| Need | Use `stream()`? |
|---|---|
| LLM token stream from a downstream provider | Yes |
| Long-running computation that produces partial results | Yes |
| Large file the client should consume incrementally | `file()` (it handles chunking) |
| Result fits in a few KB | No — `text()` / `object()` |
| Result is large but the model only needs a summary | No — summarize and return small |
| Transport is stdio | **No** — stdio doesn't support streaming |

`stream()` works on Streamable HTTP and SSE. On stdio it falls back to buffering or fails — design tools that need streaming for HTTP transports only.

## Pattern: forward an upstream stream

```typescript
import { stream, text } from "mcp-use/server";
import { z } from "zod";

server.tool(
  {
    name: "summarize-doc-stream",
    description: "Stream a summary of a document, token by token.",
    schema: z.object({ doc: z.string().min(1) }),
  },
  async ({ doc }) =>
    stream(async function* () {
      for await (const chunk of llm.streamSummary(doc)) {
        yield text(chunk);
      }
    })
);
```

Each `yield` is forwarded immediately. The model can see the response as it's generated.

## Chunking strategy

The transport handles framing — you decide chunk *content*. Two common shapes:

| Shape | When |
|---|---|
| One token per yield | LLM passthrough; smallest perceptible latency |
| Coherent units (sentence, line, paragraph) | Search results, log tails, structured records |
| Coherent groups (10 items) | Pagination-style results that make sense together |

```typescript
// Search results, 10 at a time
async function* searchInChunks(query: string) {
  for (let page = 1; page <= MAX_PAGES; page++) {
    const batch = await search(query, page);
    if (batch.length === 0) return;
    yield text(batch.map(formatHit).join("\n"));
    if (batch.length < 10) return;
  }
}
```

Yield too small (one byte at a time) and the per-chunk transport overhead dominates. Yield too large (the entire result) and you've lost the streaming benefit. A few hundred bytes to a few KB per chunk is the sweet spot for most use cases.

## Backpressure

mcp-use's `stream()` honors the underlying transport's backpressure: if the client (or an intermediate proxy) is slow to consume, your generator awaits at the `yield` point. The CPU stops producing.

What this means for upstream sources:

- **HTTP fetches with `ReadableStream`** — already backpressure-aware. Pipe and forget.
- **Database cursors** — fetch one row, yield, fetch next. Don't pre-buffer.
- **Pure CPU work** — pause via `await new Promise(setImmediate)` between iterations to yield the event loop.

```typescript
async function* dbStream(cursor: Cursor) {
  while (true) {
    const row = await cursor.next();
    if (!row) return;
    yield object(row);
  }
}
```

The `await` on `cursor.next()` naturally rate-matches the consumer.

## Aborting on disconnect

If the client disconnects mid-stream, the generator's next `yield` throws. Wrap any cleanup in `try/finally`:

```typescript
stream(async function* () {
  const cursor = await db.openCursor(query);
  try {
    while (true) {
      const row = await cursor.next();
      if (!row) return;
      yield object(row);
    }
  } finally {
    await cursor.close(); // always runs, even on client disconnect
  }
});
```

Without `finally`, an aborted stream leaks DB cursors / file handles / SSE subscriptions on the upstream.

## When to summarize instead

If the result is large *because* it has noise — full API responses, raw log dumps, redundant nesting — don't stream the noise. Filter on the server, return small. The model uses tokens to read whatever you send. Stream only what the model genuinely needs to see incrementally.

```typescript
// ❌ streams 50 KB of GitHub API JSON
yield object(rawGithubResponse);

// ✅ extract relevant fields, return small
return object({ name: r.full_name, stars: r.stargazers_count, language: r.language });
```

## Hard limits

| Limit | Recommendation |
|---|---|
| Max stream duration | Cap at the orchestrator's request timeout minus 5 s. Past that, the LB will drop the connection mid-stream. |
| Max total bytes | Set a budget (e.g. 1 MB). Track yielded bytes, abort with `error()` past the cap. |
| Max chunks | Set a count cap as a safety net against runaway loops. |

Bounded streams are debuggable. Unbounded streams hang containers.

## Don't

- Don't `stream()` a result that fits in one buffer — pure overhead, no benefit.
- Don't mix `stream()` with progress notifications (`ctx.reportProgress`) for the same data — pick one.
- Don't forget `finally` for upstream cleanup — disconnects leak.
- Don't stream from inside a `forEach`/non-async loop — generators must be `async function*`.
