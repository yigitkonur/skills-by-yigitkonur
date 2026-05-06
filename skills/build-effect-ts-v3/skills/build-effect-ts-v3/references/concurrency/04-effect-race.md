# Effect Race
Use this to run competing effects where the winner determines what happens to the losers.

## Race Semantics

Racing starts multiple effects concurrently and resolves from the first relevant
completion. Losing fibers are interrupted.

This matters because the losers are not abandoned promises. Their finalizers run
and interruption is visible to Effect's runtime.

Use racing for:

- primary versus fallback endpoints
- timeout-like alternatives
- fastest cache tier wins
- "first successful provider" selection
- speculative work where losers should stop

Do not use racing when every task must complete. Use `Effect.all` or
`Effect.forEach` with an explicit concurrency budget instead.

## `Effect.race`

`Effect.race(left, right)` returns the first successful result. If one side
fails first, the race can continue until the other side succeeds. If both fail,
the race fails.

```typescript
import { Effect } from "effect"

const primary = Effect.gen(function* () {
  yield* Effect.sleep("80 millis")
  return "primary"
})

const replica = Effect.gen(function* () {
  yield* Effect.sleep("40 millis")
  return "replica"
})

const program = Effect.race(primary, replica)
```

The loser is interrupted once the race has a winning result.

## `Effect.raceAll`

`Effect.raceAll(effects)` races an iterable and returns the first successful
result. If all effects fail, it fails with the last error encountered.

```typescript
import { Effect } from "effect"

const providers = [
  Effect.fail("cache-miss"),
  Effect.succeed("replica-a").pipe(Effect.delay("100 millis")),
  Effect.succeed("replica-b").pipe(Effect.delay("50 millis"))
] as const

const program = Effect.raceAll(providers)
```

Use `raceAll` when the candidate count is naturally dynamic. Keep candidates
bounded; racing 10,000 providers is still a resource problem.

## `Effect.raceWith`

`Effect.raceWith` gives you the `Exit` of the winner and a `Fiber` handle for
the loser. That is the escape hatch for custom race policy.

```typescript
import { Effect, Exit, Fiber } from "effect"

const fast = Effect.succeed("fast").pipe(Effect.delay("50 millis"))
const slow = Effect.succeed("slow").pipe(Effect.delay("1 second"))

const program = Effect.raceWith(fast, slow, {
  onSelfDone: (exit, loser) =>
    Exit.match(exit, {
      onFailure: () => Fiber.join(loser),
      onSuccess: (value) =>
        Fiber.interrupt(loser).pipe(Effect.as(value))
    }),
  onOtherDone: (exit, loser) =>
    Exit.match(exit, {
      onFailure: () => Fiber.join(loser),
      onSuccess: (value) =>
        Fiber.interrupt(loser).pipe(Effect.as(value))
    })
})
```

Use `raceWith` only when the standard race policy is not enough. The callback is
where mistakes happen: if you keep the loser alive, you own its lifetime.

## Race Versus Timeout

Timeout APIs are specialized races against a clock.

Prefer `Effect.timeout`, `Effect.timeoutFail`, or `Effect.timeoutTo` when the
competitor is just time. Prefer `Effect.race` when the competitor is another
meaningful effect.

```typescript
import { Effect } from "effect"

const fromCache = Effect.succeed("cached").pipe(Effect.delay("30 millis"))
const fromNetwork = Effect.succeed("network").pipe(Effect.delay("200 millis"))

const fastestValue = Effect.race(fromCache, fromNetwork)
```

## Interruption Consequences

When a race has a winner, losers are interrupted. Therefore:

- loser finalizers run
- loser semaphore permits are released
- loser scoped resources close
- `onInterrupt` handlers execute
- a slow finalizer can delay completion unless disconnected

This is a feature. It gives shutdown back-pressure. If the loser owns important
cleanup, the winner should not let the parent proceed before cleanup finishes.

## When to Disconnect

Use `Effect.disconnect` around a raced effect only when fast return matters more
than waiting for the loser's interruption to finish.

That is useful for graceful shutdown paths and latency-sensitive fallback logic,
but it should be rare. Disconnection changes timing, not ownership: the loser is
still interrupted, but the caller does not wait for the full interruption path.

See [14-effect-disconnect.md](14-effect-disconnect.md) before using it.

## Anti-Patterns

- racing effects that all must complete
- racing large dynamic collections without a size limit
- using `raceWith` and forgetting to interrupt or join the loser
- using race as a substitute for retry policy
- hiding slow finalizers with disconnection instead of fixing cleanup

## Cross-References

See also:

- [03-fiber-operations.md](03-fiber-operations.md)
- [05-effect-all-concurrency.md](05-effect-all-concurrency.md)
- [11-interruption.md](11-interruption.md)
- [13-effect-timeout.md](13-effect-timeout.md)
