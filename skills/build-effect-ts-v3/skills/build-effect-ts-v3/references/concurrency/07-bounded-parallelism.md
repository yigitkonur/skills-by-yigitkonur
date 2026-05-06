# Bounded Parallelism
Use this as the default rule for any concurrent Effect program that processes a collection.

## The Rule

Every dynamic collection fan-out must have a numeric concurrency bound.

Dynamic means the size is not proven by the code in the same file. Examples:

- rows returned from a database
- user-selected ids
- messages pulled from a queue
- files in a directory
- records in an import
- items returned by an API
- search results
- tenant ids

For these inputs, use a number:

```typescript
import { Effect } from "effect"

declare const messages: ReadonlyArray<string>
declare const handleMessage: (message: string) => Effect.Effect<void>

const program = Effect.forEach(
  messages,
  handleMessage,
  {
    concurrency: 10,
    discard: true
  }
)
```

The number is a safety limit, not just a performance setting.

## The Disaster Narrative

Today, the import has 10 items.

An agent writes:

```typescript
import { Effect } from "effect"

declare const items: ReadonlyArray<string>
declare const sendToPartner: (item: string) => Effect.Effect<void>

const program = Effect.all(
  items.map((item) => sendToPartner(item)),
  { concurrency: "unbounded" }
)
```

It passes review because 10 items today completes quickly. The partner API is
fast, staging has tiny data, and nobody sees a problem.

Tomorrow, a customer uploads 10,000 items.

The same code now attempts to start 10,000 outbound operations. The service
opens too many sockets, retries amplify traffic, the partner rate-limits the
account, telemetry volume spikes, and heap grows because every in-flight effect
holds request state. The failure may appear as timeouts, memory pressure, queue
backlog, or unrelated database errors. The root cause is still the same:
unbounded parallelism escaped review.

The fix was one line:

```typescript
import { Effect } from "effect"

declare const items: ReadonlyArray<string>
declare const sendToPartner: (item: string) => Effect.Effect<void>

const program = Effect.forEach(
  items,
  sendToPartner,
  {
    concurrency: 10,
    discard: true
  }
)
```

10 items today, 10,000 tomorrow: the program still runs at 10 in flight.

## Why Sequential Is Not Enough

Effect defaults collection combinators to sequential execution when concurrency
is omitted. Sequential is safe, but it can turn a 10-minute job into a 10-hour
job.

The production answer is not "omit concurrency forever." The answer is "set the
right bound."

```typescript
import { Effect } from "effect"

declare const tenants: ReadonlyArray<string>
declare const rebuildTenant: (tenant: string) => Effect.Effect<void>

const rebuild = Effect.forEach(
  tenants,
  rebuildTenant,
  {
    concurrency: 4,
    discard: true
  }
)
```

Four may be correct because the database pool has room for four rebuilds, not
because four sounds nice.

## Choosing a Bound

Start with the narrowest external constraint:

| Constraint | Bound from |
|---|---|
| Database work | available pool capacity for this workflow |
| Third-party API | documented rate and burst limits |
| CPU-heavy transform | core count and benchmark evidence |
| File I/O | file descriptor budget and disk behavior |
| Queue consumers | downstream throughput |
| Memory-heavy task | max heap divided by per-task footprint |

If no measurement exists, choose a conservative number and make it visible.
Visible numbers get tuned. Hidden unbounded fan-out gets paged.

## Where Bounds Belong

Put bounds at fan-out points:

- `Effect.all(effects, { concurrency: N })`
- `Effect.forEach(items, f, { concurrency: N })`
- `Stream.mapEffect(f, { concurrency: N })`
- schema annotations that perform concurrent validation
- queue consumers that spawn per-message work

For shared bottlenecks across several call sites, use a `Semaphore` in addition
to per-call concurrency.

## When `"unbounded"` Is Acceptable

Use `"unbounded"` only when:

- the collection size is fixed by source code
- the effects are cheap
- there is no external bottleneck
- the maximum cannot grow from input data

Examples: three independent startup checks, two alternative cache reads, or a
small hard-coded tuple.

Do not use `"unbounded"` for arrays just because the current array usually has
few elements.

## Review Blockers

Treat these as review blockers:

- `Effect.all(dynamicArray.map(...), { concurrency: "unbounded" })`
- `Effect.forEach(dynamicArray, f, { concurrency: "unbounded" })`
- helper functions that use `"inherit"` but no caller sets `Effect.withConcurrency`
- direct promise fan-out inside an Effect workflow
- one concurrency bound per call site when several call sites share the same API limit

## Cross-References

See also:

- [05-effect-all-concurrency.md](05-effect-all-concurrency.md)
- [06-effect-foreach-concurrency.md](06-effect-foreach-concurrency.md)
- [08-semaphore.md](08-semaphore.md)
- [13-effect-timeout.md](13-effect-timeout.md)
