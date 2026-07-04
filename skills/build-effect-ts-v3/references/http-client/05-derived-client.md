# Derived HttpApi Client
Use `HttpApiClient.make` to derive a typed client from the same `HttpApi` contract used by the server.

## Why it matters

`HttpApiClient.make(api, { baseUrl })` turns an `HttpApi` definition into a client object whose groups, endpoint names, path parameters, query parameters, payloads, headers, success values, and errors come from the contract.

```typescript
import {
  FetchHttpClient,
  HttpApi,
  HttpApiClient,
  HttpApiEndpoint,
  HttpApiGroup
} from "@effect/platform"
import { Effect, Schema } from "effect"

const User = Schema.Struct({
  id: Schema.String,
  name: Schema.String
})

const UsersApi = HttpApi.make("UsersApi").add(
  HttpApiGroup.make("users").add(
    HttpApiEndpoint.get("getUser", "/users/:id")
      .setPath(Schema.Struct({ id: Schema.String }))
      .addSuccess(User)
  )
)

const program = Effect.gen(function* () {
  const client = yield* HttpApiClient.make(UsersApi, {
    baseUrl: "https://api.example.com"
  })

  return yield* client.users.getUser({
    path: { id: "user-1" }
  })
}).pipe(Effect.provide(FetchHttpClient.layer))
```

The method call is typed from the endpoint. If the endpoint requires path params, payload, URL params, or headers, the client method requires them.

## Contract-first shape

The same `HttpApi` should define server and client behavior. Build the contract once:

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

const CreateUser = Schema.Struct({
  name: Schema.String
})

const User = Schema.Struct({
  id: Schema.String,
  name: Schema.String
})

export const UsersApi = HttpApi.make("UsersApi").add(
  HttpApiGroup.make("users").add(
    HttpApiEndpoint.post("createUser", "/users")
      .setPayload(CreateUser)
      .addSuccess(User, { status: 201 })
  )
)
```

The server mission implements that API with `HttpApiBuilder`. The client mission consumes it with `HttpApiClient.make`. See [../http-server/01-overview.md](../http-server/01-overview.md) for the server side of the same contract model.

## Client object shape

Non-top-level groups become nested properties:

```typescript
const user = yield* client.users.createUser({
  payload: { name: "Ada" }
})
```

Top-level groups expose methods directly on the client object. Most APIs should use named groups because they scale better and mirror server routing.

## Request fields

The generated method request type is assembled from endpoint schemas:

| Endpoint schema | Client request field |
|---|---|
| `setPath` | `path` |
| `setUrlParams` | `urlParams` |
| `setPayload` | `payload` |
| `setHeaders` | `headers` |

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

const Search = Schema.Struct({
  q: Schema.String,
  page: Schema.optional(Schema.NumberFromString)
})

const SearchResult = Schema.Struct({
  total: Schema.Number
})

const SearchApi = HttpApi.make("SearchApi").add(
  HttpApiGroup.make("search").add(
    HttpApiEndpoint.get("searchUsers", "/users")
      .setUrlParams(Search)
      .addSuccess(SearchResult)
  )
)
```

Calling `client.search.searchUsers` now requires `urlParams`.

```typescript
const result = yield* client.search.searchUsers({
  urlParams: { q: "effect", page: 1 }
})
```

For GET and HEAD endpoints, payload schemas are encoded as URL parameters. For methods with request bodies, payload schemas are encoded according to the endpoint payload encoding.

## Base URL

`baseUrl` prepends a URL to every generated request:

```typescript
import { FetchHttpClient, HttpApiClient } from "@effect/platform"
import { Effect } from "effect"

declare const UsersApi: typeof import("./api.js").UsersApi

const program = Effect.gen(function* () {
  const client = yield* HttpApiClient.make(UsersApi, {
    baseUrl: "https://api.example.com/v1"
  })

  return yield* client.users.createUser({
    payload: { name: "Ada" }
  })
}).pipe(Effect.provide(FetchHttpClient.layer))
```

Use `baseUrl` for the remote origin and prefix. Do not also prepend the same base URL with `HttpClient.mapRequest`.

## Transform the underlying client

`transformClient` lets you apply normal `HttpClient` transformations before the generated client sends requests.

```typescript
import {
  FetchHttpClient,
  HttpApiClient,
  HttpClient,
  HttpClientRequest
} from "@effect/platform"
import { Effect } from "effect"

declare const UsersApi: typeof import("./api.js").UsersApi

const program = Effect.gen(function* () {
  const client = yield* HttpApiClient.make(UsersApi, {
    baseUrl: "https://api.example.com",
    transformClient: (httpClient) =>
      httpClient.pipe(
        HttpClient.filterStatusOk,
        HttpClient.mapRequest(
          HttpClientRequest.setHeader("x-client", "worker")
        )
      )
  })

  return yield* client.users.createUser({
    payload: { name: "Ada" }
  })
}).pipe(Effect.provide(FetchHttpClient.layer))
```

Use this for shared headers, tracing policy, retry policy, cookies, status filtering, or request logging.

## Transform response decoding

`transformResponse` wraps the generated decode effect. It is useful for cross-cutting response logic, but keep it narrow because it runs after the raw response is received and before the generated method returns.

```typescript
import { HttpApiClient } from "@effect/platform"
import { Effect } from "effect"

declare const UsersApi: typeof import("./api.js").UsersApi

const makeClient = HttpApiClient.make(UsersApi, {
  baseUrl: "https://api.example.com",
  transformResponse: (effect) =>
    effect.pipe(
      Effect.tap(() => Effect.logInfo("decoded http api response"))
    )
})
```

Do not use `transformResponse` to guess around schema failures. Fix the shared contract or model a documented compatibility branch.

## `makeWith`, `group`, and `endpoint`

Use `make` for normal application code. Reach for lower-level constructors only when you have a concrete need:

| Constructor | Use |
|---|---|
| `make` | Build the whole client from the `HttpClient` service |
| `makeWith` | Build the whole client from an already transformed client value |
| `group` | Build one group from a large API |
| `endpoint` | Build one endpoint function |

These helpers preserve the same request and response types. They just choose how much of the reflected API becomes a value.

## Error surface

Generated methods can fail with:

- endpoint error schemas
- group error schemas
- API error schemas
- `HttpApiDecodeError` from request decoding metadata
- `HttpClientError.HttpClientError`
- `ParseResult.ParseError`

Treat those as the contract. Avoid remapping everything into a string at the client boundary; callers lose the ability to recover by tag or by status.

## Common mistakes

- Do not rebuild endpoint paths by hand once an `HttpApi` exists.
- Do not keep server and client schemas in separate files that drift from each other.
- Do not put a second base URL into `transformClient`.
- Do not ignore typed endpoint errors; they are part of the API contract.
- Do not use a derived client without providing an `HttpClient` implementation layer.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-fetch-http-client.md](02-fetch-http-client.md), [06-retries-and-timeouts.md](06-retries-and-timeouts.md), [../http-server/01-overview.md](../http-server/01-overview.md).
