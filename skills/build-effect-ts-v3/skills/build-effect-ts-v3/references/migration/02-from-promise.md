# From Promise
Use this guide to migrate promise-heavy code to lazy, typed, interruptible Effect workflows.

## Core Difference

A `Promise<A>` is already running and can reject with anything. An `Effect<A, E, R>` is a lazy description that can be run more than once, interrupted, retried, timed out, and typed by success, failure, and requirements.

The migration is not `await` to `yield*` mechanically. The migration is from hidden rejection paths to explicit errors.

## Type Mapping

| Promise shape | Effect shape |
|---|---|
| `Promise<A>` that cannot reject in practice | `Effect.Effect<A, never, never>` |
| `Promise<A>` from `fetch`, SDKs, storage, or databases | `Effect.Effect<A, BoundaryError, never>` |
| `Promise<Array<A>>` with bulk external calls | `Effect.Effect<Array<A>, E, never>` using `Effect.forEach` |
| `Promise<void>` side effect | `Effect.Effect<void, E, never>` |
| `Promise<A>` needing retry or timeout | `Effect.Effect<A, E | TimeoutError, never>` |

## Side-by-side: Wrap a Promise

| Legacy Promise | Effect |
|---|---|
| ```typescript
type Profile = { readonly id: string };

export async function getProfile(id: string): Promise<Profile> {
  const response = await fetch(`/api/profiles/${id}`);
  if (!response.ok) {
    throw new Error(response.statusText);
  }
  return (await response.json()) as Profile;
}
``` | ```typescript
import { Data, Effect } from "effect";

type Profile = { readonly id: string };

class ProfileFetchError extends Data.TaggedError("ProfileFetchError")<{
  readonly id: string;
  readonly cause: unknown;
}> {}

export const getProfile = (
  id: string,
): Effect.Effect<Profile, ProfileFetchError, never> =>
  Effect.tryPromise({
    try: () =>
      fetch(`/api/profiles/${id}`).then((response) => {
        if (!response.ok) {
          return Promise.reject(new Error(response.statusText));
        }
        return response.json() as Promise<Profile>;
      }),
    catch: (cause) => new ProfileFetchError({ id, cause }),
  });
``` |

The canonical promise wrapper is object form:

```typescript
import { Data, Effect } from "effect";

class MyError extends Data.TaggedError("MyError")<{
  readonly cause: unknown;
}> {}

const program = Effect.tryPromise({
  try: () => fetch("/api/value"),
  catch: (cause) => new MyError({ cause }),
});
```

Use this when the promise may reject or the callback may throw before returning the promise.

## Side-by-side: `await` Sequence to `Effect.gen`

| Legacy async function | Effect generator |
|---|---|
| ```typescript
type User = { readonly id: string };
type Order = { readonly id: string; readonly userId: string };

async function loadUserOrder(userId: string): Promise<Order> {
  const user = await loadUser(userId);
  const order = await loadLatestOrder(user.id);
  return order;
}
``` | ```typescript
import { Effect } from "effect";

type User = { readonly id: string };
type Order = { readonly id: string; readonly userId: string };

declare const loadUser: (
  id: string,
) => Effect.Effect<User, UserError, never>;

declare const loadLatestOrder: (
  userId: string,
) => Effect.Effect<Order, OrderError, never>;

const loadUserOrder = (
  userId: string,
): Effect.Effect<Order, UserError | OrderError, never> =>
  Effect.gen(function* () {
    const user = yield* loadUser(userId);
    const order = yield* loadLatestOrder(user.id);
    return order;
  });
``` |

The generator accumulates the failure type. If `loadUser` can fail with `UserError` and `loadLatestOrder` can fail with `OrderError`, the composed workflow can fail with either.

## Preserve Promise Callers at the Edge

Do not make every caller learn Effect at once. Export a promise facade where needed:

```typescript
import { Effect } from "effect";

export const loadUserOrderPromise = (userId: string): Promise<Order> =>
  Effect.runPromise(loadUserOrder(userId));
```

The effect remains testable and composable. The facade preserves the existing public contract.

## Side-by-side: Bulk Promise Work

| Legacy bulk promises | Effect bulk work |
|---|---|
| ```typescript
async function loadProfiles(ids: ReadonlyArray<string>): Promise<Array<Profile>> {
  return Promise.all(ids.map((id) => getProfile(id)));
}
``` | ```typescript
import { Effect } from "effect";

const loadProfiles = (
  ids: ReadonlyArray<string>,
): Effect.Effect<Array<Profile>, ProfileFetchError, never> =>
  Effect.forEach(ids, (id) => getProfile(id), { concurrency: 8 });
``` |

Use an explicit concurrency number when calling external systems. This makes the load profile part of the contract instead of an accident.

## Timeouts and Retries

Promises need manual timeout and retry loops. Effect keeps them local to the workflow:

```typescript
import { Data, Effect, Schedule } from "effect";

class ProfileTimeoutError extends Data.TaggedError("ProfileTimeoutError")<{
  readonly id: string;
}> {}

const loadProfileRobust = (
  id: string,
): Effect.Effect<Profile, ProfileFetchError | ProfileTimeoutError, never> =>
  getProfile(id).pipe(
    Effect.timeoutFail({
      duration: "5 seconds",
      onTimeout: () => new ProfileTimeoutError({ id }),
    }),
    Effect.retry(Schedule.exponential("100 millis").pipe(Schedule.compose(Schedule.recurs(3)))),
  );
```

Retries apply to typed failures. Keep retry policies narrow when a failure should not be retried.

## `Effect.promise` vs `Effect.tryPromise`

| API | Use it when |
|---|---|
| `Effect.promise` | The promise-producing function is not expected to reject and any rejection should be treated as a defect |
| `Effect.tryPromise` | The promise can reject and you want a typed failure |

For migration, default to `Effect.tryPromise`. Most legacy promises can reject even when the type does not say so.

## Anti-patterns

| Anti-pattern | Replacement |
|---|---|
| Wrapping `fetch` with `Effect.promise` | Wrap it with `Effect.tryPromise({ try, catch })` |
| Running `Effect.runPromise` inside reusable helpers | Return `Effect` and run at the boundary |
| Converting every function to `async` after using Effect | Keep Effect in the internal workflow |
| Starting multiple effects by creating promises first | Compose effects, then run once |
| Using unbounded parallelism against external APIs | Use `Effect.forEach(..., { concurrency: N })` |

## Migration Steps

1. Identify promise-returning functions that call external systems.
2. Add a tagged error class for each meaningful failure boundary.
3. Wrap each promise with `Effect.tryPromise({ try, catch })`.
4. Replace `await` chains with `Effect.gen`.
5. Replace `Promise.all` with `Effect.forEach` or `Effect.all` and explicit concurrency.
6. Keep promise facades only at public application edges.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-from-trycatch.md](03-from-trycatch.md), [07-gradual-adoption.md](07-gradual-adoption.md), [08-portable-utility.md](08-portable-utility.md).
