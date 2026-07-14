# From fp-ts
Use this guide to migrate common fp-ts shapes to Effect without losing typed errors or environment requirements.

## Core Mapping

Effect can represent the common fp-ts runtime shapes in one type: `Effect.Effect<A, E, R>`.

| fp-ts shape | Effect shape |
|---|---|
| `IO<A>` | `Effect.Effect<A, never, never>` |
| `Task<A>` | `Effect.Effect<A, never, never>` if it truly cannot reject |
| `Either<E, A>` | `Either.Either<A, E>` or `Effect.Effect<A, E, never>` |
| `TaskEither<E, A>` | `Effect.Effect<A, E, never>` |
| `Reader<R, A>` | `Effect.Effect<A, never, R>` |
| `ReaderTaskEither<R, E, A>` | `Effect.Effect<A, E, R>` |
| `Option<A>` | `Option.Option<A>` |

The mission equivalence is exact for the common async error shape: `TaskEither<E, A>` is equivalent to `Effect<A, E, never>`.

## Side-by-side: TaskEither

| fp-ts `TaskEither` | Effect |
|---|---|
| ```typescript
import * as TE from "fp-ts/TaskEither";

type User = { readonly id: string };
type UserError = { readonly _tag: "UserError"; readonly id: string };

const getUser = (id: string): TE.TaskEither<UserError, User> =>
  TE.tryCatch(
    () => fetch(`/api/users/${id}`).then((r) => r.json() as Promise<User>),
    () => ({ _tag: "UserError", id }),
  );
``` | ```typescript
import { Data, Effect } from "effect";

type User = { readonly id: string };

class UserError extends Data.TaggedError("UserError")<{
  readonly id: string;
  readonly cause: unknown;
}> {}

const getUser = (
  id: string,
): Effect.Effect<User, UserError, never> =>
  Effect.tryPromise({
    try: () => fetch(`/api/users/${id}`).then((r) => r.json() as Promise<User>),
    catch: (cause) => new UserError({ id, cause }),
  });
``` |

The right side moves from an async thunk returning an either to a lazy Effect value. The typed error remains in the error channel.

## Side-by-side: Pipe Chains

| fp-ts pipe | Effect pipe |
|---|---|
| ```typescript
import { pipe } from "fp-ts/function";
import * as TE from "fp-ts/TaskEither";

const loadLabel = (id: string) =>
  pipe(
    getUser(id),
    TE.map((user) => user.id.toUpperCase()),
    TE.chain((label) => saveLabel(label)),
  );
``` | ```typescript
import { Effect } from "effect";

const loadLabel = (
  id: string,
): Effect.Effect<string, UserError | SaveError, never> =>
  getUser(id).pipe(
    Effect.map((user) => user.id.toUpperCase()),
    Effect.flatMap((label) => saveLabel(label)),
  );
``` |

Use fluent `.pipe` or imported `pipe`; both are valid. Prefer matching the surrounding codebase style.

## Side-by-side: `Do` Notation to `Effect.gen`

| fp-ts bind chain | Effect generator |
|---|---|
| ```typescript
import { pipe } from "fp-ts/function";
import * as TE from "fp-ts/TaskEither";

const workflow = (id: string) =>
  pipe(
    TE.Do,
    TE.bind("user", () => getUser(id)),
    TE.bind("orders", ({ user }) => getOrders(user.id)),
    TE.map(({ user, orders }) => ({ user, orders })),
  );
``` | ```typescript
import { Effect } from "effect";

const workflow = (
  id: string,
): Effect.Effect<
  { readonly user: User; readonly orders: Array<Order> },
  UserError | OrderError,
  never
> =>
  Effect.gen(function* () {
    const user = yield* getUser(id);
    const orders = yield* getOrders(user.id);
    return { user, orders };
  });
``` |

`Effect.gen` is usually the clearest migration for multi-step `TaskEither` workflows.

## Either Interop

Effect v3 includes `Either` in the main package:

```typescript
import { Effect, Either } from "effect";

type ParseError = { readonly _tag: "ParseError"; readonly input: string };

const parseId = (input: string): Either.Either<number, ParseError> => {
  const value = Number(input);
  return Number.isInteger(value)
    ? Either.right(value)
    : Either.left({ _tag: "ParseError", input });
};

const parseIdEffect = (
  input: string,
): Effect.Effect<number, ParseError, never> =>
  Either.match(parseId(input), {
    onLeft: (error) => Effect.fail(error),
    onRight: (id) => Effect.succeed(id),
  });
```

Use `Either` for immediate pure decisions. Use `Effect` when the value is asynchronous, needs interruption, needs retry, or participates in a larger workflow.

## Reader and Environment

`Reader<R, A>` and `ReaderTaskEither<R, E, A>` map to the environment channel when `R` is a dependency that should be supplied by the runtime.

| fp-ts reader style | Effect service style |
|---|---|
| ```typescript
type Env = { readonly baseUrl: string };

const getUrl = (id: string) => (env: Env): string =>
  `${env.baseUrl}/users/${id}`;
``` | ```typescript
import { Context, Effect, Layer } from "effect";

class ApiConfig extends Context.Tag("ApiConfig")<
  ApiConfig,
  { readonly baseUrl: string }
>() {}

const getUrl = (id: string): Effect.Effect<string, never, ApiConfig> =>
  Effect.gen(function* () {
    const config = yield* ApiConfig;
    return `${config.baseUrl}/users/${id}`;
  });

const ApiConfigLive = Layer.succeed(ApiConfig, { baseUrl: "https://api.example.demo" });
``` |

Do not introduce services just to mirror every `Reader`. If passing an argument is simpler and the dependency is not shared, keep the utility portable.

## Option Interop

Effect uses `Option` from the main package:

```typescript
import { Effect, Option } from "effect";

class MissingHeaderError extends Error {
  readonly _tag = "MissingHeaderError";
}

const requiredHeader = (
  value: Option.Option<string>,
): Effect.Effect<string, MissingHeaderError, never> =>
  Option.match(value, {
    onNone: () => Effect.fail(new MissingHeaderError()),
    onSome: (header) => Effect.succeed(header),
  });
```

Use `Option.match` rather than extracting unsafely. Keep absence distinct from failure until the boundary where absence becomes an error.

## Concurrency Migration

fp-ts code often uses arrays of tasks and explicit traversal helpers. In Effect, use `Effect.forEach` with concurrency:

```typescript
import { Effect } from "effect";

const refreshUsers = (
  ids: ReadonlyArray<string>,
): Effect.Effect<Array<User>, UserError, never> =>
  Effect.forEach(ids, (id) => getUser(id), { concurrency: 10 });
```

This preserves typed failures while making concurrency visible.

## Migration Steps

1. Convert leaf `TaskEither<E, A>` functions to `Effect<A, E, never>`.
2. Convert `TE.chain` and `TE.map` pipelines to `Effect.flatMap` and `Effect.map`.
3. Convert complex bind chains to `Effect.gen`.
4. Keep pure `Either` and `Option` where they are already clear.
5. Map `Reader` dependencies to services only when the dependency is shared across modules.
6. Preserve public fp-ts exports temporarily with adapter functions if callers are not ready.

## Anti-patterns

| Anti-pattern | Replacement |
|---|---|
| Recreating fp-ts helper aliases around Effect | Use Effect APIs directly |
| Converting every `Either` to `Effect` | Keep pure immediate values as `Either` |
| Treating `Reader` as mandatory service migration | Use explicit arguments until services help |
| Keeping rejected promises inside `TaskEither` wrappers | Normalize with `Effect.tryPromise` |
| Migrating RxJS through fp-ts abstractions | Use `Stream` directly |

## Cross-references

See also: [02-from-promise.md](02-from-promise.md), [03-from-trycatch.md](03-from-trycatch.md), [06-from-rxjs.md](06-from-rxjs.md), [07-gradual-adoption.md](07-gradual-adoption.md).
