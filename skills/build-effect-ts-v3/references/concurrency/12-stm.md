# STM
Use this for atomic concurrent state changes across multiple transactional references or queues.

## What STM Is

STM is Software Transactional Memory.

Effect's STM lets you describe a transaction over transactional data structures
such as `TRef` and `TQueue`. The transaction commits atomically: either all
changes happen, or none do.

Use STM when correctness depends on multiple shared state reads and writes being
consistent under concurrency.

```typescript
import { Effect, STM, TRef } from "effect"

const program = Effect.gen(function* () {
  const balance = yield* STM.commit(TRef.make(100))

  const withdraw = (amount: number) =>
    STM.gen(function* () {
      const current = yield* TRef.get(balance)
      if (current < amount) {
        return yield* STM.fail("InsufficientFunds")
      }
      yield* TRef.set(balance, current - amount)
      return current - amount
    }).pipe(STM.commit)

  return yield* withdraw(30)
})
```

The read and write happen in one transaction.

## `TRef`

`TRef<A>` is a transactional reference.

Use it like `Ref` when the operations must compose transactionally with other
STM operations.

```typescript
import { Effect, STM, TRef } from "effect"

const incrementBoth = Effect.gen(function* () {
  const left = yield* STM.commit(TRef.make(0))
  const right = yield* STM.commit(TRef.make(0))

  const transaction = STM.gen(function* () {
    yield* TRef.update(left, (n) => n + 1)
    yield* TRef.update(right, (n) => n + 1)
  })

  yield* STM.commit(transaction)
})
```

Without STM, a concurrent observer could see one ref updated and the other not
updated. STM commits both changes as one unit.

## `STM.retry`

`STM.retry` suspends the transaction until one of the transactional values it
read changes. This is the core blocking primitive.

```typescript
import { Effect, STM, TRef } from "effect"

const waitUntilPositive = Effect.gen(function* () {
  const ref = yield* STM.commit(TRef.make(0))

  const awaitPositive = STM.gen(function* () {
    const value = yield* TRef.get(ref)
    if (value <= 0) {
      return yield* STM.retry
    }
    return value
  })

  yield* STM.commit(TRef.set(ref, 1))
  return yield* STM.commit(awaitPositive)
})
```

Do not build polling loops around `TRef.get`. Let STM retry and wake the
transaction when relevant state changes.

## `TQueue`

`TQueue` is a transactional queue. Its operations are STM transactions.

```typescript
import { Effect, STM, TQueue } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* STM.commit(TQueue.bounded<string>(100))

  yield* STM.commit(TQueue.offer(queue, "job-1"))
  return yield* STM.commit(TQueue.take(queue))
})
```

`TQueue.take` composes with other STM operations. That means you can atomically
take a job and update related transactional state in the same commit.

## Atomic Queue and State Update

```typescript
import { Effect, STM, TQueue, TRef } from "effect"

const program = Effect.gen(function* () {
  const queue = yield* STM.commit(TQueue.bounded<string>(100))
  const inFlight = yield* STM.commit(TRef.make(0))

  const takeJob = STM.gen(function* () {
    const job = yield* TQueue.take(queue)
    yield* TRef.update(inFlight, (n) => n + 1)
    return job
  })

  yield* STM.commit(TQueue.offer(queue, "job-1"))
  return yield* STM.commit(takeJob)
})
```

The job removal and counter increment commit together. If the transaction
retries, neither half is visible.

## STM Versus SynchronizedRef

`SynchronizedRef` serializes effectful updates to one reference. See
[../state/03-synchronizedref.md](../state/03-synchronizedref.md).

Use `SynchronizedRef` when:

- there is one shared value
- the update itself needs to run effects
- sequential update order is enough

Use STM when:

- several refs must change atomically
- a queue and counters must update together
- waiting should retry based on transactional state changes
- consistency spans multiple transactional structures

| Need | Prefer |
|---|---|
| One effectful mutable reference | `SynchronizedRef` |
| Multiple atomic references | `STM` + `TRef` |
| Atomic queue plus state | `STM` + `TQueue` |
| Wait until state changes | `STM.retry` |

STM transactions should be pure transactional logic. Do not perform arbitrary
external effects inside STM.

## Transaction Boundaries

Build transactions with `STM.gen`, then cross back into Effect with
`STM.commit`.

```typescript
import { Effect, STM, TRef } from "effect"

const program = Effect.gen(function* () {
  const ref = yield* STM.commit(TRef.make(0))

  const transaction = TRef.updateAndGet(ref, (n) => n + 1)
  const next = yield* STM.commit(transaction)

  yield* Effect.logInfo(`next value ${next}`)
})
```

Keep `STM.commit` at the boundary. This makes it clear which code is
transactional and which code is ordinary Effect logic.

## Queue Variants

`TQueue` provides several capacity strategies:

- `TQueue.bounded(capacity)` waits when full
- `TQueue.dropping(capacity)` drops new values when full
- `TQueue.sliding(capacity)` drops old values to make room
- `TQueue.unbounded()` has no capacity limit

Prefer bounded queues unless you can prove the queue size is naturally limited.
Unbounded queues move a concurrency bug into memory.

## Anti-Patterns

- using several independent `Ref` updates when atomicity is required
- polling transactional state instead of using `STM.retry`
- using STM for ordinary local variables
- putting external API calls in transactions
- choosing an unbounded queue for dynamic producer rates
- using nested semaphores when transactional state would be clearer

## Cross-References

See also:

- [06-effect-foreach-concurrency.md](06-effect-foreach-concurrency.md)
- [08-semaphore.md](08-semaphore.md)
- [09-deferred.md](09-deferred.md)
- [10-latch.md](10-latch.md)
