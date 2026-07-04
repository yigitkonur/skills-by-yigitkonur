# Folder Layout

> SKILL.md's *Standard folder layout* section routes here. This reference is the canonical map of `src/` for a TypeScript MCP server built on `mcp-use/server`. After reading it, the agent should be able to scaffold an empty repo, place any new file in the right folder on the first try, justify each folder against a concrete failure mode, and use co-located `AGENTS.md` files to keep layer-specific guard rules next to the code they govern.

## The tree, in full

```
src/
├── domain/                      # Pure business model — leaf layer.
│   ├── ports/                   # I<Capability>Gateway interfaces (named for capability, not storage).
│   ├── errors.ts                # DomainError + typed subclasses (code, recoveryHint, isRetryable).
│   ├── tool-response.ts         # ToolResponse fluent builder (immutable).
│   ├── types/                   # Pure domain types and value objects.
│   └── AGENTS.md                # Layer guard rules for editors of this folder.
│
├── application/                 # Use cases — orchestration only.
│   ├── <feature>/
│   │   ├── <feature>.usecase.ts          # One workflow per file.
│   │   └── <feature>-transforms.ts       # Optional pure data-shape helpers.
│   ├── shared/                            # Cross-feature use-case helpers.
│   └── AGENTS.md
│
├── handlers/                    # MCP tool boundary — thin.
│   ├── define-tool.ts           # defineTool() factory.
│   ├── context.ts               # HandlerContext interface (DI seam).
│   ├── schemas/                 # Shared Zod field fragments.
│   ├── <feature>/
│   │   └── <tool>.handler.ts    # One tool per file.
│   └── AGENTS.md
│
├── gateways/                    # Outbound adapters — port implementations.
│   ├── <provider>/              # SDK wrappers, error classification, mapping.
│   ├── caching-<port>.ts        # Decorators: cache-aside, retry, circuit-breaker.
│   ├── storage/                 # Persistence adapters (Redis, S3, DuckDB, etc.).
│   ├── notifiers/
│   └── AGENTS.md
│
├── presenters/                  # ToolResponse → CallToolResult.
│   ├── mcp-presenter.ts         # Sanitisation, preview rendering, _meta filtering.
│   ├── presenter.port.ts        # IMcpPresenter interface.
│   ├── response/                # Preview policy, output schema.
│   └── AGENTS.md
│
├── infrastructure/              # Composition root + cross-cutting wiring.
│   ├── server/
│   │   └── bootstrap.ts         # The single entry point.
│   ├── config/
│   │   ├── runtime-config.ts    # The only file that reads process.env.
│   │   └── validate.ts          # Zod-validated env schema.
│   ├── middleware/              # Request context, usage recording, error mapping.
│   ├── errors/
│   │   └── error-contracts.ts   # Domain code → JSON-RPC envelope mapping.
│   ├── auth/                    # OAuth provider wiring.
│   ├── observability/           # Logger (JSON to stderr — never stdout).
│   └── AGENTS.md
│
├── resources/                   # MCP resources (registered via bootstrap).
│   └── AGENTS.md
├── prompts/                     # MCP prompts (static registry).
│   └── AGENTS.md
└── shared/                      # Cross-cutting utilities.
    ├── types/                   # Local structural mirrors of MCP SDK shapes.
    ├── request-context.ts       # AsyncLocalStorage helpers.
    ├── observability/           # Logger port and helpers.
    └── AGENTS.md
```

## Naming rules per layer

These rules are enforceable by glob; a `dependency-cruiser` rule or a CI grep can spot violations.

| Layer | File suffix | Folder shape | Notes |
|-------|-------------|--------------|-------|
| `domain/` | `<entity>.ts`, `<port>-port.ts`, `errors.ts` | Group by entity / aggregate | Ports use `I<Capability>Gateway`, named for the capability, never the storage technology. |
| `application/` | `<feature>.usecase.ts`, `<feature>-transforms.ts` | Group by feature | One workflow per file; the use-case file holds orchestration, transforms are pure data-shape helpers. |
| `handlers/` | `<tool-name>.handler.ts` | Group by feature | Kebab-case unless the public MCP tool name uses underscores (then match the wire name, e.g. `execute_query.handler.ts`). One tool per file. |
| `gateways/` | `<provider>-gateway.ts`, `caching-<port>.ts`, `<storage>-store.ts` | Group by provider, then by adapter role | Decorators live next to the concrete adapter and are explicit classes, not closures. |
| `presenters/` | `mcp-presenter.ts`, `presenter.port.ts`, `response/<aspect>.ts` | One presenter, one port, several rendering helpers | The presenter is a humble object — no business logic. |
| `infrastructure/` | `bootstrap.ts`, `runtime-config.ts`, `error-contracts.ts` | Group by role (server, config, middleware, errors, observability) | Manual wiring only; no DI containers. |
| `resources/`, `prompts/` | `<resource>.ts`, `registry.ts` | Flat or grouped by capability | Wired in `bootstrap.ts`. Resources receive deps via factory; prompts are usually static. |
| `shared/` | `<utility>.ts`, `types/<shape>.ts` | Flat | No business logic; structural utilities and SDK-shape mirrors only. |

## Why each folder exists — the failure modes prevented

Every line in the tree pays back a real bug. If the agent starts questioning a folder, read this list before deleting it.

- **`domain/`** — *Why:* an MCP server that buries business rules inside `handlers/` re-couples the JSON-RPC wire shape to business invariants; the next provider rename or SDK upgrade rewrites entities along with imports. *Failure prevented:* SDK churn cascading into business logic.
- **`domain/ports/`** — *Why:* ports are owned by the layer that *calls* them, not the layer that *implements* them. *Failure prevented:* ports renamed to mirror an adapter (`IRedisRepository<Dataset>` instead of `IDatasetStore`), which leaks storage semantics into use cases.
- **`domain/errors.ts`** — *Why:* a single hierarchy with stable `code` strings is the contract the boundary error mapper depends on. *Failure prevented:* raw provider errors thrown at the model with no `recoveryHint` and no retry signal.
- **`application/<feature>/`** — *Why:* one workflow per use-case file matches one tool per handler file. *Failure prevented:* fat use cases that combine "analyse and export" until the test for "what does this tool actually do" stops being writable.
- **`application/shared/`** — *Why:* genuinely cross-feature helpers go here so feature folders do not import from each other. *Failure prevented:* a cycle between `application/<feature-a>/` and `application/<feature-b>/` that breaks lazy loading and dependency-cruiser.
- **`handlers/`** — *Why:* the handler is the trust boundary. Zod parses untrusted MCP input here and only here. *Failure prevented:* re-validation drifting into use cases until nobody knows which layer is the source of truth.
- **`handlers/define-tool.ts`** — *Why:* a single factory shape for every tool is what lets `bootstrap.ts` apply uniform middleware (auth, logging, error mapping). *Failure prevented:* twelve handlers with twelve subtly different middleware stacks.
- **`gateways/`** — *Why:* every external system goes behind a port; every adapter classifies upstream errors before the error crosses the port. *Failure prevented:* SDK error types leaking into use cases and presenters.
- **`gateways/caching-<port>.ts`** — *Why:* cache, retry, and sanitise are decorators of the same port. *Failure prevented:* cache-as-method on the gateway, which welds caching behaviour to provider-specific code.
- **`presenters/`** — *Why:* the presenter is a humble object — `ToolResponse` in, `CallToolResult` out. *Failure prevented:* presenter logic that calls a gateway "just to fetch one more thing" and ends up un-testable.
- **`infrastructure/server/bootstrap.ts`** — *Why:* one wiring file is what lets provider swaps, substitute a gateway under test, or add a new tool by editing a single place. *Failure prevented:* ad-hoc `new ConcreteGateway()` calls inside use cases that destroy testability.
- **`infrastructure/config/runtime-config.ts`** — *Why:* `process.env` reads are scattered the moment two are tolerated. *Failure prevented:* tests that cannot run without a populated `.env` and request-scoped config that silently leaks across tenants.
- **`infrastructure/middleware/`** — *Why:* the request pipeline (request context → metrics → error boundary → usage → rate limit → timeout → circuit breaker → cost summary → report capture) is load-bearing and ordered. *Failure prevented:* an error boundary that runs before request context binds, dropping the request id from every log line.
- **`infrastructure/errors/error-contracts.ts`** — *Why:* one symmetric mapping table, easy to extend, easy to audit. *Failure prevented:* a new error subclass added without updating the mapper, leaking raw `Error.message` (often containing DSNs) to the model.
- **`infrastructure/observability/`** — *Why:* the logger is a port. JSON to stderr only. *Failure prevented:* a stray `console.log` corrupting the JSON-RPC stdout wire and killing the connection.
- **`resources/` and `prompts/`** — *Why:* MCP primitives other than tools also need a home, registered last in `bootstrap.ts`. *Failure prevented:* prompts and resources scattered next to handlers, registered ad-hoc, missed by capability catalogues.
- **`shared/types/`** — *Why:* local structural mirrors of `CallToolResult`, `ToolContext`, etc. let inner layers depend on the slice they need without pulling the whole SDK. *Failure prevented:* an SDK upgrade cascading through `application/` because it imported `CallToolResult` directly.
- **`shared/request-context.ts`** — *Why:* `AsyncLocalStorage` for cross-cutting metadata avoids DI threading. *Failure prevented:* manual passing of session id through six function calls, with one of them dropping it.

## Per-folder `AGENTS.md` discipline

Every top-level folder under `src/` ships an `AGENTS.md`. This is the d4s pattern and it materially constrains agent edits. The root `CLAUDE.md` cannot reach the precision of layer-local guard rules — by the time an agent has scrolled to the relevant line, it has already started typing. Co-located `AGENTS.md` files are read at edit time.

**Use a per-folder `AGENTS.md` when:**

- The layer carries invariants that are not obvious from the file names (e.g. "every gateway must classify upstream errors before they cross the port").
- The layer has rules that look small but bite (e.g. "tool annotations must declare `destructiveHint` and `idempotentHint` honestly").
- The layer has a port-to-adapter map that an editor needs to consult before adding a new pairing.
- The layer has a compatibility boundary an outside reader cannot infer from code alone (e.g. legacy public tool names that must not be renamed).

**Keep each `AGENTS.md` short.** A long file goes unread. Aim for: one paragraph of orientation, a port-to-adapter table or rule list, and a "Common mistakes" section keyed to real PR comments. Move deep detail into a sibling reference file under `references/`. The `AGENTS.md` is a reminder, not a textbook.

**Required content per layer:**

| Layer | What its `AGENTS.md` must state |
|-------|---------------------------------|
| `domain/` | Entity invariants; `#`-private-field requirement; the error hierarchy and the `code`/`recoveryHint`/`isRetryable` contract; the rule that no SDK or framework symbols may be imported. |
| `application/` | One workflow per file; constructor-injected ports only; framework-free; transforms are pure; transaction boundary discipline. |
| `handlers/` | The `defineTool()` factory contract; `.strict()` + `.describe()` schema rules; thin handler shape (parse → call use case → render); honest `destructiveHint` / `idempotentHint`. |
| `gateways/` | Port-to-adapter map; decorator composition order; provider-error classification rule; secret-leak prevention rules. |
| `presenters/` | The humble-object rule; the sanitisation contract (forbidden `_meta` keys, redaction patterns); preview policy; surface-parity rule. |
| `infrastructure/` | bootstrap init order; middleware pipeline order; error mapping table extension rule; the "only file that reads `process.env`" rule. |
| `resources/`, `prompts/` | Registration order rule; resource-deps factory pattern. |
| `shared/` | What may live here (cross-cutting utilities, SDK structural mirrors); what may not (business logic, side effects). |

The `AGENTS.md` files are *recommendations the reviewer treats as binding*. Layer-rule violations are caught by `dependency-cruiser`; layer-invariant violations are caught by readers, and that is what these files protect.

## Test layout mirrors source layout

Tests live at `src/__tests__/<layer>/<feature>.test.ts`. The mirror is not cosmetic — it is what lets `dependency-cruiser` exclude tests from the layer-rule check while still enforcing inward-only direction across them. Test doubles live at `src/__tests__/doubles/` and conform to the same port interfaces as the real adapters; drift between a double and a real adapter is caught at compile time.

## Why "small server" is not a reason to skip layers

A one-tool MCP server still has all the layers; some layers are simply thin. The reason is concrete: the layout supports growth from one tool to twenty-five without rewriting. d4s started small and grew; the only reason that growth did not require an architectural overhaul is that every layer was already in place from day one. A "small server" exception is a debt promise that nobody pays back — by the time the third tool lands, the needed file is the file someone deleted as "ceremony".

The cost of laying out the full tree on day one is roughly an hour of work and seven near-empty `AGENTS.md` files. The cost of retrofitting it after twelve tools have been written without it is a multi-PR refactor under production traffic. Pick the cheap version.

## Verification checklist

- [ ] Every top-level folder listed above exists in `src/`, even if some are thin (a one-tool server still has all the layers).
- [ ] No top-level folder is missing an `AGENTS.md`. Each `AGENTS.md` is under ~120 lines and includes the required content for its layer.
- [ ] Use cases live one workflow per file under `application/<feature>/<feature>.usecase.ts`. No file combines two workflows.
- [ ] Handlers live one tool per file under `handlers/<feature>/<tool>.handler.ts`. No monolithic `tools/<feature>.ts` survives.
- [ ] No `index.ts` barrel files inside `src/` (a `bootstrap.ts` entry under `infrastructure/server/` does not count as a barrel).
- [ ] Tests mirror the layer structure under `src/__tests__/<layer>/<feature>.test.ts`.
- [ ] Port files are named for the capability (`IDatasetStore`, `IProviderGateway`), never for storage technology.
- [ ] `runtime-config.ts` is the only file under `src/` that reads `process.env`. `grep -rn "process\\.env" src/ | grep -v "infrastructure/config/"` returns no hits.
- [ ] `console.*` does not appear anywhere under `src/`. The logger port is the single sink, JSON to stderr only.
