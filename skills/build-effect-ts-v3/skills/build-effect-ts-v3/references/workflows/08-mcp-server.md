# MCP Server
Build an MCP-style JSON-RPC server with Effect v3 services, typed tool errors, per-request scopes, and test overrides.

Use this when a server exposes tools to an MCP client. The essential Effect pattern is `Effect.scoped` around every request so temporary resources are released when the request completes or the client disconnects.

## Primitive index

| Primitive | Read first |
|---|---|
| request scope and finalizers | [resource-management](../resource-management/02-scope.md), [resource-management](../resource-management/05-effect-scoped.md), [resource-management](../resource-management/06-add-finalizer.md) |
| typed errors and pattern matching | [error-handling](../error-handling/02-data-tagged-error.md), [error-handling](../error-handling/04-catch-tag.md), [pattern-matching](../pattern-matching/04-match-tag.md) |
| services and layers | [services-layers](../services-layers/03-effect-service.md), [services-layers](../services-layers/08-layer-scoped.md), [services-layers](../services-layers/17-fresh-vs-memoize.md) |
| schema decoding and logging | [schema](../schema/10-decoding.md), [observability](../observability/03-structured-logs.md), [platform](../platform/12-node-runtime.md) |
| streams and cancellation | [streams](../streams/02-creating-streams.md), [concurrency](../concurrency/11-interruption.md), [testing](../testing/12-testing-resources.md) |

## 1. Package setup

This minimal server uses newline-delimited JSON over standard input and output so the Effect shape is runnable without depending on unstable SDK examples. Replace the transport with the official MCP SDK adapter in production.

```typescript
{
  "type": "module",
  "scripts": {
    "dev": "tsx src/main.ts",
    "build": "tsc -p tsconfig.json",
    "test": "vitest"
  },
  "dependencies": {
    "@effect/platform": "^0.95.0",
    "@effect/platform-node": "^0.90.0",
    "effect": "^3.21.2"
  },
  "devDependencies": {
    "@effect/vitest": "^0.28.0",
    "tsx": "^4.20.0",
    "typescript": "^5.9.0",
    "vitest": "^4.0.0"
  }
}
```

## 2. Entry point

`src/main.ts` runs the transport. The request handler is provided as a service layer.

```typescript
import { NodeRuntime } from "@effect/platform-node"
import { Effect } from "effect"
import { McpTransport } from "./transport.js"
import { Tools } from "./tools.js"

McpTransport.run.pipe(
  Effect.provide(McpTransport.Default),
  Effect.provide(Tools.Default),
  NodeRuntime.runMain
)
```

Keep the transport thin. The handler should accept a request value and return a response value, so SDK transports, stdio transports, and tests all share the same logic.

## 3. Main Effect orchestration

`src/transport.ts` demonstrates the per-request scoping pattern. Each request is wrapped in `Effect.scoped`.

```typescript
import { Effect, Schema } from "effect"
import { Tools } from "./tools.js"

export class McpRequest extends Schema.Class<McpRequest>("McpRequest")({
  id: Schema.Union(Schema.String, Schema.Number),
  method: Schema.String,
  params: Schema.optional(Schema.Unknown)
}) {}

export class McpResponse extends Schema.Class<McpResponse>("McpResponse")({
  id: Schema.Union(Schema.String, Schema.Number),
  result: Schema.optional(Schema.Unknown),
  error: Schema.optional(Schema.Struct({ code: Schema.Number, message: Schema.String }))
}) {}

const decodeRequest = Schema.decodeUnknown(McpRequest)

export const handleRequest = (raw: unknown) =>
  Effect.scoped(
    Effect.gen(function*() {
      const request = yield* decodeRequest(raw)
      const tools = yield* Tools
      yield* Effect.logInfo("mcp request", { method: request.method })
      const result = yield* tools.dispatch(request.method, request.params)
      return new McpResponse({ id: request.id, result })
    }).pipe(
      Effect.catchTag("ParseError", () =>
        Effect.succeed(new McpResponse({ id: "unknown", error: { code: -32600, message: "invalid request" } }))
      ),
      Effect.catchTag("ToolError", (error) =>
        Effect.succeed(new McpResponse({ id: "unknown", error: { code: error.code, message: error.message } }))
      )
    )
  )

export class McpTransport extends Effect.Service<McpTransport>()("app/McpTransport", {
  effect: Effect.succeed({
    run: Effect.logInfo("replace with stdio JSON-RPC loop").pipe(Effect.forever)
  })
}) {}
```

In a real transport, call `handleRequest` for every SDK request. Keep `Effect.scoped` inside `handleRequest`, not around the whole server.

## 4. Per-feature service definitions

`src/tools.ts` owns tool dispatch and resource acquisition.

```typescript
import { Effect, Schema } from "effect"

export class ToolError extends Schema.TaggedError<ToolError>()("ToolError", {
  code: Schema.Number,
  message: Schema.String
}) {}

export class Workspace extends Effect.Service<Workspace>()("app/Workspace", {
  scoped: Effect.gen(function*() {
    yield* Effect.addFinalizer(() => Effect.logInfo("workspace released"))
    return {
      search: (query: string) => Effect.succeed([{ title: "Hit", query }])
    } as const
  })
}) {}

export class Tools extends Effect.Service<Tools>()("app/Tools", {
  effect: Effect.gen(function*() {
    const dispatch = (method: string, params: unknown) =>
      Effect.gen(function*() {
        const workspace = yield* Workspace
        if (method === "tools/search") {
          const query = String((params as { query?: string }).query ?? "")
          return yield* workspace.search(query)
        }
        return yield* Effect.fail(new ToolError({ code: -32601, message: "unknown tool" }))
      }).pipe(Effect.provide(Workspace.Default))

    return { dispatch } as const
  })
}) {}
```

`Workspace.Default` is scoped, so the request scope controls release. This is the pattern from the cached MCP section: every request gets a fresh scope and temporary resources release automatically.

## 5. Layer wiring

```typescript
import { Layer } from "effect"
import { McpTransport } from "./transport.js"
import { Tools } from "./tools.js"

export const ServerLayer = Layer.merge(McpTransport.Default, Tools.Default)
```

If the official SDK owns the transport loop, adapt the SDK callback to `Runtime.runPromise(runtime)(handleRequest(raw))`. Keep the runtime outside the callback and the request scope inside the handler.

## 6. Test layer override

Test dispatch without starting stdio.

```typescript
import { it } from "@effect/vitest"
import { Effect, Layer } from "effect"
import { handleRequest, McpResponse } from "../src/transport.js"
import { Tools } from "../src/tools.js"

const ToolsTest = Layer.succeed(Tools, {
  dispatch: () => Effect.succeed({ ok: true })
})

it.effect("handles one request in a request scope", () =>
  handleRequest({ id: 1, method: "tools/search", params: { query: "effect" } }).pipe(
    Effect.provide(ToolsTest),
    Effect.map((response) => expect(response).toBeInstanceOf(McpResponse))
  )
)
```

Add a resource test that proves finalizers run when a request fails. Use [testing resources](../testing/12-testing-resources.md) for that shape.

## 7. Deployment

For local desktop clients, package the compiled server and configure the client to start it over stdio. For hosted MCP, put the SDK HTTP or streaming transport at the boundary and keep `handleRequest` unchanged. Make request-scoped resources short-lived because clients can disconnect mid-call and interruption should release them immediately.

## Cross-references

See also: [AI agent](09-ai-agent.md), [microservice](06-microservice.md), [background worker](07-background-worker.md), [resource management overview](../resource-management/01-overview.md).
