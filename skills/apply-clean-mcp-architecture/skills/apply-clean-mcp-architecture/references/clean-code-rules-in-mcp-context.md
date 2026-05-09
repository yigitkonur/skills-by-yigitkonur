# Clean-Code Rules in MCP Context

> SKILL.md's *TypeScript quality bar — locked, no opt-out* section, and rule 10 in its non-negotiable list, route here. This reference covers engineering-hygiene rules that survived distillation because they materially change MCP-server behaviour. Generic Clean Code that does not change MCP-server behaviour is dropped on purpose. Each rule below names the MCP failure mode it prevents — if it does not, it does not belong here.

After reading, an agent should know exactly which hygiene rules to enforce in handler / use-case / gateway / presenter / domain / infrastructure code, why each one matters specifically for an MCP server, and which generic rules to deprioritise.

## Small functions — at one level of abstraction

The threshold this pack uses: **roughly 40 source lines per function in `domain/` and `application/`**, and **roughly 60 lines for handlers, gateways, and presenters** (the wider band reflects the mapping work those layers do). A function over 60 lines in a use case is almost certainly mixing orchestration with computation; extract sub-functions or move the computation into a `<feature>-transforms.ts` helper module under the same feature folder.

**MCP failure mode the rule prevents.** A 200-line use case that interleaves orchestration with row computation cannot be unit-tested in isolation: the orchestration test has to stub computation, and vice versa. Mixed-abstraction functions are also where business rules accidentally fork — two callers each "improve" their copy and the rules drift. In an MCP server, the rules in question include the per-tool budget, the dataset preview policy, and the secret-redaction list — drift here surfaces as inconsistent tool behaviour the model cannot reason about.

The same rule covers `domain/` entity methods: a 20-line method that updates state and emits events is fine; a 100-line method that does both **plus** computes derived values is two methods.

## Flag arguments → option objects (with the boolean explosion pattern)

Every function with more than three parameters takes a single options object. Every boolean parameter that changes behaviour is replaced by a discriminated-union mode field — `mode: 'task' | 'live'`, not `useTask: boolean`.

**MCP failure mode the rule prevents.** Boolean flags hide a second function inside the first. In an MCP tool, the agent sees the flag in the schema and has to guess which combination is valid. Two booleans yield four call shapes, three booleans yield eight; only a handful are actually supported, and the rest are silent failures. A discriminated `mode` field becomes a schema enum — the agent can target it, the use case can switch on it with `never` exhaustiveness, and a new mode is a compile error at every consumer.

The "flag explosion" specifically: when a tool needs `includeArchived`, `includeDeleted`, `includeDrafts`, the schema gains three booleans whose seven non-empty combinations are mostly nonsense. The fix is one `scope: 'active' | 'archived' | 'deleted' | 'drafts' | 'all'` field with the documented combinations encoded in the enum.

```typescript
// anti-pattern
runQuery(target: string, useTask: boolean, includeArchived: boolean, force: boolean): Promise<Rows>;

// correct
interface RunQueryOptions {
  readonly target: string;
  readonly mode: 'task' | 'live';
  readonly scope: 'active' | 'archived' | 'all';
  readonly forceRefresh: boolean;
}
runQuery(options: RunQueryOptions): Promise<Rows>;
```

Functions with three or fewer parameters that are all required and have unambiguous order can keep positional arguments. Required parameters always precede optional ones — under strict settings the alternative is a compile error, but flag the rule explicitly so reviewers do not reintroduce it.

## Side-effect discipline — gateways only

Pure computation is separated from side effects. A function either computes a result deterministically and returns it, or it performs a side effect through an injected port. There is no "compute total **and also** log" mixed signature, no "fetch and parse **and also** write to Redis" use-case helper.

The architectural rule that maps onto this: **side effects (HTTP, Redis, S3, DuckDB, OAuth, structured logging) live behind ports, and the gateway adapter is the only file that touches the SDK or the wire.** Domain helpers and use-case transforms compute; gateways effect. The presenter is humble — it shapes a response, it does not call providers.

**MCP failure mode the rule prevents.** A side effect hidden inside what looks like a query function is the worst kind of MCP-server bug to debug. Symptom: a tool reports "no rows" intermittently because the computation accidentally mutates a shared cache. Root cause: a transform function that "while reading" updated a Redis key. Once side effects are isolated to gateway adapters, the use case test runs deterministically with port mocks, and the integration test exercises the gateway through a recorded fixture or fake SDK.

The intentional-side-effect carve-out: **domain events**. Entities collect events in-memory; use cases dispatch them through an injected event-bus port **after** the durable side effect (DB / storage / Redis write) commits. Pre-commit dispatch is the original "two systems disagree" bug — the LLM is told the export is ready, then the storage write rolls back and the agent acts on phantom data. Never dispatch before durable commit.

## Immutability for domain entities and DTOs

Cross-layer DTOs use `readonly` on every field and `ReadonlyArray<T>` for collections. Catalog tables use `as const`. Function arguments are `readonly`. `Object.freeze` is reserved for runtime guarantees you can prove you need; the compile-time `readonly` is the standard.

Mutation idioms that are forbidden across layer boundaries: `arr.push()` on a value you did not own, `delete obj.prop`, in-place sort. Use `[...arr, item]` and destructure-rest to remove properties; use `[...arr].sort(…)` to copy before sorting.

**MCP failure mode the rule prevents.** A long-lived MCP process serves concurrent requests from one Node instance. Accidental mutation of a "shared" config object — a runtime-config snapshot, a capability catalog, a per-session cache key list — is the textbook race condition. Symptom: the second concurrent request sees the first request's input. With `readonly` DTOs and `as const` catalogs, the mutation is a compile error.

For entities specifically (rule 13 in SKILL.md): use `#` private fields, never the `private` keyword. `private` is compile-time only and is bypassed by `as any`; `#` is runtime-private and survives JSON round-trips and structured cloning. Entities expose only methods that preserve invariants — never mutable fields.

## Naming conventions per layer

Names come from the **domain's vocabulary**. The DataForSEO MCP uses `keyword`, `serp`, `backlink`, `dataset`, `handler_id`, `dashboard_url`. The same word means the same thing in the handler schema, the use-case command, the gateway request, and the presenter row. Do not invent generic synonyms ("query" for "keyword", "result" for "dataset").

Layer-specific naming rules:

- **Port (`domain/ports/`)** — `I<Capability>Gateway` or `I<Capability>Store`. The name expresses *what the port does*, not *what stores it*. `IDatasetStore`, not `IRedisRepository<Dataset>`. `IBacklinksGateway`, not `IDataForSeoClient`. The provider name lives in the gateway file, never in the port name.
- **Gateway (`gateways/<provider>/`)** — `<Provider><Capability>Gateway` or a decorator name (`Caching<Capability>Gateway`, `Retrying<Capability>Gateway`). The provider name is part of the class name and the file path.
- **Use case (`application/<feature>/<feature>.usecase.ts`)** — verb-phrase: `BacklinkIntelligenceUseCase`, `InspectDatasetUseCase`, `ExportDatasetUseCase`. The class has one public verb-named method (`analyze`, `inspect`, `export`).
- **Handler (`handlers/<feature>/<tool>.handler.ts`)** — `<verb>-<object>.handler.ts` matching the public MCP tool name in kebab-case. Factory exported as `create<ToolName>Handler`.
- **Presenter (`presenters/`)** — humble; shapes response. `MCPPresenter`, `IMcpPresenter` port. No verbs other than `render`.
- **Domain entity (`domain/<aggregate>/`)** — singular noun: `Dataset`, `Subscription`, `Workspace`. A `Dataset.create(...)` factory validates inputs and emits domain events; a separate `Dataset.reconstitute(...)` rebuilds from persisted form without re-validation or events. Never overload one constructor for both.
- **Branded ID (`domain/<aggregate>/<aggregate>-id.ts`)** — `<Aggregate>Id` with `parse<Aggregate>Id`, `create<Aggregate>Id`, and `is<Aggregate>Id`. The bare `as Id` cast is private to the file.

**MCP failure mode the rule prevents.** Cross-layer renames are how a Zod field becomes "subtly different" from the entity field of the same idea. The agent reading a use case should not have to translate "query" against the schema's "keyword". A consistent vocabulary across handler / use-case / gateway / presenter is also the precondition for the dependency-cruiser merge gate to enforce semantic consistency, not just import direction.

## The `console.*` ban

`console.log`, `console.warn`, `console.error`, and every other `console.*` method are forbidden anywhere in `src/`. Output goes through an injected `Logger` port; the logger emits structured JSON to **stderr** and never touches stdout.

**MCP failure mode the rule prevents.** Under stdio transport, **stdout is the JSON-RPC wire**. A single stray `console.log` in any code path that runs during a tool call writes a non-JSON line into the protocol stream, and the MCP client immediately disconnects with a parse error. The connection is dead until the server restarts. There is no recovery path — every subsequent tool call fails with the same error because the connection is gone.

This is the most common production regression source for MCP servers in this pack. It is also why HTTP-transport servers must follow the same rule: a server may run under stdio transport in dev (for `mcpc` smoke tests) and HTTP in production, and the difference is invisible until a `console.log` ships.

The Logger port lives in `domain/ports/logger.port.ts` (or `infrastructure/observability/logger.port.ts` if the domain has no need for it). The implementation in `infrastructure/observability/` writes to `process.stderr` as one JSON object per line. Per-request structured fields — `request_id`, `requester`, `tool_name`, `duration_ms`, `error_code` — are added by extending the logger port, not by leaking ad-hoc keys at call sites.

ESLint enforces the ban. The `no-console` rule is on; suppressions are not allowed in `src/`.

## Composition over inheritance — the carve-outs

The general rule is **prefer composition over inheritance**. The MCP-context-specific carve-outs:

- **Decorator stacks for ports** are composition, not inheritance. `CachingProviderGateway(RetryingGateway(SanitisingGateway(ConcreteGateway(…))))` is the canonical wiring for a provider-backed port; each decorator implements the same port and forwards to the next. Never extend a base class to "share retry logic"; wrap with a decorator.
- **`DomainError` hierarchy is inheritance, on purpose.** Subclassing `DomainError` is what gives `instanceof DomainError` matching at the boundary mapper. Each subclass has a stable `code` literal (`DATASET_NOT_FOUND`, `VALIDATION_ERROR`, `PROVIDER_ERROR`, `AUTH_ERROR`, `RATE_LIMITED`) and the `name` property must equal the class name. This is the one place a class hierarchy earns its keep — the inheritance is a closed, narrow set, and `noImplicitOverride` plus `override` keep it honest.
- **Aggregate roots** that need event-tracking may share a single `AggregateRoot` mixin or base — one level deep, no further. Deep base-class hierarchies among gateways or use cases are forbidden because "not implemented" stub methods leak into production: a subclass forgets to override, and the base method silently returns `null` or `undefined`.

**MCP failure mode the rule prevents.** Inheritance trees among gateways are how an unimplemented port method ships to production: the SDK changed, the base class added a method to forward the new arg, and three of five subclasses forgot to override. The use case sees `undefined` where it expected a typed result. With composition (decorator stacks + ports), each adapter implements the full port surface explicitly, and the compiler enforces it.

## Sequential awaits when parallel work is independent

Independent provider, storage, or Redis calls run concurrently with `Promise.all` (or `Promise.allSettled` for paid or recoverable upstream legs). Sequential `await` chains for independent work are a P1 review finding.

**MCP failure mode the rule prevents.** Per-request latency in an MCP server is dominated by the slowest external call. Three sequential 400 ms calls is 1.2 seconds visible to the agent; three concurrent 400 ms calls is 400 ms. Sequential awaits routinely take a tool from "fast enough" to "the agent retries before the response arrives", and the second attempt re-runs every paid upstream call.

Use `Promise.allSettled` (never `Promise.all`) for paid or recoverable upstream fanout. A single failed leg in `Promise.all` cancels the rest, including already-paid calls; `allSettled` lets the use case aggregate failures and surface partial-success metadata.

## Floating promises — every promise is awaited, returned, or `void`-prefixed

In a long-lived MCP process, an unhandled promise rejection either crashes the worker or silently swallows a provider error that should have surfaced as a recoverable `DomainError`. Every promise in handler, use-case, and gateway code is `await`ed, returned, or explicitly prefixed with `void` for fire-and-forget telemetry.

```typescript
// wrong — floating promise; rejection becomes an unhandled rejection event
this.cache.set(key, value);

// correct — awaited
await this.cache.set(key, value);

// correct — fire-and-forget telemetry, explicitly marked
void this.metrics.record('tool.invocation', { tool: 'analyze-backlinks' });
```

ESLint's `@typescript-eslint/no-floating-promises` is on and not opted out.

## Throw, do not return null or sentinel objects

Use cases and gateways throw `DomainError` subclasses on failure; they do not return `null` for "not found" or sentinel objects (`{ ok: false, ... }`) for "couldn't do it". Monadic outcome wrappers are not part of this standard — composition happens through thrown errors with structured `cause` chains, mapped at the handler boundary.

**MCP failure mode the rule prevents.** A sentinel return forces every caller to invent its own check. In a use case that orchestrates three gateway calls, three sentinel patterns multiply into 27 paths that the test suite has to cover. A typed throw routes through the existing handler-boundary mapper exactly once, the error envelope is consistent, and the recovery hint reaches the model.

The narrow exception: a gateway-port method whose contract is "return null for missing" (e.g. `IDatasetStore.load(id)` returning `Dataset | null`). The "missing" case is a normal, expected outcome there — not a failure — and the use case decides whether to throw a `DatasetNotFoundError` or to continue on the `null` branch. "Truly exceptional" failures still throw.

## Comments — explain *why*, not *what*

JSDoc on port interfaces and `defineTool()` configs is encouraged: those are boundary contracts that other agents read. Inline narration of obvious code is forbidden — stale comments on internal logic actively mislead the next agent who reads them.

**MCP failure mode the rule prevents.** A comment on a use-case helper that says "fetches the cached value" is helpful exactly until the helper is rewritten to fetch from a different store. The next reader believes the comment, the test passes (because the test mock matches the comment), and the production behaviour silently changes. JSDoc on the port stays accurate because the port shape is the contract — when it changes, every consumer breaks.

## What you must verify before finishing

- [ ] No `console.*` call exists in `src/`; `grep -rn "console\." src/` returns zero hits, and the project's ESLint configuration has `no-console` enabled with no per-file suppressions.
- [ ] Every cross-layer DTO field is `readonly`; collections use `ReadonlyArray<T>`; entities use `#` private fields, never `private`.
- [ ] No function in `src/application/` exceeds roughly 40 source lines; no function in `src/handlers/`, `src/gateways/`, or `src/presenters/` exceeds roughly 60. Functions over the threshold have been split into helpers in `*-transforms.ts` or have a written justification.
- [ ] Every boolean parameter that changes behaviour has been replaced with a discriminated `mode`/`scope`/`kind` field; no function in a public signature has more than three positional parameters.
- [ ] Every promise in `src/handlers/`, `src/application/`, and `src/gateways/` is `await`ed, returned, or explicitly `void`-prefixed; ESLint's `no-floating-promises` rule is on.
- [ ] Every port in `src/domain/ports/` is named for a capability (`I<Capability>Gateway` / `I<Capability>Store`); no `IRepository<T>` or `IStore<T>` survives, and no provider name leaks into a port name.
