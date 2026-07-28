# TypeScript Toolchain

Use this file for Node package installation, Corepack, TypeScript compilation, bundlers, and generated-code bottlenecks.

## CI install matrix

| Manager | CI command | Cache target | Notes |
|---|---|---|---|
| npm | `npm ci` | npm cache | Fails on lockfile/package drift; removes `node_modules` first. |
| pnpm | `pnpm install --frozen-lockfile` | pnpm store | CI freezes by default when a lockfile exists. |
| Yarn modern | `yarn install --immutable` | Yarn cache / Zero-Install cache | `--immutable-cache` for committed cache workflows. |
| Bun | `bun ci` | Bun install cache | Requires committed current `bun.lock`. |

Do not use plain `npm install` in CI when reproducibility matters. Do not cache `node_modules` by default; cache the package-manager store and measure restore versus clean install.

## Corepack and versions

- Pin Node and package-manager versions (`packageManager` field, `.nvmrc`, setup action, or explicit installer).
- Node 25+ no longer bundles Corepack; install Corepack explicitly or install the package manager directly.
- Include runtime and package-manager versions in cache keys.

## TypeScript compilation

Use project references for graph-aware repos:

```json
{
  "files": [],
  "references": [
    { "path": "packages/core" },
    { "path": "packages/cli" },
    { "path": "apps/web" }
  ]
}
```

```bash
tsc -b --pretty false
```

Cache `.tsbuildinfo` and emitted output only with keys containing TypeScript version, lockfile, and every relevant `tsconfig*.json`. On timestamp uncertainty, `tsc -b --force` is safer than a false incremental skip.

## Type checking versus transpilation

- `tsc -b` / `tsc --noEmit`: correctness gate.
- esbuild/SWC: fast emit/bundling, not a type-check replacement.

A good split is a fast typecheck job in parallel with artifact production, then a build job that uses cached typechecked packages where the graph allows.

## Generated code

Hash all of these into the cache/affected key:

- schema/IDL/source files,
- generator package/version,
- generator config,
- relevant environment variables,
- output path content.

A generated-code cache that does not include the generator version is a stale-output factory.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Lockfile works locally, fails CI | Plain install or missing frozen mode | Use manager-specific frozen CI command. |
| Cache restore slower than install | Store too large or network slower than registry | Measure; cache narrower store or skip cache. |
| TypeScript incremental stale | Shared tsbuildinfo across configs/versions | Include all tsconfigs/TS version in key or force build. |
| Bundled output lacks type safety | Transpiler treated as type checker | Keep `tsc` gate. |
| Sudden package-manager failure after Node bump | Corepack no longer bundled | Install/pin package manager explicitly. |

## Sources

- npm ci: https://docs.npmjs.com/cli/v8/commands/npm-ci (accessed 2026-07-28)
- pnpm install and CI: https://pnpm.io/cli/install ; https://pnpm.io/continuous-integration (accessed 2026-07-28)
- Yarn install: https://yarnpkg.com/cli/install (accessed 2026-07-28)
- Bun install and lockfile: https://bun.com/docs/pm/cli/install ; https://bun.com/docs/pm/lockfile (accessed 2026-07-28)
- setup-node: https://github.com/actions/setup-node (accessed 2026-07-28)
- Corepack: https://github.com/nodejs/corepack/blob/main/README.md (accessed 2026-07-28)
- TypeScript incremental and project references: https://www.typescriptlang.org/tsconfig/incremental.html ; https://www.typescriptlang.org/docs/handbook/project-references.html (accessed 2026-07-28)
