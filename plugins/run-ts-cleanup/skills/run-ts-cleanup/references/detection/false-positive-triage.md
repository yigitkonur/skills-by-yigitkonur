# False Positive Triage Protocol

A rigorous triage framework to distinguish genuine dead code from static analysis blind spots, runtime reflection, framework entry points, and dynamic import patterns.

---

## 1. Principles of Static Analysis Blind Spots

Knip parses TypeScript and JavaScript Abstract Syntax Trees (ASTs). It tracks explicit import/export bindings and declared framework conventions. Knip cannot evaluate runtime string evaluation, dynamic reflections, metadata decorators, or untyped file-system lookups without explicit hints.

Every other engine this skill drives has its own blind spot: lint engines cannot see intent, `type-coverage` cannot see provenance, and `madge` cannot see type erasure. Sections 2–6 triage dead-code findings; section 7 triages lint, type, and graph findings.

Before deleting or modifying any flagged code, apply the **Three-Question Verification Test**:

1. **Framework Lifecycle**: Is this file or symbol invoked implicitly by a framework router, file-system convention, or bundler plugin?
2. **Dynamic Invocation**: Is this identifier accessed via dynamic `import()`, template literals, dictionary indexing (`obj[key]`), or runtime reflection?
3. **Public Contract**: Is this package or module consumed by external downstream consumers beyond this repository's immediate static graph?

If the answer to any question is **YES**, do not delete the code. Reconfigure the engine to document the entry point.

---

## 2. Framework Entry Points

Modern meta-frameworks use file-based routing and special exported functions that are invoked by framework internals rather than imported by user files.

### Next.js (App Router & Pages Router)

#### App Router Conventions
Next.js App Router relies on reserved file names and function signatures:
- `page.{js,jsx,ts,tsx}`: Default export is the UI component.
- `layout.{js,jsx,ts,tsx}`: Default export is the layout component.
- `route.{js,ts}`: HTTP methods (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS`) must be exported.
- `loading.{js,jsx,ts,tsx}`, `error.{js,jsx,ts,tsx}`, `not-found.{js,jsx,ts,tsx}`: Default exports.
- `middleware.{js,ts}`: Default export or `middleware` function, plus `config` export.
- `instrumentation.{js,ts}`: `register` and `onRequestError` exports.

#### Pages Router Conventions
- Special exports: `getStaticProps`, `getServerSideProps`, `getStaticPaths`, `config`.
- Special pages: `_app.tsx`, `_document.tsx`, `_error.tsx`, `404.tsx`, `500.tsx`.

#### Knip Configuration Triage for Next.js

Ensure the `next` plugin is activated. If custom directories or non-standard paths are used, supply explicit entries:

```json
{
  "next": {
    "entry": [
      "app/**/{page,layout,loading,error,not-found,route,default,template}.{js,jsx,ts,tsx}",
      "pages/**/*.{js,jsx,ts,tsx}",
      "middleware.{js,ts}",
      "instrumentation.{js,ts}"
    ]
  }
}
```

### Remix & React Router v7

Route files export specific handlers: `loader`, `action`, `headers`, `meta`, `links`, `handle`, `ErrorBoundary`.

```json
{
  "remix": true,
  "react-router": true
}
```

If custom route modules exist outside standard glob conventions, declare them explicitly:

```json
{
  "entry": [
    "app/routes/**/*.{ts,tsx}",
    "app/root.tsx"
  ]
}
```

### Astro & Nuxt & SvelteKit

| Framework | Unused Export / File Risk | Configuration Fix |
|---|---|---|
| Astro | Content collections (`src/content/config.ts`), Astro pages (`.astro`) | Enable `"astro": true`; ensure `compilers.astro` is present |
| Nuxt | Auto-imported composables (`composables/*`), plugins (`plugins/*`) | Enable `"nuxt": true`; mark composables folder as entry |
| SvelteKit | `+page.server.ts`, `+layout.server.ts`, hooks (`hooks.server.ts`) | Enable `"svelte": true` |

---

## 3. Dynamic Imports & Code Splitting

Dynamic imports that use template literals or variables cannot be resolved statically by Knip:

```typescript
// Static analysis fails to identify target files
const loadLocale = async (lang: string) => {
  return await import(`./locales/${lang}.json`);
};
```

### Verification Command

Grep for dynamic import expressions:
```bash
rg "import\s*\(" --type ts --type js --type tsx
```

### Mitigation Pattern

Never use broad top-level `"ignore"` to solve dynamic imports. Explicitly add dynamically loaded folders to the `entry` or `project` configuration:

```json
{
  "entry": [
    "src/index.ts",
    "src/locales/*.json"
  ]
}
```

---

## 4. Runtime Reflection, Metadata & Decorators

Frameworks that use TypeScript decorators and reflection metadata (e.g., NestJS, TypeORM, MikroORM, Prisma, class-validator, tRPC) invoke code via runtime introspection.

### Identified False Positive Categories:
1. **NestJS Modules & Controllers**: Methods decorated with `@Get()`, `@Post()`, `@Injectable()` appear unused because they have no static callers.
2. **TypeORM / MikroORM Entities**: Properties decorated with `@Column()`, `@PrimaryGeneratedColumn()`, `@ManyToOne()` appear unreferenced if only populated via database queries.
3. **Class Validator DTOs**: Fields decorated with `@IsString()`, `@IsOptional()` may appear as unused class members.
4. **tRPC Routers**: Nested router procedures called by client proxies over network boundaries.

### Knip Configuration Strategy for Decorator-Heavy Code

#### Option A: Disable Unused Member Rule
Class properties and enum members are the primary targets of decorator false positives. Note that Knip v6 removed the `classMembers` rule entirely to eliminate decorator false positives; in Knip v5, set `classMembers` to `"off"`:

```json
{
  "rules": {
    "enumMembers": "warn",
    "classMembers": "off" // Knip v5 only; removed in Knip v6
  }
}
```

#### Option B: Target Specific Entities
If entity files are reported as unused files, ensure TypeORM data-source or Nest CLI configurations are declared:

```json
{
  "nest": true,
  "typeorm": true,
  "entry": [
    "src/main.ts",
    "src/database/entities/**/*.entity.ts",
    "src/database/migrations/**/*.ts"
  ]
}
```

---

## 5. Cloudflare Workers & Edge Runtimes (`workerd`)

Cloudflare Workers execute within V8 isolates rather than Node.js runtimes. Static analysis engines operating with Node.js assumptions frequently misclassify edge entry points, ambient bindings, and background execution wrappers as dead code.

### 5.1 Platform Entry Points & Handler Methods
- **Root Entry Point**: `wrangler.json`, `wrangler.jsonc`, or `wrangler.toml` designates the entry file (e.g. `"main": "src/index.ts"`). Knip's `wrangler` plugin parses this configuration automatically.
- **`ExportedHandler<Env>` Default Export**: The entry file exports default handlers:
  ```typescript
  export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> { ... },
    async scheduled(controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> { ... },
    async queue(batch: MessageBatch<unknown>, env: Env, ctx: ExecutionContext): Promise<void> { ... },
  } satisfies ExportedHandler<Env>;
  ```
  **Rule**: Never strip `export default` or prune handler lifecycle methods (`scheduled`, `queue`, `email`, `tail`) even if no internal file imports them. They are invoked directly by the platform.

### 5.2 RPC Classes: Durable Objects, WorkerEntrypoint & Workflows
Classes exported for stateful actors or RPC service bindings are referenced in Wrangler manifests rather than code:
- `DurableObject` classes (bound in `durable_objects.bindings[].class_name`)
- `WorkerEntrypoint` classes (bound as service bindings)
- `WorkflowEntrypoint` classes (bound in `workflows[].class_name`)

**Defense**: Annotate RPC classes with `/** @public */` or set `"includeEntryExports": false` in `knip.jsonc` to prevent Knip from flagging them as unused exports.

### 5.3 Ambient Type Generation & Dependencies
- **`worker-configuration.d.ts` / `env.d.ts`**: Generated by `wrangler types`. Contains ambient declarations for `interface Env` with KV, D1, R2, and secret bindings. Because it contains no imports or exports, Knip will flag it as an unreferenced file. **Never delete this file.** Add to `ignore` in `knip.jsonc`.
- **`@cloudflare/workers-types`**: Referenced strictly in `tsconfig.json` (`compilerOptions.types`). Knip flags it as an unused devDependency. Add to `ignoreDependencies`.
- **`@cloudflare/vitest-pool-workers`**: Consumed by Vitest workers pool configuration. Add to `ignoreDependencies`.

### 5.4 Async Boundary Safety: `ctx.waitUntil()`
In `workerd`, when the fetch response promise settles, isolate execution terminates or suspends immediately. Floating un-awaited promises are killed mid-flight. Any background metric, logging, or queue dispatch must be wrapped in `ctx.waitUntil(promise)`. Never strip or unwrap `ctx.waitUntil()` as "redundant wrapper bloat".

---

## 6. Public API Contracts & Published Libraries

If the repository produces an npm package, component library, or shared workspace consumed externally:

### Public API Contracts & Library Exports (`includeEntryExports` & JSDoc `@public`)

When a repository produces an npm package, component library, or shared workspace consumed externally:

#### Default Knip Behavior (`includeEntryExports: false`)
By default, Knip sets `includeEntryExports: false`. This means Knip considers all exports from designated `entry` files as consumed by external callers and will NOT report them as unused exports, even if no file inside the repository imports them.

#### Strict Entry Export Verification (`includeEntryExports: true`)
If you want Knip to verify that entry exports are actively used within an application or designated public contract:
1. Set `"includeEntryExports": true` in `knip.jsonc`.
2. Annotate intentional public library exports with `/** @public */`.
3. Configure `tags: ["-public"]` (or rely on default `@public` retention).

#### Clarification: The `!` Suffix is for `--production` Mode Only
Do NOT append `!` to entry patterns to silence unused export reports. In Knip, a trailing `!` (e.g. `"src/index.ts!"`) indicates that the file belongs to production code for the `--production` mode filter (omitting devDependencies and test files). It does not alter export reachability.

### Package Manifest Exports Contract
Verify that your `package.json` correctly defines public entry points:

```json
{
  "name": "@my-org/shared-utils",
  "main": "./dist/index.js",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.mjs",
      "require": "./dist/index.js"
    },
    "./helpers": {
      "types": "./dist/helpers.d.ts",
      "import": "./dist/helpers.mjs"
    }
  }
}
```

If `package.json#exports` points to built output (`./dist/*`), point Knip's `entry` to the corresponding source files (`src/index.ts!`, `src/helpers.ts!`).

---

## 7. Build Scripts & CLI Binaries in `package.json`

Knip inspects `scripts` in `package.json` to detect binary usage (e.g., `rimraf`, `concurrently`, `tsc`, `cross-env`).

### Common Binary False Positives
- Shell built-in utilities invoked in scripts (`echo`, `mkdir`, `cp`, `rm`, `sed`, `awk`, `cat`).
- Native binaries installed on the host runner (`git`, `docker`, `docker-compose`, `gh`, `curl`, `jq`).
- CLI commands prefixed with environment variables or npx.

### Mitigation Pattern

Register host tools in `ignoreBinaries`:

```json
{
  "ignoreBinaries": [
    "docker",
    "docker-compose",
    "git",
    "gh",
    "curl",
    "jq",
    "which"
  ]
}
```

For packages referenced exclusively via Node.js `-r` or `--loader` flags:

```json
{
  "ignoreDependencies": [
    "ts-node",
    "dotenv/config",
    "source-map-support/register"
  ]
}
```

---

## 8. Lint, Type & Graph False Positives

Dead-code findings are not the only findings that lie. Lint engines, `type-coverage`, and `madge` each report items that are correct by construction.

### 8.1 Lint: Intentionally Unused Bindings

A lint engine reports "declared but never read" without knowing whether the binding is required by a signature it does not control.

| Flagged pattern | Why it exists | Verdict |
|---|---|---|
| `(_req, res) => ...` | Positional signature fixed by Express, Fastify, or a middleware contract. | False positive |
| `catch (_err) { fallback(); }` | Error deliberately swallowed at a boundary with a documented fallback. | False positive |
| `function f(_a: string, b: number)` | Overload conformance or an interface implementation. | False positive |
| `constructor(private readonly _svc: Svc)` | NestJS or InversifyJS parameter injection; used via decorator metadata. | False positive |
| `const [, second] = tuple` | Positional destructuring gap. | False positive |
| `const unusedHelper = ...` after Wave 3 | Genuine un-export residue. | True defect |

**The underscore convention is the contract.** A binding prefixed with `_` declares deliberate non-use. Configure the engine to honour it, then treat any remaining finding as a true defect.

```jsonc
// biome.json
{
  "linter": {
    "rules": {
      "correctness": {
        "noUnusedVariables": { "level": "error", "options": { "ignoreRestSiblings": true } },
        "noUnusedFunctionParameters": "error"
      }
    }
  }
}
```

```jsonc
// eslint.config.js — @typescript-eslint/no-unused-vars
{
  "argsIgnorePattern": "^_",
  "varsIgnorePattern": "^_",
  "caughtErrorsIgnorePattern": "^_",
  "destructuredArrayIgnorePattern": "^_",
  "ignoreRestSiblings": true
}
```

```jsonc
// tsconfig.json — tsc honours the leading underscore for parameters natively
{ "compilerOptions": { "noUnusedLocals": true, "noUnusedParameters": true } }
```

Rename the binding to `_name` rather than adding a disable comment. A rename encodes intent permanently; `// eslint-disable-next-line` decays into unexplained noise.

Never resolve a lint false positive by disabling `noUnusedVariables` repository-wide — that suppresses the un-export residue the inter-wave bridge depends on detecting.

### 8.2 `type-coverage`: Counting Code You Do Not Own

`type-coverage` scores every identifier reachable from `tsconfig.json`, including code no human wrote and no human can fix.

| Counted source | Why it drags the score | Fix |
|---|---|---|
| Generated clients (Prisma, GraphQL codegen, OpenAPI, protobuf) | Emit `any` in escape hatches and index signatures. | `--ignore-files "src/generated/**"` |
| Vendored or copied third-party code | Not authored in this repository. | `--ignore-files "vendor/**"` |
| Framework route types (`.next/types`, `.astro/`, `.svelte-kit/`) | Build artefacts inside the project graph. | Exclude the directory in `tsconfig.json`. |
| Test fixtures and mock payloads | Deliberately loose shapes. | `--ignore-files "**/*.fixture.ts"` |
| `catch (e)` bindings | `unknown` or `any` by language rule before TS 4.4 `useUnknownInCatchVariables`. | `--ignore-catch` |
| Ambient `.d.ts` from `@types/*` | Not repository code. | Already excluded by default; verify `tsconfig.json` `types`/`typeRoots` are properly configured. |

```bash
type-coverage --detail --strict --at-least 95 \
  --ignore-files "src/generated/**" \
  --ignore-files "**/*.gen.ts" \
  --ignore-catch
```

Pin the ignore set in `package.json` under `typeCoverage` so the local run and CI score the identical file set. A threshold that only passes locally is not a gate.

Judge the delta, not the absolute number: compare against the pre-flight baseline recorded in [`../remediation/waves.md`](../remediation/waves.md). Cleanup that deletes well-typed code while leaving `any`-heavy code lowers coverage without adding a single `any` — a real signal, not a false positive.

### 8.3 `madge`: Cycles That Do Not Exist at Runtime

`madge` builds its graph from import syntax and does not distinguish erased type imports from value imports.

| Reported cycle | Reality | Verdict |
|---|---|---|
| `a.ts -> b.ts -> a.ts` where both edges are `import type` | Erased by the compiler; no runtime module edge exists. | False positive |
| Edge from `import { type Foo, bar }` (inline type modifier) | Only `bar` survives emit; the cycle may vanish with it. | Inspect emitted output |
| Cycle only through `.d.ts` files | Declaration files emit nothing. | False positive |
| Cycle only through path aliases | `madge` resolved the alias to the wrong file, or failed to resolve it. | Configuration defect |
| `a.ts -> b.ts -> a.ts` with a value import in each direction | Genuine initialization-order hazard. | True defect |

Verify before acting:

```bash
# 1. Make madge resolve path aliases exactly as tsc does
madge --circular --extensions ts,tsx --ts-config ./tsconfig.json src/

# 2. Inspect the two edges named in the cycle
rg -n "^import .*from '(\./b|\./a)'" src/a.ts src/b.ts
```

An edge written `import type { Foo } from './b'` — or `import { type Foo }` where every specifier carries the modifier — is erased under `isolatedModules` and `verbatimModuleSyntax`. Confirm erasure, then dismiss the cycle.

Convert borderline edges rather than restructuring: rewriting `import { Foo }` to `import type { Foo }` deletes a real runtime edge at zero risk, and `verbatimModuleSyntax: true` makes the distinction enforceable thereafter.

### 8.4 `tsc`: Declaration Emit Is Not a False Positive

`TS4023`, `TS4060`, `TS4081`, `TS2742`, and `TS2883` surface only during declaration emit (e.g. `tsc --declaration --emitDeclarationOnly --outDir /tmp/dts-check` or `tsc -b --emitDeclarationOnly`; never `tsc -b --noEmit`, which triggers `TS5094`). They are always true defects — the compiler has proven it cannot name a type in the emitted `.d.ts`. Never suppress them with `// @ts-expect-error` or by disabling `declaration`. Diagnose with [`../types/declaration-emit.md`](../types/declaration-emit.md).

---

## 9. Verification Command Suite

Execute this sequence before treating any engine finding as a true defect.

### Tier 1: Repository Text Search (Ripgrep)

Check for direct, dynamic, or string references:

```bash
# 1. Search for symbol identifier across all source files
rg -w "SYMBOL_NAME" --glob '!**/dist/**' --glob '!**/node_modules/**'

# 2. Search for dynamic property access
rg "\['SYMBOL_NAME'\]"

# 3. Search for template string references
rg "[\`'\"].*SYMBOL_NAME.*[\`'\"]"
```

Zero matches across all three is necessary but not sufficient — it clears Question 2 of the Three-Question Test only.

### Tier 2: Engine-Specific Cross-Check

Confirm the finding survives its own engine's configuration fix before escalating:

```bash
# Dead-code finding: does declaring the entry point make it disappear?
knip --include exports

# Lint finding: does the underscore convention already cover it?
rg -n "\(\s*_[a-zA-Z]" src/

# Graph finding: does alias-aware resolution still report the cycle?
madge --circular --extensions ts,tsx --ts-config ./tsconfig.json src/
```

A finding that vanishes under correct configuration was always a false positive. Codify the configuration; do not delete the code.

### Tier 3: Run the Gate

Apply the candidate removal on a scratch commit and run **the gate** — typecheck, test, build — as defined once in [`../remediation/waves.md`](../remediation/waves.md). Read the result as triage evidence:

| Gate outcome | Meaning for this finding |
|---|---|
| All three legs green | No static, test, or bundler consumer. Proceed — unless Question 1 or 3 of the Three-Question Test is still open. |
| Leg 1 typecheck red | A static consumer exists. False positive; restore. |
| Leg 2 test red | A test consumer exists. Test-only leak, not dead code. |
| Leg 3 build red only | A bundler-only edge exists — asset, glob, or dynamic `import()`. False positive; declare the entry point. |
| All green, but framework-routed | The gate cannot see file-based routing. Quarantine instead of deleting; verify in a preview deployment. |

The last row is the reason the Three-Question Test exists: a green gate disproves static death, never runtime death.

---

## 10. Triage Decision Table

| Flagged Finding | Engine | Verification Check | Decision | Remediation Action |
|---|---|---|---|---|
| Export in `app/api/*/route.ts` | Knip | Next.js App Router route handler | False Positive | Ensure `next` plugin is enabled; do not un-export. |
| `ExportedHandler` in worker entry | Knip | Cloudflare Workers runtime handler | False Positive | Retain default export; enable `wrangler: true` in Knip config. |
| `DurableObject` / RPC class export | Knip | Bound in `wrangler.json` | False Positive | Add `/** @public */` JSDoc or set `includeEntryExports: false`. |
| `worker-configuration.d.ts` file | Knip | Ambient types generated by `wrangler types` | False Positive | Never delete; add to `ignore` in `knip.jsonc`. |
| `@cloudflare/workers-types` dep | Knip | Referenced in `tsconfig.json#types` | False Positive | Add to `ignoreDependencies` in `knip.jsonc`. |
| `@cloudflare/vitest-pool-workers` dep| Knip | Consumed by Vitest workers pool | False Positive | Add to `ignoreDependencies` in `knip.jsonc`. |
| `process.env.VAR` in worker handler | lint/audit | Leaked Node.js global in `workerd` | True Defect | Replace with request-scoped `env.VAR` or `this.env.VAR`. |
| `ctx.waitUntil(promise)` call | audit | Async boundary protection in `workerd` | Invariant | Preserve untouched; prevents premature isolate termination. |
| Class method in `@Entity()` class | Knip | Decorated TypeORM field | False Positive | Removed in Knip v6; in Knip v5 set `"classMembers": "off"` or register entity in entry. |
| Function only called in `*.test.ts` | Knip | Test-Only Leak | True Defect | Move helper into test directory or un-export and test public caller. |
| Dependency `autoprefixer` | Knip | PostCSS config plugin string | False Positive | Add `"postcss": true` or add to `ignoreDependencies`. |
| CLI binary `docker` | Knip | Shell invocation in `package.json` | False Positive | Add `"docker"` to `ignoreBinaries`. |
| Export only used in same file | Knip | No external references via `rg` | True Defect | Remove `export` keyword in-place. |
| Type definition with 0 references | Knip | `rg` shows 0 matches | True Defect | Safely delete interface/type. |
| File with 0 incoming imports | Knip | `rg` shows no dynamic `import()` | True Defect | Remove file from repository via `git rm`. |
| Unused param `_req` in a handler | lint | Signature fixed by framework contract | False Positive | Configure `argsIgnorePattern: "^_"`; keep the underscore. |
| Unused `catch (_err)` binding | lint | Deliberate swallow with fallback | False Positive | Configure `caughtErrorsIgnorePattern: "^_"`. |
| Unused local after Wave 3 | lint / `tsc` `TS6133` | Un-export residue | True Defect | Clear with linter autofix in the inter-wave bridge. |
| Coverage drop in `src/generated/**` | `type-coverage` | Codegen output, not authored code | False Positive | Add `--ignore-files "src/generated/**"`; pin it in `package.json`. |
| Coverage drop with no new `any` | `type-coverage` | Well-typed code deleted, ratio shifted | True Signal | Compare against the pre-flight baseline; investigate remaining `any`. |
| Cycle where both edges are `import type` | madge | Erased at emit under `isolatedModules` | False Positive | Dismiss; enable `verbatimModuleSyntax` to keep it erased. |
| Cycle appearing only without `--ts-config` | madge | Path alias resolved incorrectly | False Positive | Re-run with `--ts-config ./tsconfig.json`. |
| Cycle with a value import each way | madge | Genuine initialization hazard | True Defect | Extract shared values into a leaf module. |
| `TS4023` / `TS2742` on declaration emit | `tsc` | Compiler cannot name a type in `.d.ts` | True Defect | Re-export the type; never suppress. |
