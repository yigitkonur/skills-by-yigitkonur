# Greenfield Walkthrough

> SKILL.md routes here when you pick the **Greenfield** mode — an empty repo (or one with only a `package.json` and an entry stub) and no `src/` layout yet. After working through this file, you should be able to walk a new TypeScript MCP server from `git init` to a tool that responds correctly through the `mcp-use` Inspector, with every guardrail from SKILL.md already enforced and every step gated by an observable check. Each step is small, independently revertable, and lists the deeper reference to read when the step needs more detail.

The pace is on purpose: every gate fires before the next step. If a gate fails, fix the failure before moving forward — do not stack a second mistake on top of the first. The exit gates use real shell commands (`pnpm tsc --noEmit`, `pnpm exec depcruise --validate`, `mcpc tools-call`) so a fresh-context reviewer can replay them.

## Step 1 — Repo bootstrap

Why first: package metadata and lockfile shape the rest of the repo. Getting `type: "module"`, the `engines` pin, and the locked `mcp-use` + `zod` versions in place before any `.ts` file exists prevents the whole "we forgot ESM and now nothing resolves" rework loop.

Files created:
- `package.json`
- `pnpm-lock.yaml`
- `.gitignore`
- `.npmrc` (optional, only if your registry needs it)

Required `package.json` shape (verbatim keys; values follow your project):
- `"type": "module"`
- `"engines": { "node": ">=20.11" }`
- `"packageManager": "pnpm@10.x"`
- `dependencies`: `"mcp-use"`, `"zod"`
- `devDependencies`: `"typescript"`, `"@types/node"`, `"dependency-cruiser"`, `"vitest"`, `"eslint"`, `"@typescript-eslint/parser"`, `"@typescript-eslint/eslint-plugin"`
- `scripts`:
  - `"typecheck": "tsc --noEmit"`
  - `"deps:validate": "depcruise src/ index.ts --config .dependency-cruiser.cjs"`
  - `"lint": "eslint src/"`
  - `"test": "vitest run"`
  - `"build": "mcp-use build"`
  - `"start": "node dist/index.js"`

Run:

```bash
pnpm install
node -e "console.log(require('./package.json').type)"
```

Exit gate: `node -e "console.log(require('./package.json').type)"` prints `module` and `pnpm install` exits 0 with `mcp-use` and `zod` resolved in `node_modules/`.

Reference: SKILL.md "Standard folder layout" lists every dependency the rest of the steps assume.

## Step 2 — `tsconfig.json` with the locked flags

Why second: every later step writes TypeScript. The locked flags from SKILL.md must be on before the first import is written, because tightening them retroactively triggers a fan-out of unrelated edits.

Files created:
- `tsconfig.json`

Required `compilerOptions` (every key is binding):

Strictness umbrella:
- `"strict": true`

Beyond-strict guards (each closes a specific runtime crash class):
- `"noUncheckedIndexedAccess": true` — array/object index access becomes `T | undefined`.
- `"exactOptionalPropertyTypes": true` — `{ key: undefined }` and "key absent" stop being equivalent.
- `"noImplicitOverride": true` — subclasses use `override`; renaming a base method orphans the subclass at compile time.
- `"noImplicitReturns": true` — every branch returns explicitly.
- `"noFallthroughCasesInSwitch": true` — switch fall-through is opt-in only.

Module shape (NodeNext is required; alternative module-resolution values break `mcp-use/server`):
- `"verbatimModuleSyntax": true`
- `"isolatedModules": true`
- `"module": "NodeNext"`, `"moduleResolution": "NodeNext"`

Build/runtime targets:
- `"target": "ES2022"`, `"lib": ["ES2022"]` (no DOM lib)
- `"outDir": "dist"`, `"rootDir": "."`, `"incremental": true`
- `"skipLibCheck": true` (turn off only when investigating an `@types/*` regression).

Run:

```bash
pnpm exec tsc --noEmit
```

Exit gate: `pnpm exec tsc --noEmit` exits 0 against the empty project.

Reference: `references/typescript-quality-bar.md` for why each flag is non-negotiable.

## Step 3 — `dependency-cruiser.cjs` as a CI-blocking gate

Why third: the boundary rules must be enforced from the first import. Adding `dependency-cruiser` after the layers exist means the first hundred imports already drift; fixing that retroactively is a refactor PR, not a cleanup.

Files created:
- `.dependency-cruiser.cjs`

Required rules (translated into `forbidden` entries):
- `domain` may not depend on anything outside `domain` (path matches `^src/domain` → forbid `^src/(application|handlers|gateways|presenters|infrastructure|resources|prompts)`).
- `application` may not depend on `^src/(handlers|gateways|presenters|infrastructure|resources|prompts)` and may not import `mcp-use`, `@modelcontextprotocol/sdk`, or `zod`.
- `gateways` may not depend on `^src/(application|handlers|presenters)`.
- `presenters` may not depend on `^src/(application|gateways|handlers)`.
- `^src/(domain|application|gateways|shared)` may not import any module whose path matches `mcp-use` or `@modelcontextprotocol/sdk`.
- `^src/(?!infrastructure/config/runtime-config)` may not contain a string literal `process\\.env`.
- No `index.ts` barrel files inside `src/` (use a `forbidden` rule with `pathNot: "^src/.*/index\\\\.ts$"` exclusion via a `comment` rule and an audit grep until depcruise itself flags it).

Run:

```bash
pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs
```

Exit gate: `pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs` exits 0 (no rules violated, even if the tree is still empty).

Reference: `references/dependency-rules.md` for the full copy-paste config and the rationale behind each rule.

## Step 4 — Folder scaffold matching SKILL.md

Why fourth: with the gates active, the scaffold itself must satisfy them on the first commit. Creating folders before files keeps the import graph empty and the gate green.

Files/folders created (empty):

```
src/
  domain/
    ports/
    types/
  application/
    shared/
  handlers/
    schemas/
  gateways/
  presenters/
    response/
  infrastructure/
    config/
    middleware/
    errors/
    observability/
    server/
  resources/
  prompts/
  shared/
    types/
```

Run:

```bash
find src -type d | sort
pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs
```

Exit gate: `find src -type d | sort` lists every directory in the SKILL.md tree, and `depcruise` exits 0.

Reference: `references/folder-layout.md` for the per-folder responsibilities.

## Step 5 — Per-folder `AGENTS.md` discipline

Why fifth: layer-specific rules travel best as files inside the layer they govern. A future agent editing `application/<feature>/<feature>.usecase.ts` is more likely to read `application/AGENTS.md` than the root SKILL.md.

Files created (each is a 5–15 line stub):
- `src/domain/AGENTS.md`
- `src/application/AGENTS.md`
- `src/handlers/AGENTS.md`
- `src/gateways/AGENTS.md`
- `src/presenters/AGENTS.md`
- `src/infrastructure/AGENTS.md`
- `src/shared/AGENTS.md`

Each file states the layer's allowed imports, forbidden imports, and one or two layer-specific rules (e.g. `domain/AGENTS.md` says "no `mcp-use` types, ever; no `process.env`; `#` private fields on entities").

Exit gate: `find src -name AGENTS.md | wc -l` reports at least 7. Open one and confirm it names the layer and the forbidden imports.

Reference: SKILL.md "Standard folder layout" (the AGENTS.md row in each layer).

## Step 6 — `infrastructure/config/runtime-config.ts`

Why sixth: the config seam is the only place that reads `process.env`. Standing it up before any gateway exists prevents the original sin of the drifted repos — env reads scattered through provider files.

Files created:
- `src/infrastructure/config/runtime-config.ts`
- `src/infrastructure/config/validate.ts` (Zod env schema; one schema per group of related secrets)
- `.env.example` at the repo root

Pattern:
- Define a `RuntimeConfig` interface with `readonly` fields for every value an inner layer needs.
- Inside `runtime-config.ts`, build a Zod schema (`z.object({...}).strict()` with `.describe()` per field), call `Schema.parse(process.env)`, and convert the parsed object into the `RuntimeConfig` shape. Throw a `ConfigError` (a `DomainError` subclass) on missing required secrets.
- Export `loadRuntimeConfig(): RuntimeConfig`. No other file in `src/` may read `process.env`.

Run:

```bash
pnpm exec tsc --noEmit
pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs
grep -rn "process\\.env" src/ | grep -v "src/infrastructure/config/runtime-config.ts"
```

Exit gate: `tsc --noEmit` and `depcruise` exit 0; the third `grep` returns no matches.

Reference: `references/dependency-rules.md` (the config-seam rule), and SKILL.md guardrail #4.

## Step 7 — First port + first gateway with decorator composition

Why seventh: the use case in step 9 will need a port to depend on. Defining the port before the gateway and the gateway before the use case forces the dependency arrow to point inward.

Files created:
- `src/domain/ports/<capability>-gateway.port.ts` — the `I<Capability>Gateway` interface, named for capability ("ListAccountsGateway"), not storage. No `mcp-use`, no Zod, no SDK types.
- `src/gateways/<provider>/<provider>-gateway.ts` — the concrete adapter implementing the port. Wraps the SDK or HTTP client. Catches upstream errors inside the gateway and re-throws them as `DomainError` subclasses **before** anything escapes through the port.
- `src/gateways/caching-<capability>-gateway.ts` — a decorator implementing the same port, delegating to the inner gateway.
- `src/gateways/retrying-<capability>-gateway.ts` — a decorator implementing the same port, applying `withRetry` to retryable errors only.

Decorator composition (in bootstrap, step 11): `CachingGateway(RetryingGateway(SanitisingGateway(ConcreteGateway(...))))`.

Exit gate: `pnpm exec tsc --noEmit` exits 0; `pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs` exits 0; `grep -rn "from 'mcp-use'" src/gateways src/domain` returns no matches.

Reference: `references/gateways-and-ports.md` for naming and decorator order; `references/error-contracts.md` for the upstream-error classification rule.

## Step 8 — First domain entity + error class

Why eighth: the use case needs domain types to construct and the gateway needs error subclasses to throw. Pure domain code lands before any orchestration.

Files created:
- `src/domain/types/<entity>.ts` — readonly DTO or class with `#` private fields (never `private`). Separate `create(...)` from `reconstitute(...)`.
- `src/domain/errors.ts` — `DomainError` base class plus subclasses (`ValidationError`, `NotFoundError`, `ProviderError`, `RateLimitError`, `AuthError`). Each carries `code: string`, `recoveryHint: string | undefined`, `isRetryable: boolean`. Use `override` on every overridden member.
- `src/domain/tool-response.ts` — immutable `ToolResponse` builder (`text(...)`, `data(...)`, `nextStep(...)`).

Exit gate: `pnpm exec tsc --noEmit` exits 0; a tiny vitest unit test (`src/__tests__/domain/<entity>.test.ts`) instantiates the entity and asserts an invariant; `pnpm test` exits 0.

Reference: `references/error-contracts.md` for the `DomainError` shape.

## Step 9 — First use case depending only on the port

Why ninth: the use case is the first place orchestration logic lives. With the port and entity in place it can be written without touching `mcp-use` at all — proving the layer boundary works before a handler exists.

Files created:
- `src/application/<feature>/<feature>.usecase.ts`

Pattern:
- Constructor takes the port (`I<Capability>Gateway`), the logger port, and any other ports it needs. No `process.env`, no `mcp-use` import, no SDK import, no Zod usage inside.
- The single public method takes a typed `Command` value object and returns a `ToolResponse` (domain object) or throws a `DomainError` subclass.

Run:

```bash
pnpm exec tsc --noEmit
grep -n "mcp-use\\|@modelcontextprotocol/sdk\\|process\\.env\\|zod" src/application/<feature>/<feature>.usecase.ts || echo CLEAN
pnpm test
```

Exit gate: `tsc --noEmit` exits 0; the `grep` prints `CLEAN`; a unit test that injects a fake port and asserts the use case returns the right `ToolResponse` passes.

Reference: SKILL.md "Use case ↔ MCP tool flow"; `references/clean-code-rules-in-mcp-context.md` for use-case constructor discipline.

## Step 10 — First handler with `defineTool()` + `HandlerContext`

Why tenth: the handler is the seam between MCP and the framework-free use case. Building it after the use case keeps the use case from leaking `mcp-use` types upward.

Files created:
- `src/handlers/define-tool.ts` — the `defineTool()` factory. Accepts `{ name, description, schema, annotations, outputSchema?, nextSteps?, execute }`. Wraps the schema with `z.object(config.schema).strict()`. Returns a `DefinedTool<TSchema>` for bootstrap to register.
- `src/handlers/context.ts` — the `HandlerContext` interface (request id, requester id, logger, presenter port, the use cases the handler needs).
- `src/handlers/<feature>/<tool>.handler.ts` — built with `defineTool()`. The `execute` function: parses input via the strict Zod schema (`.describe()` on every field), builds the `Command`, delegates to the use case, hands the `ToolResponse` to the presenter, returns the `CallToolResult`.

Each Zod field uses `.describe()` and bounds (`.min`, `.max`, `.regex`, or `.enum`). No `z.any()`, no `z.unknown()`. `destructiveHint` and `idempotentHint` are explicit on the annotations.

Exit gate: `pnpm exec tsc --noEmit` exits 0; `pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs` exits 0; `grep -rn "z\\.any\\|z\\.unknown" src/handlers` returns no matches.

Reference: `references/define-tool-pattern.md`, `references/handler-context.md`, `references/zod-at-boundary.md`.

## Step 11 — `infrastructure/server/bootstrap.ts` wiring everything

Why eleventh: bootstrap must come after every layer it wires; otherwise it imports types that don't exist yet. Constructing in the locked order is what makes the start-up deterministic.

Files created:
- `src/infrastructure/server/bootstrap.ts`
- `index.ts` (at the repo root) — the Node entry point. Calls `bootstrap()` and starts the server.
- `src/infrastructure/middleware/request-context.ts` — `AsyncLocalStorage` setup for cross-cutting metadata (request id, requester, session id).
- `src/infrastructure/errors/error-contracts.ts` — the mapping table from `DomainError.code` → JSON-RPC error envelope.
- `src/infrastructure/observability/logger.ts` — `Logger` port implementation. JSON to stderr only.
- `src/presenters/mcp-presenter.ts` and `src/presenters/presenter.port.ts`.

Bootstrap order (binding):
1. Call `loadRuntimeConfig()` first; throw on missing required secrets.
2. Build cross-cutting infrastructure next — logger first, then Redis (if any), then the OAuth provider (if any).
3. Build concrete gateways and wrap them in decorator order: `Caching(Retrying(Sanitising(Concrete(...))))`.
4. Build use cases, passing each its ports through the constructor.
5. Build handlers by calling the `defineTool()` factory once per tool.
6. Instantiate `MCPServer`. Mount the middleware pipeline (request context, logging, error mapping) on it.
7. Register the tool list, then the resource list, then the prompt list — in that fixed order.
8. Install the error-mapping boundary so domain errors become MCP envelopes here, not deeper.
9. Start the server (transport listen call).

Run:

```bash
pnpm exec tsc --noEmit
pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs
pnpm build
```

Exit gate: `tsc --noEmit`, `depcruise`, and `mcp-use build` all exit 0. The `dist/index.js` file exists.

Reference: `references/composition-root.md`.

## Step 12 — Smoke test with `mcp-use` Inspector

Why twelfth: a green build is not a working server. The first end-to-end call exercises the entire wire — schema parse → use case → gateway → presenter → response — and is the first time the runtime layout is observable.

Run (in two terminals):

```bash
# Terminal 1
pnpm start

# Terminal 2
mcp-use inspect ./dist/index.js
# Or: mcpc connect 127.0.0.1:<port>/mcp @smoke --no-profile
# mcpc --json @smoke tools-call <tool-name> '{"<arg>":"<value>"}'
```

Exit gate: the Inspector shows the tool listed; calling the tool returns a `CallToolResult` whose `content` and `structuredContent` reflect what the use case produced; the gateway was actually called (logged via the structured logger to stderr — never stdout). Liveness alone (`/health/live` if you wired one) is not enough; a real `tools-call` must round-trip.

Reference: SKILL.md "Use case ↔ MCP tool flow"; the `build-mcp-use-server` skill for transport, session, and Inspector specifics.

## Step 13 — Tests covering use case, handler, and gateway contract

Why last: tests are the proof that the architecture holds when the next change lands. Greenfield tests are cheap to write because the seams already exist.

Files created:
- `src/__tests__/application/<feature>/<feature>.usecase.test.ts` — injects a fake port; asserts the `ToolResponse`.
- `src/__tests__/handlers/<feature>/<tool>.handler.test.ts` — exercises the schema (good input, bad input, alias normalisation) and asserts the use case is called with the canonical `Command`.
- `src/__tests__/gateways/<capability>.contract.test.ts` — runs every implementation of the port (concrete, caching decorator, retry decorator) against the same set of contract assertions. This is the test that catches "the cache decorator silently changed the return shape".
- `src/__tests__/doubles/` — the in-memory adapters used by the unit tests, each implementing the port directly so they fail to compile when the port shape moves.

Run:

```bash
pnpm test
pnpm exec tsc --noEmit
pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs
pnpm lint
```

Exit gate: every command exits 0. The contract test suite runs each port implementation through the same assertions and passes.

Reference: SKILL.md "Testing expectations"; `references/audit-checklist.md` for the test-pyramid expectations.

## What you must verify before finishing

Use these as a fresh-context replay. Each is a single command whose exit code is the answer.

- `pnpm exec tsc --noEmit` exits 0 with every layer in place.
- `pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs` exits 0; no `mcp-use` import in `domain/`, `application/`, `gateways/`, or `shared/`; no `process.env` read outside `src/infrastructure/config/runtime-config.ts`; no barrel `index.ts` inside `src/`.
- A real Inspector / `mcpc` call against the running server returns a successful `CallToolResult` for the first registered tool, and the structured log line for that request appears on stderr (not stdout).
- `pnpm test` exits 0 with at least one use-case unit test, one handler test, and one gateway contract test passing.
- `grep -rn "console\\." src/ | grep -v "// allowed:"` returns no matches; `grep -rnE ": any\\b|@ts-ignore|z\\.any\\(|z\\.unknown\\(" src/` returns no matches.
