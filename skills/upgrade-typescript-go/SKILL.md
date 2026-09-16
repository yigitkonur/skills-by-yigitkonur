---
name: upgrade-typescript-go
description: "Use if upgrading a TypeScript project to the native Go compiler (TypeScript 7.0+ / tsgo) — preflight audit, tsconfig modernization, Compiler API bridging, and post-migration verification."
---

# Upgrade TypeScript Go

TypeScript 7.0 transitions the compiler and language service from a single-threaded Node.js/V8 runtime to a native Go binary (codenamed Project Corsa). This rewrite delivers 8–12x faster type checking and eliminates JavaScript heap Out-Of-Memory crashes, while preserving identical type system semantics.

This skill governs the entire migration process end-to-end: assessing the repository, modernizing compiler options, bridging legacy JavaScript Compiler API consumers, switching compiler binaries, and proving correctness through a six-tier verification gate.

## When To Use

Trigger on requests and project states like:

- *"upgrade typescript to the latest version"*, *"upgrade to typescript 7"*, *"switch to typescript go"*
- *"migrate to tsgo"*, *"make tsc faster"*, *"speed up type checking"*
- *"fix tsc out of memory errors"*, *"modernize tsconfig for typescript 7"*
- *"how do we adopt the new typescript go compiler"*

Do **NOT** use this skill for:

- *General code refactoring or cleaning unused exports* — use `run-ts-cleanup`.
- *Migrating test assertion types to Shoehorn* — use `migrate-to-shoehorn`.
- *A dirty working tree or failing baseline* — commit or fix existing test failures first.

## Non-Negotiable Safety Rails

1. **Start green.** Verify `git status --porcelain` is clean and all existing tests pass before modifying any files.
2. **Branch isolation.** Always execute the upgrade on a dedicated branch (`chore/upgrade-typescript-go`).
3. **No broken Compiler API tools.** Identify scripts relying on `import * as ts from 'typescript'` and attach the `@typescript/typescript6` compatibility bridge before removing TypeScript 6.
4. **Clean `tsconfig.json` modernization.** Purge removed options (`baseUrl`, `target: "es5"`, `moduleResolution: "node10"`) before invoking the native engine.
5. **Pass the complete 6-tier gate.** Typecheck, composite build, declaration emit, lint, test, and production build must all pass before declaring done.

## The Six-Phase Migration Workflow

```
 Phase 0 — Preflight Audit: clean tree, inventory tsconfigs, find Compiler API consumers
                              │
 Phase 1 — Config Modernization: target, moduleResolution, baseUrl, paths
                              │
 Phase 2 — Tooling & AST Bridge: attach @typescript/typescript6 if Strada required
                              │
 Phase 3 — Engine Upgrade: install typescript@latest / @typescript/native-preview
                              │
 Phase 4 — Six-Tier Verification: typecheck → composite → decls → lint → test → build
                              │
 Phase 5 — CI/CD & IDE Alignment: sanitize NODE_OPTIONS, configure LSP, update docs
```

---

### Phase 0: Preflight Audit & Baseline

1. **Working Tree & Branch**: Ensure git working tree is clean. Create migration branch:
   ```bash
   git checkout -b chore/upgrade-typescript-go
   ```
2. **Compiler API Audit**: Scan for direct imports of the legacy JavaScript `typescript` package:
   ```bash
   git grep "from ['\"]typescript['\"]"
   ```
   If found, see [references/breaking-changes/compiler-api-strada.md](references/breaking-changes/compiler-api-strada.md).
3. **Scan `tsconfig.json` Options**: Inspect all tsconfig files against [references/checklists/preflight-audit-checklist.md](references/checklists/preflight-audit-checklist.md).
4. **Establish Green Baseline**: Verify `type-check`, `test`, and `build` succeed on current setup.

---

### Phase 1: `tsconfig.json` Modernization

Update all `tsconfig*.json` files across the workspace:

1. **Target**: Replace `ES5`/`ES3` with `ES2022` or `ESNext`. See [references/breaking-changes/es5-deprecation-and-targets.md](references/breaking-changes/es5-deprecation-and-targets.md).
2. **Module Resolution**: Replace `node10`/`node` with `bundler` (for web/apps) or `NodeNext` (for Node ESM). See [references/breaking-changes/module-resolution-modernization.md](references/breaking-changes/module-resolution-modernization.md).
3. **Remove `baseUrl`**: Remove `baseUrl` and rewrite `paths` mappings to start with `./`. See [references/breaking-changes/baseurl-and-paths-migration.md](references/breaking-changes/baseurl-and-paths-migration.md).
4. **Purge Removed Flags**: Remove legacy options listed in [references/breaking-changes/removed-compiler-options.md](references/breaking-changes/removed-compiler-options.md).

---

### Phase 2: Tooling & AST Compatibility Bridging

1. **Compiler API Bridge**: For any build scripts, codegen tools, or custom ESLint rules requiring the legacy Strada API, install the bridge:
   ```bash
   pnpm add -D @typescript/typescript6
   ```
   Update scripts to import from `@typescript/typescript6`. See [references/toolchain/typescript6-compat-bridge.md](references/toolchain/typescript6-compat-bridge.md).
2. **Linter Alignment**: Verify ESLint and `@typescript-eslint` packages. See [references/ecosystem/linters-and-ast-tools.md](references/ecosystem/linters-and-ast-tools.md).
3. **Script Runners**: Replace any legacy `ts-node` references with `tsx`. See [references/ecosystem/bundlers-and-transpilers.md](references/ecosystem/bundlers-and-transpilers.md).

---

### Phase 3: Engine Upgrade & Script Switch

1. **Upgrade Dependencies**:
   ```bash
   # Option A: Full TypeScript 7.0+
   pnpm add -D typescript@latest

   # Option B: Native preview binary (tsgo)
   pnpm add -D @typescript/native-preview
   ```
   See [references/toolchain/tsgo-native-binary.md](references/toolchain/tsgo-native-binary.md).
2. **Update Package Scripts**:
   ```json
   {
     "scripts": {
       "type-check": "tsc --noEmit"
     }
   }
   ```
3. Follow the detailed step-by-step checklist in [references/checklists/step-by-step-migration-guide.md](references/checklists/step-by-step-migration-guide.md).

---

### Phase 4: Six-Tier Verification Gate

Execute all 6 tiers described in [references/checklists/post-migration-verification-gate.md](references/checklists/post-migration-verification-gate.md):

| Tier | Gate | Command |
| :--- | :--- | :--- |
| **Tier 1** | Native Type Check | `pnpm run type-check` |
| **Tier 2** | Composite References | `tsc --build --verbose` (if monorepo) |
| **Tier 3** | Declaration Emit | `tsc --declaration --emitDeclarationOnly` (if library) |
| **Tier 4** | Linter & Static Analysis | `pnpm run lint` |
| **Tier 5** | Test Suite | `pnpm test` |
| **Tier 6** | Production Build | `pnpm run build` |

If type errors or build failures occur, consult:
- Framework guidance: [references/ecosystem/nextjs-migration.md](references/ecosystem/nextjs-migration.md) or [references/ecosystem/vite-and-vitest.md](references/ecosystem/vite-and-vitest.md).
- Monorepos: [references/ecosystem/monorepos-and-project-references.md](references/ecosystem/monorepos-and-project-references.md).
- Type error fixes: [references/troubleshooting/type-error-triage.md](references/troubleshooting/type-error-triage.md).
- Declaration emit: [references/troubleshooting/declaration-emit-failures.md](references/troubleshooting/declaration-emit-failures.md).
- General traps: [references/troubleshooting/common-migration-pitfalls.md](references/troubleshooting/common-migration-pitfalls.md).

---

### Phase 5: CI/CD & IDE Alignment

1. **Sanitize CI Environment**: In CI scripts, ensure `NODE_OPTIONS` does not include worker-incompatible flags. See [references/toolchain/cicd-container-optimization.md](references/toolchain/cicd-container-optimization.md) and [references/troubleshooting/memory-and-oom-prevention.md](references/troubleshooting/memory-and-oom-prevention.md).
2. **IDE Workspace Settings**: Configure `.vscode/settings.json` to point to the workspace native SDK. See [references/toolchain/ide-and-lsp-configuration.md](references/toolchain/ide-and-lsp-configuration.md).
3. **Commit & Document**: Commit changes with `chore(deps): upgrade to typescript native (go compiler)` and update project guides.

---

## Reference Routing Matrix

### Breaking Changes
- [references/breaking-changes/compiler-api-strada.md](references/breaking-changes/compiler-api-strada.md) — Strada JS Compiler API removal, impacted tools, and migration.
- [references/breaking-changes/removed-compiler-options.md](references/breaking-changes/removed-compiler-options.md) — Matrix of removed and deprecated compiler flags.
- [references/breaking-changes/module-resolution-modernization.md](references/breaking-changes/module-resolution-modernization.md) — Migrating from `node10` to `bundler` / `nodenext`.
- [references/breaking-changes/es5-deprecation-and-targets.md](references/breaking-changes/es5-deprecation-and-targets.md) — Target modernization and ES5 removal rationale.
- [references/breaking-changes/baseurl-and-paths-migration.md](references/breaking-changes/baseurl-and-paths-migration.md) — Removing `baseUrl` and normalizing path aliases.

### Ecosystem & Frameworks
- [references/ecosystem/nextjs-migration.md](references/ecosystem/nextjs-migration.md) — Next.js 14/15/16 App Router, Turbopack, and TS plugin setup.
- [references/ecosystem/vite-and-vitest.md](references/ecosystem/vite-and-vitest.md) — Vite, Vitest, Rolldown, and checker plugins.
- [references/ecosystem/monorepos-and-project-references.md](references/ecosystem/monorepos-and-project-references.md) — pnpm workspaces, Turborepo, and composite `tsc -b`.
- [references/ecosystem/linters-and-ast-tools.md](references/ecosystem/linters-and-ast-tools.md) — ESLint, Biome, Oxlint, and AST analysis compatibility.
- [references/ecosystem/bundlers-and-transpilers.md](references/ecosystem/bundlers-and-transpilers.md) — tsx, esbuild, SWC, and deprecating ts-node.

### Toolchain & Performance
- [references/toolchain/tsgo-native-binary.md](references/toolchain/tsgo-native-binary.md) — `tsgo` binary, preview installation, and CLI flags.
- [references/toolchain/typescript6-compat-bridge.md](references/toolchain/typescript6-compat-bridge.md) — Side-by-side coexistence with `@typescript/typescript6`.
- [references/toolchain/ide-and-lsp-configuration.md](references/toolchain/ide-and-lsp-configuration.md) — VS Code, Cursor, Neovim, and LSP daemon settings.
- [references/toolchain/cicd-container-optimization.md](references/toolchain/cicd-container-optimization.md) — GitHub Actions, Cloudflare CI, and container tuning.

### Troubleshooting & Diagnostics
- [references/troubleshooting/type-error-triage.md](references/troubleshooting/type-error-triage.md) — Resolving TS2532, TS2322, TS2304, and strict mode issues.
- [references/troubleshooting/declaration-emit-failures.md](references/troubleshooting/declaration-emit-failures.md) — Isolated declarations and TS4023/TS4058 fixes.
- [references/troubleshooting/memory-and-oom-prevention.md](references/troubleshooting/memory-and-oom-prevention.md) — Memory benchmarks and OOM prevention.
- [references/troubleshooting/common-migration-pitfalls.md](references/troubleshooting/common-migration-pitfalls.md) — Catalog of real-world edge cases.

### Checklists
- [references/checklists/preflight-audit-checklist.md](references/checklists/preflight-audit-checklist.md) — Pre-upgrade readiness verification.
- [references/checklists/step-by-step-migration-guide.md](references/checklists/step-by-step-migration-guide.md) — Execution roadmap.
- [references/checklists/post-migration-verification-gate.md](references/checklists/post-migration-verification-gate.md) — Six-tier post-upgrade acceptance gate.
