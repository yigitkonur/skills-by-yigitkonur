# FetchHttpClient Layer
Provide `FetchHttpClient.layer` when your runtime has `globalThis.fetch` and you need an implementation of the `HttpClient` service.

## What the layer provides

`FetchHttpClient.layer` is a `Layer` that provides `HttpClient.HttpClient`. It delegates transport to `globalThis.fetch`, so it works in runtimes where fetch is already available.

```typescript
import { FetchHttpClient, HttpClient } from "@effect/platform"
import { Effect } from "effect"

const program = HttpClient.get("https://api.example.com/health").pipe(
  Effect.flatMap((response) => response.text),
  Effect.provide(FetchHttpClient.layer)
)
```

The layer is the boundary between platform-neutral Effect code and the runtime's HTTP implementation. Application services should depend on `HttpClient.HttpClient`, not on a concrete fetch function.

## Basic dependency shape

An outbound HTTP service normally looks like this:

```typescript
import {
  FetchHttpClient,
  HttpClient,
  HttpClientRequest,
  HttpClientResponse
} from "@effect/platform"
import { Effect, Schema } from "effect"

const Profile = Schema.Struct({
  id: Schema.String,
  displayName: Schema.String
})

class Profiles extends Effect.Service<Profiles>()("Profiles", {
  dependencies: [FetchHttpClient.layer],
  effect: Effect.gen(function* () {
    const httpClient = yield* HttpClient.HttpClient
    const apiClient = httpClient.pipe(
      HttpClient.filterStatusOk,
      HttpClient.mapRequest(
        HttpClientRequest.prependUrl("https://profiles.example.com")
      )
    )

    const get = (id: string) =>
      apiClient.get(`/profiles/${id}`).pipe(
        Effect.flatMap(HttpClientResponse.schemaBodyJson(Profile))
      )

    return { get } as const
  })
}) {}
```

This keeps all outbound calls inside the service, while the dependency list clearly says which platform implementation is required.

## Custom fetch implementation

`FetchHttpClient` exposes a `Fetch` tag. Provide it when tests, edge runtimes, or instrumentation need a specific fetch implementation.

```typescript
import { FetchHttpClient, HttpClient } from "@effect/platform"
import { Effect } from "effect"

const fakeFetch: typeof globalThis.fetch = (_input, _init) =>
  Promise.resolve(
    new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" }
    })
  )

const program = HttpClient.get("https://api.example.com/status").pipe(
  Effect.flatMap((response) => response.json),
  Effect.provide(FetchHttpClient.layer),
  Effect.provideService(FetchHttpClient.Fetch, fakeFetch)
)
```

The custom service replaces only the fetch function. The rest of the client behavior still comes from `FetchHttpClient.layer`.

## Custom RequestInit

`FetchHttpClient.RequestInit` lets you provide default fetch options. The source exposes it as a context tag for `globalThis.RequestInit`.

```typescript
import { FetchHttpClient, HttpClient } from "@effect/platform"
import { Effect } from "effect"

const program = HttpClient.get("https://api.example.com/redirect").pipe(
  Effect.flatMap((response) => Effect.logInfo(response.status)),
  Effect.provide(FetchHttpClient.layer),
  Effect.provideService(FetchHttpClient.RequestInit, {
    redirect: "manual"
  })
)
```

Use this for transport-level defaults such as redirect behavior. Put business headers, auth headers, base URLs, and query parameters on `HttpClientRequest` transformations instead.

## Layer placement

Provide the layer near the application edge:

```typescript
import { FetchHttpClient, HttpClient } from "@effect/platform"
import { Effect } from "effect"

const callExternal = HttpClient.get("https://api.example.com/health").pipe(
  Effect.flatMap((response) => response.text)
)

const runnable = callExternal.pipe(
  Effect.provide(FetchHttpClient.layer)
)
```

Inside reusable services, leave the requirement visible unless the service is intentionally platform-bound. This makes tests and alternate runtime layers easy to substitute.

## When not to use it

Use a runtime-specific client layer when the platform package offers one and you need its behavior. For example, Node projects may choose a Node-specific implementation from `@effect/platform-node`. This reference focuses on the strict platform `FetchHttpClient.layer` source because it is the common implementation shipped in `@effect/platform`.

Use `HttpApiClient.make` on top of whichever `HttpClient` implementation you provide. The typed client still needs a transport layer.

## Testing pattern

A fake fetch gives deterministic tests without leaving Effect:

```typescript
import { FetchHttpClient, HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const Status = Schema.Struct({
  ok: Schema.Boolean
})

const fetchOk: typeof globalThis.fetch = () =>
  Promise.resolve(
    new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" }
    })
  )

const testProgram = HttpClient.get("https://service.test/status").pipe(
  Effect.flatMap(HttpClientResponse.schemaBodyJson(Status)),
  Effect.provide(FetchHttpClient.layer),
  Effect.provideService(FetchHttpClient.Fetch, fetchOk)
)
```

This tests request construction, response decoding, and the fetch layer boundary without relying on external network state.

## Common mistakes

- Do not call `globalThis.fetch` directly in services that otherwise use Effect.
- Do not provide `FetchHttpClient.layer` inside every helper function; provide it once at the edge or in a service dependency list.
- Do not put base URLs into the layer. Use `HttpClient.mapRequest(HttpClientRequest.prependUrl(...))`.
- Do not assume status codes fail automatically. Add `HttpClient.filterStatusOk` or decode with explicit status handling.
- Do not use `FetchHttpClient.RequestInit` for per-request domain data. Build those fields into the request.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-request-building.md](03-request-building.md), [05-derived-client.md](05-derived-client.md), [07-request-tracing.md](07-request-tracing.md).
