# Composition Root

> SKILL.md's *Composition root (bootstrap.ts)* section routes here. After reading the agent should be able to write a `bootstrap.ts` from scratch in the locked order, justify each step against what would break if it ran earlier or later, and recognise the manual-wiring pattern as the only sanctioned form of dependency injection in this skill. There are no DI containers in this standard. There is one `bootstrap.ts`, one ordered sequence, and the rest of the codebase trusts it.

## Why one composition root, manually wired

When the wiring lives in exactly one file, swapping a provider, substituting a gateway under test, or registering a new MCP capability is a one-place edit. Ad-hoc `new ConcreteGateway(...)` calls inside use cases destroy this property and, with it, every test boundary the rest of the architecture pays for. Manual constructor injection is preferred over a DI container because, for the typical MCP server (well under fifty wirings), a container's added bundle weight and decorator overhead earns nothing. Manual DI is debuggable, type-safe end-to-end, and compatible with `verbatimModuleSyntax: true`.

The cite for this pattern is `mcp-d4s: src/infrastructure/server/bootstrap.ts`. The d4s server has roughly 25 tools, 15 ports, 10 gateway adapters, and a bootstrap that fits in one screen of phase markers — manual wiring scales further than people expect.

## The locked ordering

This is the order in `bootstrap.ts`. If any step is reversed, behaviour drifts. The phases are numbered so a reviewer can call out a regression by number.

1. **Load + validate config.** `runtimeConfig = loadRuntimeConfig()` — Zod-validated env, fails fast on missing required secrets.
2. **Instantiate cross-cutting infrastructure.** Logger configuration, Redis client(s), OAuth provider, optional cache backends.
3. **Construct concrete gateways with decorators.** Cache → retry → sanitise → concrete. Decorator order is fixed (see `gateways-and-ports.md`).
4. **Construct use cases with injected ports.** Each use case takes its dependencies through its constructor, no service-locator calls.
5. **Construct handlers via the `defineTool()` factory.** Schema + execute + nextSteps; each handler receives its use case and the presenter port.
6. **Instantiate `MCPServer` and register middleware pipeline.** Middleware order is load-bearing: `requestContext → metrics → errorBoundary → usageRecorder → rateLimit → timeout → circuitBreaker → costSummary → reportCapture` (mirrors mcp-d4s).
7. **Register tools, then resources, then prompts.** In that order. Tools first because middleware must wrap their `execute`; resources second because they may reference handler ids; prompts last because they may reference resources.
8. **Install error mapping at the boundary.** `infrastructure/errors/error-contracts.ts` translates `DomainError` subclasses into MCP JSON-RPC envelopes. Wired into the `errorBoundary` middleware.
9. **Start the server.** `await server.listen(port)`. Anything earlier risks accepting traffic before middleware is in place.

## Skeleton in full

This is the skeleton an empty repo should match — names and shapes drawn from `mcp-d4s: src/infrastructure/server/bootstrap.ts`. Replace `<feature>`, `<provider>`, etc. with concrete names.

```ts
// src/infrastructure/server/bootstrap.ts
import { MCPServer, type ServerConfig } from 'mcp-use/server';
import type { AnyToolDefinition } from '../../handlers/define-tool.js';
import { loadRuntimeConfig } from '../config/runtime-config.js';
import { logger, configureLogger } from '../observability/logger.js';
import { getRedisClients } from '../config/redis-client.js';
import { withPipeline } from '../middleware/pipeline.js';
import { runWithActiveRequestContext } from '../../shared/request-context.js';

import { ConcreteProviderGateway } from '../../gateways/<provider>/<provider>-gateway.js';
import { CachingProviderGateway } from '../../gateways/caching-provider-gateway.js';
import { RetryingProviderGateway } from '../../gateways/retrying-provider-gateway.js';
import { SanitisingProviderGateway } from '../../gateways/sanitising-provider-gateway.js';
import { RedisDatasetStore } from '../../gateways/storage/redis-dataset-store.js';
import { McpPresenter } from '../../presenters/mcp-presenter.js';

import { AnalyseDomainUseCase } from '../../application/<feature>/<feature>.usecase.js';

import { createAnalyseDomainHandler } from '../../handlers/<feature>/<tool>.handler.js';

import { registerResources } from '../../resources/registry.js';
import { registerPrompts } from '../../prompts/registry.js';

export async function bootstrap(): Promise<void> {
  // ─── 1. Config ───────────────────────────────────────────────
  // First, because every step downstream depends on resolved values.
  // No process.env reads anywhere else; runtime-config.ts is the seam.
  const runtimeConfig = loadRuntimeConfig();
  configureLogger({ level: runtimeConfig.server.logLevel });

  // ─── 2. Cross-cutting infrastructure ─────────────────────────
  // Logger, Redis, OAuth provider — anything a gateway might need.
  // Construct before gateways so decorators have the backing services.
  const { client: redis } = await getRedisClients(runtimeConfig.redis.url);
  logger.info('bootstrap_redis_ready');

  // ─── 3. Gateways with decorators ─────────────────────────────
  // Order is fixed: cache → retry → sanitise → concrete (outer-to-inner).
  // Reversing the order changes semantics: caching a sanitised response
  // is correct; sanitising a cached one means the first miss leaks.
  const concreteGateway = new ConcreteProviderGateway({
    baseUrl: runtimeConfig.provider.baseUrl,
    credentials: runtimeConfig.provider.credentials,
  });
  const sanitised = new SanitisingProviderGateway(concreteGateway);
  const retried = new RetryingProviderGateway(sanitised, { maxAttempts: 3 });
  const providerGateway = new CachingProviderGateway(retried, redis, {
    keyPrefix: 'mcp:cache:',
    ttlSeconds: 24 * 60 * 60,
  });

  const datasetStore = new RedisDatasetStore({ redis });
  const presenter = new McpPresenter();

  // ─── 4. Use cases ────────────────────────────────────────────
  // Constructor-injected ports only. Use cases never see env vars,
  // never see mcp-use, never see concrete gateways through their
  // import statements — only through these constructor arguments.
  const analyseDomainUC = new AnalyseDomainUseCase({
    providerGateway,
    datasetStore,
  });

  // ─── 5. Handlers via defineTool() ────────────────────────────
  // Each handler receives its use case + the presenter port. The
  // factory returns an AnyToolDefinition; bootstrap registers it.
  const handlers: AnyToolDefinition[] = [
    createAnalyseDomainHandler(analyseDomainUC, presenter),
    // …one per tool, one file each.
  ];

  // ─── 6. MCPServer + middleware pipeline ──────────────────────
  // Server is constructed AFTER handlers so it can register them
  // immediately; middleware is wrapped onto each handler.execute
  // at registration time.
  const serverOptions: ServerConfig = {
    name: runtimeConfig.server.name,
    version: runtimeConfig.server.version,
    host: runtimeConfig.server.host,
  };
  const server = new MCPServer(serverOptions);

  // Middleware wraps each handler.execute at register time. Pipeline
  // order is load-bearing — see infrastructure/middleware/pipeline.ts.
  // requestContext MUST be first so every downstream layer (logging,
  // error mapping, usage) sees the same AsyncLocalStorage scope.
  const registerNative = (tool: AnyToolDefinition): void => {
    const wrappedExecute = withPipeline(tool.execute, tool.TOOL_NAME);
    server.tool({ ...tool.definition, execute: wrappedExecute });
  };

  // ─── 7. Tools, then resources, then prompts ──────────────────
  // Tools first: middleware wraps their execute paths.
  // Resources second: may reference staged handler ids that tools mint.
  // Prompts last: may reference both tool names and resource URIs.
  for (const tool of handlers) registerNative(tool);
  registerResources(server, { datasetStore /* + others */ });
  registerPrompts(server);

  // ─── 8. Error mapping at the boundary ────────────────────────
  // The errorBoundary middleware (already in the pipeline above)
  // delegates to infrastructure/errors/error-contracts.ts, which
  // maps DomainError subclasses to MCP JSON-RPC envelopes.
  // Nothing to register here — it's wired through the pipeline.
  logger.info('bootstrap_error_mapping_active');

  // ─── 9. Start ────────────────────────────────────────────────
  // Last. Anything earlier risks accepting traffic before middleware
  // is in place. listen() blocks until the transport is bound.
  await server.listen(runtimeConfig.server.port);
  logger.info('bootstrap_complete', { port: runtimeConfig.server.port });
}
```

## Why each phase order matters — the failure modes

- **Config first.** If gateways construct before config validates, a missing `PROVIDER_API_KEY` becomes a runtime error during the first tool call — when the model is on the line — instead of a fail-fast at boot time.
- **Cross-cutting infrastructure before gateways.** A gateway decorator that takes a Redis client cannot be constructed before the Redis client connects. Reversing this order makes the decorator's constructor either lazy (hides errors until first cache lookup) or eager (crashes during gateway construction with no log context).
- **Decorator order: cache → retry → sanitise → concrete.** Outer to inner. Sanitisation happens before caching writes the entry, so the cache stores already-sanitised values; reversing means the first cache miss leaks pre-sanitised data, and every subsequent hit returns properly sanitised data — a bug only the first request sees, which is the worst kind to debug.
- **Use cases after gateways.** Use cases take ports through their constructors. The port instances must exist by the time the use case constructs.
- **Handlers after use cases.** A handler factory wraps `execute` over a use case; the use case must exist.
- **`MCPServer` after handlers.** The server's `tool()` registration takes a handler; both must be ready before the call. Constructing the server too early is harmless until the first registration races a request — and stdio transport gives no warning before the race fires.
- **Middleware before tool registration.** The pipeline wraps each handler's `execute` at registration time. Registering before the pipeline is configured means the first tool gets unwrapped middleware, which is silent and tested only by a failing prod request.
- **Tools, then resources, then prompts.** Resources may reference staged `handler_id` values that tools mint; prompts may reference tool names and resource URIs. The reverse order works for tools and resources separately but breaks the moment a resource handler synthesises a default that depends on a registered tool list.
- **Error mapping before `listen()`.** The `errorBoundary` middleware needs the mapping table loaded; in this skeleton both are wired through the pipeline, so the requirement is "the pipeline is composed before `listen()` returns" — which the explicit `await server.listen()` at the bottom enforces.
- **`listen()` last.** The transport binds; the server starts accepting traffic. Any uninitialised dependency at this point crashes during the first request, not at boot.

## Forbidden bootstrap patterns

- **No business logic.** Bootstrap wires; it does not compute. If the agent starts writing an `if (provider === 'X')` inside `bootstrap.ts`, the branch belongs in a factory function or a config-driven gateway selection, not in the wiring.
- **No `process.env` reads.** Even in `bootstrap.ts`. Every env read goes through `runtimeConfig`. Bootstrap reads `runtimeConfig.x.y`; the config seam reads `process.env`.
- **No DI container.** No `inversify`, `tsyringe`, `awilix`, or hand-rolled service locator. Manual constructor injection is the convention.
- **No global singletons.** Every dependency a use case or handler needs comes through its constructor. Singletons (logger, Redis client) are created once *in bootstrap* and passed in; they are not imported as module-level globals from inside a use case.
- **No conditional registration based on `NODE_ENV` outside of structural choices** (e.g. picking an in-memory test store vs. a Redis store). "Test" and "production" exercise the same code paths; the only thing that varies is which adapter the bootstrap picks.

## What "load-bearing" means for this file

Every phase number above maps to a real production regression observed in one of the five reference repos. When a reviewer says a phase is "load-bearing", they mean the build still passes, the tests still pass, but the next traffic spike or the next provider rename surfaces a bug that bisects to a phase reorder. Treat the phase ordering as a contract, not a style choice.

## Verification checklist

- [ ] `bootstrap.ts` is the only file in `src/` that calls `new MCPServer(...)`. `grep -rn "new MCPServer" src/` returns exactly one hit.
- [ ] `bootstrap.ts` is the only file in `src/` that calls `new <Concrete>Gateway(...)` for any gateway. `grep -rnE "new [A-Z][A-Za-z]*Gateway" src/ | grep -v "infrastructure/server/bootstrap.ts"` returns nothing.
- [ ] Phases 1–9 appear in `bootstrap.ts` in the listed order, marked with comment dividers so a reviewer can scan them.
- [ ] Decorator construction follows `cache → retry → sanitise → concrete` (outer → inner). The constructor argument list reads inside-out: outermost is on the left of the assignment, innermost is the deepest constructor argument.
- [ ] No DI container library is in `package.json` dependencies.
- [ ] No `process.env` access anywhere in `bootstrap.ts`. All env values come through `runtimeConfig`.
- [ ] `await server.listen(...)` is the last statement of `bootstrap`. Nothing constructs after it.
- [ ] Tools are registered before resources; resources before prompts. Reordering must be a deliberate, commented exception.
- [ ] Tests that exercise the bootstrap path use the same composition root with adapter swaps (in-memory vs. Redis). The test setup helper instantiates the same use cases the production root does.
