# Refactor Playbook

> SKILL.md routes here when you pick the **Refactor** mode — an MCP server with a `src/` tree that has drifted from the standard. The canonical drift example is `mcp-ads-meta` (monolithic `src/tools/<feature>.ts` files like `src/tools/lead-forms.ts` at ~459 lines and `src/tools/accounts.ts` at ~477 lines, inline `server.tool(...)` registrations across 154 files importing `mcp-use`, no `handlers/` folder at all, a thin `application/` / `use-cases/` layer that covers only `analytics`, `insights`, and `shared/`, and `process.env` reads scattered through `src/infrastructure/config.ts` and `src/infrastructure/auth/config.ts`). After working through this file, you should be able to land seven small PRs that flip the architecture inside-out — config seam first, gateways next, then use cases, handlers, bootstrap, presenter and error contracts, and finally the TypeScript quality bar — each PR independently revertable, each gated by a fresh `dependency-cruiser` rule that activates only after the PR merges.

The order is fixed because the order is architectural. Every later PR depends on the seams the earlier PRs introduced. Resist the urge to merge them out of order or to combine two — that is exactly the big-bang the playbook is here to prevent.

Before you start: read `mcp-ads-meta/src/tools/lead-forms.ts`, `mcp-ads-meta/src/tools/accounts.ts`, and `mcp-ads-meta/src/index.ts` so you have a concrete picture of the drift. The patterns named below are visible there.

## PR 1 — Config seam

Goal (observable outcome): every `process.env` read in the repo is concentrated inside `src/infrastructure/config/runtime-config.ts`. Inner layers receive resolved config values via constructor injection. The post-merge `dependency-cruiser` rule fails the build the moment any other file reads `process.env` again.

Files moved/changed (mapped onto `mcp-ads-meta` for concreteness — adapt to the target repo):
- Create `src/infrastructure/config/runtime-config.ts` and `src/infrastructure/config/validate.ts` (Zod env schema).
- Migrate the env reads currently in `src/infrastructure/config.ts` (lines around 19, 32, 42, 136, 287, 337) into the new file. Replace each call site with a parameter on the consumer's constructor.
- Migrate the env reads currently in `src/infrastructure/auth/config.ts` (lines around 146 and 195 that default to `process.env`) into the same seam. The auth module receives a typed `RuntimeOAuthConfig` from bootstrap.
- Delete the legacy `src/infrastructure/config.ts` only if it is empty after the move; otherwise leave a re-export shim and remove it in a follow-up commit inside the same PR.
- Add `.env.example` at the repo root listing every variable the schema requires.

Dependency-cruiser rule activated after merge:

```
{
  name: 'no-env-outside-config-seam',
  severity: 'error',
  comment: 'Only runtime-config may read process.env',
  from: { pathNot: '^src/infrastructure/config/runtime-config\\.ts$' },
  to:   { path: 'process\\.env' }
}
```

Smoke test (proves no behaviour regressed): start the server with the same `.env` you used before the PR and call one read-only tool through `mcpc --no-profile` (or the `mcp-use` Inspector). The response shape and content match the pre-PR baseline. Capture both runs to a file and `diff`.

Rollback path: revert PR 1. Inner layers go back to reading `process.env` directly. The depcruise rule is removed with the revert. Nothing later depends on this PR yet, so the working tree compiles cleanly.

## PR 2 — Gateway isolation

Goal (observable outcome): every external API call lives behind a port in `src/domain/ports/` with a concrete adapter in `src/gateways/<provider>/`. Decorators (cache → retry → sanitise → concrete) are wired explicitly. Use cases see only the port. Provider error types stop at the gateway and re-throw as `DomainError` subclasses.

Files moved/changed:
- Create `src/domain/ports/<capability>-gateway.port.ts` for each capability the existing tools need (Graph API list/get/create, ad library snapshots, audience operations, insights). Name ports by capability ("ListAdsGateway"), not storage ("MetaSdkClient"). The port file imports nothing outside `src/domain/`.
- Create `src/gateways/meta-graph/meta-graph-gateway.ts` (or the equivalent for the target provider). Move the SDK / HTTP-client calls currently buried inside `src/tools/lead-forms.ts`, `src/tools/accounts.ts`, `src/tools/ad-library.ts`, etc. into this gateway. The pre-existing `src/domain/upstream-errors.ts` types (`GraphApiError`, `RateLimitError`) are caught at the gateway and re-thrown as `DomainError` subclasses (`ProviderError`, `RateLimitError` whose `isRetryable` flag is set correctly).
- Create decorator adapters: `src/gateways/caching-<capability>-gateway.ts`, `src/gateways/retrying-<capability>-gateway.ts`, `src/gateways/sanitising-<capability>-gateway.ts`. Each implements the same port and delegates to the next.
- Move shared helpers like `mcp-ads-meta/src/use-cases/shared/pagination.ts` into the gateway (it is a transport concern), or wrap it in a port if a use case truly needs it.
- Replace the direct `from "mcp-use/server"` imports inside the tool files with calls to the use case (which still does not exist as of this PR — the temporary stop is a use-case-shaped helper inside the same tool file, removed in PR 3).

Dependency-cruiser rule activated after merge:

```
{
  name: 'no-mcp-use-in-gateways-or-domain',
  severity: 'error',
  comment: 'Provider adapters and domain layer must be SDK-free',
  from: { path: '^src/(gateways|domain)' },
  to:   { path: 'mcp-use|@modelcontextprotocol/sdk' }
}
```

Plus tighten the import matrix: `^src/gateways` may not import `^src/(application|handlers|presenters)`.

Smoke test: call one read-only tool via `mcpc` and assert the response matches the PR 1 baseline. Also assert that an upstream 429 (induce by running against a throttled token, or by injecting a fake gateway in a test) surfaces to the model as a `RATE_LIMIT` `DomainError` envelope with `isRetryable: true`, never as a raw `GraphApiError`.

Rollback path: revert PR 2. The provider calls move back into the tool files; PR 3 has not landed yet, so no use case depends on the port. The depcruise rule is removed with the revert.

## PR 3 — Use cases

Goal (observable outcome): every tool's orchestration lives in a `src/application/<feature>/<feature>.usecase.ts` (or `src/use-cases/<feature>/<feature>.usecase.ts` if the repo prefers the legacy name — be consistent). Use cases depend only on `domain/` and `shared/`. They take ports via constructor injection and return a `ToolResponse` (domain object) or throw a `DomainError`. No `mcp-use` import inside.

Files moved/changed (mapping `mcp-ads-meta` drift):
- Carve `mcp-ads-meta/src/tools/lead-forms.ts` into one use case per public tool name. Each lands as `src/application/lead-forms/<tool>.usecase.ts`. The branching logic that currently lives inside one giant `server.tool(...)` callback is split per branch.
- Repeat for `src/tools/accounts.ts`, `src/tools/ad-library.ts`, `src/tools/auth.ts`, `src/tools/advantage-plus.ts`, and `src/tools/ad-library-snapshots.ts` — every monolithic tool file becomes a folder of use cases.
- Move pure data-shape helpers (no I/O, no SDK use) into `src/application/<feature>/<feature>-transforms.ts` neighbours.
- Promote the existing `src/use-cases/analytics/` and `src/use-cases/insights/` folders to the same naming convention — they are already partway there.
- Stop the use case from constructing concrete gateways. Bootstrap will inject them in PR 5; meanwhile the temporary "wired in the tool file" hand-off remains until PR 4 cuts the handler boundary.

Dependency-cruiser rule activated after merge:

```
{
  name: 'application-may-only-import-domain-shared',
  severity: 'error',
  from: { path: '^src/application' },
  to:   { pathNot: '^src/(application|domain|shared)' }
},
{
  name: 'no-mcp-use-in-application',
  severity: 'error',
  from: { path: '^src/application' },
  to:   { path: 'mcp-use|@modelcontextprotocol/sdk|^src/(handlers|gateways|presenters|infrastructure|resources|prompts)' }
}
```

Smoke test: write a unit test per new use case that injects a fake port (in-memory adapter implementing the port directly) and asserts the returned `ToolResponse`. Also rerun the `mcpc` round-trip from PR 1 and assert the response remains shape-equivalent.

Rollback path: revert PR 3. Orchestration falls back into the tool files. The depcruise rules are removed with the revert. Tests in `src/__tests__/application/` are removed alongside.

## PR 4 — Handlers

Goal (observable outcome): every public MCP tool has its own file under `src/handlers/<feature>/<tool>.handler.ts`, built with `defineTool()`. The handler parses input via Zod (`.strict()` + `.describe()`), builds a `Command` object, calls the use case, hands the `ToolResponse` to the presenter, and returns the `CallToolResult`. There are no inline `server.tool(...)` calls anywhere outside bootstrap.

Files moved/changed:
- Create `src/handlers/define-tool.ts` (the factory) and `src/handlers/context.ts` (the `HandlerContext` interface).
- Create `src/handlers/schemas/` with shared Zod field fragments. Move the existing alias-normalisation patterns (e.g. the `data_type` alias preprocess) into the handler schema layer; the use case sees only canonical values.
- For each use case in PR 3, create the matching `src/handlers/<feature>/<tool>.handler.ts` file. Annotations must declare `destructiveHint` and `idempotentHint` honestly; `title` is provided.
- Replace each `server.tool(...)` call in `mcp-ads-meta/src/tools/<feature>.ts` with a `defineTool({...})` export. The tool files become 1-import-thick shims while PR 5 collapses them.

Dependency-cruiser rule activated after merge:

```
{
  name: 'one-tool-per-file',
  severity: 'error',
  comment: 'Handler files must export exactly one DefinedTool',
  from: { path: '^src/handlers/.*\\.handler\\.ts$' },
  // enforced via lint rule + path glob; depcruise checks the dependency direction
  to:   { pathNot: '^src/(domain|application|presenters|shared|handlers)' }
},
{
  name: 'handlers-no-direct-gateway',
  severity: 'error',
  from: { path: '^src/handlers' },
  to:   { path: '^src/gateways' }
}
```

Smoke test: replay every public tool through `mcpc --json @target tools-call <name> '{...}'` against the same fixtures the repo's existing tests use. Assert response equivalence with the pre-PR-1 baseline. Run `grep -rn "server\\.tool(" src/` and confirm only `src/infrastructure/server/bootstrap.ts` (or the location PR 5 will introduce) calls it once per tool, via the registered `defineTool` factory output — and that no path under `src/tools/` does.

Rollback path: revert PR 4. `defineTool()`-based handlers disappear; the tool files retain their use-case calls from PR 3. Bootstrap (PR 5) does not exist yet, so the working tree still compiles using the pre-PR-4 `server.tool(...)` registrations restored by the revert.

## PR 5 — Bootstrap

Goal (observable outcome): construction lives in exactly one place — `src/infrastructure/server/bootstrap.ts`. No other file constructs gateways, instantiates `MCPServer`, or registers tools/resources/prompts. The order is locked.

Files moved/changed:
- Create `src/infrastructure/server/bootstrap.ts`.
- Move every `new ConcreteGateway(...)` call from where it currently lives (likely `src/index.ts`, the legacy `src/infrastructure/bootstrap.ts` if present, and possibly inside the tool files) into the new bootstrap.
- Apply the locked construction order:
  1. Call `loadRuntimeConfig()` first.
  2. Build cross-cutting infrastructure: logger, Redis client, OAuth provider.
  3. Build concrete gateways and wrap each in the decorator stack `Caching(Retrying(Sanitising(Concrete(...))))`.
  4. Build use cases; inject each its ports via the constructor.
  5. Build handlers by calling `defineTool()` once per tool.
  6. `new MCPServer(...)`; mount the middleware pipeline (request context, logging, error mapping) on it.
  7. Register the tool list, then the resource list, then the prompt list — in that fixed order.
  8. Install the error-mapping boundary so domain errors become MCP envelopes here, not deeper.
  9. Start the server (transport listen call).
- Delete the now-empty `src/tools/<feature>.ts` shims. The folder may disappear entirely or remain empty for one more commit if cleanup imports are still pending.
- Update `src/index.ts` to import and call the new `bootstrap()`.

Dependency-cruiser rule activated after merge:

```
{
  name: 'one-composition-root',
  severity: 'error',
  from: { pathNot: '^src/infrastructure/server/bootstrap\\.ts$' },
  to:   { path: 'mcp-use/server.*MCPServer|new MCPServer' }
},
{
  name: 'no-tool-registration-outside-bootstrap',
  severity: 'error',
  from: { pathNot: '^src/infrastructure/server/bootstrap\\.ts$' },
  to:   { path: '\\.tool\\(|\\.resource\\(|\\.prompt\\(' }
}
```

Smoke test: start the server. Hit one read-only and one destructive (idempotent or guarded) tool through `mcpc`. Confirm the response matches PR 1's baseline. Run `grep -rn "new MCPServer\\|server\\.tool(" src/` and confirm only `bootstrap.ts` matches.

Rollback path: revert PR 5. Construction returns to the scattered call sites that PR 4 introduced (`defineTool()` outputs registered ad-hoc). The depcruise rules are removed with the revert. Tools still work because PR 4's handlers are still present.

## PR 6 — Presenter and error contracts

Goal (observable outcome): all response shaping lives in `src/presenters/mcp-presenter.ts`, behind an `IMcpPresenter` port the handlers depend on. A `ToolResponse` builder lives in `src/domain/tool-response.ts`. Errors flow through `src/infrastructure/errors/error-contracts.ts`, which maps every `DomainError.code` to a stable JSON-RPC envelope. No raw provider error reaches the model; secrets (provider names, DSNs, signed URLs, auth tokens) are stripped before they hit `_meta` or `structuredContent`.

Files moved/changed:
- Create `src/domain/tool-response.ts` (immutable builder: `text(...)`, `data(...)`, `nextStep(...)`).
- Create `src/presenters/presenter.port.ts` (`IMcpPresenter` interface) and `src/presenters/mcp-presenter.ts` (concrete). Move all formatting code currently in handler files (Markdown rendering, TSV/CSV emission, `_meta` assembly, dashboard URL stitching) into the presenter.
- Create `src/infrastructure/errors/error-contracts.ts`. Build the symmetric mapping table: `DomainError.code` → `{ jsonRpcCode, message, isRetryable, recoveryHint }`. Install the mapper at the handler boundary (the `defineTool` middleware applied in bootstrap, PR 5).
- Replace every raw `throw new Error(...)` and re-throw of provider errors with a `DomainError` subclass throw. The gateway is the only place where the raw provider error is caught; it re-throws a `DomainError`. The use case throws domain errors; the handler does not throw.
- Add the redaction allowlist used by the presenter to strip provider names, DSNs, internal `s3://` paths, signed URLs, OAuth tokens.

Dependency-cruiser rule activated after merge:

```
{
  name: 'presenters-no-application-or-gateway',
  severity: 'error',
  from: { path: '^src/presenters' },
  to:   { path: '^src/(application|gateways|handlers)' }
},
{
  name: 'no-raw-error-throw-in-handlers',
  severity: 'warn',
  comment: 'Handlers should never construct Error directly',
  from: { path: '^src/handlers' },
  to:   { path: '^Error\\(|new Error\\(' }
}
```

Plus a unit test that asserts the error mapping table covers every `DomainError` subclass exhaustively (a `never` switch ends the mapper).

Smoke test: induce a known provider failure (rate-limit token, malformed input that the schema accepts but the provider rejects) and call the tool through `mcpc`. The response carries a stable `code`, an LLM-readable `recoveryHint`, and `isRetryable`. No DSN, signed URL, or provider name appears in the envelope. Capture stdout from the server: it must remain pure JSON-RPC; logs must hit stderr only.

Rollback path: revert PR 6. Handlers shape responses inline again and re-throw raw provider errors. The depcruise rules are removed with the revert. Tools still serve traffic with degraded error messaging — usable but with the leakage risk PR 6 closed.

## PR 7 — TypeScript quality bar enforcement

Goal (observable outcome): `tsconfig.json` flips to the locked SKILL.md flag set in one PR. Every error surfaced by the tightening is resolved in the same PR. No new behaviour ships — only types tighten.

Files moved/changed:
- Update `tsconfig.json` to add (or confirm): `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`, `isolatedModules`, `module: "NodeNext"`, `moduleResolution: "NodeNext"`, `target: "ES2022"`, `lib: ["ES2022"]`.
- Resolve every newly surfaced error. Common shapes:
  - Add explicit return types to every exported function in `domain/`, `application/`, `gateways/`, `presenters/`, `handlers/`, `infrastructure/`, `shared/`.
  - Replace `any`, `as any`, `@ts-ignore`, `z.any()`, `z.unknown()` with concrete types or Zod schemas. `@ts-expect-error` is allowed only with a one-line justification.
  - Convert type-only imports to `import type` (or inline `import { type X }`).
  - Convert object spreads under `exactOptionalPropertyTypes` to a `pickDefined()` helper.
  - Brand opaque IDs that cross the boundary (`AdAccountId`, `CampaignId`, `AdSetId`).
- Add ESLint rules that mirror the depcruise discipline (`@typescript-eslint/no-explicit-any: error`, `@typescript-eslint/consistent-type-imports`, `no-console: error`, `@typescript-eslint/no-floating-promises: error`).

Dependency-cruiser rule activated after merge: no new structural rule; instead the merge gate now includes a stricter `tsc --noEmit` and `eslint src/`. Add a CI job that runs both as blocking.

Smoke test: `pnpm typecheck && pnpm lint && pnpm test && pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs && pnpm build` exits 0. Replay one read-only tool and one destructive tool through `mcpc`; outputs match the PR 1 baseline.

Rollback path: revert PR 7. The locked flags relax to whatever the repo had before. Code that depended on the new strict semantics (e.g. `pickDefined()` helpers, branded IDs) keeps working at runtime; only the compile-time guarantees regress.

## What you must verify before finishing

These are the fresh-context checkpoints. Each is observable; none requires reading the diff.

- `pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs` exits 0 with all seven PRs landed; the rule list contains the entries from PRs 1–6.
- `grep -rn "process\\.env" src/ | grep -v "src/infrastructure/config/runtime-config.ts"` returns no matches.
- `grep -rn "mcp-use" src/domain src/application src/gateways src/shared` returns no matches; `find src/handlers -name "*.handler.ts" | xargs -n1 wc -l | awk '{print $1}' | sort -n | tail -1` is bounded (each handler small enough to belong to one tool).
- `grep -rn "new MCPServer\\|server\\.tool(\\|server\\.resource(\\|server\\.prompt(" src/` returns matches only inside `src/infrastructure/server/bootstrap.ts`.
- `mcpc --json @target tools-call <each-tool> '{...}'` round-trips return outputs equivalent to the PR 1 baseline; an induced upstream failure surfaces a `DomainError` envelope with `code`, `recoveryHint`, and `isRetryable`, with no provider names, DSNs, or signed URLs in the response payload.
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` all exit 0 after PR 7.
