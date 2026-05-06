# Effect Timeout
Use this to put time bounds on effects while preserving typed interruption and cleanup behavior.

## Timeout Is Cancellation

Timeouts are concurrency tools. A timeout races work against time and interrupts
the work when the time limit wins.

That means:

- finalizers run
- `onInterrupt` handlers run
- semaphore permits are released
- scoped resources close
- slow interruption cleanup can delay the caller

Use timeouts at boundaries where waiting forever is not acceptable.

## `Effect.timeout`

In `effect@3.21.2`, `Effect.timeout(effect, duration)` returns the original
success value if the effect completes in time. If the duration expires, it fails
with `Cause.TimeoutException`.

```typescript
import { Effect } from "effect"

const request = Effect.gen(function* () {
  yield* Effect.sleep("2 seconds")
  return "response"
})

const program = request.pipe(
  Effect.timeout("500 millis")
)
```

Use this when timeout should be a typed failure in the error channel.

## `Effect.timeoutFail`

Use `Effect.timeoutFail` when the timeout error should be your domain-specific
error type.

```typescript
import { Effect } from "effect"

class PartnerTimeout {
  readonly _tag = "PartnerTimeout"
}

declare const callPartner: Effect.Effect<string, "PartnerUnavailable">

const program = callPartner.pipe(
  Effect.timeoutFail({
    duration: "2 seconds",
    onTimeout: () => new PartnerTimeout()
  })
)
```

This keeps timeout handling in the typed error model your application already
uses.

## `Effect.timeoutTo`

Use `Effect.timeoutTo` when timeout is an ordinary value decision rather than a
failure.

```typescript
import { Effect, Either } from "effect"

declare const readReplica: Effect.Effect<string, "ReplicaUnavailable">

const program = readReplica.pipe(
  Effect.timeoutTo({
    duration: "100 millis",
    onSuccess: (value): Either.Either<string, "TimedOut"> =>
      Either.right(value),
    onTimeout: (): Either.Either<string, "TimedOut"> =>
      Either.left("TimedOut")
  })
)
```

Use this for fallback logic where timeout is expected and should be modeled as
data.

## `Effect.timeoutOption`

When you want `Option` specifically, use `Effect.timeoutOption`.

```typescript
import { Effect, Option } from "effect"

declare const getCachedValue: Effect.Effect<string>

const program = Effect.gen(function* () {
  const result = yield* getCachedValue.pipe(
    Effect.timeoutOption("50 millis")
  )

  return Option.match(result, {
    onNone: () => "cache too slow",
    onSome: (value) => value
  })
})
```

This is the Option-returning timeout API in v3 source. Do not document
`Effect.timeout` as returning `Option`.

## Timeout and `race`

Timeout APIs are specialized races against a clock.

Prefer timeout APIs when time is the only competitor. Prefer `Effect.race` when
another effect is a real alternative.

```typescript
import { Effect } from "effect"

declare const primary: Effect.Effect<string>
declare const fallback: Effect.Effect<string>

const fastest = Effect.race(
  primary.pipe(Effect.timeout("500 millis")),
  fallback
)
```

The losing branch is interrupted.

## Timeout Placement

Put the timeout around the operation whose latency budget you mean.

```typescript
import { Effect } from "effect"

declare const connect: Effect.Effect<void>
declare const query: Effect.Effect<string>

const onlyQueryTimed = Effect.gen(function* () {
  yield* connect
  return yield* query.pipe(Effect.timeout("1 second"))
})
```

This times only the query, not connection setup. If the whole workflow has a
budget, wrap the whole workflow.

## Timeout and Bounded Parallelism

Timeout does not replace concurrency limits.

If 10,000 requests start at once and each times out after one second, the system
still had 10,000 requests in flight. Use both:

```typescript
import { Effect } from "effect"

declare const ids: ReadonlyArray<string>
declare const fetchOne: (id: string) => Effect.Effect<string, "FetchError">

const program = Effect.forEach(
  ids,
  (id) => fetchOne(id).pipe(Effect.timeout("2 seconds")),
  { concurrency: 20 }
)
```

The timeout bounds duration. The concurrency option bounds pressure.

## Cross-References

See also:

- [04-effect-race.md](04-effect-race.md)
- [05-effect-all-concurrency.md](05-effect-all-concurrency.md)
- [07-bounded-parallelism.md](07-bounded-parallelism.md)
- [11-interruption.md](11-interruption.md)
