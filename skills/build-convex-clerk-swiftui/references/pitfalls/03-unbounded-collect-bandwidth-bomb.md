# Unbounded .collect() — The Bandwidth Bomb

## Use This When
- Writing or reviewing a Convex query that returns a list of documents.
- Investigating high bandwidth usage or slow subscription updates.
- Deciding between `.collect()`, `.take(N)`, and `.paginate()`.

## The Problem

Server-side `.collect()` without `.withIndex()` or `.take()` performs a full table scan and returns every document. Because subscriptions are reactive, the query re-runs and re-sends the entire result set every time any document in the table changes. A table with 10,000 documents re-transmits all 10,000 on every single insertion, update, or deletion.

This looks fine in development with 50 test documents. In production it destroys bandwidth quota and makes the app sluggish.

## The Fix: Always Bound Queries

```typescript
// GOOD: Bounded query with index
export const listRecent = query({
  args: { channelId: v.id("channels") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("messages")
      .withIndex("by_channel", (q) => q.eq("channelId", args.channelId))
      .order("desc")
      .take(50);
  },
});
```

For large result sets, use `.paginate()` with `paginationOptsValidator`.

## Never Use .collect().length for Counting

Reading every document just to count them is wasteful. Maintain a counter document updated by mutations, or use the aggregate component.

```typescript
// GOOD: Counter document — reads 1 document, not N
export const getMessageCount = query({
  args: { channelId: v.id("channels") },
  handler: async (ctx, args) => {
    const channel = await ctx.db.get(args.channelId);
    return channel?.messageCount ?? 0;
  },
});
```

## Swift-Side Impact

The subscription call in Swift looks innocent but may trigger unbounded reads:

```swift
client.subscribe(to: "messages:listRecent", with: ["channelId": channelId], yielding: [Message].self)
    .receive(on: DispatchQueue.main)
    .removeDuplicates()
    .asResult()
    .sink { [weak self] result in ... }
    .store(in: &cancellables)
```

Always verify the backend query uses `.withIndex()` + `.take(N)` or `.paginate()`.

## Bandwidth Reference

| Query Pattern | Documents Read per Update | Approximate Bandwidth |
|---|---|---|
| `.collect()` on 100K docs | 100,000 | ~100MB per update |
| `.withIndex().take(50)` | 50 | ~50KB per update |
| `.withIndex().first()` | 1 | ~1KB per update |
| Counter document | 1 | ~100 bytes per update |

## Avoid
- `.collect()` without `.withIndex()` or `.take()` on any table expected to grow.
- `.collect().length` for counting — use counter documents or the aggregate component.
- Assuming small dev datasets prove a query is production-safe.
- Subscribing to unbounded queries from Swift without reviewing the backend function.

## Read Next
- [../backend/02-indexes-query-shaping-and-performance.md](../backend/02-indexes-query-shaping-and-performance.md)
- [../backend/03-queries-mutations-actions-scheduling.md](../backend/03-queries-mutations-actions-scheduling.md)
- [../advanced/01-pagination-live-tail-and-history.md](../advanced/01-pagination-live-tail-and-history.md)
