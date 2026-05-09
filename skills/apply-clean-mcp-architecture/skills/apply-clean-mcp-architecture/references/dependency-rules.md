# Dependency Rules

> SKILL.md's *Layer boundaries (the import matrix)* section routes here. After reading, you should be able to score any import statement in any file against the matrix; you should be able to drop the `dependency-cruiser.cjs` config below into a fresh repo and see the build fail on the first `domain/` → `gateways/` violation. The matrix is not a recommendation — it is the build gate that survives staff turnover.

## Why imports are a build gate, not a review gate

Documented architecture rots in two sprints. A reviewer who waves through "one tiny `mcp-use` import in a use case" will not be the reviewer six months later when twelve more have followed. Tool-enforced rules survive that drift. Inward-only direction is the rule that, when broken, makes every other Clean Architecture investment in the codebase worthless: once a use case imports a concrete gateway, you can no longer test or evolve either one independently. So the matrix runs as `dependency-cruiser` in CI, and a violation fails the build like any type error.

## The matrix in full

For each row, "May import" lists everything allowed; "Forbidden" calls out the items that look tempting and must be refused. The skill does not use bundlers — Node ESM resolution only — so the matrix is pure source-import discipline. The token "bundler" appears once below to explicitly forbid that toolchain.

| Layer | May import from | Forbidden imports |
|-------|-----------------|-------------------|
| `domain/` | (nothing — leaf layer) | `mcp-use`, `@modelcontextprotocol/sdk`, `zod`, `process.env`, any I/O, any other `src/` layer. |
| `application/` | `domain/`, `shared/` | `mcp-use`, `@modelcontextprotocol/sdk`, frameworks, concrete gateways, `presenters/`, `handlers/`, `infrastructure/`, `process.env`. |
| `handlers/` | `domain/`, `application/`, `presenters/` (port type only), `zod`, `mcp-use` types and helpers, `shared/types/` | Calling external APIs directly, reading config, instantiating gateways, importing concrete presenter classes. |
| `gateways/` | `domain/` (ports, errors), `shared/`, third-party SDKs | `application/`, `handlers/`, `mcp-use`, `presenters/`, `infrastructure/`. |
| `presenters/` | `domain/`, `mcp-use` response helpers (`text`, `object`, `mix`, `markdown`, `error`), `shared/` | `application/`, `gateways/`, `handlers/`, `infrastructure/`. |
| `infrastructure/` | All other layers (this is the wiring layer) | (none — everything composes here, but inner layers must still not import back). |
| `resources/`, `prompts/` | `domain/`, `application/`, `mcp-use` types, `shared/` | Direct gateway use, `process.env`, instantiating gateways. |
| `shared/` | `domain/` only | Side effects, business logic, framework imports, any other layer. |

## Edge cases the matrix decides for you

- **A type-only import across a forbidden boundary** is still forbidden. The fact that `verbatimModuleSyntax: true` makes it zero-cost at runtime does not undo the architectural coupling. Move the type to `domain/` or `shared/types/` instead.
- **A test file** mirrors its layer's rules but may import from `__tests__/doubles/` and from any layer it directly tests. The cruiser config below excludes `__tests__/` from the inner-layer rules and applies a separate test-only rule.
- **A presenter using `mcp-use` response helpers** (`text`, `object`, `mix`, `markdown`) is the *only* sanctioned `mcp-use` import outside `handlers/`, `resources/`, `prompts/`, and `infrastructure/`. The presenter does not call `MCPServer`, does not register tools, does not read sessions — just shape helpers.
- **A handler that needs an SDK shape** (e.g. a slice of `CallToolResult`) imports a local mirror from `shared/types/`, not from `mcp-use` or `@modelcontextprotocol/sdk` directly. SDK-version churn updates one file in `shared/types/`, not every handler.

## How violations look in practice

```ts
// ❌ application/<feature>/<feature>.usecase.ts
import { mix } from 'mcp-use/server';            // application must not see mcp-use
import { ProcessEnvVars } from 'node:process';   // application must not read env
import { DataForSeoGateway } from '../../gateways/dataforseo/dataforseo-gateway.js'; // concrete gateway

// ✅ application/<feature>/<feature>.usecase.ts
import type { IProviderGateway } from '../../domain/ports/provider-gateway.js';
import { ToolResponse } from '../../domain/tool-response/tool-response.js';
import { ValidationError } from '../../domain/errors.js';
```

```ts
// ❌ domain/<entity>/<entity>.ts
import { z } from 'zod';                                              // domain stays Zod-free
import type { CallToolResult } from '@modelcontextprotocol/sdk/...';  // and SDK-free

// ✅ domain/<entity>/<entity>.ts
// (no third-party imports — language primitives only)
```

## Copy-paste `dependency-cruiser` config

Save this file as `dependency-cruiser.cjs` at the repo root (the `.cjs` extension is required because the project is `"type": "module"` in `package.json` — `dependency-cruiser` itself is CommonJS). Wire it into CI as a hard gate (`pnpm dlx dependency-cruiser src` in a `deps:validate` script).

```cjs
/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    // ── 1. Inward-only direction ──────────────────────────────────────────
    // domain/ may import nothing from any other src/ layer.
    {
      name: 'no-domain-import-application',
      severity: 'error',
      from: { path: '^src/domain/' },
      to: { path: '^src/application/' },
    },
    {
      name: 'no-domain-import-handlers',
      severity: 'error',
      from: { path: '^src/domain/' },
      to: { path: '^src/handlers/' },
    },
    {
      name: 'no-domain-import-gateways',
      severity: 'error',
      from: { path: '^src/domain/' },
      to: { path: '^src/gateways/' },
    },
    {
      name: 'no-domain-import-presenters',
      severity: 'error',
      from: { path: '^src/domain/' },
      to: { path: '^src/presenters/' },
    },
    {
      name: 'no-domain-import-infrastructure',
      severity: 'error',
      from: { path: '^src/domain/' },
      to: { path: '^src/infrastructure/' },
    },
    {
      name: 'no-domain-import-resources',
      severity: 'error',
      from: { path: '^src/domain/' },
      to: { path: '^src/(resources|prompts)/' },
    },

    // application/ may only import from domain/ and shared/.
    {
      name: 'no-application-import-handlers',
      severity: 'error',
      from: { path: '^src/application/' },
      to: { path: '^src/handlers/' },
    },
    {
      name: 'no-application-import-gateways',
      severity: 'error',
      from: { path: '^src/application/' },
      to: { path: '^src/gateways/' },
    },
    {
      name: 'no-application-import-presenters',
      severity: 'error',
      from: { path: '^src/application/' },
      to: { path: '^src/presenters/' },
    },
    {
      name: 'no-application-import-infrastructure',
      severity: 'error',
      from: { path: '^src/application/' },
      to: { path: '^src/infrastructure/' },
    },
    {
      name: 'no-application-import-mcp-use-or-sdk',
      severity: 'error',
      comment: 'application/ must stay framework-free; SDK shape changes must not ripple here.',
      from: { path: '^src/application/' },
      to: { path: 'node_modules/(mcp-use|@modelcontextprotocol/sdk)' },
    },

    // gateways/ may only import from domain/, shared/, and third-party SDKs.
    {
      name: 'no-gateways-import-application',
      severity: 'error',
      from: { path: '^src/gateways/' },
      to: { path: '^src/application/' },
    },
    {
      name: 'no-gateways-import-handlers',
      severity: 'error',
      from: { path: '^src/gateways/' },
      to: { path: '^src/handlers/' },
    },
    {
      name: 'no-gateways-import-presenters',
      severity: 'error',
      from: { path: '^src/gateways/' },
      to: { path: '^src/presenters/' },
    },
    {
      name: 'no-gateways-import-mcp-use',
      severity: 'error',
      from: { path: '^src/gateways/' },
      to: { path: 'node_modules/mcp-use' },
    },

    // presenters/ may only import from domain/, shared/, and mcp-use response helpers.
    {
      name: 'no-presenters-import-application',
      severity: 'error',
      from: { path: '^src/presenters/' },
      to: { path: '^src/application/' },
    },
    {
      name: 'no-presenters-import-gateways',
      severity: 'error',
      from: { path: '^src/presenters/' },
      to: { path: '^src/gateways/' },
    },
    {
      name: 'no-presenters-import-handlers',
      severity: 'error',
      from: { path: '^src/presenters/' },
      to: { path: '^src/handlers/' },
    },
    {
      name: 'no-presenters-import-infrastructure',
      severity: 'error',
      from: { path: '^src/presenters/' },
      to: { path: '^src/infrastructure/' },
    },

    // handlers/ must not call concrete gateways or read config.
    {
      name: 'no-handlers-import-gateways-concretely',
      severity: 'error',
      comment:
        'Handlers receive ports through HandlerContext. Importing a concrete gateway means the handler is wiring its own infrastructure.',
      from: { path: '^src/handlers/' },
      to: { path: '^src/gateways/' },
    },
    {
      name: 'no-handlers-import-infrastructure',
      severity: 'error',
      from: { path: '^src/handlers/' },
      to: { path: '^src/infrastructure/' },
    },

    // shared/ must not import from any other src/ layer.
    {
      name: 'no-shared-import-other-layers',
      severity: 'error',
      from: { path: '^src/shared/' },
      to: { path: '^src/(application|handlers|gateways|presenters|infrastructure|resources|prompts)/' },
    },

    // ── 2. Single config seam ─────────────────────────────────────────────
    // process.env reads only in infrastructure/config/.
    {
      name: 'no-process-env-outside-config',
      severity: 'error',
      comment:
        'runtime-config.ts is the only file that reads process.env. Anywhere else is a build error.',
      from: { path: '^src/', pathNot: '^src/infrastructure/config/' },
      to: { path: 'node:process|^process$' },
    },

    // ── 3. mcp-use placement ──────────────────────────────────────────────
    // mcp-use only in handlers/, resources/, prompts/, presenters/, infrastructure/.
    {
      name: 'no-mcp-use-outside-allowed-layers',
      severity: 'error',
      comment:
        'mcp-use imports are restricted to layers that talk to the protocol surface. Inner layers stay SDK-free.',
      from: {
        path: '^src/',
        pathNot:
          '^src/(handlers|resources|prompts|presenters|infrastructure)/',
      },
      to: { path: 'node_modules/(mcp-use|@modelcontextprotocol/sdk)' },
    },

    // ── 4. No barrel re-exports inside src/ ───────────────────────────────
    // index.ts files (other than infrastructure/server/) are forbidden.
    {
      name: 'no-barrel-files',
      severity: 'error',
      comment:
        'Barrels cause cold-start regressions and circular imports. Direct file imports only. The single allowed location is infrastructure/server/.',
      from: {
        path: '^src/',
      },
      to: {
        path: '^src/(?!infrastructure/server/).*/index\\.ts$',
      },
    },

    // ── 5. Forbid stdout corruption sources ───────────────────────────────
    {
      name: 'no-console-anywhere',
      severity: 'error',
      comment: 'console.* corrupts the JSON-RPC stdout wire under stdio transport. Use the Logger port.',
      from: { path: '^src/' },
      to: { path: '^src/.*' },
      // The console.* check is implemented via lint, not module import — keep this stub
      // here so reviewers know where to look. Real enforcement lives in eslint.config.js
      // with `no-console: 'error'` for src/, allowed in src/__tests__/.
    },

    // ── 6. Cycle detection ────────────────────────────────────────────────
    {
      name: 'no-circular',
      severity: 'error',
      from: {},
      to: { circular: true },
    },

    // ── 7. Orphan detection ───────────────────────────────────────────────
    {
      name: 'no-orphans',
      severity: 'warn',
      from: {
        orphan: true,
        pathNot: ['\\.test\\.ts$', '\\.spec\\.ts$', '^src/index\\.ts$'],
      },
      to: {},
    },
  ],

  options: {
    doNotFollow: { path: ['node_modules', 'dist'] },
    exclude: { path: ['^src/__tests__/'] },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: 'tsconfig.json' },
    enhancedResolveOptions: {
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default'],
      extensions: ['.ts', '.js', '.json'],
    },
    cache: {
      strategy: 'content',
      folder: 'node_modules/.cache/dependency-cruiser',
    },
  },
};
```

## Wiring it into the merge gate

Add a script to `package.json`:

```json
{
  "scripts": {
    "deps:validate": "dependency-cruiser src --config dependency-cruiser.cjs --no-config-validate"
  }
}
```

Run it in CI alongside `tsc --noEmit`, `eslint`, and the test suite. Treat findings as build failures, never warnings — warnings get ignored, build failures actually block. If a new rule is justified, change the config, do not silence the rule.

## Coordinating with TypeScript

`dependency-cruiser` catches cross-layer imports. TypeScript's `verbatimModuleSyntax: true` (required by the locked `tsconfig`) catches the case where a value-import from an outer layer accidentally pulls runtime code into an inner layer. The two work together: the cruiser sees the edge in the import graph; TypeScript sees that the edge is value, not type. Use `import type` for every type-only cross-layer import, and the runtime dependency direction is provable at compile time.

## What you must verify before finishing

- [ ] The `dependency-cruiser.cjs` block above is at the repo root, named exactly `dependency-cruiser.cjs`, and is reachable by `pnpm exec dependency-cruiser src`.
- [ ] `pnpm deps:validate` runs to completion and reports zero `error`-severity findings on a clean tree.
- [ ] Inserting a deliberate violation (e.g. `import { mix } from 'mcp-use/server'` into an `application/` file) makes `pnpm deps:validate` fail with the exact rule name `no-mcp-use-outside-allowed-layers`.
- [ ] Inserting a deliberate `process.env.X` read into an `application/` or `gateways/` file makes the validator fail with `no-process-env-outside-config`.
- [ ] Adding an `index.ts` re-export inside `src/application/` or `src/handlers/` makes the validator fail with `no-barrel-files`.
- [ ] CI fails the build, not just emits a warning, when any of these rules trip.
- [ ] No `eslintrc` override silences `no-console` for `src/` (tests excepted).
- [ ] No file under `src/` imports `mcp-use` outside the allowed layers (`handlers/`, `resources/`, `prompts/`, `presenters/`, `infrastructure/`).
