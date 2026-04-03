# Date.now() In Queries Breaks Reactivity

## Use This When
- Writing a Convex query that filters by time (e.g., "messages from the last hour").
- Debugging a subscription whose results do not update as expected.
- Designing time-window features on top of reactive subscriptions.

## The Problem

Convex queries are deterministic functions. The reactive system re-runs a query when the **data it reads** changes. `Date.now()` is not data — it is a side-channel that changes every millisecond. Using it in a query breaks caching and makes reactivity unpredictable: the result may become stale without the system knowing to re-run, or it may re-run at arbitrary times.

```typescript
// BAD: Query result depends on wall-clock time
export const getRecentMessages = query({
  handler: async (ctx) => {
    const oneHourAgo = Date.now() - 60 * 60 * 1000;
    return await ctx.db
      .query("messages")
      .withIndex("by_time", (q) => q.gte("createdAt", oneHourAgo))
      .collect();
  },
});
```

## Fix 1: Pass Time As Argument From Client

The query becomes deterministic for any given argument set. The Swift client resubscribes periodically with an updated time window:

```swift
// Resubscribe every 5 minutes with updated time boundary
let oneHourAgo = Date().timeIntervalSince1970 * 1000 - 3_600_000
cancellable = client.subscribe(
    to: "messages:getRecentMessages",
    with: ["since": oneHourAgo],
    yielding: [Message].self
)
.receive(on: DispatchQueue.main)
.removeDuplicates()
.asResult()
.sink { [weak self] result in ... }
```

Use a `Timer.publish(every: 300, ...)` to tear down and recreate the subscription on the desired interval.

## Fix 2: Boolean Flags Updated By Scheduled Functions

Use a cron job to flip an `isRecent` boolean on documents. The query reads only database fields — fully deterministic, fully reactive:

```typescript
// convex/crons.ts
const crons = cronJobs();
crons.interval("update recent flags", { minutes: 5 },
  internal.maintenance.updateRecentFlags);
export default crons;

// Query: pure deterministic
export const getRecentMessages = query({
  handler: async (ctx) => {
    return await ctx.db
      .query("messages")
      .withIndex("by_recent", (q) => q.eq("isRecent", true))
      .take(100);
  },
});
```

## Fix 3: Bucket Time Into Discrete Windows

Round the time argument to the nearest hour so the query argument changes infrequently, reducing resubscription churn.

## Avoid
- `Date.now()` or any non-deterministic expression inside a `query` handler.
- `Math.random()` or other side-channels in queries for the same reason.
- Assuming the reactive system will "eventually" re-run a non-deterministic query — it tracks database reads, not JavaScript expressions.

## Read Next
- [../backend/03-queries-mutations-actions-scheduling.md](../backend/03-queries-mutations-actions-scheduling.md)
- [03-unbounded-collect-bandwidth-bomb.md](03-unbounded-collect-bandwidth-bomb.md)
- [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md)
