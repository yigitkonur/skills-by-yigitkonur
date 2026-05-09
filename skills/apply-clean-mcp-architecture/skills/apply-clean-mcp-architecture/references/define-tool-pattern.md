# The `defineTool()` Factory Pattern

> This reference expands the SKILL.md section "Use case <-> MCP tool flow" and the `Where MCP primitives live` table. It is for the `Implementing` mode: an existing clean-architecture repo is adding or auditing a tool. After reading it the agent should know what shape the factory has, where its file lives, what its config object carries, how the registration pipeline wraps it, and how `bootstrap.ts` plugs the result into the `MCPServer`. Schema-authoring rules (`.strict()`, `.describe()`, banning `z.any()` / `z.unknown()`) are deferred to `build-mcp-use-server` — this file owns the *placement* of the schema and the architectural shape of the factory, not the field-level Zod rules.

## Why a factory at all

Direct calls to `server.tool({ ... }, async (args, ctx) => ...)` scattered across feature files are how a server drifts. Each call site forgets one thing: an annotation, an output schema, an error mapper, a logging line. A `defineTool()` factory is the single place where:

- the Zod raw shape is wrapped in `z.object(shape).strict()`
- annotations get sane defaults (`destructiveHint`, `idempotentHint`)
- the optional `outputSchema` falls back to a shared default
- `nextSteps` are dual-rendered into both `structuredContent.nextSteps` and the human-readable text body
- the `execute` function stays raw — middleware (auth, request-context, error mapping, observability, cost-meter) is wrapped at registration, not here

If a handler bypasses the factory and calls `server.tool()` itself, the middleware pipeline cannot wrap it uniformly and every cross-cutting concern degrades to per-handler discipline. That degradation is observable in `mcp-ads-meta/src/tools/*.ts`: each module re-implements its own logging line, its own dry-run wrapper, its own error sanitiser.

## Where it lives

```
src/handlers/
├── define-tool.ts           # The factory itself (this file). One per repo.
├── context.ts               # HandlerContext interface — see references/handler-context.md
├── schemas/                 # Cross-tool field fragments (geo, pagination, filters)
├── shared/                  # Cross-tool helpers (extract-owner, alias map builders)
└── <feature>/
    └── <tool>.handler.ts    # One tool per file. Calls defineTool().
```

The factory file is co-located with handlers because that is the only layer that may import `mcp-use/server` types. It must not move into `infrastructure/`, `application/`, or `shared/`. Keep `define-tool.ts` exactly one file — never split it into a `define-tool/` directory with sub-modules. The factory is small on purpose.

## Canonical signature

The factory accepts a Zod **raw shape** (a `Record<string, ZodTypeAny>`), not a pre-built `z.object()`. That is what lets it apply `.strict()` and inspect field-level metadata uniformly. It returns a typed-erased `DefinedTool<TSchema>` that bootstrap can collect into a heterogeneous array. The `execute` arg type is derived as `z.infer<z.ZodObject<TSchema>>` so call sites get full inference without redeclaring the input type.

```ts
// src/handlers/define-tool.ts
import { z } from 'zod';
import type { ToolAnnotations, ToolDefinition } from 'mcp-use/server';
import type { CallToolResult } from '../shared/types/mcp-types.js';
import type { McpUseToolContext } from '../shared/types/mcp-tool-context.js';
import { ToolResultOutputSchema } from '../presenters/response/response-schema.js';

export interface ToolConfig<TSchema extends z.ZodRawShape> {
  readonly name: string;
  readonly description: string;
  readonly annotations?: ToolAnnotations & Record<string, unknown>;
  readonly outputSchema?: z.ZodTypeAny;
  /** Raw Zod shape — the factory wraps it in z.object().strict(). */
  readonly schema: TSchema;
  readonly nextSteps?: ReadonlyArray<{
    readonly tool: string;
    readonly label: string;
    readonly description?: string;
  }>;
  readonly execute: (
    args: z.infer<z.ZodObject<TSchema>>,
    extra?: McpUseToolContext,
  ) => Promise<CallToolResult>;
}

export interface DefinedTool<TSchema extends z.ZodRawShape> {
  readonly definition: ToolDefinition<z.infer<z.ZodObject<TSchema>>>;
  readonly schema: TSchema;
  readonly metadata: {
    readonly name: string;
    readonly description: string;
    readonly annotations?: ToolAnnotations & Record<string, unknown>;
  };
  readonly TOOL_NAME: string;
  readonly nextSteps: ReadonlyArray<{ tool: string; label: string; description?: string }>;
  readonly execute: (
    args: z.infer<z.ZodObject<TSchema>>,
    extra?: McpUseToolContext,
  ) => Promise<CallToolResult>;
}

// Type erasure for heterogeneous registration arrays. The single `any` here is
// architectural — a closed sum type would grow linearly with every new tool.
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- justified erasure
export type AnyToolDefinition = DefinedTool<any>;

export function defineTool<TSchema extends z.ZodRawShape>(
  config: ToolConfig<TSchema>,
): DefinedTool<TSchema> {
  const annotations = config.annotations === undefined
    ? undefined
    : { destructiveHint: false, ...config.annotations };

  const definition: DefinedTool<TSchema>['definition'] = {
    name: config.name,
    description: config.description,
    schema: z.object(config.schema).strict(),
    outputSchema: config.outputSchema ?? ToolResultOutputSchema,
    ...(annotations !== undefined ? { annotations } : {}),
  };

  return {
    definition,
    schema: config.schema,
    metadata: {
      name: config.name,
      description: config.description,
      ...(annotations !== undefined ? { annotations } : {}),
    },
    TOOL_NAME: config.name,
    nextSteps: config.nextSteps ?? [],
    execute: config.execute,
  };
}
```

A few points on this signature that are non-obvious:

- The generic parameter is `TSchema extends z.ZodRawShape`, not `z.ZodObject<...>`. **Why:** raw-shape generics let the factory wrap the object once and centralise `.strict()`. Pre-built objects bypass that seam.
- `AnyToolDefinition` exists so `bootstrap.ts` can hold heterogeneous tools in one array. **Why:** without erasure the registry would be a sum type that has to be edited every time a tool is added — exactly the file-fan-out the architecture is trying to avoid.
- `execute` is typed to return `CallToolResult`, not `ToolResponse`. **Why:** the presenter has already converted `ToolResponse` to `CallToolResult` by the time `execute` returns. Handlers do that conversion inline (`return presenter.render(domainResponse)`).

## What each config field is for

Each field has one job; conflate them and the factory's purpose collapses.

- `name` — the wire-level tool identifier the LLM client calls. Kebab-case (`analyze-domain`). The exception is when an existing public tool name uses underscores (`execute_query`); preserve it. **Why:** the tool name is API surface; renaming breaks every saved agent prompt.
- `description` — the spec the LLM reads to decide whether to call this tool. Use XML-tagged sections (`<usecase>`, `<when_to_use>`, `<when_not_to_use>`, `<output>`). **Why:** structured descriptions outperform prose in tool-selection accuracy.
- `annotations` — `title`, `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`. State them honestly. A read tool is read-only, idempotent. An export/cancel/cleanup tool is destructive. Lying via the default `destructiveHint: false` for a destructive tool is a security regression. **Why:** MCP clients gate destructive tools behind user confirmation only if the hint is accurate.
- `outputSchema` — the structured contract for clients that consume `structuredContent`. Default to `ToolResultOutputSchema` (the shared envelope under `presenters/response/`). Override only when the tool genuinely returns a different structured shape. **Why:** without `outputSchema`, MCP-aware clients cannot validate, render, or chain the tool's output.
- `schema` — the **raw** Zod shape (a record of fields), not a `z.object()`. Field-level rules belong to `build-mcp-use-server`'s `references/04-tools/`. This skill cares only that the field shape is a raw record so the factory can apply `.strict()`. **Why:** keeps the wrap-and-validate seam in exactly one place.
- `nextSteps` — agent-guidance hints rendered into both `structuredContent.nextSteps` and the human-readable text. **Why:** agents that only parse text and agents that only parse structured data must converge on the same next-step list; one-surface rendering is invisible to half the clients.
- `execute` — the raw handler function. Two arguments: `args` (already Zod-parsed) and `extra` (the optional `McpUseToolContext`). Returns `Promise<CallToolResult>`. The body is thin: parse-derive inputs, build a use-case command, await the use case, render through the presenter, return.

## A minimal handler using the factory

This is the canonical handler shape. It is intentionally short. Every handler in the repo should look roughly like this.

```ts
// src/handlers/keywords/research-keywords.handler.ts
import { z } from 'zod';
import { defineTool, type AnyToolDefinition } from '../define-tool.js';
import type { KeywordResearchUseCase } from '../../application/keywords/keyword-research.usecase.js';
import type { IMcpPresenter } from '../../presenters/mcp-presenter.port.js';
import { extractOwner } from '../shared/extract-owner.js';

export function createResearchKeywordsHandler(
  useCase: KeywordResearchUseCase,
  presenter: IMcpPresenter,
): AnyToolDefinition {
  return defineTool({
    name: 'research-keywords',
    description:
      '<usecase>Discover keyword candidates for a seed term.</usecase>'
      + '<when_to_use>Use when planning a topic cluster or content brief.</when_to_use>'
      + '<output>Returns a bounded preview plus a handler_id for follow-up refinement.</output>',
    annotations: {
      title: 'Research Keywords',
      readOnlyHint: true,
      idempotentHint: true,
      openWorldHint: true,
    },
    schema: {
      seed: z.string().trim().min(1).describe('Seed keyword. Must be non-empty after trim.'),
      location: z.string().trim().min(2).describe('Two-letter ISO country code or canonical city slug.'),
      limit: z.number().int().min(1).max(200).default(20).describe('Max candidates returned (default 20).'),
    },
    nextSteps: [
      { tool: 'analyze-keywords', label: 'Score the candidate set' },
      { tool: 'compare-keywords', label: 'Rank candidates against competitors' },
    ],
    execute: async (args, extra) => {
      const response = await useCase.research({
        seed: args.seed,
        location: args.location,
        limit: args.limit,
        requesterScope: extractOwner(extra),
      });
      return presenter.render(response);
    },
  });
}
```

What this does NOT do, on purpose:

- It does not branch on `args.location` to call different providers. Branching by mode is a use-case concern.
- It does not build the response envelope. The presenter does that.
- It does not log. The middleware pipeline records request-id, tool name, duration, and error code uniformly.
- It does not catch errors. The boundary mapper installed in `bootstrap.ts` translates `DomainError` to the MCP envelope.
- It does not read `process.env`. The use case received its dependencies via injection at composition time.

If a handler grows past this shape, what it grew is a use-case responsibility that leaked outward. Push it back.

## Bootstrap wiring

The factory's output is registered at exactly one place. The composition root collects every handler factory's result, wraps each `execute` with the shared middleware pipeline, and registers it on the `MCPServer`.

```ts
// src/infrastructure/server/bootstrap.ts (excerpt)
import { withPipeline } from '../middleware/pipeline.js';
import type { AnyToolDefinition } from '../../handlers/define-tool.js';

function registerNative(server: MCPServer, tool: AnyToolDefinition): void {
  const wrapped = withPipeline(tool.execute, tool.TOOL_NAME);
  server.tool(tool.definition, wrapped as Parameters<typeof server.tool>[1]);
  logger.info('tool_registered', { tool: tool.TOOL_NAME });
}

// ... after gateways and use cases are constructed:
const keywordResearchUC = new KeywordResearchUseCase(seoGateway, datasetStore, logger);
registerNative(server, createResearchKeywordsHandler(keywordResearchUC, presenter));
```

`withPipeline` is the typed middleware composer. It threads the request-context `AsyncLocalStorage` binding, attaches the structured logger, classifies thrown `DomainError`s into JSON-RPC envelopes, and records usage. The handler does not import `withPipeline` — only the composition root does. **Why:** if handlers wired their own middleware, the result would be twelve different auth implementations across twelve handlers. The architectural seam is here.

Bootstrap order around tool registration is fixed: gateways first, then use cases, then handlers via factories, then `MCPServer` instantiation, then middleware pipeline registration, then tools (`registerNative` per handler), then resources, then prompts, then error mapping installation, then `server.start()`. Re-ordering breaks observability or auth coverage. See `references/composition-root.md` for the full sequence.

## Cross-references — defer to `build-mcp-use-server`

This file deliberately stops at the architectural shape of the factory. The protocol-mechanics questions belong to the neighbour skill:

- Field-level Zod rules (which kinds of fields, how `.describe()` and `.strict()` are written, why concrete schemas beat catch-all types) — `build-mcp-use-server` `references/04-tools/`.
- Response helpers (`text`, `object`, `mix`, `error`, `widget`) used inside `presenter.render(...)` — `build-mcp-use-server` `references/05-responses/`.
- `ctx.elicit`, `ctx.sample`, `ctx.client.can()` invocation patterns inside `execute` — `build-mcp-use-server` `references/12-elicitation/`, `references/13-sampling/`, `references/16-client-introspection/`.
- Output-schema authoring (what `ToolResultOutputSchema` should look like for the target repo) — `build-mcp-use-server` `references/04-tools/` plus `references/05-responses/`.

If the agent starts adding rules about which Zod field types a tool may use, stop and route the rule to the other skill. This file is the placement spec; that file is the field-content spec.

## Verification checklist

Before claiming a handler is correctly wired with `defineTool()`, observe each of these. Not "intend to satisfy" — observe.

- The new file lives at `src/handlers/<feature>/<tool>.handler.ts` and exports exactly one factory function whose name matches the tool. Run `ls src/handlers/<feature>/` and confirm.
- The factory function returns `AnyToolDefinition` (or `DefinedTool<TSchema>`); it does **not** call `server.tool()` itself. `grep -n "server.tool" src/handlers/` should return zero hits in the new file.
- The handler's `execute` body has at most these phases: derive the input (alias preprocessing OK here), call one use-case method, return `presenter.render(...)`. No provider branching, no `process.env`, no logging, no try/catch other than to translate Zod parse failures via the schema layer.
- Bootstrap registers the handler exactly once via the shared `registerNative` (or equivalent) helper, in the same group as its sibling tools. `grep -n "createMyToolHandler" src/infrastructure/server/bootstrap.ts` returns exactly one hit.
- `pnpm typecheck` and the dependency-cruiser layer check both pass on the new file with no suppressions added.
- A unit test exercises the handler with a fake use case and a fake presenter and asserts the schema parses a known-good payload and rejects an unknown field (`.strict()` coverage).
