---
name: apply-clean-mcp-architecture
description: Use skill if you are designing, refactoring, or auditing a TypeScript MCP server and need a Clean-Architecture standard for folder layout, layer boundaries, mcp-use placement, and TypeScript quality.
---

# Apply Clean MCP Architecture

This skill is the architectural standard for **TypeScript MCP servers built with `mcp-use/server`**. It tells you where every file goes, what each layer may import, how MCP primitives connect to use cases, and what the TypeScript quality bar is. It is opinionated and strict on purpose. If you are working on a TypeScript MCP server, follow it. If something below feels uncomfortable, the skill is the answer, not the question — read the **Why** lines, not just the rules.

For the actual mechanics of `mcp-use` — tool registration, response helpers, sessions, auth flows, transports, capability gating — defer to `build-mcp-use-server`. This skill answers **where & with what discipline**; `build-mcp-use-server` answers **how**.

## Trigger boundary

Use this skill when:
- Designing a new TypeScript MCP server.
- Auditing or reviewing an existing TypeScript MCP server (your own or an unfamiliar one).
- Refactoring an MCP server that has drifted: monolithic tool files, scattered `process.env` reads, inline `mcp-use` imports across business logic, missing application layer.
- Adding a new tool, resource, or prompt to an existing MCP server and you want it to land in the right place.
- Reviewing a pull request against an MCP server and you want a checklist with teeth.

Do NOT use this skill for:
- Servers built directly with `@modelcontextprotocol/sdk` and no `mcp-use` — see `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2`.
- MCP **client** apps (`build-mcp-use-client`) or `MCPAgent` orchestration (`build-mcp-use-agent`).
- MCP Apps **widget** (browser-side React/JSX) work — see `build-mcp-use-apps-widgets`.
- Non-MCP TypeScript work. There is no general-purpose Clean Architecture or TypeScript skill in this pack any longer; the load-bearing rules from the deleted `apply-clean-architecture` and `develop-typescript` are absorbed here for MCP servers only. For a non-MCP project, port the rules from this skill yourself or pick one of the framework-specific `build-*` skills.

## Neighbors and when to also load

- **Always load `build-mcp-use-server` alongside this skill** when MCP wiring is involved (tool registration, response helpers, sessions, transports, auth, capability gating, deploy). This skill never duplicates that one.
- Load `build-mcp-use-apps-widgets` if the server ships a widget.
- This skill replaces the deleted `apply-clean-architecture` and `develop-typescript` for MCP-server work; do not look for them.

## Mode detection — pick one before doing anything

Read the request and the repo state. Pick exactly one of:

| Mode | Trigger | First action |
|------|---------|--------------|
| **Greenfield** | New repo, no `src/` yet, or `src/` has only a `package.json` and entry stub | Open `references/greenfield-walkthrough.md`. Scaffold the layout, then implement. |
| **Refactor** | `src/` exists but is drifted (monolithic `tools/`, no `application/` or `use-cases/`, `mcp-use` imports outside `handlers/` and `infrastructure/`, `process.env` reads scattered) | Open `references/refactor-playbook.md`. One PR per layer; do not big-bang. |
| **Review** | A PR or an existing repo to grade against the standard | Open `references/audit-checklist.md`. Score every line item; report graded findings. |
| **Implementing** | Adding a tool/resource/prompt to a repo that already follows the standard | Open `references/define-tool-pattern.md` and `references/handler-context.md`. Follow the existing layering. |
| **Ask** | The user wants advice without modifying the codebase | Answer using this SKILL.md and the relevant references. State which mode would apply if the user asked you to act. |

If the mode is unclear, **ask**. Do not silently default to one mode and start writing code.

## Hard guardrails — non-negotiable

These rules are absolute. They are why this skill exists. Do not negotiate them down because a server is "small" or "we'll fix it later." Every one of them comes from a real failure observed across the five reference repos.

1. **Inner layers never import outer layers.** `domain/` imports nothing outside itself. `application/` imports only `domain/` and `shared/`. Violation invalidates every other architectural investment in the codebase.
2. **No `mcp-use` or `@modelcontextprotocol/sdk` types inside `domain/` or `application/`.** Not in imports, not in type aliases, not in JSDoc. SDK shape changes must not ripple through your business logic.
3. **One composition root.** `bootstrap.ts` (or `infrastructure/server/bootstrap.ts`) is the **only** file that constructs concrete gateways, instantiates the `MCPServer`, and registers tools/resources/prompts. No other file may.
4. **One config seam.** `infrastructure/config/runtime-config.ts` is the **only** file in the codebase that reads `process.env`. Anywhere else is a build error. Validate env with Zod; throw on missing required secrets.
5. **`mcp-use` imports only in `handlers/`, `resources/`, `prompts/`, `presenters/` (response helpers only), and `infrastructure/`.** Never in `domain/`, `application/`, `gateways/`, or `shared/` (except local structural-type mirrors).
6. **Zod at the handler boundary only.** `.strict()` and `.describe()` on every field. Use cases and domain trust their inputs. Never re-validate inside.
7. **Forbidden TypeScript:** no bare `any`, no `as any`, no `@ts-ignore`, no `z.any()`, no `z.unknown()` (use a concrete schema). `@ts-expect-error` is allowed only with a one-line justification naming the constraint that forces it.
8. **`import type` for every type-only cross-layer import.** `verbatimModuleSyntax: true` in tsconfig is required. This is what proves at compile time that the runtime dependency direction is preserved.
9. **`tsconfig` flags are locked.** `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`. All required. No exceptions.
10. **Never log to stdout.** stdout is the JSON-RPC wire when running over stdio transport. Use a `Logger` port. JSON to stderr only. `console.*` is forbidden.
11. **Never throw raw provider errors at the model.** Every gateway classifies upstream errors into a `DomainError` subclass with a `code`, a `recoveryHint`, and an `isRetryable` flag before the error crosses the port boundary.
12. **Never dispatch domain events / "next steps" before the durable side effect commits.** Pre-commit dispatch is how an LLM acts on phantom data that didn't persist.
13. **`#` private fields on entities are preferred over the `private` keyword.** `private` is compile-time only and bypassed by `as any`; `#` is runtime-private and bypass-resistant. If the codebase enforces `@typescript-eslint/no-explicit-any` plus a `dependency-cruiser` rule blocking `as any` in entity files, `private` is acceptable as practically equivalent — the lint chain provides equivalent protection. Choose one path per repo and apply uniformly.
14. **One tool per file, organised by feature.** Monolithic `tools/<feature>.ts` files are a refactor target, not a destination.
15. **No barrel files (`index.ts` re-exports) inside application code.** Direct file imports only. Barrels are the most common cause of cold-start regressions and circular deps.

These are restated at the bottom of this file under "Guardrails (recall)". If you only remember one section of this skill, remember this list.

## Standard folder layout

This is the layout. Every TypeScript MCP server in this pack should match. No variations for "small" servers — a 1-tool server still has all the layers; some are simply thin.

```
src/
├── domain/                  # Pure entities, value objects, port interfaces, error classes, ToolResponse builder
│   ├── ports/               # I<Capability>Gateway interfaces (named for capability, not storage)
│   ├── errors.ts            # DomainError base + typed subclasses (code, recoveryHint, isRetryable)
│   ├── tool-response.ts     # ToolResponse fluent builder (immutable)
│   └── types/               # Pure domain types and value objects
│
├── application/             # Use cases — orchestration, depends only on domain/ and shared/
│   ├── <feature>/
│   │   ├── <feature>.usecase.ts
│   │   └── <feature>-transforms.ts   # Optional pure data-shape helpers
│   └── shared/              # Cross-feature use-case helpers
│
├── handlers/                # MCP tool handlers — thin
│   ├── define-tool.ts       # defineTool() factory (schema + execute + nextSteps)
│   ├── context.ts           # HandlerContext interface (DI seam for handlers)
│   ├── schemas/             # Shared Zod field fragments
│   └── <feature>/
│       └── <tool>.handler.ts
│
├── gateways/                # Outbound adapters — port implementations
│   ├── <provider>/          # SDK wrappers, error classification, request/response mapping
│   ├── caching-*.ts         # Decorators: cache-aside, retry, circuit-breaker
│   ├── storage/             # Persistence adapters (Redis, S3, DuckDB, ...)
│   └── notifiers/
│
├── presenters/              # ToolResponse → CallToolResult
│   ├── mcp-presenter.ts     # Sanitization, preview rendering, _meta filtering
│   ├── presenter.port.ts    # IMcpPresenter interface (handler depends on this, not the impl)
│   └── response/            # Preview policy, output schema
│
├── infrastructure/          # Composition root + cross-cutting wiring
│   ├── server/
│   │   └── bootstrap.ts     # The single entry point
│   ├── config/
│   │   ├── runtime-config.ts  # The only file that reads process.env
│   │   └── validate.ts        # Zod-validated env schema
│   ├── middleware/          # Pipeline (request context, usage recording, error mapping)
│   ├── errors/
│   │   └── error-contracts.ts # Domain code → JSON-RPC code mapping
│   ├── auth/                # OAuth provider wiring
│   └── observability/       # Logger (JSON to stderr — never stdout)
│
├── resources/               # MCP resources (registered via bootstrap)
├── prompts/                 # MCP prompts (static registry)
└── shared/                  # Cross-cutting utilities
    ├── types/               # Local structural types mirroring MCP SDK shapes
    └── request-context.ts   # AsyncLocalStorage helpers
```

Full rationale and file-naming conventions: `references/folder-layout.md`.

## Layer boundaries (the import matrix)

| Layer | May import from | Forbidden imports |
|-------|-----------------|-------------------|
| `domain/` | (nothing — leaf layer) | `mcp-use`, `@modelcontextprotocol/sdk`, `zod`, `process.env`, any I/O |
| `application/` | `domain/`, `shared/` | `mcp-use`, SDK, frameworks, concrete gateways, `process.env` |
| `handlers/` | `domain/`, `application/`, `presenters/` (port only), `zod`, `mcp-use` types, `shared/types/` | Calling external APIs directly, reading config, instantiating gateways |
| `gateways/` | `domain/` (ports, errors), `shared/`, third-party SDKs | `application/`, `handlers/`, `mcp-use`, presenters |
| `presenters/` | `domain/`, `mcp-use` response helpers (`text`, `object`, `mix`, `error`), `shared/` | `application/`, `gateways/`, `handlers/` |
| `infrastructure/` | All other layers (composition root) | (none — this is the wiring layer) |
| `resources/`, `prompts/` | `domain/`, `application/`, `mcp-use` types | Direct gateway use, `process.env` |
| `shared/` | `domain/` only | Side effects, business logic |

Enforce this with `dependency-cruiser` as a CI-blocking gate. The skill ships a copy-paste config: `references/dependency-rules.md`.

## TypeScript quality bar — locked, no opt-out

These rules apply to **every** file in the codebase, regardless of layer.

- **`tsconfig`:** `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true`, `noImplicitOverride: true`, `noImplicitReturns: true`, `noFallthroughCasesInSwitch: true`, `verbatimModuleSyntax: true`, `module: "NodeNext"` *or* `"Node16"`, `moduleResolution: "NodeNext"` *or* `"Node16"`. **Never** `module: "bundler"`, `"ESNext"`, or `moduleResolution: "node"` for an MCP server — they break `mcp-use/server` resolution. `Node16` is a frozen alias of `NodeNext` (TS 5.x); both are acceptable.
- **No `any`. No `@ts-ignore`. No unchecked `as`. No `z.any()` / `z.unknown()`.** `@ts-expect-error` allowed only with a justification.
- **Explicit return types on every exported function** in `domain/`, `application/`, `gateways/`, `handlers/`, `presenters/`, `infrastructure/`, `shared/`. Inferred returns drift; explicit returns are the cross-layer contract.
- **Branded IDs for every opaque token leaving the boundary** — `HandlerId`, `DatasetId`, `DashboardRef`, etc. The branded constructor validates format before casting.
- **Discriminated unions for every multi-state value** — errors with `code`, results with state tags, render modes. Use `never` exhaustiveness checks in switches.
- **`#` private fields on entity classes**, not `private`. Compile-time `private` is bypassable; `#` is not.
- **`import type` for every type-only cross-layer import.** This proves runtime dependency direction at compile time.
- **No barrel re-exports inside `src/`.** Direct file imports.
- **`unknown` + Zod-narrowing** at every external boundary (env vars, gateway responses, persisted data on rehydrate). Never trust `any` from a third party.
- **Local structural types** in `shared/types/` mirror the bits of `CallToolResult`, `ToolContext`, etc. you depend on. Handlers depend on those, not on SDK types directly. SDK version churn updates one file.
- **No `console.*`.** Use the `Logger` port. Output goes to stderr as JSON; never stdout.
- **`pickDefined()` helper** for object construction under `exactOptionalPropertyTypes`. Conditional spread (`...(cond ? { key } : {})`) is acceptable but inconsistent; pick one and apply it everywhere.

Full deep-dive: `references/typescript-quality-bar.md`. Zod-specific rules at the handler boundary: `references/zod-at-boundary.md`. Narrowing patterns and generic signatures: `references/narrowing-and-generics.md`. Generic engineering hygiene reframed for MCP context (small functions, immutability, no flag arguments, side-effect discipline): `references/clean-code-rules-in-mcp-context.md`.

## Where MCP primitives live

| Primitive | File location | Notes |
|-----------|---------------|-------|
| Tool definition | `handlers/<feature>/<tool>.handler.ts` | Built with `defineTool()`; one tool per file. Mechanics → `build-mcp-use-server`. |
| Tool input schema | Inline in the handler for tool-specific shapes; shared fragments under `handlers/schemas/` | `.strict()` + `.describe()` always. |
| Resource definition | `resources/<resource>.ts` | Wired in `bootstrap.ts`; receives deps via factory. |
| Prompt definition | `prompts/registry.ts` (static) or `prompts/<prompt>.ts` (parameterised) | Registered last in bootstrap. |
| Response shaping | `presenters/mcp-presenter.ts` | `ToolResponse` (domain) → `CallToolResult` via `mix(text, object)`. Sanitises secrets. |
| `MCPServer` instantiation | `infrastructure/server/bootstrap.ts` only | Nowhere else. |
| Auth/OAuth wiring | `infrastructure/auth/` + `bootstrap.ts` | Auth-derived identity flows through request context. |
| `ctx.elicit()`, `ctx.sample()` | `handlers/<feature>/<tool>.handler.ts` only | Guarded by `ctx.client.can()`. Use cases never see `ctx`. |

Full coordination map between this skill and `build-mcp-use-server`: `references/coordinate-with-build-mcp-use-server.md`.

## Use case ↔ MCP tool flow

```
MCP client
   │
   ▼
mcp-use server  ← registered in bootstrap.ts only
   │
   ▼
handler (handlers/<feature>/<tool>.handler.ts)
   │  parses Zod schema (.strict(), .describe())
   │  resolves HandlerContext (auth, request id) via injection
   │  may invoke ctx.elicit / ctx.sample / ctx.client.can() — handler-only
   ▼
use case (application/<feature>/<feature>.usecase.ts)
   │  receives validated, normalised inputs + injected ports
   │  orchestrates port calls
   │  builds and returns a ToolResponse (domain object)
   │  throws DomainError subclass on failure
   ▼
gateway (gateways/<provider>/...)
   │  port implementation — wraps SDK or HTTP client
   │  classifies provider errors → DomainError subclass before crossing port
   ▼
presenter (presenters/mcp-presenter.ts)
   │  ToolResponse → CallToolResult via mix(text(...), object(...))
   │  redacts secrets, applies preview policy
   ▼
mcp-use response → MCP client
```

The handler is **thin** (schema parse + delegate + render). The use case is **framework-free** (no `ctx`, no `mcp-use`, no `process.env`). The gateway is **isolated** (the only place that knows about the provider). The presenter is **stupid** (humble object — no business logic, just shape and sanitise).

Full handler walkthrough: `references/define-tool-pattern.md`. `HandlerContext` shape and DI seam: `references/handler-context.md`.

## Gateways and ports

- Every external API, every persistence target, every cross-process service goes behind an `I<Capability>Gateway` port. Name the port for what it **does**, not for what it stores. `IDatasetStore`, not `IRedisRepository<Dataset>`.
- The adapter classifies upstream errors into `DomainError` subclasses **before** the error crosses the port. Provider-specific exception types never escape the gateway.
- Decorators compose: `CachingProviderGateway(RetryingGateway(SanitisingGateway(ConcreteGateway(...))))`. Wire them in `bootstrap.ts`.
- Provider names, internal URLs, credentials, and SDK error stacks **never** leak past the gateway. The presenter doesn't sanitise these — the gateway does, before the use case ever sees them.
- Accept cross-layer DTO duplication. The handler-input shape, the use-case command, the gateway request, the gateway response, the presenter row, and the MCP response shape are five distinct types. Do not collapse them. Shared types are the most common architectural decay vector and the source of provenance leaks (cache fields → tool response).

Deep dive: `references/gateways-and-ports.md`.

## Composition root (bootstrap.ts)

Strict ordering. Manual wiring only — no DI containers. The order is:

1. Load + validate config (`runtime-config.ts`).
2. Instantiate cross-cutting infrastructure (Redis client, logger, OAuth provider).
3. Construct concrete gateways, applying decorators (cache → retry → sanitise → concrete).
4. Construct use cases with injected ports.
5. Construct handlers via the `defineTool()` factory.
6. Instantiate `MCPServer`. Register middleware pipeline.
7. Register tools, then resources, then prompts.
8. Install error mapping at the boundary.
9. Start the server.

If any step's order is reversed, behaviour drifts. Skeleton: `references/composition-root.md`.

## Error handling

- `DomainError` base class in `domain/errors.ts`. Subclasses with discriminator `code` (e.g., `'VALIDATION_ERROR'`, `'NOT_FOUND'`, `'PROVIDER_ERROR'`, `'AUTH_ERROR'`, `'RATE_LIMIT'`).
- Every error carries `recoveryHint` (LLM-readable) and `isRetryable` (bool).
- One mapping table — `infrastructure/errors/error-contracts.ts` — translates `code` → MCP JSON-RPC error envelope. The table is symmetric and easy to extend.
- Throw inside; map at the handler boundary; **never** throw raw provider errors at the model.
- `Result<T, E>` types are not used in this standard. Throw/catch with structured `cause` chains is the convention. Composition happens via thrown errors, not monadic chaining.

Full hierarchy + mapping table: `references/error-contracts.md`.

## Request context

Use `AsyncLocalStorage` (Node ≥ 18) to bind:
- requester identity (from auth)
- session id
- request id
- cost accumulator (if billing is tracked)

Established once in middleware (`infrastructure/middleware/request-context.ts`). Read anywhere downstream without DI threading. **Never** stash mutable application state, business inputs, or results in the context — only cross-cutting metadata.

Full pattern: `references/request-context.md`.

## Logging & observability

- The logger is a port. Tests inject a no-op logger.
- All logs are JSON to **stderr**. stdout is the JSON-RPC wire under stdio transport — corrupting it kills the connection.
- Per-request structured fields: `request_id`, `requester`, `tool_name`, `duration_ms`, `error_code` (when applicable). Add new fields by extending the logger port, not by leaking ad-hoc keys at call sites.

## Testing expectations

- **Unit**: handlers (schema parse + use-case mock), use cases (port mocks), gateways (recorded SDK fixtures or fake SDK).
- **Contract**: every port has a contract test; every gateway implementation passes it. This is what catches "the cache decorator silently changed the return shape" before production.
- **Integration**: full bootstrap with in-memory adapters; tool calls round-tripped through the wire.
- Tests of `mcp-use` itself are out of scope — that skill ships its own test patterns.
- Mirror the layer structure in tests: `__tests__/<layer>/<feature>.test.ts`. Per-folder `AGENTS.md` co-located guardrails are encouraged when a layer has invariants worth surfacing to reviewers.

## Greenfield workflow (Mode 1)

Step-by-step from empty repo to first running tool, with exit gates at each step: `references/greenfield-walkthrough.md`. Summary: scaffold the folder tree → write `tsconfig.json` and `dependency-cruiser.cjs` → write `runtime-config.ts` → add the first port + first gateway → add the first use case → add the first handler with `defineTool()` → wire `bootstrap.ts` → smoke-test with `mcp-use` Inspector. Each step is independently revertable.

## Refactor workflow (Mode 2)

Drift fix playbook for repos that have monolithic `tools/`, missing `application/`, or scattered `mcp-use` imports: `references/refactor-playbook.md`. The PR sequence is fixed: config seam → gateways → use cases → handlers → bootstrap. One PR per layer. Do not big-bang. Each PR must be independently revertable.

## Review workflow (Mode 3)

Audit checklist with line items grouped by layer, scored P0/P1/P2: `references/audit-checklist.md`. Output is a graded report with per-layer scores and an ordered remediation list. P0 items block merge; P1 items require a follow-up issue; P2 items are nits.

## Coordinate with `build-mcp-use-server`

This skill answers **where & with what discipline**. `build-mcp-use-server` answers **how**. When you reach a question this skill doesn't answer — Zod schema details for a specific MCP feature, OAuth provider setup, session store choice, transport selection, widget rendering, deploy target — load that skill and follow it. The handoff is documented at `references/coordinate-with-build-mcp-use-server.md`.

When in doubt: the new skill answers structural questions; `build-mcp-use-server` answers protocol-mechanics questions.

## Common mistakes

| Mistake | Why it's bad | Fix |
|---------|--------------|-----|
| Monolithic `src/tools/<feature>.ts` with 5+ tools per file | One tool's failure obscures the others; testing requires importing the whole file; `mcp-use` imports leak into business logic | One tool per file under `handlers/<feature>/<tool>.handler.ts`. Use `defineTool()`. |
| `mcp-use` imported in a use case or domain file | SDK changes ripple through business logic; testing requires the whole MCP wire | Move the import to `handlers/` or `infrastructure/`. Use a local structural type in `shared/types/` if the use case needs an SDK shape. |
| `process.env` read inside a use case or gateway | Tests can't run without env; multi-tenant config leaks across requests | Read once in `runtime-config.ts`. Pass values into the constructor. |
| Use case calls a gateway implementation directly (`new DataForSeoGateway(...)`) | Use case can't be tested; circular constructor explosion | Inject the port. Wire the concrete in `bootstrap.ts`. |
| Raw provider errors thrown at the model | Leaks SDK internals; the LLM can't recover; no `recoveryHint` | Classify at the gateway. Throw a `DomainError` subclass with `code` + `recoveryHint`. Map to MCP envelope at the boundary. |
| `console.log` anywhere | stdio transport: corrupts the JSON-RPC wire and kills the connection | Inject a `Logger` port. JSON to stderr. |
| Domain entity uses `private` instead of `#` private fields | `private` is compile-time only; `as any` bypasses it; runtime invariants don't hold | Use `#` fields. |
| Pre-commit dispatch of "next steps" / domain events | LLM acts on phantom data that never persisted | Pull events from the entity **after** the use case's durable side effect commits. |
| Single shared DTO across handler/use-case/gateway/presenter | Shape changes at the gateway leak into MCP responses; provenance fields surface in tool output | Five distinct types. Map between them explicitly. |
| Barrel re-exports (`index.ts` per folder) | Cold-start regressions; circular imports | Direct file imports. |
| `z.any()` or `z.unknown()` in a tool schema | Tool calls cannot be validated; LLM gets no hint about acceptable input | Concrete schema with `.strict()` and `.describe()` on every field. |
| Inferred return types on cross-layer exports | Type drifts silently across refactors; LSP performance degrades on large codebases | Explicit return types on every exported function. |
| `private` keyword used for layer-internal helpers in entities (instead of file-scoping) | Compile-time visibility doesn't enforce architectural boundaries | Co-locate helpers in the same file with module-private functions. Cross-file boundaries are enforced by `dependency-cruiser`. |

Anti-pattern catalogue with concrete repo examples: `references/anti-patterns.md`.

## Guardrails (recall)

The hard rules from the top of this skill, restated for retention:

1. Inner layers never import outer layers.
2. No `mcp-use` or `@modelcontextprotocol/sdk` types in `domain/` or `application/`.
3. One composition root (`bootstrap.ts`).
4. One config seam (`infrastructure/config/runtime-config.ts`).
5. `mcp-use` only in `handlers/`, `resources/`, `prompts/`, `presenters/`, `infrastructure/`.
6. Zod at the handler boundary only; `.strict()` + `.describe()` always.
7. No `any`, no `@ts-ignore`, no `z.any()`, no `z.unknown()`.
8. `import type` + `verbatimModuleSyntax: true`.
9. The locked `tsconfig` flag list applies; no exceptions.
10. JSON to stderr. Never `console.*`. Never stdout.
11. Domain errors with `code` + `recoveryHint`; never throw raw provider errors.
12. Dispatch domain events / next steps **after** durable commit.
13. `#` private fields on entities.
14. One tool per file.
15. No barrel files in `src/`.

If you cannot satisfy a guardrail because of a hard external constraint, the response is to surface that constraint, not to relax the guardrail.

## References

Architecture & boundaries:
- `references/folder-layout.md` — full tree, naming conventions, rationale.
- `references/dependency-rules.md` — import matrix + copy-paste `dependency-cruiser` config.
- `references/composition-root.md` — `bootstrap.ts` skeleton and ordering rules.
- `references/gateways-and-ports.md` — port naming, gateway shape, decorators.
- `references/presenter-and-tool-response.md` — `ToolResponse` builder, presenter sanitisation, secrets policy.
- `references/request-context.md` — AsyncLocalStorage usage and what crosses the boundary.
- `references/error-contracts.md` — `DomainError` hierarchy, JSON-RPC code mapping, `recoveryHint`.

MCP-handler patterns:
- `references/define-tool-pattern.md` — `defineTool()` factory shape and lifecycle.
- `references/handler-context.md` — `HandlerContext` interface, what to inject, auth flow.
- `references/coordinate-with-build-mcp-use-server.md` — touch-points and handoffs.

TypeScript quality:
- `references/typescript-quality-bar.md` — locked `tsconfig`, `import type`, `verbatimModuleSyntax`, branded IDs, local structural SDK types.
- `references/zod-at-boundary.md` — `.strict()`, `.describe()`, shared field fragments, no `z.any()` / `z.unknown()`.
- `references/narrowing-and-generics.md` — `unknown` narrowing, `satisfies`, discriminated unions, generic port signatures.
- `references/clean-code-rules-in-mcp-context.md` — engineering-hygiene rules that earn their keep in MCP context.

Workflows:
- `references/greenfield-walkthrough.md` — scaffold-to-first-tool guide (Mode 1).
- `references/refactor-playbook.md` — drift-fix playbook, one PR per layer (Mode 2).
- `references/audit-checklist.md` — line-item review checklist (Mode 3).

Anti-patterns:
- `references/anti-patterns.md` — what the drifted repos got wrong, why, and the fix path.
