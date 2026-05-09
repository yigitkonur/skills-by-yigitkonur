# Anti-patterns observed across the reference repos

> This reference expands the SKILL.md sections "Common mistakes" and "Hard guardrails — non-negotiable." It catalogues the concrete drift observed in the reference repos (`mcp-ads-meta` is the primary source; `mcp-d4s`, `mcp-ads-google`, and `mcp-gsc` contributed lower-grade smells). After reading it you should be able to recognise each anti-pattern in a code review, justify why it is wrong, point at a concrete repo file that exhibits it, and apply a fix that lands the code on the canonical pattern in `references/define-tool-pattern.md` and `references/handler-context.md`.

Every entry follows the same shape: **Anti-pattern**, **Why it's bad**, **Concrete repo example**, **Fix**, **How to detect**. If an entry has no concrete repo example, it does not appear here. Audit signals (greps, `dependency-cruiser` rules) target patterns visible in the reference repos at the time of writing — adapt path globs to your own repo before pasting them into CI.

## Handlers

### 1. Monolithic feature file with several tools registered side-by-side

- **Anti-pattern:** A single `tools/<feature>.ts` file (or worse, a `.ts` file in `tools/` that re-exports from a sibling `<feature>/` folder) that registers many tools through a sequence of `server.tool({ ... }, async (args, ctx) => ...)` calls. The file is hundreds of lines, mixes schemas, error helpers, compact-summary mappers, and inline business decisions.
- **Why it's bad:** A failure in one tool's wiring breaks every other tool that imports the same file; testing requires importing the whole module; cross-cutting middleware cannot be applied uniformly because each `server.tool` call sites its own log lines and error mappers; the `mcp-use` import pollutes the whole module so any cross-layer leak (e.g. a use-case helper imported here) inherits the SDK dependency.
- **Concrete repo example:** `mcp-ads-meta/src/tools/auth.ts` (475 lines, registers many auth tools, hand-rolled error envelope helpers inline), `mcp-ads-meta/src/tools/lead-forms.ts` (459 lines), `mcp-ads-meta/src/tools/accounts.ts` (477 lines), `mcp-ads-meta/src/tools/result-sets/register.ts` (508 lines registering the result-set toolset in one file).
- **Fix:** Split into one file per tool under `src/handlers/<feature>/<tool>.handler.ts`. Each file exports one `createXHandler(useCase, presenter)` factory that returns `defineTool({ ... })`'s output. The composition root collects them. See `references/define-tool-pattern.md` for the canonical shape; `mcp-d4s/src/handlers/analyze-domain.handler.ts` is the model.
- **How to detect:** `find src/tools src/handlers -name '*.ts' -not -name 'index.ts' -exec wc -l {} \; | awk '$1 > 200'` flags suspicious modules. A `dependency-cruiser` rule rejects more than one `server.tool(` invocation per file: a forbidden regex of `/server\.tool\(/g` with a count threshold of 1.

### 2. Direct `server.tool()` call instead of `defineTool()`

- **Anti-pattern:** A handler module imports `MCPServer` from `mcp-use/server` and calls `server.tool({ name, schema, ... }, async (args, ctx) => ...)` directly. There is no factory; the registration happens at import time or inside an exported `register*` function called from a barrel.
- **Why it's bad:** The shared registration pipeline (`withPipeline`) cannot wrap the handler uniformly; annotations, default `outputSchema`, and `nextSteps` dual-rendering must be re-implemented per tool; the `MCPServer` reference threads through the handler module, breaking the rule that only the composition root mentions it.
- **Concrete repo example:** `mcp-ads-meta/src/tools/campaigns/list-campaigns.handler.ts` (calls `server.tool(...)` directly inside `registerListCampaignsTool`), and the analogous shape in `mcp-ads-meta/src/tools/audiences/create-audience.handler.ts`. Compare against `mcp-d4s/src/handlers/analyze-domain.handler.ts` which returns from `defineTool(...)` and never sees `server`.
- **Fix:** Introduce a `src/handlers/define-tool.ts` factory whose contract matches `references/define-tool-pattern.md`. Refactor each `register*Tool(server, client)` into a `create*Handler(useCase, presenter)` that returns `AnyToolDefinition`. Bootstrap calls `server.tool(tool.definition, withPipeline(tool.execute, tool.TOOL_NAME))`.
- **How to detect:** `grep -rn "server\.tool(" src/handlers src/tools` should match only files in `src/infrastructure/server/`. Any other hit is a finding.

### 3. Handler imports a concrete client/gateway

- **Anti-pattern:** A handler module's import list includes a concrete client type (e.g. `MetaAdsGateway` as the actual concrete class, a Redis client, a Google Ads SDK class) and the registration function takes that concrete as an argument: `register*Tool(server: MCPServer, client: MetaAdsGateway): void`.
- **Why it's bad:** The handler can no longer be unit-tested without standing up a real gateway; the layer rule "handlers depend on `application/` use cases via injected ports" is silently violated; the gateway's SDK shape leaks through the handler into the LLM-visible behaviour.
- **Concrete repo example:** `mcp-ads-meta/src/tools/campaigns/list-campaigns.handler.ts` takes `MetaAdsGateway` directly (`function registerListCampaignsTool(server: MCPServer, client: MetaAdsGateway): void`) and then calls `autoPaginate(client, ...)` inline rather than going through a use case.
- **Fix:** The handler factory accepts a use case and a presenter. The use case constructor receives the gateway port. Bootstrap wires the chain: gateway -> use case -> handler. The handler never imports a gateway type. See `references/handler-context.md` for the seam.
- **How to detect:** `dependency-cruiser` rule that forbids `src/handlers/**` from importing `src/gateways/**` or any module exporting a class whose name ends in `Gateway`/`Client`/`Store`/`Adapter`.

### 4. Handler does business logic and provider branching

- **Anti-pattern:** Inside the `execute` body, the handler branches on input fields to choose providers, builds upstream request bodies, runs filters, or formats responses for the wire. The `execute` function exceeds ~50 lines.
- **Why it's bad:** Business logic in the handler is invisible to the use case test surface; the rule that the handler is a thin parse-delegate-render shim breaks; cross-cutting middleware (cost-meter, redaction) cannot reason about the work it now does.
- **Concrete repo example:** `mcp-ads-meta/src/tools/campaigns/list-campaigns.handler.ts` builds filters inline via `buildCampaignFilters`, calls `autoPaginate` directly against the gateway, and shapes a compact summary in the same `async (args, ctx) => ...` body — there is no use case between the handler and the gateway. Contrast `mcp-d4s/src/handlers/analyze-domain.handler.ts` whose `execute` body is alias preprocessing + `useCase.analyzeDomain(input)` + `presenter.render(...)`.
- **Fix:** Extract every line that touches provider request shapes, filters, or response transforms into `src/application/<feature>/<feature>.usecase.ts`. The handler's `execute` keeps only: derive the use-case command from `args`, await the use case, render through the presenter.
- **How to detect:** Per-handler line-count check: `awk '/execute: async/,/^[[:space:]]*}\)/{c++} END{print c}'` should report under ~40 lines per handler; manual review for any control flow that depends on input field values inside `execute`.

## Use cases / application layer

### 5. Missing application layer

- **Anti-pattern:** The repo has `src/tools/` (or `src/handlers/`), `src/domain/`, `src/gateways/`, `src/infrastructure/`, but **no** `src/application/` (or `src/use-cases/`) directory — or it exists but contains only "shared" helpers, not real per-feature use cases. Handlers call gateways directly.
- **Why it's bad:** The skill's whole layered model rests on the use case being the unit the handler delegates to and the test mocks. Without it, every handler test must mock the gateway shape, every business rule lives at the handler edge, and refactoring across tools that share a workflow is impossible without copy-paste.
- **Concrete repo example:** `mcp-ads-meta/src/use-cases/` contains only `analytics/`, `insights/`, and `shared/` — all of `src/tools/campaigns/`, `src/tools/audiences/`, `src/tools/ads/`, `src/tools/conversions/`, `src/tools/creatives/`, `src/tools/lead-forms.ts`, `src/tools/insights.ts` etc. have no matching use-case file.
- **Fix:** Create `src/application/<feature>/<feature>.usecase.ts` per feature. Move the orchestration out of the handler (gateway calls, filtering, transforms) into the use case. The use case takes ports via its constructor; bootstrap wires concrete gateways behind those ports.
- **How to detect:** For every `src/handlers/<feature>/` (or `src/tools/<feature>/`) directory, confirm a matching `src/application/<feature>/` exists. CI script: `comm -23 <(ls src/handlers) <(ls src/application)` should produce empty output (after filtering shared directories).

### 6. Use case imports `mcp-use`

- **Anti-pattern:** A file under `src/use-cases/` or `src/application/` imports from `mcp-use/server` (or `@modelcontextprotocol/sdk`). Common slip: a "shared" helper in `use-cases/shared/` calls `object()`, `text()`, or `error()` to build a response.
- **Why it's bad:** Couples business logic to the wire shape and the SDK version; makes the use case impossible to unit-test without a `mcp-use` runtime; SDK changes ripple into every use case that imports the helper.
- **Concrete repo example:** `mcp-ads-meta/src/use-cases/shared/dry-run.ts` line 15: `import { object } from "mcp-use/server";` — this helper is then invoked from every write-tool handler, so the SDK dependency reaches half the surface.
- **Fix:** Move the response-construction step out of the use case. The use case returns a framework-free `ToolResponse` (a domain object); the presenter, sitting in `src/presenters/`, is the only file allowed to import `mcp-use` response helpers (`text`, `object`, `mix`, `error`). For dry-run specifically, the use case returns a typed `DryRunPreview` discriminated union; the presenter renders it.
- **How to detect:** `dependency-cruiser` rule forbidding `src/application/**` and `src/use-cases/**` from importing anything matching `^mcp-use(/.*)?$` or `^@modelcontextprotocol/sdk(/.*)?$`. Run `grep -rn "from .mcp-use" src/application src/use-cases` — every hit is a finding.

### 7. Monadic-envelope return types in inner layers

- **Anti-pattern:** Use cases or domain services return a custom `Ok` / `Err` envelope ("`ok`-or-fail" tuple shapes, success/failure tagged unions used as a control-flow primitive). Each caller has to invent a check (`if (envelope.ok) ... else ...`). The error half is built by the use case rather than thrown.
- **Why it's bad:** This skill locks throw/catch with a `DomainError` hierarchy at the boundary mapper. Mixing envelope-style returns with throwing gateways forces every caller to translate; the boundary mapper cannot reason uniformly about failure paths.
- **Concrete repo example:** Not directly present in the reference repos (the skill's locked decision is to throw); the failure mode is observable as the *risk* in any new codebase that ports patterns from the legacy `apply-clean-architecture` skill, which used envelope examples. The dropped-rule note in `/tmp/apply-clean-mcp-arch-workspace/distilled-apply-clean-architecture.md` flags this conflict explicitly. (Treated here as a guard; if your repo already has this shape, it qualifies as the concrete example: e.g. any `src/application/**/*.usecase.ts` whose return type uses `ok(...)` / `err(...)` constructors.)
- **Fix:** Throw a `DomainError` subclass with `code`, `recoveryHint`, `isRetryable`. Catch only at layer boundaries (handler edge -> JSON-RPC envelope; gateway edge -> classify and rethrow as `DomainError`). Use cases and entities do not catch.
- **How to detect:** `grep -rn "return ok(\|return err(\|: Ok<\|: Err<" src/application src/use-cases src/domain` — every hit is a finding.

## Gateways / ports

### 8. Generic over-typed gateway port that returns `<T>` everywhere

- **Anti-pattern:** A single port interface like `interface MetaAdsGateway { get<T>(path: string, params?: Record<string, unknown>): Promise<T>; post<T>(...): Promise<T>; ... }` covers every conceivable upstream call. The use case picks the type parameter at the call site.
- **Why it's bad:** The port is not a domain capability; it is a typed `fetch`. Use cases now know about HTTP paths, request bodies, and pagination shapes — the gateway is no longer hiding the provider. Error classification cannot live behind the port because every method returns the raw upstream payload typed as `T`.
- **Concrete repo example:** `mcp-ads-meta/src/domain/ports.ts` line 8: `export interface MetaAdsGateway { get<T>(path: string, params?: Record<string, unknown>): Promise<T>; ... }`. The handler `mcp-ads-meta/src/tools/campaigns/list-campaigns.handler.ts` then calls `autoPaginate<CampaignRecord>(client, '/${accountId}/campaigns', ...)` — the path string and the response shape are leaking through the port.
- **Fix:** Replace the generic port with capability-named ports per feature: `interface ICampaignReader { listForAccount(accountId: AccountId, filter: CampaignFilter): Promise<readonly Campaign[]> }`. The adapter in `gateways/` knows the HTTP path; the use case knows only the capability. Errors are classified inside the adapter and rethrown as `DomainError`.
- **How to detect:** `grep -rn "Promise<T>" src/domain/ports*.ts src/domain/ports/` — generic port methods returning bare `T` are the smoking gun.

### 9. Provider error reaches the handler unclassified

- **Anti-pattern:** The gateway throws (or rethrows) the provider SDK's error class as-is. The handler — or worse, the use case — has to type-check `if (caught instanceof RateLimitError) ... else if (caught instanceof GraphApiError) ...` to decide what to do.
- **Why it's bad:** Provider exception types are SDK churn risks; the use case becomes coupled to the provider; recovery hints are scattered (every handler invents its own message); the LLM gets inconsistent guidance.
- **Concrete repo example:** `mcp-ads-meta/src/tools/campaigns/list-campaigns.handler.ts` calls `handleCampaignError("list-campaigns", caught, ctx)`, which (per the project's `tools.md` rule) does the `if (caught instanceof RateLimitError) ... if (caught instanceof GraphApiError) ...` branch tree at the handler edge. Every monolithic tool module re-implements this same dispatch.
- **Fix:** Inside the gateway adapter (`src/gateways/<provider>/`), catch the SDK error, classify into a `DomainError` subclass (`RateLimitDomainError`, `UpstreamProviderError`, `AuthRevokedError`, ...) with `code`, `recoveryHint`, `isRetryable`, and rethrow. The handler does not catch; the boundary mapper installed in `bootstrap.ts` translates `DomainError` to the JSON-RPC envelope.
- **How to detect:** `grep -rn "instanceof.*Error" src/handlers src/tools src/application` — every hit indicates classification leaking outward; it should appear only inside `src/gateways/**` and `src/infrastructure/errors/**`.

### 10. Caching/decorator wiring outside the composition root

- **Anti-pattern:** A use case or a handler instantiates `new CachingProviderGateway(new RetryingGateway(new ConcreteGateway(...)))` inside its own module. Or a feature folder owns a `caching.ts` that mutates a global gateway reference at import time.
- **Why it's bad:** Decorator order is a deploy-time choice; embedding it in the use case file means tests cannot opt out; cold-start regressions (at-import-time wiring) become invisible; the layer rule "concrete construction lives in `bootstrap.ts` only" is broken.
- **Concrete repo example:** `mcp-ads-meta/src/use-cases/shared/dry-run.ts` (a use-case-layer module) imports `{ object } from "mcp-use/server"` and effectively shapes the response — same pattern as decorator-leak. (For a decorator-stacking example specifically, see any repo where `gateways/` exports a fully-wrapped instance rather than a class — the smell is structurally identical.)
- **Fix:** Construct decorators in `src/infrastructure/server/bootstrap.ts` only. Pass the wrapped instance into use cases via constructor injection. Each gateway file in `src/gateways/` exports the class, not a pre-wrapped singleton.
- **How to detect:** `grep -rn "new .*Gateway(\|new .*Decorator(" src/application src/use-cases src/handlers src/tools` — every hit is a finding.

## Presenters / response shaping

### 11. Hand-rolled error envelopes scattered across handlers

- **Anti-pattern:** Each handler module defines its own `errorEnvelopeResult({...})` builder, or imports a project-wide one and calls it inline whenever an error is caught. The presenter is bypassed.
- **Why it's bad:** Error envelopes drift between handlers; secret-redaction policy is duplicated and decays; the rule "the presenter is the only file that shapes `CallToolResult`" breaks; the boundary mapper's job overlaps with the handler's.
- **Concrete repo example:** `mcp-ads-meta/src/tools/auth.ts` line 4 imports `errorEnvelopeResult from "../presenters/error-envelope.js"` and calls it at handler-edge sites (line 280, line 398). The auth handler catches a domain error and shapes the envelope itself rather than letting the boundary mapper translate.
- **Fix:** Use cases throw `DomainError` subclasses. The boundary mapper installed by `bootstrap.ts` (`src/infrastructure/errors/error-contracts.ts`) translates `code` -> JSON-RPC envelope. The presenter renders **success** envelopes only; failure envelopes are the boundary mapper's job. Delete handler-edge error envelopes once the mapper is in place.
- **How to detect:** `grep -rn "errorEnvelopeResult\|buildErrorEnvelope" src/handlers src/tools` — every hit indicates a missing boundary mapper. The mapper should be registered once in `bootstrap.ts`.

### 12. Response built inline in the handler instead of via the presenter

- **Anti-pattern:** The handler `execute` body returns `object({ ... })` (or `text(...)`, or a hand-built `{ content: [...], structuredContent: {...} }` object) directly. There is no presenter call.
- **Why it's bad:** Same axis as #11. Provenance fields (cache flags, internal IDs) leak into the wire because there is no humble-object scrubbing layer; preview policy (row caps, TSV vs JSON, redaction) is reinvented per handler; widget payloads cannot be shaped uniformly.
- **Concrete repo example:** `mcp-ads-meta/src/tools/campaigns/list-campaigns.handler.ts` returns `object({ count, items, ... })` directly inside `execute`. There is no `presenter.render(...)`.
- **Fix:** Use cases return a domain `ToolResponse` object. The handler calls `presenter.render(response)`. The presenter (`src/presenters/mcp-presenter.ts`) is the **only** file that imports `mcp-use` response helpers and the only file that decides preview policy.
- **How to detect:** `grep -rn "return object(\|return text(\|return mix(\|return error(" src/handlers src/tools` — every hit outside `src/presenters/` is a finding.

## Infrastructure / wiring

### 13. Barrel cascades across feature folders

- **Anti-pattern:** Every feature folder under `src/tools/` or `src/handlers/` ships an `index.ts` that re-exports its siblings. Importing one tool transitively loads them all.
- **Why it's bad:** Cold-start cost in serverless deploys is proportional to the loaded module count; circular dependencies become possible the moment two feature folders cross-reference; tree-shaking cannot prune dead code; the dependency graph that `dependency-cruiser` would otherwise enforce gets blurred.
- **Concrete repo example:** `mcp-ads-meta/src/tools/audiences/index.ts` re-exports four sibling handlers, `mcp-ads-meta/src/tools/insights/index.ts`, `mcp-ads-meta/src/tools/reporting/index.ts`, `mcp-ads-meta/src/tools/ad-sets/index.ts`, `mcp-ads-meta/src/tools/intelligence/index.ts`, plus the top-level `mcp-ads-meta/src/tools/index.ts` (191 lines of imports + a `registerAllTools(server, client, ...)` function).
- **Fix:** Direct imports only. `bootstrap.ts` imports each handler factory by file path: `import { createAnalyzeDomainHandler } from '../../handlers/domain/analyze-domain.handler.js'`. No `index.ts` files in `src/`.
- **How to detect:** `find src -name 'index.ts' -not -path 'src/index.ts'` — every hit is a finding (the top-level `src/index.ts` is the entry stub and is allowed). A `dependency-cruiser` rule forbids any module in `src/handlers/**` or `src/application/**` from importing a path ending in `index.js` (the `.ts` -> `.js` rewrite under NodeNext makes this the lint-time check).

### 14. Multiple composition roots

- **Anti-pattern:** More than one file in the repo instantiates `MCPServer`, registers tools, or calls `new ConcreteGateway(...)`. Common shape: a top-level `register*Tools(server, ...)` in `src/tools/index.ts` plus another path in `src/index.ts` plus a third in some testing harness.
- **Why it's bad:** Bootstrap order is load-bearing (config -> infra -> gateways -> use cases -> handlers -> server -> middleware -> tools -> resources -> prompts -> error mapping -> start). Splitting it across files makes the order invisible; one path drifts; the system behaves differently in tests vs production for reasons no one can pinpoint.
- **Concrete repo example:** `mcp-ads-meta/src/tools/index.ts` runs `registerAllTools(server, client, analyticsRuntime, config, resultSetRegistry)` doing real wiring (line 70 onward), while `mcp-ads-meta/src/infrastructure/bootstrap.ts` is supposed to be the composition root. The actual tool-registration ordering is split across both.
- **Fix:** Collapse all wiring into `src/infrastructure/server/bootstrap.ts`. Feature modules export factories (`createXHandler`); the bootstrap calls them in the documented order. `src/index.ts` is a thin entry stub that calls `await bootstrap()` and starts the server. Nothing else constructs concrete gateways.
- **How to detect:** `grep -rn "new MCPServer(\|server\.tool(\|server\.resource(\|server\.prompt(" src` — every hit must be in exactly one file (`src/infrastructure/server/bootstrap.ts`).

### 15. Scattered `process.env` reads

- **Anti-pattern:** Use cases, gateways, handlers, or response builders read `process.env.<KEY>` directly (often "just for a feature flag"). The `infrastructure/config/runtime-config.ts` rule is broken silently.
- **Why it's bad:** Tests must set env vars to construct the unit; multi-tenant config leaks across requests; missing-secret diagnostics are spread across the codebase rather than centralised; type narrowing on env values rots.
- **Concrete repo example:** `mcp-ads-meta/src/infrastructure/auth/config.ts` reads `process.env` (acceptable — it lives under `infrastructure/config*`); but the `META_ADS_MCP_ENABLED_GROUPS`-style logic referenced in `mcp-ads-meta/CLAUDE.md` ("`META_ADS_MCP_ENABLED_GROUPS` changes the visible surface") indicates env-flag branching was historically scattered. Any new repo that has `grep -rn "process.env" src --include='*.ts' | grep -v "src/infrastructure/config"` returning hits is in this state.
- **Fix:** All `process.env` reads in one file: `src/infrastructure/config/runtime-config.ts`. The file uses Zod to validate the env shape and exports a typed `runtimeConfig` object. Other modules receive the values via constructor injection.
- **How to detect:** A `dependency-cruiser` rule forbidding any file outside `src/infrastructure/config/**` from importing `process.env` references; or the explicit grep above as a CI gate.

## Types / contracts

### 16. Single shared DTO across handler / use case / gateway / presenter

- **Anti-pattern:** A type defined in `domain/` (or worse, exported from a barrel) is used as the shape for the handler input, the use-case command, the gateway request, the gateway response, and the presenter row. "DRY" was the reason; "provenance leak" is the consequence.
- **Why it's bad:** When the gateway adds a cache-tag field, it surfaces in the LLM-visible structured content; when the use case adds an internal cost-metric, it leaks into the upstream HTTP request body; refactoring the upstream provider's shape forces a coordinated edit across every layer.
- **Concrete repo example:** `mcp-ads-meta/src/domain/ports.ts` exports `interface AdLibraryResponse { data: Record<string, unknown>[]; paging?: { ... }; rate_limit_warning?: string; rate_limit_consumed?: { used: ...; remaining: ...; reset_at: ... } }` — the upstream paging shape and rate-limit metadata are co-mingled in the same type the use case sees, so any handler that returns `data` directly leaks `rate_limit_consumed`.
- **Fix:** Five distinct types: handler input, use-case command, gateway request, gateway response, presenter row. Map between them explicitly; do not collapse. Cache provenance / paging metadata stays inside the gateway type and is dropped in the mapping step before crossing into the use case.
- **How to detect:** `grep -rn "import type .*Response.*}.*ports" src/handlers src/application` — handler / use-case files importing a gateway-response type directly are findings.

### 17. `z.any()` / `z.unknown()` in a tool input schema

- **Anti-pattern:** A handler's Zod schema declares a field as `z.any()` or unconstrained `z.unknown()`, often as a "passthrough" parameter. Sometimes it slips into the root via `z.object({ ... }).passthrough()`.
- **Why it's bad:** The LLM gets no hint about acceptable input; payloads can be arbitrarily large; the upstream provider 4xx-storms; the validation boundary the skill defends collapses.
- **Concrete repo example:** Not directly present in the locked schemas of the reference repos (the project lints against it). But the pattern recurs in any module that "temporarily" accepts a generic `Record<string, unknown>` input. As a generic check, `grep -rn "z.any()\\|z.unknown()" src/handlers src/tools` flags every site; the failure mode appears in any new code that copies the legacy shape from `mcp-ads-meta/src/domain/ports.ts`'s `AdLibrarySearchParams { [key: string]: unknown }` into a tool schema.
- **Fix:** Concrete schema with `.strict()` on the root and bounded fields (enum, regex, min/max, ISO date pattern). Refer to `build-mcp-use-server`'s `references/04-tools/` for the field-level rules; this skill insists only that the rule be applied at the handler boundary.
- **How to detect:** `grep -rn "z\.any()\|z\.unknown()" src/handlers src/tools` — every hit is a finding. CI: ESLint rule `no-restricted-syntax` matching `CallExpression[callee.object.name='z'][callee.property.name=/^(any|unknown)$/]`.

### 18. `private` keyword on entity fields instead of `#`

- **Anti-pattern:** A domain entity uses `private fieldName: T` to mark internal state. The compiler enforces visibility at type-check time only.
- **Why it's bad:** `as any` shortcuts (which appear in any MCP-typed codebase eventually) bypass the visibility check at runtime. Invariants the entity claims to protect are not protected.
- **Concrete repo example:** Any entity in `mcp-ads-meta/src/domain/value-objects.ts` that uses `private` for internal state. (The reference repo's value objects are mostly thin newtype wrappers; the failure mode appears as soon as a real entity with invariants is added.) Compare to `mcp-d4s/src/domain/dataset/dataset-id.ts` which uses `#`-private fields.
- **Fix:** Replace `private fieldName` with `#fieldName`. Update accessors. The transition is mechanical.
- **How to detect:** `grep -rn "^[[:space:]]*private " src/domain` — every hit on an entity (not a port) is a finding.

## What you must verify before finishing

Before claiming you have caught a repo's drift, observe each of these.

- For every anti-pattern flagged in your audit report, you cite a file path that exists. `ls <path>` resolves; the line numbers are within the current file length.
- The grep / `dependency-cruiser` detection rule for each finding actually returns the cited hit. You ran it; you did not assume.
- Every finding maps to a specific fix in `references/define-tool-pattern.md`, `references/handler-context.md`, `references/composition-root.md`, `references/gateways-and-ports.md`, or this file. No "vague refactor" findings.
- The fix path is independently revertable (one PR, one layer) per the refactor playbook in `references/refactor-playbook.md`. You did not bundle handler splits with gateway re-typing in one diff.
- When the cited example is from a reference repo (not the user's), you flagged it as a comparison anchor, not as the user's bug. The user's repo gets its own anti-pattern citations from its own grep output.
