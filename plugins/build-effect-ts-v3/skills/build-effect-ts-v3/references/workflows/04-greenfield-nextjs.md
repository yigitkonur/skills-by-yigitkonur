# Greenfield Next.js
Build a Next.js app with Effect v3 services, route-handler runtimes, Schema validation, and test layer overrides.

Use this when the project needs React UI plus server-side route handlers. The critical rule is to create a server runtime at module scope and run request Effects through that runtime, instead of constructing layers inside every handler.

## Primitive index

| Primitive | Read first |
|---|---|
| managed runtime and `Effect.runtime` | [services-layers](../services-layers/14-managed-runtime.md), [core](../core/03-running-effects.md) |
| route input validation with Schema | [schema](../schema/02-schema-struct.md), [schema](../schema/10-decoding.md), [error-handling](../error-handling/03-schema-tagged-error.md) |
| services and layer composition | [services-layers](../services-layers/03-effect-service.md), [services-layers](../services-layers/10-layer-provide.md), [services-layers](../services-layers/15-effect-provide.md) |
| frontend atom bridge | [frontend-atom](../frontend-atom/11-effect-runtime-bridge.md), [frontend-atom](../frontend-atom/05-react-hooks.md) |
| HTTP client, config, tests | [http-client](../http-client/03-request-building.md), [config](../config/02-basic-config.md), [testing](../testing/08-test-layers.md) |

## 1. Package setup

```typescript
{
  "type": "module",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest"
  },
  "dependencies": {
    "effect": "^3.21.2",
    "next": "^16.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@effect/vitest": "^0.28.0",
    "typescript": "^5.9.0",
    "vitest": "^4.0.0"
  }
}
```

## 2. Entry point

`src/effect-runtime.ts` builds a runtime from layers once. Route handlers import `runPromise`.

```typescript
import { ManagedRuntime } from "effect"
import { Notes } from "./notes.js"

export const runtime = ManagedRuntime.make(Notes.Default)
export const runPromise = runtime.runPromise
```

For edge runtime deployments, verify every dependency is edge-compatible before using Node-only packages. If a route needs per-request scoped resources, wrap the program in `Effect.scoped`.

## 3. Main Effect orchestration

`app/api/notes/route.ts` decodes input, calls the service, and maps failures to `Response`.

```typescript
import { Effect, Schema } from "effect"
import { runPromise } from "../../../src/effect-runtime.js"
import { CreateNote, Notes, NoteNotFound } from "../../../src/notes.js"

const decodeCreate = Schema.decodeUnknown(CreateNote)

const toJson = (status: number, body: unknown) =>
  Response.json(body, { status })

export const GET = () =>
  runPromise(
    Effect.gen(function*() {
      const notes = yield* Notes
      const items = yield* notes.list
      return toJson(200, items)
    })
  )

export const POST = (request: Request) =>
  runPromise(
    Effect.gen(function*() {
      const body = yield* Effect.promise(() => request.json())
      const input = yield* decodeCreate(body)
      const notes = yield* Notes
      const created = yield* notes.create(input)
      return toJson(201, created)
    }).pipe(
      Effect.catchTags({
        ParseError: () => Effect.succeed(toJson(400, { error: "invalid payload" })),
        NoteNotFound: (error: NoteNotFound) => Effect.succeed(toJson(404, error))
      })
    )
  )
```

Keep `Response` construction at the route edge. Services return domain data and typed failures.

## 4. Per-feature service definitions

`src/notes.ts` is framework-independent.

```typescript
import { Effect, Ref, Schema } from "effect"

export class Note extends Schema.Class<Note>("Note")({
  id: Schema.String,
  title: Schema.String,
  body: Schema.String
}) {}

export class CreateNote extends Schema.Class<CreateNote>("CreateNote")({
  title: Schema.String,
  body: Schema.String
}) {}

export class NoteNotFound extends Schema.TaggedError<NoteNotFound>()("NoteNotFound", {
  id: Schema.String
}) {}

export class Notes extends Effect.Service<Notes>()("app/Notes", {
  effect: Effect.gen(function*() {
    const store = yield* Ref.make(new Map<string, Note>())

    const list = Ref.get(store).pipe(Effect.map((notes) => [...notes.values()]))

    const create = (input: CreateNote) =>
      Effect.gen(function*() {
        const id = `note-${Date.now()}`
        const note = new Note({ id, ...input })
        yield* Ref.update(store, (notes) => new Map(notes).set(id, note))
        return note
      })

    const get = (id: string) =>
      Ref.get(store).pipe(
        Effect.flatMap((notes) => {
          const note = notes.get(id)
          return note ? Effect.succeed(note) : Effect.fail(new NoteNotFound({ id }))
        })
      )

    return { list, create, get } as const
  })
}) {}
```

## 5. Layer wiring

The first version has one service. Add database, config, and logger layers without changing route handlers.

```typescript
import { Config, Effect } from "effect"
import { Notes } from "./notes.js"

export const AppConfig = Config.string("APP_NAME").pipe(Config.withDefault("notes"))
export const loadAppName = Effect.config(AppConfig)
export const AppLayer = Notes.Default
```

In real projects, model configuration as a service instead of passing plain strings around. Use [config providers](../config/08-config-providers.md) when deploying to platforms with nonstandard config sources.

## 6. Test layer override

Route tests can replace the runtime module or call the service program directly with an override.

```typescript
import { it } from "@effect/vitest"
import { Effect, Layer } from "effect"
import { CreateNote, Note, Notes } from "../src/notes.js"

const NotesTest = Layer.succeed(Notes, {
  list: Effect.succeed([new Note({ id: "n1", title: "Test", body: "Body" })]),
  create: (input: CreateNote) => Effect.succeed(new Note({ id: "n2", ...input })),
  get: (id: string) => Effect.succeed(new Note({ id, title: "Test", body: "Body" }))
})

it.effect("lists notes through the service", () =>
  Effect.gen(function*() {
    const notes = yield* Notes
    const items = yield* notes.list
    expect(items[0]?.id).toBe("n1")
  }).pipe(Effect.provide(NotesTest))
)
```

For route-handler integration tests, call `GET()` or `POST(request)` and inspect the returned `Response`. Keep service tests more numerous than HTTP edge tests.

## Workflow checklist

1. Keep the runtime in one module.
2. Build the runtime from layers, not from raw constructors.
3. Keep each route handler as a thin edge adapter.
4. Decode request bodies with Schema.
5. Return framework `Response` values only at the edge.
6. Keep services framework-independent.
7. Keep typed errors in services and mapping in routes.
8. Use `Effect.scoped` for per-request resources.
9. Keep browser components separate from server services.
10. Use Effect Atom only on the client side.
11. Add route tests for status-code mapping.
12. Add service tests for business behavior.
13. Review edge compatibility before deploying route handlers to edge.
14. Keep database layers out of client bundles.

## 7. Deployment

Deploy the app with the platform's normal Next.js adapter. Serverless handlers may reuse module-scope runtimes between invocations, so keep runtime construction pure and layer-managed. When using a database layer, make it scoped and rely on the runtime to close resources during platform teardown where supported.

## Cross-references

See also: [React SPA](03-greenfield-react-spa.md), [HTTP API](02-greenfield-http-api.md), [AI agent](09-ai-agent.md), [managed runtime](../services-layers/14-managed-runtime.md).
