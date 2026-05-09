# `HandlerContext` — the dependency-injection seam for handlers

> This reference expands the SKILL.md section "Use case <-> MCP tool flow" — specifically the rule that the handler "may invoke `ctx.elicit` / `ctx.sample` / `ctx.client.can()` — handler-only" and the row in the `Where MCP primitives live` table that says `ctx.elicit()` and `ctx.sample()` belong only in `handlers/<feature>/<tool>.handler.ts`. After reading it you should be able to write a `HandlerContext` interface from scratch in a fresh repo, decide what to inject and what to keep out, and route `ctx.client.can()`-gated capabilities through the handler without leaking them into use cases.

## What `HandlerContext` is, and is not

`HandlerContext` is the **architectural** dependency bag handed to the handler factory at composition time. It is not the per-request `McpUseToolContext` that `mcp-use` passes as the second argument to `execute`. The two work together but answer different questions:

- `HandlerContext` (this file) — assembled in `bootstrap.ts`, passed to factory functions like `createSeoSerpHandler(ctx)`. Holds **stable** dependencies: gateways (via ports), the presenter, capability gates, request-context readers, optional sampling and elicitation hooks. Lives for the process lifetime.
- `McpUseToolContext` (`shared/types/mcp-tool-context.ts`) — the per-call MCP runtime context. Holds **per-request** state: auth payload, session id, transport-specific request handle, `ctx.client.can`, `ctx.elicit`, `ctx.sample`. Mutates per request.

The handler closes over `HandlerContext` and reads `McpUseToolContext` from the second `execute` argument. The use case sees neither. This is what makes the use case framework-free.

## What goes inside

A `HandlerContext` may carry only types whose **purpose is** to support handler-edge concerns. Anything that belongs to the use case (a gateway it directly uses, a domain service) is passed to the use-case constructor in `bootstrap.ts`, not threaded through this context.

Allowed contents:

- **Port references the handler itself reads.** Rare. Most handlers do not call gateways directly; they call use cases. The few exceptions: a credential-registry port the handler uses to gate `ctx.elicit` ("ask the user to authorise scope X"), or a capability-registry the handler queries before deciding whether to surface a tool action. **Why:** if the handler delegates everything, the use case ends up doing handler-edge work (auth gating, elicitation flows) and the framework-free promise breaks.
- **Presenter port (`IMcpPresenter`).** The handler always renders through it. **Why:** keeps `presenter.render(...)` the only path from `ToolResponse` to `CallToolResult`.
- **Capability gates / cost planners.** Concrete reading is OK: `ctx.config.COST_PLANNER_THRESHOLD_UNITS`, `ctx.config.ENABLE_MUTATIONS`. **Why:** which features are enabled in this deploy is a wiring concern; the use case shouldn't branch on it.
- **Optional `sample`, `elicit`, `progress` adapter handles.** These adapters bind their per-request `McpUseToolContext` via `AsyncLocalStorage`, then expose a stable function the handler can call. **Why:** the handler invokes them; the use case is forbidden to. Putting them on `HandlerContext` (not on a use-case input) keeps the boundary obvious.
- **Transport awareness.** A `'stdio' | 'http'` field is fine — some tools' guidance differs between transports (e.g. progress notifications work only on http). **Why:** transport is a deployment fact, not a domain rule.

Forbidden contents:

- **Concrete clients.** No raw `Redis` instance, no `googleads.GoogleAdsApi`, no Supabase SDK handle. Handlers depend on ports; concretes live behind gateways. **Why:** any handler test would have to mock the SDK shape.
- **Environment values directly.** No `ctx.redisUrl`, no `ctx.supabaseServiceRoleKey`. The handler should never see config that isn't already a typed gate. **Why:** that is what `infrastructure/config/runtime-config.ts` is for; threading env into `HandlerContext` re-introduces the scattered-config decay.
- **Mutable state.** No `ctx.sessionsCount`, no shared in-memory map. The MCP server is concurrent; mutable state in a long-lived context object is the textbook race. **Why:** request-scoped state belongs in the per-request `AsyncLocalStorage` request-context, not on `HandlerContext`.
- **Use-case implementations.** Handlers receive the use case directly as a constructor argument to the factory (`createXHandler(useCase, presenter)`), not via `ctx.useCase`. **Why:** keeps the dependency graph readable in `bootstrap.ts` — one line per (handler, use case, presenter) triple.
- **Logger as a free-form bag.** If you inject a logger, it's a typed `Logger` port with named methods (`info`, `warn`, `error`). No `ctx.log: any`. **Why:** unstructured logger handles attract `console.log`-style ad hoc keys that break observability.

## A canonical `HandlerContext`

Below is a complete `HandlerContext` shape modelled after `mcp-ads-google/src/handlers/context.ts` and adapted to the locked rules of this skill. Drop unused fields rather than padding the interface — only the lines you actually need belong.

```ts
// src/handlers/context.ts
import type { IMcpPresenter } from '../presenters/mcp-presenter.port.js';
import type { ISeoGateway } from '../domain/ports/seo-gateway.port.js';
import type { ICredentialRegistry } from '../domain/ports/credential-registry.port.js';
import type { ICapabilityCatalog } from '../domain/ports/capability-catalog.port.js';
import type { ICostPlanner } from '../domain/ports/cost-planner.port.js';
import type { Logger } from '../shared/observability/logger.port.js';
import type { RequesterScope } from '../domain/ports/requester-scope.js';

export type Transport = 'stdio' | 'http';

export interface HandlerConfig {
  readonly ENABLE_MUTATIONS?: boolean;
  readonly DEFAULT_LIMIT?: number;
  readonly COST_PLANNER_THRESHOLD_UNITS?: number;
}

export interface SampleRequest {
  readonly messages: readonly unknown[];
  readonly systemPrompt?: string;
  readonly maxTokens?: number;
}

export interface ElicitRequest {
  readonly message: string;
  readonly requestedSchema?: unknown;
  readonly timeoutMs?: number;
}

export interface ProgressAdapter {
  begin(token: string, message?: string, total?: number): Promise<void>;
  update(token: string, progress: number, total?: number, message?: string): Promise<void>;
  complete(token: string, message?: string): Promise<void>;
  cancel(token: string, message?: string): Promise<void>;
}

export interface HandlerContext {
  readonly transport: Transport;
  readonly config: HandlerConfig;
  readonly presenter: IMcpPresenter;
  readonly logger: Logger;
  readonly seoGateway: ISeoGateway;
  readonly capabilityCatalog: ICapabilityCatalog;
  readonly credentialRegistry: ICredentialRegistry;
  readonly costPlanner?: ICostPlanner;
  /** Bound by middleware; resolves the requester from per-request AsyncLocalStorage. */
  readonly resolveRequesterScope: (extra: unknown) => RequesterScope;
  /** Optional. Present when the runtime supports MCP sampling. */
  readonly sample?: (request: SampleRequest) => Promise<unknown>;
  /** Optional. Present when the runtime supports MCP elicitation. */
  readonly elicit?: <T>(request: ElicitRequest) => Promise<T | null>;
  readonly progress?: ProgressAdapter;
}
```

A handful of points carry the architectural weight of this shape:

- Every field is `readonly`. **Why:** prevents "while I'm here" mutation in a handler that would race against concurrent requests.
- Gateway fields are typed against ports (`ISeoGateway`), never against concretes. **Why:** the handler test injects a fake; the dependency-cruiser layer rule rejects a concrete import.
- `sample` and `elicit` are optional. **Why:** clients that do not advertise the capability simply do not provide them, and the handler `ctx.client.can('sampling')`-gates usage against the per-request `McpUseToolContext` before invoking. The architectural rule: handlers may; use cases may not.
- `resolveRequesterScope` is a function on the context, not a value. **Why:** the requester is per-request; resolving it from the per-call `extra` keeps the scope fresh and avoids leaking last-request identity into the next call.

## How the context flows

```
bootstrap.ts
  composes HandlerContext from:
    - constructed gateways
    - constructed presenter
    - constructed logger
    - middleware-bound resolveRequesterScope
    - optional adapters (sampling, elicitation, progress)
  |
  v
createMyToolHandler(ctx, useCase) -- factory closes over ctx
  |
  v
defineTool({ execute: async (args, extra) => {
   const requester = ctx.resolveRequesterScope(extra);    // per-request
   if (extra?.client?.can?.('elicitation') && ctx.elicit) {
     // handler-only invocation, gated by per-request capability
     await ctx.elicit({ message: '...' });
   }
   const response = await useCase.run({ ...args, requester });
   return ctx.presenter.render(response);
}})
```

Read this top-to-bottom: the handler holds **stable** deps on `HandlerContext`, reads **per-request** facts off `extra` (`McpUseToolContext`), and never lets either reach the use case beyond the validated, scope-tagged input object.

## A handler that uses both

Below is a complete handler illustrating the seam. It rate-checks via the cost planner before running the use case, optionally elicits an approval if the planned cost crosses a threshold, and renders the result through the presenter.

```ts
// src/handlers/seo/seo-serp.handler.ts
import { z } from 'zod';
import { defineTool, type AnyToolDefinition } from '../define-tool.js';
import type { HandlerContext } from '../context.js';
import type { SerpIntelUseCase } from '../../application/seo/serp-intel.usecase.js';

export function createSeoSerpHandler(
  ctx: HandlerContext,
  useCase: SerpIntelUseCase,
): AnyToolDefinition {
  return defineTool({
    name: 'seo-serp',
    description:
      '<usecase>Fetch SERP rankings, features, and volatility for a keyword.</usecase>'
      + '<output>Returns a bounded preview plus a handler_id for follow-up refinement.</output>',
    annotations: {
      title: 'SEO SERP',
      readOnlyHint: true,
      idempotentHint: true,
      openWorldHint: true,
    },
    schema: {
      keyword: z.string().trim().min(1).describe('Target keyword.'),
      location: z.string().trim().min(2).describe('Two-letter country code.'),
      depth: z.number().int().min(10).max(100).default(20).describe('SERP depth.'),
    },
    execute: async (args, extra) => {
      const requester = ctx.resolveRequesterScope(extra);

      const planned = ctx.costPlanner?.planSerpFetch({ depth: args.depth });
      const threshold = ctx.config.COST_PLANNER_THRESHOLD_UNITS ?? 100;

      if (
        planned !== undefined
        && planned.units > threshold
        && extra?.client?.can?.('elicitation')
        && ctx.elicit
      ) {
        const approved = await ctx.elicit<{ approve: boolean }>({
          message: `This call will use ~${planned.units} units. Approve?`,
          requestedSchema: { type: 'object', properties: { approve: { type: 'boolean' } } },
          timeoutMs: 30_000,
        });
        if (approved?.approve !== true) {
          return ctx.presenter.render({
            kind: 'cancelled',
            reason: 'cost_approval_declined',
            estimatedUnits: planned.units,
          });
        }
      }

      const response = await useCase.run({
        keyword: args.keyword,
        location: args.location,
        depth: args.depth,
        requester,
      });
      return ctx.presenter.render(response);
    },
  });
}
```

What this illustrates:

- `extra` is typed (`McpUseToolContext`) but only its handler-relevant fields (`client.can`, the bag the middleware decoded) are read. **Why:** handlers do not unwrap auth payloads, request ids, or session ids by hand — those are read via `ctx.resolveRequesterScope(extra)` and the structured logger.
- `ctx.client.can('elicitation')` is checked **before** invoking `ctx.elicit`. **Why:** clients without the capability throw or hang if you call it; gating is non-optional.
- The use case is invoked once with a typed input including `requester`. The use case has no idea elicitation happened — it just receives an authenticated request. **Why:** that is the boundary this skill defends.
- Failure paths render through `ctx.presenter.render(...)`, never via raw `error()` calls. **Why:** the presenter is the only layer that knows how to shape error envelopes consistent with the success envelope.

## What the handler may do; what only the use case may do

| Operation | Handler | Use case |
|---|---|---|
| Read `extra` (`McpUseToolContext`) | yes | no |
| Call `ctx.client.can('sampling')` / `ctx.client.can('elicitation')` | yes | no |
| Call `ctx.sample(...)` | yes | no |
| Call `ctx.elicit(...)` | yes | no |
| Call `ctx.progress.update(...)` | yes (handler holds the token) | no |
| Resolve requester from `extra` | yes (via `ctx.resolveRequesterScope`) | receives it as input |
| Read `ctx.config.<flag>` | yes (gating) | no — config is injected at construction |
| Build a `Command` for the use case | yes | n/a |
| Call gateways | rarely (capability/credential gates only) | yes |
| Build a `ToolResponse` | no | yes |
| Build a `CallToolResult` | no — delegates to presenter | no |

The architectural reason for the asymmetry is the same in every row: the **use case must remain runnable without `mcp-use`**. A unit test should be able to instantiate it with port mocks, call its method, and assert on the returned `ToolResponse`. The moment a use case reads `ctx.client.can(...)`, that test needs an MCP runtime, and the boundary has rotted.

## Cited shapes

- `mcp-d4s/src/handlers/define-tool.ts` — the factory pattern this skill was distilled from.
- `mcp-d4s/src/shared/types/mcp-tool-context.ts` — the local structural mirror of `ToolContext` from `mcp-use/server`. Handlers depend on this, not on `mcp-use`'s exported type, so SDK churn touches one file.
- `mcp-ads-google/src/handlers/context.ts` — the canonical `HandlerContext` shape with optional `sample`, `elicit`, `progress` adapters and a typed `HandlerConfig`. Read it before designing yours.
- `mcp-ads-google/src/handlers/seo/serp.ts` — a handler that consumes `HandlerContext`, gates on `ctx.client.can`, and never lets the per-request context reach the use case.

## Cross-references

- The `defineTool()` factory itself: `references/define-tool-pattern.md`.
- The per-request `AsyncLocalStorage` context (request-id, requester, session-id) and how middleware binds it: `references/request-context.md`.
- `ctx.elicit`, `ctx.sample`, `ctx.client.can` mechanics, request-shape rules, capability detection — `build-mcp-use-server` `references/12-elicitation/`, `references/13-sampling/`, `references/16-client-introspection/`.
- Port naming and gateway construction: `references/gateways-and-ports.md`.

## What you must verify before finishing

Before claiming the handler-context wiring is correct, observe each of these.

- `src/handlers/context.ts` exists, exports an `interface HandlerContext { ... }` whose every field is `readonly`, and contains no concrete-client types. Run `grep -n "interface HandlerContext" src/handlers/context.ts`.
- The interface contains no `process.env`-derived raw values. `grep -n "Url\|Key\|Secret" src/handlers/context.ts` returns only port-typed handles, not strings.
- No file outside `src/handlers/`, `src/resources/`, `src/prompts/`, or `src/infrastructure/` imports `HandlerContext`. `grep -rn "from .*handlers/context" src/application/ src/domain/ src/gateways/ src/presenters/` returns zero hits.
- `ctx.elicit` and `ctx.sample` are called only inside files under `src/handlers/`. `grep -rn "ctx\.elicit\|ctx\.sample" src/application/ src/domain/` returns zero hits.
- Every place that calls `ctx.elicit` / `ctx.sample` first calls `ctx.client.can(...)`. `grep -B 5 "ctx.elicit\|ctx.sample" src/handlers/**/*.ts` shows a `client.can` check above every site.
- A unit test exists that constructs a fake `HandlerContext` (all ports replaced with fakes), runs a handler, and asserts the use case received a known input — no real `mcp-use` runtime involved.
