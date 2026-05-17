# Portable Utility Mode
Use this guide to write Effect utilities with `R = never` so consumers do not need layers or runtime wiring.

## Canonical Reference

The canonical community reference for this migration mode is `/tmp/effect-corpus/skills/millionco_expect_effect-portable-patterns.md`. Its central rule is directly useful for gradual adoption: build self-contained effects, keep the requirement channel at `never`, and run them as promises only at the outer boundary.

This mode is not a rejection of services. It is the lowest-friction adoption shape when a project wants Effect's typed errors, retries, timeouts, tracing, and composition without asking every caller to provide layers.

## Portable Type Shape

```typescript
import { Effect } from "effect";

type Portable<A, E> = Effect.Effect<A, E, never>;
```

Read it as: this utility can succeed with `A`, fail with `E`, and requires no environment.

## Side-by-side: Promise Utility to Portable Effect

| Promise utility | Portable Effect utility |
|---|---|
| ```typescript
type User = { readonly id: string };

export async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) {
    throw new Error(response.statusText);
  }
  return (await response.json()) as User;
}
``` | ```typescript
import { Data, Effect } from "effect";

type User = { readonly id: string };

class FetchUserError extends Data.TaggedError("FetchUserError")<{
  readonly id: string;
  readonly cause: unknown;
}> {}

export const fetchUser = Effect.fn("fetchUser")(function* (id: string) {
  return yield* Effect.tryPromise({
    try: () =>
      fetch(`/api/users/${id}`).then((response) => {
        if (!response.ok) {
          return Promise.reject(new Error(response.statusText));
        }
        return response.json() as Promise<User>;
      }),
    catch: (cause) => new FetchUserError({ id, cause }),
  });
});
``` |

The exported utility still has `R = never`. Consumers can call it from Effect code or wrap it with a promise facade.

## Simpler Function Form

Use this form when explicit generator return typing would distract from the API:

```typescript
import { Data, Effect } from "effect";

class DecodeError extends Data.TaggedError("DecodeError")<{
  readonly cause: unknown;
}> {}

export const decodeJson = <A>(
  input: string,
): Effect.Effect<A, DecodeError, never> =>
  Effect.try({
    try: () => JSON.parse(input) as A,
    catch: (cause) => new DecodeError({ cause }),
  });
```

Portable does not mean every function must use `Effect.fn`. Use `Effect.fn` for named workflows and tracing. Use a normal function when that is clearer.

## Side-by-side: Caller Experience

| Existing promise caller | Boundary call with portable Effect |
|---|---|
| ```typescript
async function render(id: string): Promise<string> {
  const user = await fetchUser(id);
  return user.id;
}
``` | ```typescript
import { Effect } from "effect";

const renderEffect = (
  id: string,
): Effect.Effect<string, FetchUserError, never> =>
  fetchUser(id).pipe(
    Effect.map((user) => user.id),
  );

export const render = (id: string): Promise<string> =>
  Effect.runPromise(renderEffect(id));
``` |

The application edge gets a plain promise. The internals keep typed failures until the last line.

## Portable Error Rules

| Rule | Reason |
|---|---|
| Use `Data.TaggedError` for recoverable failures | Enables `Effect.catchTag` and structured diagnostics |
| Store unknown causes in a field | Keeps foreign failures visible without spreading unknown types |
| Avoid plain string failures | Strings do not carry recovery context |
| Avoid one mega-error for every case | Tags should describe recovery choices |
| Keep errors exported when callers recover | Callers need the class or union type |

## Portable Retry and Timeout

```typescript
import { Data, Effect, Schedule } from "effect";

class TimeoutError extends Data.TaggedError("TimeoutError")<{
  readonly operation: string;
}> {}

export const fetchUserRobust = (
  id: string,
): Effect.Effect<User, FetchUserError | TimeoutError, never> =>
  fetchUser(id).pipe(
    Effect.timeoutFail({
      duration: "5 seconds",
      onTimeout: () => new TimeoutError({ operation: "fetchUser" }),
    }),
    Effect.retry(Schedule.exponential("100 millis").pipe(Schedule.compose(Schedule.recurs(3)))),
  );
```

No layer is needed for this. The retry policy and timeout are part of the utility's behavior.

## Portable Concurrency

```typescript
import { Effect } from "effect";

export const fetchUsers = (
  ids: ReadonlyArray<string>,
): Effect.Effect<Array<User>, FetchUserError | TimeoutError, never> =>
  Effect.forEach(ids, (id) => fetchUserRobust(id), { concurrency: 8 });
```

Always set a concurrency limit for bulk external work. A portable utility can still protect downstream systems.

## When to Leave Portable Mode

Move from `R = never` to services when dependencies become shared infrastructure:

| Symptom | Keep portable? |
|---|---|
| A function takes a one-off argument | Yes |
| Several modules pass the same client everywhere | Consider a service |
| Tests need many replacement implementations | Consider a service |
| Startup already wires infrastructure layers | Consider a service |
| A utility just validates or transforms data | Yes |

Services are a scaling tool. Portable utilities are a migration tool.

## Anti-patterns

| Anti-pattern | Replacement |
|---|---|
| Adding a service requirement to every helper | Keep `R = never` until dependency injection helps |
| Hiding `Effect.runPromise` inside reusable utilities | Return `Effect` and run at the outer boundary |
| Wrapping promise failures with `Effect.promise` | Use `Effect.tryPromise({ try, catch })` |
| Returning untagged errors | Use tagged error classes |
| Exporting only promise facades | Also export the Effect workflow for new code |

## Migration Steps

1. Pick a promise utility that has real failure behavior.
2. Define a tagged error class.
3. Wrap the foreign call with `Effect.tryPromise({ try, catch })`.
4. Keep the return type as `Effect.Effect<A, E, never>`.
5. Add retry, timeout, and bounded concurrency if they are part of the boundary's job.
6. Export a promise facade only for existing callers.
7. Move new internal callers to the Effect-returning utility.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-from-promise.md](02-from-promise.md), [05-from-neverthrow.md](05-from-neverthrow.md), [07-gradual-adoption.md](07-gradual-adoption.md).
