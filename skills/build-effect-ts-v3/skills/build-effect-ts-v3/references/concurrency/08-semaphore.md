# Semaphore
Use this to enforce a shared concurrency limit across independent Effect workflows.

## What a Semaphore Solves

`Effect.makeSemaphore(permits)` creates a permit counter. Work can acquire
permits before running and releases them when it completes.

Use a semaphore when a limit is shared across call sites or workflows.

`Effect.forEach(..., { concurrency: N })` limits one collection fan-out.
`Semaphore.withPermits(1)` can limit all work that shares the same semaphore,
even if that work starts from different functions.

## Basic Pattern

```typescript
import { Effect, Fiber } from "effect"

const program = Effect.gen(function* () {
  const semaphore = yield* Effect.makeSemaphore(2)

  const guarded = semaphore.withPermits(1)(
    Effect.logInfo("inside critical section")
  )

  yield* Effect.all(
    [guarded, guarded, guarded],
    { concurrency: "unbounded", discard: true }
  )
})
```

The outer `Effect.all` may start all three effects, but only two can be inside
the guarded region at the same time.

## Rate-Limit Shared API Pattern

Use this when several features call the same third-party API and the account has
one shared limit.

```typescript
import { Effect } from "effect"

type PartnerRequest = {
  readonly id: string
  readonly payload: string
}

type PartnerResponse = {
  readonly requestId: string
  readonly accepted: boolean
}

declare const postToPartner: (
  request: PartnerRequest
) => Effect.Effect<PartnerResponse, "PartnerUnavailable">

const makePartnerClient = Effect.gen(function* () {
  const apiLimit = yield* Effect.makeSemaphore(5)

  const submit = (request: PartnerRequest) =>
    apiLimit.withPermits(1)(
      postToPartner(request)
    )

  const bulkSubmit = (requests: ReadonlyArray<PartnerRequest>) =>
    Effect.forEach(
      requests,
      submit,
      { concurrency: "unbounded" }
    )

  return { submit, bulkSubmit } as const
})
```

Every caller that uses `submit` shares the same five-permit limit. A bulk job,
a retry path, and a request handler cannot accidentally exceed the partner
account's concurrent request budget.

This is the key distinction:

- collection concurrency limits one call site
- a semaphore limits a shared resource

Use both when needed.

## Permit Counts

Most guarded operations use one permit.

Use multiple permits when operations consume different amounts of capacity.

```typescript
import { Effect } from "effect"

declare const runSmallQuery: Effect.Effect<void>
declare const runLargeQuery: Effect.Effect<void>

const program = Effect.gen(function* () {
  const databaseBudget = yield* Effect.makeSemaphore(10)

  yield* Effect.all(
    [
      databaseBudget.withPermits(1)(runSmallQuery),
      databaseBudget.withPermits(5)(runLargeQuery)
    ],
    { concurrency: 2, discard: true }
  )
})
```

This makes cost visible. A large query consumes more of the shared database
budget than a small query.

## Interruption Safety

`withPermits` releases permits when the protected effect succeeds, fails, or is
interrupted.

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const semaphore = yield* Effect.makeSemaphore(1)

  const guarded = semaphore.withPermits(1)(
    Effect.sleep("1 minute").pipe(
      Effect.onInterrupt(() => Effect.logInfo("guarded work interrupted"))
    )
  )

  const fiber = yield* Effect.fork(guarded)
  yield* Effect.sleep("100 millis")
  yield* Fiber.interrupt(fiber)
})
```

If the permit were not released on interruption, the next caller could deadlock.
The semaphore API handles this cleanup for you.

## `withPermitsIfAvailable`

Use `withPermitsIfAvailable` for non-blocking admission control.

```typescript
import { Effect, Option } from "effect"

declare const expensiveRefresh: Effect.Effect<string>

const refreshIfIdle = Effect.gen(function* () {
  const semaphore = yield* Effect.makeSemaphore(1)
  const result = yield* semaphore.withPermitsIfAvailable(1)(expensiveRefresh)

  return Option.match(result, {
    onNone: () => "already running",
    onSome: (value) => value
  })
})
```

Use this for "skip if busy" semantics. Do not use it when every task must
eventually run.

## Semaphore Versus Bounded `forEach`

| Need | Tool |
|---|---|
| Limit one batch of work | `Effect.forEach` with `concurrency` |
| Limit one array of already-built effects | `Effect.all` with `concurrency` |
| Limit a shared API across features | `Effect.makeSemaphore` |
| Model weighted capacity | `withPermits(n)` |
| Skip when capacity is unavailable | `withPermitsIfAvailable(n)` |

The common production pattern is both: a batch-level bound to avoid retaining
too much local work, plus a semaphore for the shared external bottleneck.

## Avoiding Deadlocks

Keep semaphore usage simple:

- acquire the fewest permits needed
- do not acquire semaphores in inconsistent order
- do not wait on work that needs the same permits you already hold
- keep protected regions as small as possible
- prefer one shared semaphore per external bottleneck

If you need atomic updates across several pieces of shared state, use STM
instead of nested semaphores.

## Cross-References

See also:

- [05-effect-all-concurrency.md](05-effect-all-concurrency.md)
- [06-effect-foreach-concurrency.md](06-effect-foreach-concurrency.md)
- [07-bounded-parallelism.md](07-bounded-parallelism.md)
- [12-stm.md](12-stm.md)
