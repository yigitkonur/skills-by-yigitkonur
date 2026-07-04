# Effect ForEach Concurrency
Use this to map over collections with effects while preserving bounded parallelism.

## What `Effect.forEach` Does

`Effect.forEach(items, f, options)` applies an effectful function to every item.

Use it when you have values and need to produce effects from them. It avoids the
extra step of building `items.map(f)` before passing that array to `Effect.all`.

```typescript
import { Effect } from "effect"

declare const accountIds: ReadonlyArray<string>
declare const loadAccount: (id: string) => Effect.Effect<{ id: string }>

const program = Effect.forEach(
  accountIds,
  (id) => loadAccount(id),
  { concurrency: 8 }
)
```

The result order matches the input order.

## Use It for Dynamic Input

When input comes from users, databases, queues, files, HTTP responses, or other
systems, assume it can grow.

```typescript
import { Effect } from "effect"

declare const invoiceIds: ReadonlyArray<string>
declare const sendInvoice: (id: string) => Effect.Effect<void>

const sendInvoices = Effect.forEach(
  invoiceIds,
  (id) => sendInvoice(id),
  {
    concurrency: 5,
    discard: true
  }
)
```

The important part is not the API choice. It is the budget: at most five invoice
sends are in flight.

## The Index Argument

The mapping function receives `(value, index)`.

```typescript
import { Effect } from "effect"

const program = Effect.forEach(
  ["alpha", "beta", "gamma"],
  (name, index) =>
    Effect.logInfo(`processing ${index}:${name}`),
  {
    concurrency: 2,
    discard: true
  }
)
```

Use the index for observability, stable ordering keys, or batching metadata. Do
not use it to infer completion order. With concurrency, completion order is not
input order.

## `discard: true`

Use `discard: true` when each effect's value is not needed.

```typescript
import { Effect } from "effect"

declare const paths: ReadonlyArray<string>
declare const warmFileCache: (path: string) => Effect.Effect<void>

const warmAll = Effect.forEach(
  paths,
  warmFileCache,
  {
    concurrency: 16,
    discard: true
  }
)
```

This prevents accidental result accumulation and tells reviewers the work is
side-effecting by design.

## Batching Dynamic Work

Use batching when the external system works better with chunks. Keep both chunk
size and chunk concurrency explicit.

```typescript
import { Array, Effect } from "effect"

declare const ids: ReadonlyArray<string>
declare const indexBatch: (ids: ReadonlyArray<string>) => Effect.Effect<void>

const rebuild = Effect.forEach(
  Array.chunksOf(ids, 100),
  (batch) => indexBatch(batch),
  {
    concurrency: 3,
    discard: true
  }
)
```

This constrains both dimensions:

- at most 100 items per request
- at most 3 requests in flight

Without both limits, a future input spike can still overload a downstream
service.

## Helper Functions and `"inherit"`

Use `concurrency: "inherit"` inside reusable helpers when the caller should set
the budget.

```typescript
import { Effect } from "effect"

const processWithCallerBudget = <A>(
  items: Iterable<A>,
  f: (item: A) => Effect.Effect<void>
) =>
  Effect.forEach(items, f, {
    concurrency: "inherit",
    discard: true
  })

declare const jobs: ReadonlyArray<string>
declare const runJob: (job: string) => Effect.Effect<void>

const program = processWithCallerBudget(jobs, runJob).pipe(
  Effect.withConcurrency(4)
)
```

This is useful for libraries and shared services. At application boundaries,
prefer numeric budgets that can be reasoned about operationally.

## Failure Behavior

`Effect.forEach` fails when the mapping effect fails. Concurrent siblings may be
interrupted as part of fail-fast behavior.

When processing work where every item should be attempted, wrap each result
explicitly.

```typescript
import { Effect } from "effect"

declare const records: ReadonlyArray<string>
declare const validateRecord: (record: string) => Effect.Effect<string, string>

const validateAll = Effect.forEach(
  records,
  (record) => Effect.either(validateRecord(record)),
  { concurrency: 8 }
)
```

This returns one `Either` per record and does not stop at the first validation
failure.

## ForEach Versus All

| Situation | Prefer |
|---|---|
| You already have effects | `Effect.all` |
| You have values and a function that returns effects | `Effect.forEach` |
| You do not need results | `Effect.forEach(..., { discard: true })` |
| You need a fixed tuple or struct result | `Effect.all` |
| You need batching over values | `Effect.forEach` |

## Cross-References

See also:

- [05-effect-all-concurrency.md](05-effect-all-concurrency.md)
- [07-bounded-parallelism.md](07-bounded-parallelism.md)
- [08-semaphore.md](08-semaphore.md)
- [12-stm.md](12-stm.md)
