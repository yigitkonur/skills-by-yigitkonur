# Gradual Adoption
Use this guide to place Effect at stable boundaries while existing Promise, fp-ts, neverthrow, or RxJS callers continue working.

## Adoption Principle

Migrate where the codebase already has pain: retries, timeouts, typed errors, resource cleanup, concurrency, and stream processing. Do not start by rewriting every pure helper. A small boundary with strong failure semantics is more valuable than a broad rewrite with unstable public APIs.

The best first boundary usually has three traits:

- It calls an external system.
- It already has fallback or retry behavior.
- It has callers that can tolerate a facade while internals change.

## Side-by-side: Preserve the Public API

| Existing public function | Effect inside with same facade |
|---|---|
| ```typescript
type User = { readonly id: string };

export async function loadUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return (await response.json()) as User;
}
``` | ```typescript
import { Data, Effect } from "effect";

type User = { readonly id: string };

class UserLoadError extends Data.TaggedError("UserLoadError")<{
  readonly id: string;
  readonly cause: unknown;
}> {}

const loadUserEffect = (
  id: string,
): Effect.Effect<User, UserLoadError, never> =>
  Effect.tryPromise({
    try: () => fetch(`/api/users/${id}`).then((r) => r.json() as Promise<User>),
    catch: (cause) => new UserLoadError({ id, cause }),
  });

export const loadUser = (id: string): Promise<User> =>
  Effect.runPromise(loadUserEffect(id));
``` |

This lets internal code compose the effect while external callers keep using `Promise`.

## Boundary Shapes

| Boundary | Keep outside | Use inside |
|---|---|
| Web handler | Framework request and response | Effect workflow for validation and IO |
| SDK wrapper | Existing promise API | `Effect.tryPromise` and tagged errors |
| Batch job | CLI command entry | Effect workflow with bounded concurrency |
| UI event stream | Framework-specific observable or signal | `Stream` for data pipeline if it leaves UI code |
| Validation helper | Plain value or `Either` | Effect only when composed with IO |
| Shared utility | Promise facade if needed | Portable `R = never` effect |

## Side-by-side: Adapter for fp-ts Callers

| Existing fp-ts caller | Effect implementation with adapter |
|---|---|
| ```typescript
import * as TE from "fp-ts/TaskEither";

declare const saveUser: (
  user: User,
) => TE.TaskEither<SaveError, User>;
``` | ```typescript
import { Effect } from "effect";
import * as TE from "fp-ts/TaskEither";

const saveUserEffect = (
  user: User,
): Effect.Effect<User, SaveError, never> =>
  persistUser(user);

const saveUser = (user: User): TE.TaskEither<SaveError, User> =>
  () =>
    Effect.runPromise(
      Effect.either(saveUserEffect(user)),
    );
``` |

Adapters are temporary. Keep them thin and close to the boundary so internal code does not continue to grow around the old abstraction.

## Side-by-side: Adapter for neverthrow Callers

| Existing neverthrow caller | Effect implementation with adapter |
|---|---|
| ```typescript
import { ResultAsync } from "neverthrow";

declare const charge: (
  request: ChargeRequest,
) => ResultAsync<Receipt, ChargeError>;
``` | ```typescript
import { Effect, Either } from "effect";
import { err, ok, ResultAsync } from "neverthrow";

const chargeEffect = (
  request: ChargeRequest,
): Effect.Effect<Receipt, ChargeError, never> =>
  submitCharge(request);

const charge = (
  request: ChargeRequest,
): ResultAsync<Receipt, ChargeError> =>
  ResultAsync.fromPromise(
    Effect.runPromise(Effect.either(chargeEffect(request))),
    (cause) => ({ _tag: "ChargeError", cause }),
  ).andThen((value) =>
    Either.match(value, {
      onLeft: (error) => err(error),
      onRight: (receipt) => ok(receipt),
    }),
  );
``` |

This adapter is intentionally uglier than the Effect implementation. That is a signal to keep adapters at the edge and not build new domain code on them.

## Error Normalization

Normalize unknown errors once per external boundary:

```typescript
import { Data, Effect } from "effect";

class ExternalServiceError extends Data.TaggedError("ExternalServiceError")<{
  readonly service: string;
  readonly cause: unknown;
}> {}

const callExternal = (
  service: string,
  url: string,
): Effect.Effect<Response, ExternalServiceError, never> =>
  Effect.tryPromise({
    try: () => fetch(url),
    catch: (cause) => new ExternalServiceError({ service, cause }),
  });
```

After this point, downstream code handles `ExternalServiceError`, not unknown rejection values.

## Where to Run

Run effects at the application edge:

| Code location | Run with `Effect.runPromise`? |
|---|---|
| HTTP route handler | Yes |
| CLI main | Yes |
| Worker entrypoint | Yes |
| React event handler facade | Yes, if the UI layer expects promises |
| Library helper | No |
| Service method used by other Effect code | No |
| Stream operator | No |

Running too early collapses the typed error channel back into promise rejection.

## Migration Sequence

1. Pick one external boundary.
2. Define tagged errors for expected failures.
3. Wrap foreign promises or throws.
4. Compose internal steps with `Effect.gen`.
5. Add timeout, retry, and concurrency where the old code had implicit behavior.
6. Keep a facade for old callers.
7. Move adjacent callers to the Effect API when the boundary has stabilized.
8. Delete the adapter after no callers need it.

## Anti-patterns

| Anti-pattern | Replacement |
|---|---|
| Rewriting pure code before unsafe boundaries | Start at IO and concurrency boundaries |
| Exporting both old and new APIs everywhere | Keep one adapter near the boundary |
| Running effects in the middle of domain code | Return effects until the application edge |
| Introducing services on day one | Keep `R = never` until shared dependency wiring matters |
| Treating streams as promise arrays | Use `Stream` for multi-value flows |

## Cross-references

See also: [01-overview.md](01-overview.md), [02-from-promise.md](02-from-promise.md), [04-from-fp-ts.md](04-from-fp-ts.md), [06-from-rxjs.md](06-from-rxjs.md), [08-portable-utility.md](08-portable-utility.md).
