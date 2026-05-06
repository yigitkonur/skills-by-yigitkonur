# From RxJS
Use this guide to migrate multi-value reactive flows to `Stream`, not to single-shot `Effect`.

## Core Difference

An RxJS `Observable<A>` can emit zero, one, or many values over time. A plain `Effect<A, E, R>` produces one success value or one failure when run. The Effect equivalent for Observable-style flows is `Stream.Stream<A, E, R>`.

Use `Effect` for one operation. Use `Stream` for sequences, subscriptions, event feeds, chunked processing, and incremental output.

## Type Mapping

| RxJS shape | Effect ecosystem shape |
|---|---|
| `Observable<A>` | `Stream.Stream<A, E, R>` |
| `Promise<A>` from `firstValueFrom` | `Effect.Effect<A, E, R>` only when one value is intended |
| `map` | `Stream.map` |
| `mergeMap` for effectful work | `Stream.mapEffect` |
| `toArray` | `Stream.runCollect` |
| `Subject` event bridge | `Queue` or `PubSub` plus `Stream` |
| Subscription cleanup | Scoped stream acquisition and interruption |

## Side-by-side: Array Source

| RxJS Observable | Effect Stream |
|---|---|
| ```typescript
import { from, map, Observable } from "rxjs";

const ids$: Observable<string> = from(["a", "b", "c"]);

const labels$ = ids$.pipe(
  map((id) => id.toUpperCase()),
);
``` | ```typescript
import { Stream } from "effect";

const ids: Stream.Stream<string> = Stream.fromIterable(["a", "b", "c"]);

const labels = ids.pipe(
  Stream.map((id) => id.toUpperCase()),
);
``` |

This is the simple migration for finite streams. The output is still a stream, not a single effect.

## Side-by-side: Effectful Mapping

| RxJS mergeMap | Effect Stream |
|---|---|
| ```typescript
import { from, mergeMap } from "rxjs";

const users$ = from(["1", "2", "3"]).pipe(
  mergeMap((id) => loadUserPromise(id), 4),
);
``` | ```typescript
import { Stream } from "effect";

const users = Stream.fromIterable(["1", "2", "3"]).pipe(
  Stream.mapEffect((id) => loadUser(id), { concurrency: 4 }),
);
``` |

`loadUser` should return `Effect.Effect<User, UserError, never>`. `Stream.mapEffect` preserves the typed failure in the stream error channel.

## Collecting a Stream

When the caller really needs an array, run the stream into a chunk:

```typescript
import { Chunk, Effect, Stream } from "effect";

const collectUsers: Effect.Effect<Array<User>, UserError, never> =
  Stream.fromIterable(["1", "2", "3"]).pipe(
    Stream.mapEffect((id) => loadUser(id), { concurrency: 3 }),
    Stream.runCollect,
    Effect.map((chunk) => Chunk.toReadonlyArray(chunk).slice()),
  );
```

Do this at a boundary. Do not collect an unbounded event stream.

## Single Value Boundary

If an Observable was only used as a promise workaround, migrate to `Effect` directly:

| RxJS as single value | Effect as single value |
|---|---|
| ```typescript
import { firstValueFrom } from "rxjs";

async function loadOne(id: string): Promise<User> {
  return firstValueFrom(loadUserObservable(id));
}
``` | ```typescript
import { Effect } from "effect";

const loadOne = (
  id: string,
): Effect.Effect<User, UserError, never> =>
  loadUser(id);
``` |

Only use this migration when the source semantically emits one value.

## Error Channel

RxJS errors are terminal notifications. Stream failures are typed terminal failures:

```typescript
import { Data, Effect, Stream } from "effect";

class DecodeEventError extends Data.TaggedError("DecodeEventError")<{
  readonly cause: unknown;
}> {}

const decodeEvents = (
  events: Stream.Stream<unknown>,
): Stream.Stream<Event, DecodeEventError, never> =>
  events.pipe(
    Stream.mapEffect((value) =>
      Effect.try({
        try: () => decodeEvent(value),
        catch: (cause) => new DecodeEventError({ cause }),
      }),
    ),
  );
```

Typed stream failures compose with downstream stream processing.

## Backpressure Mindset

RxJS is push-oriented. Effect streams are pull-oriented and designed for memory-conscious processing. This affects migration:

| RxJS habit | Stream habit |
|---|---|
| Producers push to subscribers | Consumers pull through the stream |
| Backpressure is operator-specific | Pulling gives natural demand control |
| Subscription lifetime is manual | Runtime interruption controls lifetime |
| Many flows end with subscription callbacks | Stream programs end by running a sink or collector |

## Boundary Strategy

1. Keep existing Observables at UI framework boundaries if the UI expects them.
2. Convert backend, worker, and batch data flows to `Stream`.
3. Convert one-shot Observable wrappers to `Effect`.
4. Use `Stream.mapEffect` for async work inside stream processing.
5. Use `Stream.runCollect` only for finite streams.
6. Avoid collecting event streams that are intended to stay open.

## Anti-patterns

| Anti-pattern | Replacement |
|---|---|
| Migrating every `Observable<A>` to `Effect<A, E, R>` | Use `Stream.Stream<A, E, R>` |
| Calling `firstValueFrom` to avoid stream migration | Keep a stream unless the source is truly one-shot |
| Collecting a live event feed into memory | Process incrementally with `Stream` operators |
| Hiding stream errors in untyped callbacks | Use typed stream failures |
| Recreating push subscriptions inside Effect helpers | Use Stream, Queue, or PubSub boundaries |

## Cross-references

See also: [01-overview.md](01-overview.md), [02-from-promise.md](02-from-promise.md), [04-from-fp-ts.md](04-from-fp-ts.md), [07-gradual-adoption.md](07-gradual-adoption.md).
