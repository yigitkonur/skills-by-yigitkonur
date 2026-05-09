---
name: apply-clean-mcp-architecture
description: Use skill if you are placing, refactoring, or reviewing mcp-use/server TypeScript MCP code and need layer boundaries, folder layout, and TypeScript gates.
---

# Apply Clean MCP Architecture

This skill is the architectural standard for **TypeScript MCP servers built with `mcp-use/server`**. It decides file placement, layer boundaries, import direction, request flow, and TypeScript gates. It does not teach the exact `mcp-use/server` API; that belongs to `build-mcp-use-server`.

Structural questions resolve here. Mechanical questions route out:

- **Here:** where code lives, what each layer may import, what bootstrap wires, how discipline is verified.
- **`build-mcp-use-server`:** exact tool/resource/prompt APIs, response helpers, auth, sessions, transports, deploy, Inspector, MCP Apps/widgets, React-side widget patterns, and CSP.
- **`build-mcp-use-client`:** MCP clients.
- **`build-mcp-use-agent`:** `MCPAgent` orchestration.
- **`build-mcp-server-sdk-v1` / `build-mcp-server-sdk-v2`:** raw SDK servers without `mcp-use`.
- **`optimize-agent-ergonomics`:** general agentic optimization, token-cost, tool-description quality, security posture, or runtime usability audits not centered on folder layout or layer boundaries.

For non-MCP TypeScript projects, use the relevant framework skill or the repo's own patterns.

## Trigger Boundary

Use this skill for TypeScript `mcp-use/server` servers when the task is:

- Greenfield design.
- Refactor of drifted layering.
- Review or audit of architecture boundaries.
- Placement of a new tool, resource, prompt, presenter, port, gateway, config seam, or bootstrap wiring.
- PR review where folder layout, import direction, TypeScript gates, or Clean Architecture rules are in scope.

Do not use it for:

- Raw `@modelcontextprotocol/sdk` server mechanics.
- Client apps or `MCPAgent` work.
- Widget React code, CSP mechanics, session/auth transport recipes, deploy, or Inspector usage.
- General MCP usability/security/cost optimization unless the concrete question is structural placement.

## Pinned Defaults

| Decision | Default |
|---|---|
| Stack | TypeScript `mcp-use/server` |
| Composition root | `src/infrastructure/server/bootstrap.ts` or equivalent entry wrapper |
| Config seam | `src/infrastructure/config/runtime-config.ts` |
| Env validation | Zod in the config seam only |
| Tool input validation | Zod at the handler boundary |
| Use-case validation | None; use cases trust validated commands |
| Boundary gate | `dependency-cruiser` plus TypeScript/lint |
| Logger sink | JSON to stderr, never stdout |
| Response seam | `ToolResponse` in domain, `McpPresenter` in presenters |

## Mode Selection

Pick exactly one mode before editing.

| Mode | Trigger | First action |
|---|---|---|
| **Greenfield** | No `src/` yet, or only a package stub exists | Follow the greenfield walkthrough from the routing table. |
| **Refactor** | Existing server has monolithic tools, missing application layer, scattered env reads, or protocol imports in business logic | Follow the staged refactor playbook. |
| **Review** | Existing repo or PR needs a structural grade | Run the audit checklist and report P0/P1/P2 findings. |
| **Implementing** | Clean layered repo needs a tool, resource, prompt, or boundary component | Follow the define-tool and handler-context patterns, then wire through bootstrap. |
| **Ask** | Advice only, no edits | Answer with the selected mode and the relevant routed references. |

If evidence contradicts the selected mode, state the contradiction once and continue with the mode that matches the codebase.

## Guardrails

These rules are absolute for this skill.

1. **Inner layers never import outer layers.** `domain/` imports nothing outside itself. `application/` imports only `domain/` and `shared/`.
2. **No `mcp-use` or SDK types in `domain/` or `application/`.** SDK shape churn must not ripple into business logic.
3. **One composition root.** The root constructs concrete gateways, instantiates `MCPServer`, registers tools/resources/prompts, and starts the server.
4. **One config seam.** `runtime-config.ts` is the only file that reads `process.env`; env is validated with Zod there.
5. **`mcp-use` imports stay at the protocol edge.** Allowed layers: `handlers/`, `resources/`, `prompts/`, `presenters/` for response helpers, and `infrastructure/`.
6. **Zod at boundaries.** Handler input schemas live at the handler boundary; root objects are strict; no `z.any()` or `z.unknown()` at tool boundaries; use cases and domain do not revalidate.
7. **Forbidden TypeScript stays forbidden.** No bare `any`, `as any`, `@ts-ignore`, or unjustified `@ts-expect-error`.
8. **Type-only imports use `import type`.** `verbatimModuleSyntax: true` is required.
9. **Locked TypeScript flags apply.** `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`, NodeNext/Node16 module settings.
10. **No stdout logging.** `console.*` is forbidden under `src/`; stdout is the JSON-RPC wire under stdio.
11. **Provider errors classify at gateways.** Raw provider errors become `DomainError` subclasses before crossing a port.
12. **Domain events and next steps emit after durable commit.** Never dispatch before the side effect succeeds.
13. **Entity privacy is runtime-enforced.** Prefer `#` private fields; `private` is acceptable only with equivalent lint and `as any` blocks.
14. **One tool per file.** Monolithic tool files are refactor targets.
15. **No application barrels.** Direct imports only; `index.ts` barrels inside `src/` cause cycles and cold-start regressions.

When a hard external constraint blocks a guardrail, report the constraint and the smallest compensating boundary. Do not silently weaken the rule.

## Canonical Layout

Keep the spine tree short; use the folder-layout reference for rationale, full naming rules, exceptions, and per-folder `AGENTS.md` guidance.

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

Enforce the matrix with `dependency-cruiser` as a CI-blocking gate.

## MCP Primitive Placement

| Primitive | Structural home | Mechanical owner |
|---|---|---|
| Tool handler | `handlers/<feature>/<tool>.handler.ts` | `build-mcp-use-server` for exact API fields |
| Tool input schema | Inline in handler; shared fragments in `handlers/schemas/` | `build-mcp-use-server` for field recipes |
| Resource | `resources/<resource>.ts` or `resources/<widget-name>/` | `build-mcp-use-server` for resource/widget mechanics |
| Prompt | `prompts/registry.ts` or `prompts/<prompt>.ts` | `build-mcp-use-server` for prompt mechanics |
| Response shaping | `presenters/mcp-presenter.ts` | `build-mcp-use-server` for helper choice |
| `MCPServer` construction | composition root only | `build-mcp-use-server` for constructor/API details |
| Auth/session/transport wiring | `infrastructure/` plus composition root | `build-mcp-use-server` for provider/store/transport recipes |
| `ctx.elicit()`, `ctx.sample()`, client capability checks | handlers only | `build-mcp-use-server` for invocation mechanics |

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

## Audit Smells

During review, check these first before deep reading:

- `mcp-use` imported from `domain/`, `application/`, `gateways/`, or `shared/`.
- `process.env` outside `infrastructure/config/runtime-config.ts`.
- `server.tool(` outside the composition root.
- handler files over ~250 lines or monolithic `src/tools/*.ts`.
- `new *Gateway(...)` outside bootstrap.
- `z.any()` / `z.unknown()` in handler schemas.
- `console.*` under `src/`.
- `index.ts` barrels under application code.

Use the anti-pattern catalogue only after the first sweep identifies likely drift.

## Validation

Minimum gates for structural work:

- `python3 scripts/validate-skills.py` when editing this skills pack.
- Project typecheck and lint for target MCP repos.
- `dependency-cruiser` import-boundary gate.
- Focused unit tests for changed handlers/use cases/gateways/presenters.
- End-to-end MCP call only when wiring, bootstrap, transport, auth/session, or response surfaces changed.

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
