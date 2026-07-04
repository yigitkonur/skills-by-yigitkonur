---
name: build-clean-mcp-architecture
description: Use skill if you are placing, refactoring, or auditing TypeScript mcp-use/server code under src/ and need Clean Architecture layer boundaries, folder layout, import direction, or dependency-cruiser gates.
---

# Apply Clean MCP Architecture

Architectural standard for **TypeScript MCP servers built with `mcp-use/server`**. Decides where files live, what each layer may import, what bootstrap wires, and how the discipline is enforced. Mechanical recipes (exact APIs, auth, transports, widgets) live in `build-mcp-use-server`.

## When to use this skill

Trigger on phrases or contexts like:

- *"where should this tool / gateway / presenter / port live?"*
- *"refactor this monolithic `src/tools/*.ts` into clean layers"*
- *"audit this MCP server's architecture"* / *"PR review for layering"*
- *"set up `dependency-cruiser` for an mcp-use server"*
- *"why is `mcp-use` imported from `domain/` or `application/`?"*
- *"scaffold a greenfield `mcp-use/server` repo with proper folders"*
- *"`process.env` is being read all over the codebase — fix the seam"*
- *"design ports, adapters, and provider error classification"*

Do **NOT** use this skill when:

- The question is a raw `@modelcontextprotocol/sdk` server mechanic — use `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `convert-mcp-sdk-v1-to-v2`.
- The question is an `mcp-use/server` API recipe (tool helpers, auth, sessions, transports, widgets, CSP, Inspector, deploy) — use `build-mcp-use-server`.
- The work is on a client app or `MCPAgent` — use `build-mcp-use-client` or `build-mcp-use-agent`.
- The concern is general agentic usability, token cost, tool-description quality, or runtime UX rather than folder layout or layer boundaries — that is out of scope for this structural skill.

If the task is structural placement *inside* an `mcp-use/server` repo, this skill owns it. If it is a mechanical recipe *outside* of placement, route out.

## Pinned Defaults

| Decision | Default |
|---|---|
| Stack | TypeScript `mcp-use/server` |
| Composition root | `src/infrastructure/server/bootstrap.ts` (or equivalent entry wrapper) |
| Config seam | `src/infrastructure/config/runtime-config.ts` |
| Env validation | Zod, in the config seam only |
| Tool input validation | Zod at the handler boundary |
| Use-case validation | None; use cases trust validated commands |
| Boundary gate | `dependency-cruiser` plus TypeScript/lint |
| Logger sink | JSON to stderr, never stdout |
| Response seam | `ToolResponse` in domain, `McpPresenter` in presenters |

## Mode Selection

Pick exactly one mode before editing. If evidence contradicts the picked mode, name the contradiction once and continue with the mode that matches the codebase.

| Mode | Trigger | First action |
|---|---|---|
| **Greenfield** | No `src/` yet, or only a package stub exists | Read `references/greenfield-walkthrough.md`. |
| **Refactor** | Existing server has monolithic tools, missing application layer, scattered env reads, or protocol imports in business logic | Read `references/refactor-playbook.md`. |
| **Review** | Existing repo or PR needs a structural grade | Read `references/audit-checklist.md`; report P0/P1/P2 findings. |
| **Implementing** | Clean layered repo needs a tool, resource, prompt, or boundary component | Read `references/define-tool-pattern.md` and `references/handler-context.md`. |
| **Ask** | Advice only, no edits | Answer with the mode and route to the relevant references below. |

## Guardrails

These rules are absolute. When a hard external constraint blocks one, report the constraint and the smallest compensating boundary — do not silently weaken the rule.

1. **Inner layers never import outer layers.** `domain/` imports nothing outside itself. `application/` imports only `domain/` and `shared/`.
2. **No `mcp-use` or SDK types in `domain/` or `application/`.** SDK shape churn must not ripple into business logic.
3. **One composition root.** It constructs concrete gateways, instantiates `MCPServer`, registers tools/resources/prompts, and starts the server.
4. **One config seam.** `runtime-config.ts` is the only file that reads `process.env`; env validates with Zod there.
5. **`mcp-use` imports stay at the protocol edge.** Allowed: `handlers/`, `resources/`, `prompts/`, `presenters/` (response helpers), and `infrastructure/`.
6. **Zod at boundaries.** Handler input schemas live at the handler boundary; root objects strict; no `z.any()`/`z.unknown()` at tool boundaries; use cases and domain do not revalidate.
7. **Forbidden TypeScript stays forbidden.** No bare `any`, `as any`, `@ts-ignore`, or unjustified `@ts-expect-error`.
8. **Type-only imports use `import type`.** `verbatimModuleSyntax: true` required.
9. **Locked TS flags.** `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`, NodeNext/Node16 module settings.
10. **No stdout logging.** `console.*` forbidden under `src/`; stdout is the JSON-RPC wire under stdio.
11. **Provider errors classify at gateways.** Raw provider errors become `DomainError` subclasses before crossing a port.
12. **Domain events and next steps emit after durable commit.** Never dispatch before the side effect succeeds.
13. **Entity privacy is runtime-enforced.** Prefer `#` private fields; `private` is acceptable only with equivalent lint and `as any` blocks.
14. **One tool per file.** Monolithic tool files are refactor targets.
15. **No application barrels.** Direct imports only; `index.ts` barrels inside `src/` cause cycles and cold-start regressions.

## Canonical Layout

```text
src/
├── domain/          # pure entities, ports, errors, ToolResponse
├── application/     # use cases and pure transforms
├── handlers/        # tool schemas, defineTool(), handler factories
├── gateways/        # outbound adapter implementations and decorators
├── presenters/      # ToolResponse -> MCP CallToolResult
├── infrastructure/  # config, middleware, errors, auth, observability, bootstrap
├── resources/       # MCP resources, including server-side widget resources
├── prompts/         # MCP prompts
└── shared/          # structural types and cross-cutting helpers
```

Full naming rules, rationale, and per-folder `AGENTS.md` guidance: `references/folder-layout.md`.

## Import Matrix

| Layer | May import from | Must not import |
|---|---|---|
| `domain/` | same layer only | `mcp-use`, SDK, Zod, I/O, any outer layer |
| `application/` | `domain/`, `shared/` | protocol APIs, concrete gateways, handlers, presenters, infrastructure, env |
| `handlers/` | `domain/`, `application/`, presenter port, Zod, protocol-edge types | concrete gateways, config reads, direct provider calls |
| `gateways/` | domain ports/errors, shared types, provider SDKs | application, handlers, presenters, `mcp-use` |
| `presenters/` | domain response objects, response helpers, shared types | application, gateways, handlers |
| `infrastructure/` | all layers | reverse imports from inner layers |
| `resources/`, `prompts/` | domain, application, protocol-edge types | direct gateway construction, env |
| `shared/` | domain types only | side effects, business logic, framework imports |

Enforce as a CI-blocking gate; copy-paste config in `references/dependency-rules.md`.

## MCP Primitive Placement

| Primitive | Structural home (this skill) | Mechanical owner (route out) |
|---|---|---|
| Tool handler | `handlers/<feature>/<tool>.handler.ts` | `build-mcp-use-server` |
| Tool input schema | Inline in handler; shared fragments in `handlers/schemas/` | `build-mcp-use-server` |
| Resource | `resources/<resource>.ts` or `resources/<widget-name>/` | `build-mcp-use-server` |
| Prompt | `prompts/registry.ts` or `prompts/<prompt>.ts` | `build-mcp-use-server` |
| Response shaping | `presenters/mcp-presenter.ts` | `build-mcp-use-server` |
| `MCPServer` construction | composition root only | `build-mcp-use-server` |
| Auth/session/transport wiring | `infrastructure/` plus composition root | `build-mcp-use-server` |
| `ctx.elicit()`, `ctx.sample()`, capability checks | handlers only | `build-mcp-use-server` |

Blended decisions split via `references/coordinate-with-build-mcp-use-server.md`.

## Request Flow

```text
MCP client
  -> mcp-use server registered in bootstrap
  -> handler parses schema and resolves request context
  -> use case receives validated command and ports
  -> gateway wraps external systems and classifies provider errors
  -> use case returns ToolResponse or throws DomainError
  -> presenter renders MCP response and sanitises output
  -> mcp-use response returns to client
```

The handler is thin: parse, derive command, delegate, render. The use case is framework-free. The gateway hides providers. The presenter shapes data and redacts; it does not make business decisions.

## Audit Smells (sweep first)

Detect these before deep reading:

- `mcp-use` imported from `domain/`, `application/`, `gateways/`, or `shared/`.
- `process.env` outside `infrastructure/config/runtime-config.ts`.
- `server.tool(` outside the composition root.
- handler files over ~250 lines or monolithic `src/tools/*.ts`.
- `new *Gateway(...)` outside bootstrap.
- `z.any()` / `z.unknown()` in handler schemas.
- `console.*` under `src/`.
- `index.ts` barrels under application code.

After the sweep, look up concrete examples and fix paths in `references/anti-patterns.md`.

## Validation

Minimum gates for structural work:

- `python3 scripts/validate-skills.py` when editing this skills pack.
- Project typecheck and lint for target MCP repos.
- `dependency-cruiser` import-boundary gate.
- Focused unit tests for changed handlers/use cases/gateways/presenters.
- End-to-end MCP call only when wiring, bootstrap, transport, auth/session, or response surfaces changed.

Bundled read-only audit helpers (run from the target MCP project root, or pass the project root as the first argument):

| Need | Script | Doc |
|---|---|---|
| Grep likely layer-import, env, console, and barrel violations | `scripts/audit-layer-imports.sh` | `scripts/audit-layer-imports.md` |
| Check canonical folders and expected seams | `scripts/check-folder-layout.sh` | `scripts/check-folder-layout.md` |
| Check likely Zod boundary violations | `scripts/check-zod-boundary.sh` | `scripts/check-zod-boundary.md` |

Claim only the verification rung actually reached.

## Completion Output

Finish apply/review/refactor work with:

- selected mode
- changed layers and files
- guardrails checked
- scripts/tests run
- validation rung reached
- unresolved constraints or accepted deviations

For Review mode, lead with findings ordered by severity and include replayable evidence.

## Reference Routing

| Read when | Reference | Decision it answers |
|---|---|---|
| Need full tree, naming rules, folder rationale, or per-folder `AGENTS.md` guidance | `references/folder-layout.md` | Which folder owns a file and why it exists. |
| Need copy-paste import rules or `dependency-cruiser` config | `references/dependency-rules.md` | Which imports are legal and how CI enforces them. |
| Need the single-root construction order or bootstrap skeleton | `references/composition-root.md` | What constructs where and in what order. |
| Designing or auditing ports, gateways, decorators, or provider error classification | `references/gateways-and-ports.md` | How external systems cross into the application. |
| Building response objects, presenters, sanitisation, or preview policy | `references/presenter-and-tool-response.md` | How domain responses become MCP envelopes. |
| Adding request identity, session id, request id, or cost tracking | `references/request-context.md` | What belongs in AsyncLocalStorage and how it is bound. |
| Designing `DomainError`, JSON-RPC mapping, or recovery hints | `references/error-contracts.md` | How failures move from domain/gateway to MCP response. |
| Adding or auditing a tool handler factory | `references/define-tool-pattern.md` | What `defineTool()` returns and how handlers stay thin. |
| Designing handler dependency injection or capability-gated edge behavior | `references/handler-context.md` | What belongs in `HandlerContext` versus per-request MCP context. |
| Splitting structural and mechanical ownership with `build-mcp-use-server` | `references/coordinate-with-build-mcp-use-server.md` | Which skill owns a blended decision. |
| Checking TypeScript compiler flags, `import type`, branded IDs, or structural SDK mirrors | `references/typescript-quality-bar.md` | What the TypeScript gate requires. |
| Placing Zod schemas or auditing validation boundaries | `references/zod-at-boundary.md` | Where schemas live and where field mechanics route out. |
| Narrowing `unknown`, generic port signatures, discriminated unions, or `satisfies` records | `references/narrowing-and-generics.md` | How types stay precise without `any`. |
| Applying Clean Code rules that materially affect MCP behavior | `references/clean-code-rules-in-mcp-context.md` | Which hygiene rules matter and why. |
| Starting a new `mcp-use/server` repo from scratch | `references/greenfield-walkthrough.md` | Step-by-step scaffold and gates. |
| Repairing an existing drifted repo | `references/refactor-playbook.md` | The staged PR sequence and rollback path. |
| Reviewing an existing repo or PR | `references/audit-checklist.md` | P0/P1/P2 audit rubric and report shape. |
| Looking up concrete drift examples and fix paths | `references/anti-patterns.md` | How common violations appear and how to detect them. |
