# Greenfield React SPA
Build a React SPA that uses Effect v3 services, Effect Atom state, Schema decoding, and replaceable test layers.

Use this when the app is client-side only and needs typed data loading, local state, and mutations. The key move is to keep Effects and services outside components, then bridge them into React through Effect Atom.

## Primitive index

| Primitive | Read first |
|---|---|
| atoms, atom families, React hooks | [frontend-atom](../frontend-atom/02-atom-make.md), [frontend-atom](../frontend-atom/03-atom-families.md), [frontend-atom](../frontend-atom/05-react-hooks.md) |
| mutations, cache invalidation, runtime bridge | [frontend-atom](../frontend-atom/08-mutations.md), [frontend-atom](../frontend-atom/09-cache-invalidation.md), [frontend-atom](../frontend-atom/11-effect-runtime-bridge.md) |
| HTTP client and schema body decoding | [http-client](../http-client/02-fetch-http-client.md), [http-client](../http-client/04-response-decoding.md), [schema](../schema/10-decoding.md) |
| services, layers, errors | [services-layers](../services-layers/03-effect-service.md), [services-layers](../services-layers/14-managed-runtime.md), [error-handling](../error-handling/04-catch-tag.md) |
| Option and UI state | [data-types](../data-types/02-option.md), [state](../state/02-ref.md), [testing](../testing/10-spy-layers.md) |

## 1. Package setup

```typescript
{
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest"
  },
  "dependencies": {
    "@effect-atom/atom-react": "^0.54.0",
    "@effect/platform": "^0.95.0",
    "@effect/platform-browser": "^0.71.0",
    "effect": "^3.21.2",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.0.0",
    "typescript": "^5.9.0",
    "vite": "^7.0.0",
    "vitest": "^4.0.0"
  }
}
```

## 2. Entry point

`src/main.tsx` creates the React root and provides the Effect Atom runtime layer. The runtime is built once at the application boundary.

```typescript
import { Atom, RegistryProvider } from "@effect-atom/atom-react"
import { createRoot } from "react-dom/client"
import { App } from "./ui.js"
import { AppLayer, runtime } from "./runtime.js"

createRoot(document.getElementById("root")!).render(
  <RegistryProvider initialValues={[Atom.initialValue(runtime.layer, AppLayer)]}>
    <App />
  </RegistryProvider>
)
```

`src/runtime.ts` exports the atom runtime for atom modules.

```typescript
import { FetchHttpClient } from "@effect/platform"
import { Atom } from "@effect-atom/atom-react"
import { Layer } from "effect"
import { TodoClient } from "./services.js"

export const AppLayer = Layer.merge(TodoClient.Default, FetchHttpClient.layer)
export const runtime = Atom.runtime(AppLayer)
```

If the bundler does not support JSX in `main.tsx`, keep the same code in `main.jsx` and import typed modules from TypeScript files. Keep `Effect.runPromise` out of components; the runtime bridge owns execution.

## 3. Main Effect orchestration

`src/atoms.ts` turns service calls into component-readable atoms. Components subscribe; services do the work.

```typescript
import { Effect } from "effect"
import { runtime } from "./runtime.js"
import { TodoClient } from "./services.js"

export const todosAtom = runtime.atom(
  Effect.gen(function*() {
    const client = yield* TodoClient
    return yield* client.list
  })
)

export const createTodoAtom = runtime.fn((title: string) =>
  Effect.gen(function*() {
    const client = yield* TodoClient
    const created = yield* client.create(title)
    return created
  }),
  { reactivityKeys: ["todos"] }
)

export const emptyTodos: readonly [] = []
```

Do not store `null` while loading. Use atom result states or [Option](../data-types/02-option.md) for optional domain values.

## 4. Per-feature service definitions

`src/services.ts` wraps the remote API and decodes payloads with Schema.

```typescript
import { HttpClient, HttpClientRequest, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

export class Todo extends Schema.Class<Todo>("Todo")({
  id: Schema.String,
  title: Schema.String,
  completed: Schema.Boolean
}) {}

export class TodoClient extends Effect.Service<TodoClient>()("app/TodoClient", {
  effect: Effect.gen(function*() {
    const http = yield* HttpClient.HttpClient
    const api = http.pipe(
      HttpClient.filterStatusOk,
      HttpClient.mapRequest(HttpClientRequest.prependUrl("/api"))
    )

    const list = api.get("/todos").pipe(
      Effect.flatMap(HttpClientResponse.schemaBodyJson(Schema.Array(Todo))),
      Effect.scoped
    )

    const create = (title: string) =>
      api.post("/todos", { body: HttpClientRequest.bodyUnsafeJson({ title }) }).pipe(
        Effect.flatMap(HttpClientResponse.schemaBodyJson(Todo)),
        Effect.scoped
      )

    return { list, create } as const
  })
}) {}
```

If the SPA talks to an external API, prepend the full URL from `Config.string("API_BASE_URL")` in a layer and keep the component code unchanged.

## 5. Layer wiring

The live graph is browser HTTP plus the feature service.

```typescript
import { FetchHttpClient } from "@effect/platform"
import { Layer } from "effect"
import { TodoClient } from "./services.js"

export const AppLayer = Layer.merge(TodoClient.Default, FetchHttpClient.layer)
```

When adding feature modules, compose one service per API area and merge them at the runtime provider. Do not let React components import platform clients directly.

## 6. Test layer override

Override `TodoClient` for component tests and atom tests. This avoids mocking `fetch`.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect, Layer } from "effect"
import { Todo, TodoClient } from "../src/services.js"

export const TodoClientTest = Layer.succeed(TodoClient, {
  list: Effect.succeed([
    new Todo({ id: "t1", title: "Write docs", completed: false })
  ]),
  create: (title) =>
    Effect.succeed(new Todo({ id: "t2", title, completed: false }))
})

export const testRuntime = Atom.runtime(TodoClientTest)
```

In component tests, initialize the registry with `Atom.initialValue(testRuntime.layer, TodoClientTest)`. Use [spy layers](../testing/10-spy-layers.md) when assertions need to prove a mutation was invoked.

## Workflow checklist

1. Put schemas and services outside React components.
2. Create the runtime once at the root.
3. Provide browser HTTP at the runtime edge.
4. Keep atoms as thin Effect wrappers around services.
5. Keep mutations invalidating the atoms they affect.
6. Use Schema decoding for every remote response.
7. Keep optional UI domain state out of `null`.
8. Use atom loading and failure states in components.
9. Avoid calling platform clients from components.
10. Keep local storage atoms separate from remote data atoms.
11. Add a test layer for each remote service.
12. Use spy layers for mutation assertions.
13. Keep Vite config ordinary unless Effect-specific needs appear.
14. Keep development proxying outside the service code.
15. Model API base URL as config when it changes by environment.
16. Decode bootstrap config before creating the runtime.
17. Test atom behavior before broad component snapshots.
18. Keep component text independent from Effect internals.
19. Use `Effect.scoped` around HTTP response body decoding.
20. Keep cache invalidation explicit.
21. Add atom families only for keyed resources.
22. Review [keep alive](../frontend-atom/04-keep-alive.md) before pinning atoms.
23. Review [local storage atoms](../frontend-atom/10-atoms-with-localstorage.md) before persisting state.
24. Build once before deployment.
25. Keep this workflow client-only; use the Next.js workflow for server handlers.

## 7. Deployment

Build with Vite and serve static assets from any CDN or static host. If the SPA reads runtime configuration, load a JSON bootstrap document and decode it with Schema before creating the runtime. For browser-only deployments, prefer `FetchHttpClient.layer`; Node platform layers belong in SSR, tests, or build scripts.

## Cross-references

See also: [Next.js fullstack](04-greenfield-nextjs.md), [AI agent](09-ai-agent.md), [adding Effect to existing code](05-adding-effect-existing.md), [frontend atom overview](../frontend-atom/01-overview.md).
