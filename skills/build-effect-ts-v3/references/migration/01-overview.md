# Migration Overview
Use this guide to choose where Effect enters an existing TypeScript codebase without forcing a rewrite.

## Migration Goal

Effect migration is not a flag day rewrite. The useful first step is to put Effect around unreliable boundaries: network calls, decoding, retries, timeouts, queues, streams, database calls, and multi-step workflows that currently hide errors in rejected promises or thrown exceptions.

Keep the rest of the codebase stable while the new boundary returns either a plain `Promise`, an `Either`, or a domain value that callers already understand. Once the boundary is stable, move more logic inward.

## What Changes

| Legacy habit | Effect habit |
|---|---|
| Rejected `Promise` carries unknown failure | `Effect<A, E, R>` carries typed failure `E` |
| `try` blocks mix success and failure paths | `Effect.gen` sequences success and typed failures |
| Ad hoc retry loops | `Effect.retry` with `Schedule` |
| Manual timeout and cancellation wiring | `Effect.timeoutFail` and runtime interruption |
| `Promise.all` over many external calls | `Effect.all` with explicit concurrency |
| `Observable` for event streams | `Stream` for pull-based stream processing |
| Dependency access from globals | Services and layers, or portable `R = never` utilities |

## Side-by-side Boundary

| Legacy async boundary | Effect boundary |
|---|---|
| ```typescript
type User = { readonly id: string; readonly name: string };

export async function loadUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);

  if (!response.ok) {
    throw new Error(`User ${id} failed`);
  }

  return (await response.json()) as User;
}
``` | ```typescript
import { Data, Effect } from "effect";

type User = { readonly id: string; readonly name: string };

class UserLoadError extends Data.TaggedError("UserLoadError")<{
  readonly id: string;
  readonly cause: unknown;
}> {}

export const loadUser = (id: string): Effect.Effect<User, UserLoadError, never> =>
  Effect.tryPromise({
    try: () => fetch(`/api/users/${id}`).then((response) => {
      if (!response.ok) {
        return Promise.reject(new Error(response.statusText));
      }
      return response.json() as Promise<User>;
    }),
    catch: (cause) => new UserLoadError({ id, cause }),
  });
``` |

The Effect version keeps the public behavior explicit: success is `User`, failure is `UserLoadError`, and no services are required because `R = never`.

## Reading the Type

```typescript
import { Effect } from "effect";

type Program = Effect.Effect<string, Error, never>;
```

Read the type as: this program may produce a `string`, may fail with `Error`, and requires no environment. The mission shorthand is `Effect<A, E, R>`.

For migration work, keep a small glossary:

| Old type | Effect type |
|---|---|
| `Promise<A>` | `Effect<A, UnknownBoundaryError, never>` when the promise can reject |
| `TaskEither<E, A>` | `Effect<A, E, never>` |
| `Reader<R, A>` | `Effect<A, never, R>` if `R` is a service requirement |
| `ReaderTaskEither<R, E, A>` | `Effect<A, E, R>` |
| `Result<A, E>` from neverthrow | `Either.Either<A, E>` or `Effect<A, E, never>` |
| `Observable<A>` | `Stream.Stream<A, E, R>` |

## Boundary Strategy

Start at the outside:

1. Wrap unsafe promise APIs with `Effect.tryPromise`.
2. Convert thrown exceptions into tagged errors at the boundary.
3. Keep public exports stable by running with `Effect.runPromise` only at application edges.
4. Introduce `Stream` for multi-value flows instead of forcing them into single-shot effects.
5. Introduce services and layers only when shared dependencies become painful.

Do not migrate pure functions first. A pure function already has a clear contract. Migrate the places where failures, concurrency, cancellation, retries, and resource cleanup are currently implicit.

## When to Keep `R = never`

Portable utility mode is the most useful bridge for teams that are not ready for Effect services. A utility with `R = never` can be imported anywhere and run as a promise at the edge:

```typescript
import { Effect } from "effect";

export const normalizeName = (input: string): Effect.Effect<string, never, never> =>
  Effect.succeed(input.trim().toLowerCase());

export const normalizeNamePromise = (input: string): Promise<string> =>
  Effect.runPromise(normalizeName(input));
```

This style gives typed composition without making callers provide layers.

## Where Services Fit Later

Use services when the same dependency appears in many functions, when tests need replacement implementations, or when startup wiring is already centralized. Until then, explicit function arguments are simpler and keep migration low-risk.

```typescript
import { Effect } from "effect";

type ClockLike = {
  readonly now: () => Date;
};

export const stamp = (
  clock: ClockLike,
  value: string,
): Effect.Effect<string, never, never> =>
  Effect.succeed(`${clock.now().toISOString()}:${value}`);
```

This is still valid Effect code. It simply does not use the environment channel.

## Common Gotchas

| Gotcha | Correction |
|---|---|
| Treating `Effect` like an already-running promise | Effects are lazy descriptions; run them at the boundary |
| Wrapping rejected promises with `Effect.promise` | Use `Effect.tryPromise` with a `catch` mapper |
| Catching Effect failures with language exceptions | Use `Effect.catchTag`, `Effect.catchTags`, or `Effect.catchAll` |
| Migrating `Observable` to plain `Effect` | Use `Stream`; an effect is single-shot |
| Adding layers to every helper | Keep helpers portable until shared dependencies justify services |
| Running effects inside library helpers | Return effects from helpers; run at the application edge |

## Adoption Checklist

- Pick one boundary, not one entire subsystem.
- Define tagged errors before composing workflows.
- Preserve caller-facing types until consumers are ready.
- Keep bulk parallelism bounded with `{ concurrency: N }`.
- Treat `Stream` separately from single-shot workflows.
- Keep portable utilities at `R = never`.
- Add service requirements only when dependency wiring becomes the real problem.

## Cross-references

See also: [02-from-promise.md](02-from-promise.md), [03-from-trycatch.md](03-from-trycatch.md), [07-gradual-adoption.md](07-gradual-adoption.md), [08-portable-utility.md](08-portable-utility.md).
