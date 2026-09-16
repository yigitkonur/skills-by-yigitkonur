# Preflight Audit Checklist

Run this checklist **before** modifying any dependencies or configuration files.

## 1. Baseline Git & Branch Health
- [ ] Working tree is clean: `git status --porcelain` returns no uncommitted changes.
- [ ] Working on a dedicated branch: `git checkout -b chore/upgrade-typescript-go`.
- [ ] Record current TypeScript version: `npx tsc --version`.

## 2. Dependency & Tooling Audit
- [ ] **Compiler API Consumers**: Search for direct imports of `typescript`:
  ```bash
  git grep "from ['\"]typescript['\"]"
  ```
- [ ] **Transpilation Runners**: Check `package.json` for `ts-node`, `ttypescript`, `ts-patch`.
- [ ] **Linters & Parsers**: Check `@typescript-eslint/parser` and `@typescript-eslint/eslint-plugin` versions (target v8+).

## 3. `tsconfig.json` Configuration Scan
- [ ] Scan all `tsconfig*.json` files for deprecated options:
  - [ ] `target: "es5"` / `"es3"`
  - [ ] `moduleResolution: "node10"` / `"node"`
  - [ ] `baseUrl`
  - [ ] `module: "amd"` / `"umd"` / `"system"`
  - [ ] `noImplicitUseStrict`, `keyofStringsOnly`, `suppressExcessPropertyErrors`

## 4. Green Baseline Verification Gate
- [ ] Current type check passes with exit code 0: `pnpm run type-check` (or `npx tsc --noEmit`).
- [ ] Current test suite passes: `pnpm test` (or `vitest run` / `jest`).
- [ ] Current production build succeeds: `pnpm run build`.

Do NOT proceed if the baseline is red. Fix existing bugs before upgrading compiler versions.
