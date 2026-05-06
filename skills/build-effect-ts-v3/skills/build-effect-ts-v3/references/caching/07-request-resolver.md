# RequestResolver
Use this to batch and deduplicate many independent requests into fewer backend calls.

`RequestResolver` is Effect's dataloader pattern. Instead of each `getUserById(id)` effect directly calling a backend, each effect describes a `Request`. Effect batches compatible requests and asks a resolver to complete all of them.

## Core Types

The v3 source model is:

```typescript
import { Array as Arr, Effect, Request, RequestResolver } from "effect"

declare const request: {
  <A extends Request.Request<any, any>, R>(
    dataSource: RequestResolver.RequestResolver<A, R>
  ): (self: A) => Effect.Effect<
    Request.Request.Success<A>,
    Request.Request.Error<A>,
    R
  >
}

declare const makeBatched: <A extends Request.Request<any, any>, R>(
  run: (requests: Arr.NonEmptyArray<A>) => Effect.Effect<void, never, R>
) => RequestResolver.RequestResolver<A, R>
```

The batch passed to `makeBatched` is non-empty.

Every request received by the resolver must be completed. If any request is left unresolved, query execution can fail.

## Define a Request

Use `Request.TaggedClass` for request data:

```typescript
import { Data, Request } from "effect"

interface User {
  readonly id: string
  readonly name: string
}

class GetUserError extends Data.TaggedError("GetUserError")<{
  readonly id: string
}> {}

class GetUserById extends Request.TaggedClass("GetUserById")<
  User,
  GetUserError,
  {
    readonly id: string
  }
> {}
```

The request type says: this request succeeds with `User` or fails with `GetUserError`.

## Batch N User Fetches Into One Query

This resolver turns N `GetUserById` requests into one backend call:

```typescript
import { Data, Effect, HashMap, Option, Request, RequestResolver } from "effect"

interface User {
  readonly id: string
  readonly name: string
}

class GetUserError extends Data.TaggedError("GetUserError")<{
  readonly id: string
}> {}

class GetUserById extends Request.TaggedClass("GetUserById")<
  User,
  GetUserError,
  {
    readonly id: string
  }
> {}

declare const fetchUsersByIds: (
  ids: ReadonlyArray<string>
) => Effect.Effect<ReadonlyArray<User>, GetUserError>

const GetUserByIdResolver = RequestResolver.makeBatched(
  (requests: ReadonlyArray<GetUserById>) =>
    Effect.gen(function* () {
      const ids = requests.map((request) => request.id)
      const users = yield* fetchUsersByIds(ids)

      const usersById = HashMap.fromIterable(
        users.map((user) => [user.id, user])
      )

      yield* Effect.forEach(
        requests,
        (request) => {
          const user = HashMap.get(usersById, request.id)

          return Request.completeEffect(
            request,
            Option.match(user, {
              onNone: () => Effect.fail(new GetUserError({ id: request.id })),
              onSome: Effect.succeed
            })
          )
        },
        { concurrency: "unbounded", discard: true }
      )
    })
)

const getUserById = (id: string) =>
  Effect.request(new GetUserById({ id }), GetUserByIdResolver)
```

If five fibers call `getUserById` in a batching region, the resolver receives those five requests together and performs one `fetchUsersByIds(ids)` query.

## Caller Pattern

Use Effect concurrency with batching enabled at the call site:

```typescript
import { Effect } from "effect"

const loadUsers = (ids: ReadonlyArray<string>) =>
  Effect.forEach(ids, getUserById, {
    concurrency: 16,
    batching: true
  })

declare const getUserById: (id: string) => Effect.Effect<User, GetUserError>

interface User {
  readonly id: string
  readonly name: string
}
class GetUserError {
  readonly _tag = "GetUserError"
}
```

Use explicit concurrency. Batching is most useful when multiple requests are allowed to be discovered before the resolver runs.

## Request Cache

Effect has a request cache separate from `Cache.make`. It deduplicates identical requests within a program when request caching is enabled.

```typescript
import { Effect, Request } from "effect"

const program = Effect.gen(function* () {
  const a = yield* getUserById("user-1")
  const b = yield* getUserById("user-1")
  yield* Effect.logInfo("Duplicate request can be cached", { a, b })
}).pipe(
  Effect.withRequestCaching(true)
)

const withCustomRequestCache = Effect.gen(function* () {
  const requestCache = yield* Request.makeCache({
    capacity: 256,
    timeToLive: "1 minute"
  })

  return program.pipe(Effect.withRequestCache(requestCache))
})

declare const getUserById: (id: string) => Effect.Effect<User, GetUserError>
interface User {
  readonly id: string
}
class GetUserError {
  readonly _tag = "GetUserError"
}
```

Use `Effect.withRequestCaching(false)` for code paths where every request must be reissued.

## Completing Requests

Inside resolvers, complete every request with one of:

- `Request.succeed(request, value)`
- `Request.fail(request, error)`
- `Request.complete(request, exit)`
- `Request.completeEffect(request, effect)`

`Request.completeEffect` is usually easiest because it lets you preserve typed success and failure in normal Effect style.

## Resolver Combinators

Useful v3 resolver combinators:

| Combinator | Use |
|---|---|
| `RequestResolver.batchN(n)` | Limit resolver parallelism |
| `RequestResolver.around(before, after)` | Run setup and teardown around resolver execution |
| `RequestResolver.aroundRequests(before, after)` | Observe the request list around execution |
| `RequestResolver.contextFromServices(...)` | Build resolver context from services |
| `RequestResolver.provideContext(context)` | Provide resolver requirements |
| `RequestResolver.race(that)` | Race resolvers and use the first completion |

## Anti-patterns

- Do not write `Effect.forEach(ids, fetchUserById)` when the backend supports batch fetch.
- Do not call a separate SQL query per request inside `makeBatched`.
- Do not leave missing users unresolved; complete each request with a typed failure.
- Do not use `Cache.make` when the actual goal is to combine N ids into one query.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-cache-make.md](02-cache-make.md), [04-effect-cached.md](04-effect-cached.md), [06-keyed-pool.md](06-keyed-pool.md)
