# Audit Checklist

> SKILL.md routes here when you pick the **Review** mode — you have an MCP server (yours or unfamiliar) and need to grade it against the standard. This checklist is layer-grouped, every item has a unique ID, a binary yes/no question, a P0/P1/P2 priority, and a concrete "How to verify" instruction. After working through this file, you should be able to walk through any TypeScript MCP server in this pack, score every item, and produce a graded report whose verdict (merge / merge with follow-up issues / block) is determined mechanically by the P0 and P1 counts. Every item is answerable from inspection alone — no special tooling beyond `grep`, `find`, `node`, and (where listed) `pnpm exec`.

The checklist is the same regardless of whether you are reviewing a pull request, an existing repo at a point in time, or a refactor's incremental commit. Use the priority field to triage: P0 items block merge, P1 items require a follow-up issue tracked in the PR description, P2 items are informational and noted in the report's "Nits" section without gating.

## Layout

- **LAYOUT-01** — Does `src/` contain the standard top-level folders (`domain/`, `application/`, `handlers/`, `gateways/`, `presenters/`, `infrastructure/`, `resources/`, `prompts/`, `shared/`)? **Priority:** P0. **How to verify:** `find src -maxdepth 1 -type d | sort` and confirm each folder is present. A `use-cases/` folder in place of `application/` is acceptable only if the rest of the repo is internally consistent.
- **LAYOUT-02** — Is there exactly one tool per file under `src/handlers/<feature>/<tool>.handler.ts`, with no monolithic `src/tools/<feature>.ts` carrying multiple tools? **Priority:** P0. **How to verify:** `find src/handlers -name "*.handler.ts" | xargs -n1 wc -l | awk '{print $1}' | sort -n | tail -5` shows none exceeding ~250 lines; `find src/tools -maxdepth 1 -name "*.ts" 2>/dev/null` returns nothing or only a deprecated re-export shim.
- **LAYOUT-03** — Is the presenter port (`IMcpPresenter`) defined in `src/presenters/presenter.port.ts` and a concrete implementation in `src/presenters/mcp-presenter.ts`? **Priority:** P1. **How to verify:** `ls src/presenters/presenter.port.ts src/presenters/mcp-presenter.ts` succeeds.
- **LAYOUT-04** — Are per-folder `AGENTS.md` files present and current? **Priority:** P2. **How to verify:** `find src -name AGENTS.md | wc -l` returns at least 7; spot-read one to confirm it states the layer's allowed and forbidden imports.
- **LAYOUT-05** — Are domain entities and ports placed in `src/domain/` (with `errors.ts`, `tool-response.ts`, `ports/`, `types/` present)? **Priority:** P1. **How to verify:** `ls src/domain/errors.ts src/domain/tool-response.ts src/domain/ports src/domain/types`.
- **LAYOUT-06** — Is shared Zod field reuse confined to `src/handlers/schemas/` rather than scattered across handler files? **Priority:** P2. **How to verify:** `find src/handlers/schemas -type f -name "*.ts"` returns at least one file when more than two handlers share a field shape; cross-tool duplication of the same Zod fragment is a refactor flag.
- **LAYOUT-07** — Are gateway decorator files named for the capability they wrap (e.g. `caching-<capability>-gateway.ts`, `retrying-<capability>-gateway.ts`) rather than for storage tech? **Priority:** P2. **How to verify:** `ls src/gateways/caching-*.ts src/gateways/retrying-*.ts 2>/dev/null` returns capability-named files; `grep -rn "RedisRepository\\|MongoStore" src/gateways` returns no matches that leak storage names through the port.

## Boundary

- **BOUNDARY-01** — Is `dependency-cruiser` configured and run as a CI-blocking gate? **Priority:** P0. **How to verify:** `cat .dependency-cruiser.cjs` exists and has rules referencing `^src/(domain|application|gateways|handlers|presenters|infrastructure)`; `grep -n "depcruise\\|dependency-cruiser" package.json` shows a `deps:validate` (or equivalent) script invoked from CI.
- **BOUNDARY-02** — Is `mcp-use` imported only from `handlers/`, `resources/`, `prompts/`, `presenters/` (response helpers), and `infrastructure/`? **Priority:** P0. **How to verify:** `grep -rn "from ['\"]mcp-use" src/domain src/application src/gateways src/shared` returns no matches.
- **BOUNDARY-03** — Is `process.env` read only from inside `src/infrastructure/config/`? **Priority:** P0. **How to verify:** `grep -rn "process\\.env" src/ | grep -v "src/infrastructure/config/"` returns no matches. The conventional filename is `runtime-config.ts` but any name under `src/infrastructure/config/` (e.g. `defaults.ts`, `secrets.ts`, `create-config.ts`) is acceptable provided env reads do not appear elsewhere. One narrow exception: bootstrap-time `process.env` writes that hand env values to the `mcp-use` framework's own debug knob (e.g. `process.env.MCP_DEBUG_LEVEL = config.debug`) are allowed when they carry a one-line comment naming the framework hand-off.
- **BOUNDARY-04** — Do inner layers avoid importing outer layers? **Priority:** P0. **How to verify:** `pnpm exec depcruise src/ index.ts --config .dependency-cruiser.cjs` exits 0; spot-check `grep -rn "from ['\"]\\.\\./gateways\\|from ['\"]\\.\\./infrastructure\\|from ['\"]\\.\\./presenters" src/domain src/application` returns no matches.
- **BOUNDARY-05** — Are there no barrel `index.ts` files inside `src/` other than the entry points required by `mcp-use` (e.g. `src/index.ts` if the project uses one)? **Priority:** P1. **How to verify:** `find src -mindepth 2 -name "index.ts"` returns no matches (or only the entry point if structurally required).
- **BOUNDARY-06** — Is there exactly one composition root (`src/infrastructure/server/bootstrap.ts`)? **Priority:** P0. **How to verify:** `grep -rn "new MCPServer\\|MCPServer(" src/` matches only `src/infrastructure/server/bootstrap.ts`; `grep -rn "\\.tool(\\|\\.resource(\\|\\.prompt(" src/` matches only the same file (or its imported registry helpers).
- **BOUNDARY-07** — Are concrete gateways constructed only inside bootstrap (not inside use cases, handlers, or presenters)? **Priority:** P0. **How to verify:** `grep -rn "new [A-Z][A-Za-z]*Gateway(" src/` returns matches only in `src/infrastructure/server/bootstrap.ts`. `new` calls inside `src/application/` or `src/handlers/` are P0 findings.
- **BOUNDARY-08** — Does `dependency-cruiser` block at least the eight load-bearing rules: env-outside-config, mcp-use-in-domain, mcp-use-in-application, mcp-use-in-gateways, application-importing-outer-layers, presenters-importing-application-or-gateways, no-cycles, no-barrel-files? **Priority:** P1. **How to verify:** `grep -E "name:" .dependency-cruiser.cjs | wc -l` returns at least 8; spot-read each to confirm the rule names target the listed concerns.

## TypeScript quality

- **TYPESCRIPT-01** — Does `tsconfig.json` carry the locked flags (`strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`, `module: "NodeNext"` *or* `"Node16"`, `moduleResolution: "NodeNext"` *or* `"Node16"`)? **Priority:** P0. **How to verify:** `node -e "console.log(JSON.stringify(JSON.parse(require('fs').readFileSync('tsconfig.json','utf8').replace(/\\/\\/.*$/gm,'')).compilerOptions, null, 2))"` — every flag appears with the required value. `Node16` and `NodeNext` are both accepted (`Node16` is a frozen alias of `NodeNext` as of TS 5.x); `bundler`, `ESNext` for `module`, or `node` for `moduleResolution` are P0 fails — they break `mcp-use/server` resolution.
- **TYPESCRIPT-02** — Are there no occurrences of bare `any`, `as any`, `@ts-ignore`, `z.any()`, or `z.unknown()` in `src/`? **Priority:** P0. **How to verify:** `grep -rnE ": any\\b|as any\\b|@ts-ignore|z\\.any\\(|z\\.unknown\\(" src/` returns no matches. `@ts-expect-error` is allowed only when accompanied by a one-line justification on the same or following line; verify with `grep -rnB1 "@ts-expect-error" src/` and inspect each hit.
- **TYPESCRIPT-03** — Do all exported functions in `domain/`, `application/`, `gateways/`, `handlers/`, `presenters/`, `infrastructure/`, `shared/` have explicit return types? **Priority:** P1. **How to verify:** `grep -rnE "^export (default )?function [A-Za-z_]+\\([^)]*\\) *\\{" src/` — every match has an explicit return type after the parameter list. ESLint rule `@typescript-eslint/explicit-module-boundary-types` should be enabled and reported via `pnpm lint`.
- **TYPESCRIPT-04** — Are type-only cross-layer imports written with `import type`? **Priority:** P1. **How to verify:** `grep -rnE "^import \\{[^}]+\\} from" src/ | grep -v "import type"` — manually triage each hit; ones whose imported names are only used in type position must be `import type`. ESLint's `consistent-type-imports` (`fixStyle: 'separate-type-imports'`) catches this automatically when `pnpm lint` runs.
- **TYPESCRIPT-05** — Are opaque IDs branded at the boundary? **Priority:** P1. **How to verify:** `grep -rnE "type [A-Z][A-Za-z]*Id =" src/domain` returns at least one branded type per identifier the MCP wire carries (account id, session id, dataset id, handler id). The brand constructor validates input before casting.
- **TYPESCRIPT-06** — Is `package.json` set to `"type": "module"` and are imports using ESM with explicit `.js` extensions on relative paths? **Priority:** P0. **How to verify:** `node -e "console.log(require('./package.json').type)"` prints `module`; `grep -rnE "from ['\"]\\.\\.?/[^'\"]+['\"]" src/ | grep -vE "\\.js['\"]\\)?$"` returns no matches (relative imports without `.js`).
- **TYPESCRIPT-07** — Are there no `console.*` calls anywhere in `src/`? **Priority:** P0. **How to verify:** `grep -rnE "console\\.(log|info|warn|error|debug)" src/` returns no matches. The structured logger port is the only sanctioned output path; JSON goes to stderr. **Narrow exception (P1, not P0):** `console.error` calls in pre-logger startup boundaries — the entry point or env-validation phase that runs before the logger has been constructed — are tolerable if each carries a one-line comment justifying that no logger is yet available. More than two such hits in a repo is still a P0 finding because it suggests the logger is being constructed too late.
- **TYPESCRIPT-08** — Are domain entity invariants protected at runtime, not just at compile time? **Priority:** P2. **How to verify:** Either (a) `grep -rn "  #[a-zA-Z]" src/domain` returns matches on each entity that holds invariants — `#` is runtime-private and bypass-resistant, or (b) the codebase uses the `private` keyword on entities **and** the project enforces `@typescript-eslint/no-explicit-any` plus a `dependency-cruiser` rule blocking `as any` casts in entity files — the combination produces equivalent practical protection. Audit fails this item only if neither path is present.
- **TYPESCRIPT-09** — Are non-null assertions (`!`) avoided unless immediately preceded by a runtime guard? **Priority:** P1. **How to verify:** `grep -rnE "[a-zA-Z_]\\)?![\\.\\(]" src/ | grep -v "// checked"` — triage each hit; an unguarded `!` is a P0 promotion when found inside a use case or gateway.
- **TYPESCRIPT-10** — Are `Promise.allSettled` (not `Promise.all`) used for paid or recoverable upstream fanouts inside use cases? **Priority:** P2. **How to verify:** `grep -rn "Promise\\.all(" src/application` and audit each hit — paid/recoverable legs should be `allSettled` so a single failure does not cancel the rest.

## MCP wiring

- **MCP-01** — Is the `defineTool()` factory used for every tool, with `{ name, description, schema, annotations, outputSchema?, nextSteps?, execute }`? **Priority:** P0. **How to verify:** `grep -rn "defineTool(" src/handlers` matches every handler file; `grep -rn "server\\.tool(" src/` matches only `bootstrap.ts`. Annotations on each handler include explicit `destructiveHint` and `idempotentHint`.
- **MCP-02** — Are tools, resources, and prompts registered exclusively from bootstrap, in the locked order (tools → resources → prompts)? **Priority:** P0. **How to verify:** Read `src/infrastructure/server/bootstrap.ts`; the registration block is a single sequential pass and no other file matches `grep -rn "\\.tool(\\|\\.resource(\\|\\.prompt(" src/`.
- **MCP-03** — Is auth/OAuth wiring confined to `src/infrastructure/auth/` (with config from the config seam) **or** delegated entirely to the `mcp-use` framework's own auth integration in bootstrap? **Priority:** P1. **How to verify:** Either path A — `find src/infrastructure/auth -type f` returns auth-wiring files; or path B — bootstrap configures auth through `mcp-use`'s built-in provider (e.g. `oauth: oauthSupabaseProvider({...})`) and no auth code lives outside that single bootstrap call. In both cases, `grep -rn "Bearer\\|OAuth\\|access_token" src/handlers src/application src/gateways src/domain` shows only token-shape consumption (e.g. branded `AccessToken` types) — never raw extraction or env reads.
- **MCP-04** — Do `ctx.elicit()`, `ctx.sample()`, and `ctx.client.can()` calls appear only inside handlers? **Priority:** P1. **How to verify:** `grep -rn "ctx\\.elicit\\|ctx\\.sample\\|ctx\\.client\\.can\\|extra\\.elicit\\|extra\\.sample" src/application src/domain src/gateways` returns no matches. Use cases never see the MCP context.
- **MCP-05** — Does every Zod tool input schema use `.strict()` at the top level and `.describe()` on every field, with explicit bounds (`.min`, `.max`, `.regex`, or `.enum`) on free-form fields? **Priority:** P0. **How to verify:** `grep -rn "z\\.object" src/handlers | grep -v "\\.strict()"` returns no matches; spot-read three handlers and confirm every field has `.describe(...)` and a bound.
- **MCP-06** — Does each tool declare `outputSchema` (custom or shared)? **Priority:** P1. **How to verify:** `grep -rn "outputSchema" src/handlers` matches every handler; tools whose output is described only in markdown are a P1 finding.

## Errors and responses

- **ERROR-01** — Does the codebase carry a `DomainError` hierarchy with subclasses each exposing `code`, `recoveryHint`, and `isRetryable`? **Priority:** P0. **How to verify:** `grep -nE "class [A-Z][A-Za-z]*Error extends DomainError" src/domain/errors.ts` lists at least `ValidationError`, `NotFoundError`, `ProviderError`, `RateLimitError`, `AuthError`. The base class declares all three properties as `readonly`.
- **ERROR-02** — Is there a single `error-contracts` mapping table that maps every `DomainError.code` to a JSON-RPC envelope, and does it use a `never`-typed switch fall-through to force exhaustiveness? **Priority:** P0. **How to verify:** `cat src/infrastructure/errors/error-contracts.ts` exists; the switch ends with `const _exhaustive: never = err.code` (or equivalent). A unit test asserts every `DomainError` subclass is covered.
- **ERROR-03** — Do gateway adapters classify upstream errors into `DomainError` subclasses before the error crosses the port? **Priority:** P0. **How to verify:** `grep -rn "throw new \\(GraphApi\\|RateLimit\\|Provider\\)Error\\|throw new [A-Z][A-Za-z]*Error" src/gateways` shows domain errors thrown; `grep -rn "throw err\\|throw error\\|throw e\\b" src/gateways` returns no unwrapped re-throws of provider errors.
- **ERROR-04** — Are secrets stripped before they reach the wire (provider names, DSNs, signed URLs, OAuth tokens, internal `s3://` paths) at **at least one** of the two layers that can see them: the gateway (preferred — strip before the use case ever sees the secret) or the presenter (defence-in-depth — strip again at the wire)? **Priority:** P0. **How to verify:** Either (a) gateways carry an explicit redaction or sanitisation step before returning to the application layer (`grep -rn "redact\\|sanitize\\|FORBIDDEN_KEYS\\|SECRET_KEYS\\|stripSecrets" src/gateways` returns matches), or (b) the presenter does (`grep -n "redact\\|sanitize\\|FORBIDDEN_KEYS\\|SECRET_KEYS" src/presenters/mcp-presenter.ts` returns matches). At least one layer must have an explicit allowlist or denylist; both layers having one is the gold standard. A unit test injects a payload containing each forbidden key and asserts the rendered envelope omits it.
- **ERROR-05** — Are catch blocks typed `catch (err: unknown)` and narrowed before property access? **Priority:** P1. **How to verify:** `grep -rnE "catch \\(err: any\\)|catch \\(error: any\\)|catch\\(err\\)|catch \\(\\)" src/` returns no matches; `grep -rnE "catch \\([a-z_]+: unknown\\)" src/` returns matches throughout.
- **ERROR-06** — Are domain "next steps" or events dispatched only after the durable side effect commits? **Priority:** P1. **How to verify:** Spot-read each use case that dispatches events: the dispatch line follows the `await store.save(...)` / `await gateway.commit(...)` line, never precedes it. Pre-commit dispatches feed the model phantom data.

## Request context

- **CONTEXT-01** — Is `AsyncLocalStorage` established in `src/infrastructure/middleware/request-context.ts` and threaded through the bootstrap pipeline? **Priority:** P1. **How to verify:** `grep -n "AsyncLocalStorage" src/infrastructure/middleware/request-context.ts src/shared/request-context.ts` matches; bootstrap registers the middleware before tool registration.
- **CONTEXT-02** — Does the request context carry only cross-cutting metadata (request id, requester id, session id, cost accumulator) and never application state, business inputs, or results? **Priority:** P1. **How to verify:** Read the context interface; assert no field names match domain concepts (e.g. `dataset`, `campaign`, `result`). `grep -rn "context\\.set\\|context\\.run\\(" src/application` returns no matches — use cases do not push business state into the context.
- **CONTEXT-03** — Is requester identity always derived from verified auth (never from raw bearer-payload reads inside handlers)? **Priority:** P1. **How to verify:** `grep -rn "decodeJwt\\|jwt\\.decode\\|atob.*token" src/handlers src/application` returns no matches; identity flows from `infrastructure/auth/` into the request context, and consumers read the context only.

## Tests

- **TEST-01** — Do unit tests for use cases inject port mocks (in-memory fakes implementing the port directly), with no `mcp-use` import inside the test file? **Priority:** P1. **How to verify:** `grep -rln "from ['\"]mcp-use" src/__tests__/application` returns no matches; spot-read one test and confirm the use case is instantiated with `new InMemoryFooGateway()`-style doubles.
- **TEST-02** — Is there a contract test per port that runs every implementation (concrete + decorators) through the same assertion set? **Priority:** P1. **How to verify:** `find src/__tests__ -name "*.contract.test.ts"` returns at least one file per port; the file iterates over `[concrete, caching, retrying]` adapters via `describe.each`.
- **TEST-03** — Do tests of pure use cases avoid importing `mcp-use` entirely? **Priority:** P0. **How to verify:** `grep -rln "from ['\"]mcp-use" src/__tests__/application src/__tests__/domain` returns no matches. Tests of handlers may import `mcp-use` types; tests of pure orchestration must not.
- **TEST-04** — Are test doubles colocated under `src/__tests__/doubles/` and do they implement the same port interface as the real adapters (so port-shape drift is a compile error)? **Priority:** P1. **How to verify:** `find src/__tests__/doubles -name "*.ts"` returns one file per port; each file exports a class that `implements I<Capability>Gateway`.
- **TEST-05** — Is there at least one end-to-end smoke test that round-trips a tool call through bootstrap (in-memory adapters), proving the wire shape works? **Priority:** P2. **How to verify:** `find src/__tests__ -name "*.smoke.test.ts" -o -name "*.e2e.test.ts" | head` returns a file; the test starts the server with in-memory doubles and asserts `tools-call` returns the expected `CallToolResult`.

## Grading rubric

The audit is graded mechanically. The reviewer's judgement applies only to whether the verification command actually proves the item — not to whether the priority should change.

- **P0 count = 0** → merge is allowed (assuming the rest of the review process clears). The verdict line at the top of the report reads `Verdict: merge`.
- **P0 count ≥ 1** → merge is **blocked**. Each P0 must be fixed in the same PR (or a stacked PR landing first). Do not approve "fix in follow-up" for P0 items; that is the path that produced the drift this skill exists to prevent. The verdict line reads `Verdict: block`. The merge-blocking implication is unconditional: a single P0 hold is enough to block, regardless of how many other items pass.
- **P1 count ≥ 1** → merge is allowed only when each P1 finding has a corresponding follow-up issue filed and linked from the PR description. The PR description's "Follow-ups" section names each issue by URL. If the issue is not yet filed, the verdict line reads `Verdict: merge with follow-ups (N issues required)`. Filing the issues is part of the audit's deliverable, not a future task.
- **P2 count** → informational only. Listed in the report's "Nits" section without gating. They become P1 if they accumulate (more than ten in one PR is itself a P1 finding about review hygiene).
- The rubric is mechanical so two reviewers running it against the same repo at the same SHA reach the same verdict. If two reviewers disagree on a finding's priority, the higher priority wins for the verdict — an item flagged P0 by one reviewer and P1 by another is treated as P0 until the disagreement is resolved.

## Recommended report format

Every audit produces one report. The shape is fixed so the author can scan it without learning a new layout each time.

```
# Audit — <repo>@<sha>

**Verdict:** merge | merge with follow-ups | block

## Summary
- Items inspected: <N>
- P0: <count>   (merge-blocking)
- P1: <count>   (follow-up issues required if merging)
- P2: <count>   (informational)

## P0 findings (merge-blocking)
- <ID> — <one-line summary>. Evidence: <command + output or file:line>.
- ...

## P1 findings (follow-up issues required)
- <ID> — <one-line summary>. Suggested issue title: "<title>". Evidence: <command + output>.
- ...

## P2 nits
- <ID> — <one-line summary>.

## Per-layer score
- Layout: <pass | <count> findings>
- Boundary: <pass | <count> findings>
- TypeScript quality: <pass | <count> findings>
- MCP wiring: <pass | <count> findings>
- Errors and responses: <pass | <count> findings>
- Request context: <pass | <count> findings>
- Tests: <pass | <count> findings>

## Verification commands run
- <command 1>
- <command 2>
- ...
```

Cite the exact command for each P0 finding so the author can replay it. Do not paraphrase the verification — paste the command. The "Verification commands run" section at the bottom is the audit's reproducibility contract: a different reviewer pulling the same SHA must be able to replay every command and reach the same conclusion.

When the report is delivered as a PR comment rather than a standalone document, keep the shape but collapse "P2 nits" into a single bullet listing the IDs (a reviewer scanning a PR comment cares about merge-blocking issues first; nits are noise unless asked for). When the report is delivered as a checked-in file in the repo, the full shape applies.

## What a fast audit looks like in practice

For a sub-50-tool MCP server with the standard layout, an audit completes in roughly 20–40 minutes if the repo is healthy and 60–120 minutes if it is drifted. The phases:

1. **Inventory** (5 min): `find src -maxdepth 2 -type d` and `find src -name "*.ts" | wc -l` to size the surface; open one handler, one use case, one gateway, and `bootstrap.ts` to get a feel for naming and shape.
2. **Boundary sweep** (10 min): run the boundary `grep` checks above. The four results — `process.env` outside config, `mcp-use` in inner layers, monolithic `tools/` files, `new MCPServer` outside bootstrap — predict 80% of the eventual P0 count.
3. **Layer-by-layer line items** (15 min): walk the checklist top to bottom, recording yes / no / not applicable in your notes.
4. **Spot-read three random handlers** (5 min): confirm the schema discipline (TYPESCRIPT-02, MCP-05) and the use-case delegation (no business logic in the handler). Three is enough; the patterns repeat.
5. **Render the report** (5 min): fill in the template above. Resist the urge to soften priorities; a P0 count is a verdict, not an opinion.

## Anti-patterns the boundary sweep should catch on the first pass

These are the patterns that produced the drift in the canonical example (`mcp-ads-meta`). When the boundary sweep finds any of them, the report's P0 section will be non-empty before you reach the line-item walk.

- **Monolithic `src/tools/<feature>.ts` with `server.tool(...)` called inline.** A file at `src/tools/lead-forms.ts` of ~459 lines or `src/tools/accounts.ts` of ~477 lines, importing `mcp-use/server` directly and registering several tools in one file, is the highest-signal failure mode. It violates LAYOUT-02, BOUNDARY-02, and MCP-01 simultaneously.
- **`process.env` reads in `src/infrastructure/config.ts` plus `src/infrastructure/auth/config.ts` plus a sprinkle inside business code.** The `BOUNDARY-03` `grep` will find them all. A repo that has the seam in one place but is leaking through `auth/config.ts` is mid-refactor and needs a follow-up issue, not a fresh audit.
- **No `handlers/` folder at all.** Some drifted repos route directly from `src/tools/<feature>.ts` to `src/use-cases/<feature>/`, skipping the `defineTool()` factory. LAYOUT-02 and MCP-01 are both P0 in that case.
- **Use cases that import `mcp-use` for "convenience" types.** `BOUNDARY-02` catches this. The fix is a local structural type in `src/shared/types/` mirroring the SDK shape — the use case depends on the local type.
- **`new ConcreteGateway(...)` calls inside use cases or handlers.** `BOUNDARY-07` catches this. Construction belongs in bootstrap. Anything else means the use case can't be tested without the network.
- **Raw provider error types (`GraphApiError`, `RateLimitError`, SDK-emitted shapes) re-thrown out of the gateway.** `ERROR-03` catches this with `grep -rn "throw err" src/gateways`. Each hit is a P0; the upstream error must be classified into a `DomainError` subclass first.

## Worked example — applying the rubric to `mcp-ads-meta`

A reviewer pointing the checklist at `mcp-ads-meta` at the time of writing would record:

- **LAYOUT-02 = no (P0).** Evidence: `wc -l src/tools/lead-forms.ts src/tools/accounts.ts src/tools/auth.ts` shows 459, 477, 475 lines per file. Each registers multiple tools.
- **BOUNDARY-02 = no (P0).** Evidence: `grep -rln "from \"mcp-use" src/ | wc -l` returns 154 — far more than the handler-only surface should produce.
- **BOUNDARY-03 = mostly no (P0).** Evidence: `grep -rn "process.env" src/` returns hits inside `src/infrastructure/config.ts` (lines 19, 32, 42, 136, 287, 337) and `src/infrastructure/auth/config.ts` (lines 146, 195) — concentrated but still spread across two files; the fix is to consolidate into `src/infrastructure/config/runtime-config.ts`.
- **MCP-01 = no (P0).** Evidence: `grep -rn "server.tool(" src/tools/lead-forms.ts` matches multiple times. No `defineTool()` factory exists.
- **TYPESCRIPT-01 = partial (P1).** Evidence: open `tsconfig.json` and confirm which locked flags are absent.

A reviewer who stops at this point — five P0s in five minutes — has enough to write `Verdict: block`. The remaining checklist walk is for the follow-up issue list, not for changing the verdict.

For comparison, the audit produces a clean verdict on `mcp-d4s` (`Verdict: merge` with one or two P2 nits) and a "merge with follow-ups" verdict on the cleaner siblings (`mcp-gsc`, `mcp-ga4`, `mcp-ads-google`) — all of which adopt the standard but each carries one or two follow-ups around the request-context boundary or the test-double colocation.

## After the report — what the author owes back

The audit is not delivered into a void. The PR author (or repo maintainer) owes a small set of mechanical responses:

- For each P0 finding: a code change in the same PR, or a stacked PR landing first. The PR description's "Audit response" section names each P0 ID and links to the commit that resolves it.
- For each P1 finding: a follow-up issue filed before merge. The issue title matches the suggested issue title from the report. The issue body contains the same "Evidence" line the report carried, so a future reader does not have to re-derive the finding.
- For each P2 nit: nothing required. The next audit may flag it again if it persists; that is acceptable.

A re-audit is run against the next SHA on the same branch. Items previously flagged P0 that have been resolved appear in the new report's "Resolved" appendix, not the live findings — the appendix is a goodwill record so the author sees their work acknowledged.

## Triggers that force a fresh audit

Some changes warrant a re-audit even when the PR diff looks small:

- A new external dependency added to `package.json` (especially anything matching `mcp-*`, `*-sdk`, or a provider client). `BOUNDARY-02`, `BOUNDARY-07`, and `ERROR-03` are the relevant items.
- A new env var added to `.env.example` or `runtime-config.ts`. `BOUNDARY-03` and the config-seam contract.
- A new tool added under `src/handlers/<feature>/`. `LAYOUT-02`, `MCP-01`, `MCP-05`, `MCP-06`.
- Any change that touches `src/infrastructure/server/bootstrap.ts`. The locked construction order is load-bearing; a re-audit confirms it is preserved.

A small diff is not a small audit when it crosses one of those triggers. Run the full checklist; the cost is bounded by the boundary sweep at the start.

## Quick-reference command bundle

Paste this block into a terminal at the repo root to run the boundary sweep in one pass. Each command maps to one or more checklist items.

```bash
# Boundary sweep
grep -rn "process\\.env" src/ | grep -v "src/infrastructure/config/runtime-config.ts"   # BOUNDARY-03
grep -rln "from ['\"]mcp-use" src/domain src/application src/gateways src/shared        # BOUNDARY-02
grep -rn "new MCPServer\\|server\\.tool(\\|server\\.resource(\\|server\\.prompt(" src/  # BOUNDARY-06, MCP-02
grep -rn "new [A-Z][A-Za-z]*Gateway(" src/ | grep -v "src/infrastructure/server/bootstrap.ts"  # BOUNDARY-07
find src/handlers -name "*.handler.ts" | xargs -n1 wc -l | awk '{print $1}' | sort -n | tail -5  # LAYOUT-02

# TypeScript bar
grep -rnE ": any\\b|as any\\b|@ts-ignore|z\\.any\\(|z\\.unknown\\(" src/                # TYPESCRIPT-02
grep -rnE "console\\.(log|info|warn|error|debug)" src/                                  # TYPESCRIPT-07
grep -rnE "catch \\(err: any\\)|catch \\(error: any\\)|catch\\(err\\)" src/             # ERROR-05

# MCP wiring
grep -rn "z\\.object" src/handlers | grep -v "\\.strict()"                              # MCP-05
grep -rn "outputSchema" src/handlers                                                    # MCP-06
grep -rn "ctx\\.elicit\\|ctx\\.sample\\|extra\\.elicit\\|extra\\.sample" src/application src/domain src/gateways  # MCP-04
```

Empty output is the desired state for everything except `find src/handlers ... wc -l` (which should print short numbers) and `grep -rn "outputSchema" src/handlers` (which should match every handler). When any "should be empty" command produces output, copy that output into the report's evidence column verbatim — paraphrasing it makes the report harder to replay.

## What you must verify before finishing

These are the closing checkpoints. Each is an observable command whose output backs your verdict.

- Every checklist item has a recorded answer (yes / no / not applicable). The total count of items answered is at least 28; the per-category counts meet or exceed the minimums (Layout ≥ 4, Boundary ≥ 5, TypeScript quality ≥ 6, MCP wiring ≥ 4, Errors and responses ≥ 4, Request context ≥ 2, Tests ≥ 3).
- The verdict at the top of the report is consistent with the rubric: P0 = 0 yields merge; P0 ≥ 1 yields block; any P1 ≥ 1 with a merge verdict has follow-up issue links in the PR description.
- Each P0 finding cites the exact `grep`, `find`, or `pnpm exec` command (or the file path and line) that proved it. A reviewer reading only the report can replay every check without rerunning the audit from scratch.
- The report names the per-layer score, so the author can see at a glance which layer(s) need work — not just the global pass/fail.
