# Request Context

> SKILL.md's *Request context* section routes here. After reading you should be able to set up `AsyncLocalStorage` in `shared/request-context.ts`, bind a context in middleware once per tool call, and read it from anywhere downstream without DI threading — and you should know exactly which fields belong in the context (cross-cutting metadata only) and which do not (mutable application state, business inputs, results).

## Why `AsyncLocalStorage` instead of DI threading

Every tool call carries a small bag of cross-cutting metadata: who is calling, which session they are part of, which request id this is, how much the call has cost so far. This metadata is read by the logger, the usage recorder, the cost summariser, and occasionally by a gateway that needs to scope a cache key. Threading it through every function signature is noisy, error-prone, and the kind of mechanical refactor that tempts an agent to skip a callsite.

Node's `AsyncLocalStorage` (stable since Node 16, hardened in 18 and beyond) keeps the metadata in scope for the entire async tree of a tool call. The middleware binds it once at the top of the call; downstream code reads it on demand. The context survives `await`, `Promise.all`, `setImmediate`, and timer callbacks — which is exactly what an MCP request looks like once you account for parallel gateway fanout.

The alternative — passing a `RequestContext` argument through every function — costs a sizeable refactor every time you add a new field, and one missed callsite produces a hard-to-reproduce production bug where a downstream lookup silently uses the wrong session.

## What goes IN the context

Cross-cutting metadata only:

- **Requester identity** — verified user id derived from authentication. Never derived from a raw bearer payload or a client-reported `ctx.client.user()` value (those are forgeable). Set only by the verified-auth middleware.
- **Session id** — the `mcp-session-id` header value (or the equivalent for stdio transport). Survives the entire call.
- **Request id** — a per-call uuid the logger and the usage recorder both quote. Generated at the top of the middleware pipeline.
- **Cost accumulator** — if billing is tracked, a mutable counter that gateways increment on every paid upstream call. The cost-summary middleware reads it at the end of the call.
- **Abort signal** — the `AbortSignal` for the call, so a downstream timeout middleware can propagate cancellation.

That is the entire allow-list. If you find yourself reaching for a field that isn't on this list, the answer is almost always "use a constructor argument or a function parameter, not the context".

## What does NOT go in the context

The temptation to stash "convenience" values in the context is the failure mode this section exists to prevent. None of the following belong:

- **Mutable application state.** A use case's intermediate results, a domain entity, a partial response — anything the use case is computing. The context is shared across the async tree; mutating it is the textbook race condition.
- **Business inputs.** The Zod-parsed tool arguments. They go through the use case as a typed `Command` object. Reading them through the context bypasses the type system.
- **Results.** The `ToolResponse` the use case returns. The presenter receives it through a function call, not the context.
- **Gateway clients.** The Redis client, the SDK handle. Those come through constructors at composition time.
- **Configuration.** `runtimeConfig` is constructed once and passed in at composition time. Reading it through the context is the slow road back to scattered `process.env` reads.
- **Per-call caches.** A request-scoped memoisation map looks tempting; it is also a memory leak waiting for the next long-lived request.

The shape of the rule: the context carries metadata *about* the call, not data *of* the call.

## Setup in `shared/request-context.ts`

This is the single source of truth. The cite is `mcp-d4s: src/shared/request-context.ts`, simplified for the new-skill audience.

```ts
// shared/request-context.ts
import { AsyncLocalStorage } from 'node:async_hooks';

export interface RequesterScope {
  readonly requesterUserId?: string;
  readonly requesterSessionId?: string;
}

export interface ActiveRequestContext extends RequesterScope {
  readonly requestId: string;
  readonly mcpSessionId?: string;
  readonly abortSignal?: AbortSignal;
  /**
   * Mutable cost accumulator. Gateways increment it; the cost-summary
   * middleware reads it at the end of the call. The mutability is
   * intentional and confined to a single field with a documented
   * write contract — gateways may add only positive numbers.
   */
  readonly cost: { value: number };
}

const storage = new AsyncLocalStorage<ActiveRequestContext>();

/**
 * Run `fn` with the given context bound for its entire async subtree.
 * Called once by the request-context middleware at the top of the
 * pipeline. Never call this from inside a use case or a gateway.
 */
export async function runWithActiveRequestContext<T>(
  context: ActiveRequestContext,
  fn: () => Promise<T>,
): Promise<T> {
  return storage.run(context, fn);
}

/**
 * Read the active context from anywhere in the call's async subtree.
 * Returns undefined when called outside a request (e.g. during boot).
 */
export function getActiveRequestContext(): ActiveRequestContext | undefined {
  return storage.getStore();
}

/**
 * Read just the requester scope — userId + sessionId. The most common
 * downstream read; lifted out so callers don't have to know the full
 * context shape.
 */
export function getActiveRequesterScope(): RequesterScope | undefined {
  const ctx = storage.getStore();
  if (!ctx) return undefined;
  const scope: RequesterScope = {};
  if (ctx.requesterUserId !== undefined) {
    Object.assign(scope, { requesterUserId: ctx.requesterUserId });
  }
  if (ctx.requesterSessionId !== undefined) {
    Object.assign(scope, { requesterSessionId: ctx.requesterSessionId });
  }
  return scope;
}

/**
 * Add to the request's running cost. Idempotent for `0`. Throws on
 * negative inputs — a gateway that reports a refund is a bug, not a
 * normal flow.
 */
export function addRequestCost(amount: number): void {
  if (amount < 0) {
    throw new Error('addRequestCost: negative cost not permitted');
  }
  const ctx = storage.getStore();
  if (!ctx) return;
  ctx.cost.value += amount;
}
```

## The middleware that establishes the context

The context-binder middleware runs first in the pipeline (see `composition-root.md` for the full pipeline order). Its only job is to construct an `ActiveRequestContext` and run the rest of the call inside it.

```ts
// infrastructure/middleware/request-context.ts
import { randomUUID } from 'node:crypto';
import type { Middleware, ToolContext, ToolHandler } from './types.js';
import {
  runWithActiveRequestContext,
  type ActiveRequestContext,
} from '../../shared/request-context.js';

/**
 * First middleware in the pipeline. Binds the AsyncLocalStorage scope
 * for the entire async subtree of a tool call. Subsequent middleware
 * (logger, error boundary, usage recorder, cost summary) all read from
 * this scope; downstream gateways and use cases do too.
 *
 * The bind happens BEFORE error mapping and BEFORE logging so every
 * downstream layer sees the same request_id.
 */
export function requestContext(): Middleware {
  return (next: ToolHandler): ToolHandler => {
    return async (ctx: ToolContext) => {
      const requestId = randomUUID();
      const requesterScope = resolveRequesterScopeFromAuth(ctx);
      const sessionId = resolveSessionIdFromTransport(ctx);

      const activeContext: ActiveRequestContext = {
        requestId,
        ...(requesterScope.requesterUserId !== undefined
          ? { requesterUserId: requesterScope.requesterUserId }
          : {}),
        ...(requesterScope.requesterSessionId !== undefined
          ? { requesterSessionId: requesterScope.requesterSessionId }
          : {}),
        ...(sessionId !== undefined ? { mcpSessionId: sessionId } : {}),
        ...(ctx.signal !== undefined ? { abortSignal: ctx.signal } : {}),
        cost: { value: 0 },
      };

      return runWithActiveRequestContext(activeContext, async () => next(ctx));
    };
  };
}

/**
 * Identity is read ONLY from verified-auth surfaces (the auth provider
 * populates these on the ToolContext). Raw bearer payloads and
 * client-reported user ids are forgeable; never read identity from those.
 *
 * The exact lookup paths depend on how `mcp-use` exposes auth in your
 * version; the rule is "verified path only".
 */
function resolveRequesterScopeFromAuth(_ctx: ToolContext): {
  requesterUserId?: string;
  requesterSessionId?: string;
} {
  // Implementation depends on auth provider wiring; see
  // mcp-d4s: src/shared/request-context.ts for the verified-only
  // extraction logic.
  return {};
}

function resolveSessionIdFromTransport(ctx: ToolContext): string | undefined {
  // Read mcp-session-id header for HTTP-streamable; equivalent for stdio.
  const sid = (ctx as { sessionId?: unknown }).sessionId;
  return typeof sid === 'string' && sid.trim().length > 0 ? sid.trim() : undefined;
}
```

The middleware mounts in `bootstrap.ts` as the first stage of the pipeline:

```ts
// infrastructure/middleware/pipeline.ts
import { requestContext } from './request-context.js';
import { metrics } from './metrics.js';
import { errorBoundary } from './error-boundary.js';
// …

export function withPipeline<T>(handler: ToolHandler, toolName: string): ToolHandler {
  return compose([
    requestContext(),    // first — every other layer reads from this scope
    metrics(toolName),
    errorBoundary(),
    // usageRecorder, rateLimit, timeout, circuitBreaker, costSummary, reportCapture
  ])(handler);
}
```

If `requestContext` is not first, the error boundary runs without a request id in scope, the logger drops the correlation key, and per-request observability falls apart. The order is non-negotiable.

## Reading the context from downstream code

Anywhere in the async tree below the binder, read with `getActiveRequestContext()` or the narrower `getActiveRequesterScope()`:

```ts
// Inside a gateway adapter:
import { getActiveRequesterScope, addRequestCost } from '../shared/request-context.js';

async function fetchSomething(req: ProviderRequest): Promise<ProviderResponse> {
  const scope = getActiveRequesterScope();
  // Use scope.requesterUserId for per-tenant cache keys, log scoping, etc.
  const result = await callSdk(req);
  addRequestCost(result.cost);
  return mapToDomain(result);
}
```

```ts
// Inside the structured logger:
import { getActiveRequestContext } from '../shared/request-context.js';

export function info(event: string, fields: Record<string, unknown>): void {
  const ctx = getActiveRequestContext();
  const enriched = {
    event,
    request_id: ctx?.requestId,
    requester: ctx?.requesterUserId,
    session: ctx?.mcpSessionId,
    ...fields,
  };
  process.stderr.write(JSON.stringify(enriched) + '\n');
}
```

The use case rarely reads the context — a use case has its inputs through its `Command` object and its dependencies through its constructor. The context is a tool for cross-cutting *infrastructure* code (logger, usage recorder, cost summariser) and for gateways that need to scope a cache key by tenant.

## Concurrency and the parallel-call trap

`AsyncLocalStorage` survives `Promise.all` and `Promise.allSettled` — every leg sees the same context that was bound at the top. This is what makes it correct for parallel gateway fanout. It does *not* survive across calls to `setTimeout`/`setImmediate` that re-enter the event loop without the binder; in normal MCP server code that case does not arise (every async path begins with an awaited or returned promise), but if you ever bridge into a global queue or a worker thread, re-bind explicitly with `runWithActiveRequestContext`.

For request-scoped *adapters* (a sampling adapter that needs a per-request `client.sample()` handle, an elicitation adapter likewise), the convention is to expose a `runWithContext(extra, fn)` method on the adapter and have the handler compose it once at the top of `execute`. Each adapter's per-request binding plugs into its own `AsyncLocalStorage`; the request-context binder sits above and outside those.

## Local-auth-bypass is a config decision, not a code-path decision

If you support a loopback dev mode, the bypass is resolved in `infrastructure/config/runtime-config.ts` and surfaces as a flag. The middleware reads the flag and either resolves identity from the bypass scope or from verified auth — but the use case and the gateway never see the flag. The moment a bypass branch lives inside a use case, the production path and the dev path stop being the same path, and your tests stop telling you anything about production behaviour.

## What you must verify before finishing

- [ ] `shared/request-context.ts` defines exactly one `AsyncLocalStorage<ActiveRequestContext>` instance. No other file constructs one for cross-cutting metadata.
- [ ] The context is bound by exactly one middleware (`infrastructure/middleware/request-context.ts`), and that middleware is the **first** stage of the pipeline.
- [ ] The context carries only the allow-listed fields (`requestId`, `requesterUserId?`, `requesterSessionId?`, `mcpSessionId?`, `abortSignal?`, `cost`). No business inputs, no results, no use-case state.
- [ ] Use cases do not call `getActiveRequestContext()` for business inputs. A grep across `application/` for `getActiveRequestContext` finds at most uses for cost reporting or for identity needed by a domain rule (e.g. tenant-scoped invariants).
- [ ] Identity is resolved from verified-auth surfaces only. The middleware's identity-extraction function does not read raw bearer payloads or client-reported user ids.
- [ ] Tests of use cases run without binding a request context (use cases must work with `getActiveRequestContext() === undefined`); tests of gateways and middleware bind a synthetic context with `runWithActiveRequestContext`.
- [ ] The structured logger reads `requestId`, `requesterUserId`, and `mcpSessionId` from the context on every emission so per-request fields appear without the call site having to pass them.
- [ ] No `setImmediate` / `setTimeout` callback that originates inside a tool call escapes the context (verified by reading any `setTimeout(...)` callsite in `src/` and confirming the work either completes synchronously or re-binds the context).
