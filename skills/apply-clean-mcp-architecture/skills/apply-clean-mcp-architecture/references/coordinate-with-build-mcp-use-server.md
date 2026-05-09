# Coordinating `apply-clean-mcp-architecture` with `build-mcp-use-server`

> This reference expands the SKILL.md section "Coordinate with `build-mcp-use-server`" and the closing line of the same section: "the new skill answers structural questions; `build-mcp-use-server` answers protocol-mechanics questions." After reading it the agent should be able to look at any incoming request and route it to the right skill in one step, instead of pulling both and reconciling. The two skills are designed to compose, not overlap; this file is the seam.

## The two questions

Every MCP-server task lands in one of two question families.

1. **Structural — answered here.** Where does this code live? What can this layer import? Who owns this concern? How do these layers exchange data? What does the import graph look like? What is the architectural shape of the factory or context?

2. **Mechanical — answered by `build-mcp-use-server`.** What is the exact API of `mcp-use`'s helper for this thing? What field names does the response helper expect? Which capability flag gates this? How do I declare CSP for a widget? What does the OAuth provider config object look like? Which CLI command generates types?

When a request blends both, split it. Do the architectural placement first using this skill (which file, which layer, what shape), then load the neighbour skill for the mechanics (which API, which fields, which flag).

`build-mcp-use-server` now owns MCP Apps/widget mechanics in the same skill as server mechanics. That includes React-side widget patterns, `McpUseProvider`, `useWidget`, `useCallTool`, CSP declarations, widget metadata, asset hosting, and Inspector/widget validation. This skill owns only server-side placement: `src/resources/<widget-name>/`, bootstrap wiring, and the boundary flow between use cases, resources, tools, and presenters.

## Touch-points table

Read this row-by-row. It is not exhaustive but it covers every overlap that has caused two-skill confusion in the reference repos.

| Concern | Owned by | Notes on the split |
|---|---|---|
| Tool registration: where the file lives, what shape the factory has, how `bootstrap.ts` wires it | `apply-clean-mcp-architecture` | `defineTool()` factory layout, `handlers/<feature>/<tool>.handler.ts` placement, the rule that only the composition root may call `server.tool()`. |
| Tool registration: which fields a tool config object accepts, what `annotations` flags do, how `mcp-use/server` validates the registration | `build-mcp-use-server` | API surface of `server.tool(...)` and `defineTool`-style helpers exposed by `mcp-use`. |
| Zod boundary invariants: schemas live at the handler boundary, root objects are strict, no `z.any()` / `z.unknown()` at boundaries, no use-case/domain revalidation | `apply-clean-mcp-architecture` | These are placement and trust-boundary rules. They survive `mcp-use` API changes. |
| Zod schema authoring: field bounds, refinement recipes, generated types, client-facing schema mechanics, exact `mcp-use/server` registration shape | `build-mcp-use-server` | Field-level and API-specific rules belong to the protocol-mechanics skill. |
| Schema placement: where shared field fragments live | `apply-clean-mcp-architecture` | `src/handlers/schemas/` for cross-tool fragments; tool-specific shapes inline in the handler. The neighbour skill never decides this. |
| Response shape: `ToolResponse` builder in `domain/`, presenter in `presenters/`, the `presenter.render(...)` seam | `apply-clean-mcp-architecture` | Layered ownership: domain owns the framework-free response object; presenter is the only file that imports `mcp-use` response helpers. |
| Response helpers: `text()`, `object()`, `mix()`, `error()`, `widget()` and when to choose each | `build-mcp-use-server` | Use them inside the presenter only. Any rule about which helper to use for what content lives in the neighbour skill. |
| Output schema: required on every tool, default to a shared envelope | `both` | The rule "every tool ships an `outputSchema`" comes from this skill. The exact `ToolResultOutputSchema` definition (field shapes, naming, structured-content keys) is `build-mcp-use-server`. |
| OAuth provider wiring: where the config lives, where it is constructed, how it reaches handlers via `HandlerContext` | `apply-clean-mcp-architecture` | `infrastructure/auth/` constructs the provider; `bootstrap.ts` is the single composition root; auth-derived identity flows through request context. |
| OAuth provider mechanics: DCR vs proxy, scope mapping, browser flow, refresh, debug | `build-mcp-use-server` | Provider-specific recipes (`auth0`, `better-auth`, `workos`, `keycloak`, `supabase`, `oauth-proxy`) all live there. |
| Session store: where the choice is made, where the adapter is constructed, how middleware binds it to `AsyncLocalStorage` | `apply-clean-mcp-architecture` | `infrastructure/session/` adapter, `bootstrap.ts` instantiation, request-context binding. |
| Session store: memory / filesystem / redis / custom adapter APIs, lifecycle, distributed retention | `build-mcp-use-server` | The adapter interface and per-store recipes live there. |
| Transport choice: stdio vs streamable-http vs serverless | `build-mcp-use-server` | Decision matrix and per-transport setup. This skill says only "the choice is per-deploy and is made in `bootstrap.ts` / the entry file." |
| Transport-driven architectural rules: never log to stdout under stdio, presenter sanitises before any wire write | `apply-clean-mcp-architecture` | The rule survives across transports because it is a layer rule, not a transport rule. |
| Capability gating: where `ctx.client.can('elicitation')` / `'sampling')` checks may live | `apply-clean-mcp-architecture` | Handlers only. Use cases never see `ctx`. The rule lives here even though the API is in the neighbour skill. |
| Capability gating: which capabilities exist, what `ctx.client.can(...)` returns for each, the underlying introspection API | `build-mcp-use-server` | `references/16-client-introspection/`. |
| Elicitation flow: how the handler invokes it, that the use case never sees it | `apply-clean-mcp-architecture` | Architectural rule: handler-only. Use cases stay framework-free. |
| Elicitation mechanics: form mode vs URL mode, multi-step, anti-patterns | `build-mcp-use-server` | `references/12-elicitation/`. |
| Sampling flow: where the handler invokes it; the rule that domain code never imports it | `apply-clean-mcp-architecture` | Same boundary as elicitation. |
| Sampling mechanics: string vs extended API, model preferences, callbacks, progress | `build-mcp-use-server` | `references/13-sampling/`. |
| Resources: file location (`src/resources/`), wiring (`bootstrap.ts` only), receiving deps via factories | `apply-clean-mcp-architecture` | This skill places the file and gates the wiring. |
| Resources: static, templates, binary/image, URI conventions, subscriptions | `build-mcp-use-server` | Per-shape recipes belong to the neighbour skill. |
| Prompts: where they live (`src/prompts/`), registration order in bootstrap (last) | `apply-clean-mcp-architecture` | Layer rule. |
| Prompts: static, templates, completable, prompt engineering | `build-mcp-use-server` | Author-time mechanics. |
| Widget hosting: which layer the server-side widget config lives in (`src/resources/<widget-name>/`), how it is wired in bootstrap, how widget data crosses layer boundaries | `apply-clean-mcp-architecture` | Architectural placement only. |
| Widget hosting mechanics: `widgetMetadata`, CSP declaration, `server.uiResource()`, `tool.widget.name` matching, React-side widget patterns | `build-mcp-use-server` | The same current `build-mcp-use-server` skill owns MCP Apps/widget mechanics; do not route to the removed legacy widget split. |
| Error handling: `DomainError` hierarchy, `code` / `recoveryHint` / `isRetryable`, gateway classifies before crossing the port, single mapping table at the boundary | `apply-clean-mcp-architecture` | The error model is architectural. |
| Error response shaping: `error()` helper vs `throw`, expected-vs-unexpected failure semantics | `build-mcp-use-server` | The "use `error()` for expected failures, `throw` for truly unexpected" rule lives in the neighbour skill; this skill provides the typed-error model that feeds it. |
| Logging: structured logger as a port, JSON to stderr, never stdout | `apply-clean-mcp-architecture` | Layer rule with security implications under stdio transport. |
| Logging: `ctx.log` API, `Logger` from `mcp-use`, `MCP_DEBUG_LEVEL`, Winston migration | `build-mcp-use-server` | The wire-level mechanics. |
| Request-context: `AsyncLocalStorage` binding established in middleware, what crosses the boundary, what does not | `apply-clean-mcp-architecture` | Architectural pattern. The neighbour skill does not cover this — it is repo-architecture-specific. |
| Composition root: bootstrap order, manual wiring only, no DI containers, decorator stacking | `apply-clean-mcp-architecture` | The whole composition-root playbook. |
| Composition root: which entry file to pick (`index.ts` / `src/server.ts` / `src/mcp-server.ts` / serverless handler) | `build-mcp-use-server` | Setup matrix at `references/02-setup/`. This skill assumes the file exists and dictates what it must do. |
| Deploy targets: mcp-use Cloud, Supabase, Cloud Run, Vercel, Fly, Cloudflare Workers, Deno Deploy | `build-mcp-use-server` | All deploy mechanics. |
| Deploy-time architectural invariants: no env reads outside `infrastructure/config/`, gateway adapters are the only files that talk to external services, decorators wired in `bootstrap.ts` only | `apply-clean-mcp-architecture` | These do not change between deploy targets. |
| Anti-patterns: monolithic `tools/` files, inline `mcp-use` imports in business logic, missing application layer, scattered `process.env`, barrel cascades, anaemic domain | `apply-clean-mcp-architecture` | Architectural anti-patterns. See `references/anti-patterns.md`. |
| Anti-patterns: secrets in widget state, missing `isPending` guard, raw `fetch` instead of `useCallTool`, CSP omissions, `z.any()` in a tool schema | `build-mcp-use-server` | Surface-level mechanics anti-patterns. |
| Validation tooling: Inspector walkthrough, `mcp-use dev`, curl handshake, `mcp-use generate-types` | `build-mcp-use-server` | Validation mechanics. |
| Validation gates: `dependency-cruiser` boundary check is a CI-blocking gate, contract tests for every port | `apply-clean-mcp-architecture` | Architectural validation that lives in CI. |

If a row's "Owned by" column is `both`, the split is described in the "Notes" cell. Always read the note before assuming overlap.

## When in doubt — the routing rubric

Use this rubric when the request does not fit a row above.

1. **"Where does X live?"** — `apply-clean-mcp-architecture`.
2. **"What can layer A import?"** — `apply-clean-mcp-architecture`.
3. **"What is the import direction between A and B?"** — `apply-clean-mcp-architecture`.
4. **"What does this `mcp-use/server` API accept?"** — `build-mcp-use-server`.
5. **"How do I configure / call / declare X with `mcp-use`?"** — `build-mcp-use-server`.
6. **"Should I use `error()` or `throw`?"** — `build-mcp-use-server` (mechanics rule), but model the error using `apply-clean-mcp-architecture`'s `DomainError` first.
7. **"Why is this rule absolute?"** — read the **Why** line. If it cites a layer-boundary failure mode, this skill owns it. If it cites a wire-level or capability-detection failure mode, the neighbour skill owns it.
8. **"Both skills seem to mention this."** — read each skill's section. If one says "deferred to the other," follow the route. If neither defers, the agent found a missed handoff — surface it instead of guessing.

A practical heuristic: if the answer's destination is a **file path** in the target repo, the answer is a structural question. If the answer's destination is an **API call** to `mcp-use`, the answer is a mechanical question.

## Worked routing examples

Each example below is a request the agent might receive. The right move is to split the response into the structural half and the mechanical half, in that order.

**"Add a `cancel-export` tool."**
- Structural: place the file at `src/handlers/exports/cancel-export.handler.ts`. The use case `CancelExportUseCase` lives at `src/application/exports/cancel-export.usecase.ts`. The gateway port `IExportRunner` already exists; if not, create it under `src/domain/ports/`. Annotate as `destructiveHint: true` because cancel is a destructive action against running work — that classification is structural.
- Mechanical: Zod schema for `args.exportId` (concrete, bounded, `.describe()`d), response shape via `presenter.render(...)`, decision to use `error()` vs `throw` for the "no such export" case. Switch to `build-mcp-use-server` for those.

**"Add OAuth via Auth0 to this server."**
- Structural: provider construction in `src/infrastructure/auth/auth0-provider.ts`; wired in `bootstrap.ts` only; the auth-derived requester identity is bound onto the request-context `AsyncLocalStorage` in middleware; handlers read it via `ctx.resolveRequesterScope(extra)`. No handler imports the Auth0 SDK.
- Mechanical: which Auth0 fields the `mcp-use` provider config takes, scope mapping, browser-flow callback URL, refresh-token handling, debug logs. Switch to `build-mcp-use-server` `references/11-auth/providers/auth0.md`.

**"My MCP server crashes on stdio with garbled JSON."**
- Structural: someone is logging to stdout. Audit `grep -rn "console\." src/` and replace with the injected `Logger` port. Confirm the logger writes JSON to stderr only. The architectural rule predates the SDK and survives transport changes.
- Mechanical: which `mcp-use` debug knobs help diagnose the symptom (`MCP_DEBUG_LEVEL`, the Inspector RPC log). Switch to `build-mcp-use-server` `references/15-logging/` and `references/20-inspector/`.

**"Should this tool ship a widget or just structured content?"**
- Structural: where the widget config and `resources/<widget>/` directory would live, who wires `server.uiResource(...)` (the composition root, no one else), how widget data flows from use case to the resource handler. Even before the choice is made, the placement is settled by the layout rules.
- Mechanical: cost-benefit of MCP Apps widgets vs structured content alone, capability detection (`ctx.client.supportsApps()`), CSP declaration, dual-protocol concerns. Switch to `build-mcp-use-server` `references/18-mcp-apps/`.

**"My tool's input schema lets the LLM crash the provider."**
- Structural: confirm the schema lives at the handler boundary, not deeper. Confirm no use case re-validates. Confirm the gateway classifies the upstream 4xx into a `DomainError` with a useful `recoveryHint`.
- Mechanical: rewrite the field-level Zod (bounds, regex, enums, `.describe()`, `.strict()`). Switch to `build-mcp-use-server` `references/04-tools/` for the field-authoring rules and `references/26-anti-patterns/` for the catalogue of unbounded-input failure modes.

The pattern is the same in every example: structural first (where, what shape, who owns), mechanical second (which API, which field, which flag). Mechanical answers wait until the structural question has been routed through this skill.

## Forbidden duplication

The two skills must not paraphrase each other. The following kinds of content are explicitly forbidden inside `apply-clean-mcp-architecture`:

- Field-by-field documentation of a `mcp-use/server` API. Cross-reference instead.
- Step-by-step setup of a transport or deploy target. Cross-reference instead.
- A capability matrix of which clients support `elicitation` / `sampling` / `mcpApps`. Cross-reference instead.
- Any rule whose **why** is "the SDK requires it" rather than "the layer boundary requires it." If the rule survives a hypothetical `mcp-use` API change, it belongs here. If it would change with the SDK, it belongs in the neighbour skill.

The same rule applies in reverse: `build-mcp-use-server` does not paraphrase clean-architecture rules. When in doubt, the rule "if `mcp-use` shipped a v3 with a different API, would this rule still hold?" decides ownership: yes -> here; no -> neighbour.

## What this means in practice

A new tool request lands. The right sequence is:

1. **Scope-decide here.** Which feature folder is this? Does the use case already exist or is it new? Is a new port needed? (`apply-clean-mcp-architecture`.)
2. **Place the file.** `src/handlers/<feature>/<tool>.handler.ts`. The factory call lives there. (`apply-clean-mcp-architecture`.)
3. **Schema and response field shape.** Switch to `build-mcp-use-server` for which Zod patterns to use, which response helper, what `outputSchema` shape clients expect. (`build-mcp-use-server`.)
4. **Wire it up.** Back to `apply-clean-mcp-architecture` for `bootstrap.ts` ordering, decorator stacking, capability registration.
5. **Validate.** Both skills contribute: layer-boundary check (this skill via `dependency-cruiser`); Inspector / curl handshake / `mcp-use dev` (neighbour skill).

A tool review request lands. The right sequence is:

1. **Layer audit first.** Use this skill's `references/audit-checklist.md`. Score every layer-boundary item.
2. **Mechanics audit second.** Switch to `build-mcp-use-server` `references/26-anti-patterns/` for tool-design and schema anti-patterns at the wire level.

The order matters. A schema that looks fine field-by-field is still wrong if it sits in the wrong layer; a perfect layer placement still fails if the schema lets the LLM crash the upstream provider with an unbounded payload.

## Skill-load checklist

When the agent is about to load this skill, the neighbour skill, or both, run this short check:

| Situation | Load |
|---|---|
| Designing a new MCP server from scratch | both, this skill first (greenfield walkthrough) |
| Refactoring a server with monolithic `tools/` and missing application layer | this skill (refactor playbook) |
| Adding a tool to a clean-layered repo | both, this skill for placement, neighbour for schema and response mechanics |
| Reviewing a PR for layer-boundary violations | this skill (audit checklist) |
| Diagnosing a wire-level handshake failure (Inspector, curl, `mcp-use dev`) | neighbour skill |
| Deciding between transports / sessions / auth providers | neighbour skill (recipes); confirm placement of the resulting wiring with this skill |
| Authoring or auditing widget code | both: this skill for where the widget config lives, neighbour for the React-side patterns and CSP |
| Migrating from a different MCP server SDK | neighbour skill's migration cluster; reapply this skill's layout afterwards |

A common mistake is loading the neighbour skill alone for a "small" change and then watching the change cascade because the new code landed in the wrong layer. If the change touches files outside the test directory, this skill is in scope.

## Verification checklist

Before claiming a handoff is correct, observe each of these.

- Every cross-skill route in the output names the destination skill explicitly (`build-mcp-use-server` or `apply-clean-mcp-architecture`) and the section / cluster within it. No bare "see the other skill."
- No part of the answer paraphrases content from the neighbour skill's SKILL.md or its references. If the answer contains more than one sentence about an `mcp-use` API, the answer is paraphrasing.
- Every stated rule has a **why** line that names the failure mode. If the failure mode is "the SDK requires it," the rule should not be in the answer at all — it belongs in the neighbour skill.
- The user can act on the answer using exactly one skill at a time. No context flip is required between both for a single decision.
- When the request blends layers and mechanics, split it explicitly: "for X, follow `apply-clean-mcp-architecture`; for Y, follow `build-mcp-use-server`."
