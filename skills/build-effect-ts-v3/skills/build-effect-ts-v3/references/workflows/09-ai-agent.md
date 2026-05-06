# AI Agent
Build an Effect v3 AI agent with tool services, Schema-defined inputs, `Schema.standardSchemaV1`, and test overrides.

Use this when an application needs LLM calls with typed tool use. This workflow shows both Effect-native tool services and Standard Schema v1 export for libraries such as the Vercel AI SDK.

## Primitive index

| Primitive | Read first |
|---|---|
| `@effect/ai` toolkits and language model | [frontend atom Vercel AI SDK](../frontend-atom/12-vercel-ai-sdk.md), [schema](../schema/14-annotations.md), [schema](../schema/15-json-schema.md) |
| `Schema.standardSchemaV1` | [frontend atom Vercel AI SDK](../frontend-atom/12-vercel-ai-sdk.md), [schema](../schema/10-decoding.md), [schema](../schema/13-filters.md) |
| services, layers, config | [services-layers](../services-layers/03-effect-service.md), [services-layers](../services-layers/11-layer-providemerge.md), [config](../config/03-config-redacted.md) |
| HTTP client and observability | [http-client](../http-client/02-fetch-http-client.md), [observability](../observability/07-span-scoped.md), [observability](../observability/10-metric-tagged.md) |
| tests and anti-patterns | [testing](../testing/10-spy-layers.md), [anti-patterns](../anti-patterns/18-ai-hallucinations.md), [anti-patterns](../anti-patterns/05-unbounded-parallelism.md) |

## 1. Package setup

```typescript
{
  "type": "module",
  "scripts": {
    "dev": "tsx src/main.ts",
    "build": "tsc -p tsconfig.json",
    "test": "vitest"
  },
  "dependencies": {
    "@effect/ai": "^0.30.0",
    "@effect/ai-openai": "^0.30.0",
    "@effect/platform": "^0.95.0",
    "@effect/platform-node": "^0.90.0",
    "ai": "^5.0.0",
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

`src/main.ts` runs one prompt from the command line. Server apps can reuse the same layer graph from a route handler runtime.

```typescript
import { NodeHttpClient, NodeRuntime } from "@effect/platform-node"
import { OpenAiClient, OpenAiLanguageModel } from "@effect/ai-openai"
import { Config, Effect, Layer } from "effect"
import { Agent } from "./agent.js"
import { SearchToolsLive } from "./tools.js"

const OpenAi = OpenAiClient.layerConfig({
  apiKey: Config.redacted("OPENAI_API_KEY")
}).pipe(Layer.provide(NodeHttpClient.layerUndici))

const Model = OpenAiLanguageModel.model("gpt-4o-mini")

Agent.answer("Find a concise Effect v3 migration checklist").pipe(
  Effect.provide(Agent.Default),
  Effect.provide(SearchToolsLive),
  Effect.provide(NodeHttpClient.layerUndici),
  Effect.provide(Model),
  Effect.provide(OpenAi),
  NodeRuntime.runMain
)
```

Use `Config.redacted` for provider credentials. Keep model selection at the layer edge so tests can replace it.

## 3. Main Effect orchestration

`src/agent.ts` coordinates the model call and tool set.

```typescript
import { LanguageModel } from "@effect/ai"
import { Effect } from "effect"
import { SearchToolkit } from "./tools.js"

export class Agent extends Effect.Service<Agent>()("app/Agent", {
  effect: Effect.gen(function*() {
    const answer = (prompt: string) =>
      LanguageModel.generateText({
        prompt,
        toolkit: SearchToolkit
      }).pipe(
        Effect.map((response) => response.text),
        Effect.withSpan("Agent.answer")
      )

    return { answer } as const
  })
}) {}
```

Keep prompt construction in the agent service. Keep external data access in tools.

## 4. Per-feature service definitions

`src/tools.ts` defines a tool once, exports a Standard Schema v1 object for non-Effect tool adapters, and implements handlers through a layer.

```typescript
import { Tool, Toolkit } from "@effect/ai"
import { HttpClient, HttpClientRequest, HttpClientResponse } from "@effect/platform"
import { Effect, Layer, Schema } from "effect"

export class SearchInput extends Schema.Class<SearchInput>("SearchInput")({
  query: Schema.String.annotations({ description: "Search query" }),
  limit: Schema.Number.pipe(Schema.between(1, 5)).annotations({ description: "Maximum result count" })
}) {}

export const SearchInputStandard = Schema.standardSchemaV1(SearchInput)

export class SearchHit extends Schema.Class<SearchHit>("SearchHit")({
  title: Schema.String,
  url: Schema.String
}) {}

const Search = Tool.make("Search", {
  description: "Search internal documentation",
  success: Schema.Array(SearchHit),
  failure: Schema.Never,
  parameters: {
    query: Schema.String.annotations({ description: "Search query" }),
    limit: Schema.Number.pipe(Schema.between(1, 5)).annotations({ description: "Maximum result count" })
  }
})

export const SearchToolkit = Toolkit.make(Search)

export class SearchBackend extends Effect.Service<SearchBackend>()("app/SearchBackend", {
  effect: Effect.gen(function*() {
    const http = yield* HttpClient.HttpClient
    const client = http.pipe(HttpClient.mapRequest(HttpClientRequest.prependUrl("https://example.com")))
    return {
      search: (input: SearchInput) =>
        client.get("/search", { urlParams: { q: input.query, limit: String(input.limit) } }).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(Schema.Array(SearchHit))),
          Effect.scoped,
          Effect.orDie
        )
    } as const
  })
}) {}

export const SearchToolsLive = SearchToolkit.toLayer(
  Effect.gen(function*() {
    const backend = yield* SearchBackend
    return {
      Search: (input: SearchInput) => backend.search(input)
    }
  })
).pipe(Layer.provide(SearchBackend.Default))
```

`SearchInputStandard` is the adapter point for Vercel AI SDK tools. See [Vercel AI SDK bridge](../frontend-atom/12-vercel-ai-sdk.md) before mixing Effect tools and non-Effect tool runtimes.

## 5. Layer wiring

```typescript
import { NodeHttpClient } from "@effect/platform-node"
import { Layer } from "effect"
import { Agent } from "./agent.js"
import { SearchBackend, SearchToolsLive } from "./tools.js"

export const AgentLayer = Layer.mergeAll(
  Agent.Default,
  SearchToolsLive,
  SearchBackend.Default,
  NodeHttpClient.layerUndici
)
```

Provider-specific language-model layers are supplied by the entry point. That keeps the agent testable without network calls.

## 6. Test layer override

Override the tool handler layer or the backend service. Tool tests should not call a live model.

```typescript
import { it } from "@effect/vitest"
import { Effect, Layer } from "effect"
import { SearchBackend, SearchInput, SearchHit, SearchInputStandard } from "../src/tools.js"

const SearchBackendTest = Layer.succeed(SearchBackend, {
  search: (input: SearchInput) =>
    Effect.succeed([
      new SearchHit({ title: input.query, url: "https://example.test/result" })
    ])
})

it.effect("validates tool input through Standard Schema", () =>
  Effect.sync(() => SearchInputStandard["~standard"].validate({ query: "effect", limit: 2 })).pipe(
    Effect.map((result) => expect("value" in result).toBe(true))
  )
)
```

For agent tests, replace `LanguageModel` with a deterministic model layer if the package exposes one, or test prompt/tool orchestration separately. Keep live-provider tests opt-in.

## 7. Deployment

Deploy the agent where outbound HTTP calls and model-provider credentials are supported. Route handlers should create a managed runtime once and run each prompt through that runtime, while CLI tools can use `NodeRuntime.runMain`. For production, record tool latency and model failures with spans and metrics because tool orchestration can fail independently of the model call.

## Cross-references

See also: [MCP server](08-mcp-server.md), [Next.js fullstack](04-greenfield-nextjs.md), [React SPA](03-greenfield-react-spa.md), [Vercel AI SDK bridge](../frontend-atom/12-vercel-ai-sdk.md).
