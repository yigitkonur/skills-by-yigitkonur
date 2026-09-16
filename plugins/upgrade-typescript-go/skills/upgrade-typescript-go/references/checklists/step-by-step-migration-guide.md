# Step-by-Step Migration Guide

Execute the upgrade in five controlled phases.

## Phase 1: Modernize `tsconfig.json` Files

1. Open root `tsconfig.json` (and all workspace `tsconfig.*.json` files).
2. Set `"target": "ESNext"` or `"ES2022"`.
3. Set `"moduleResolution": "bundler"` (for apps/bundlers) or `"NodeNext"` (for pure Node ESM).
4. Remove `"baseUrl"` and rewrite `"paths"` aliases to start with `./`.
5. Remove any deprecated compiler flags (`noImplicitUseStrict`, `keyofStringsOnly`, etc.).

## Phase 2: Install Compiler API Bridge (If Required)

If Phase 0 identified scripts importing `typescript` directly:
```bash
pnpm add -D @typescript/typescript6
```
Update AST script imports from `import ts from 'typescript'` to `import ts from '@typescript/typescript6'`.

## Phase 3: Upgrade TypeScript to Native Go Engine

Install the latest native compiler:

```bash
# Option A: Full TypeScript 7.0+
pnpm add -D typescript@latest

# Option B: Native preview binary (tsgo)
pnpm add -D @typescript/native-preview
```

## Phase 4: Align `package.json` Scripts

Ensure scripts invoke the native compiler:

```json
{
  "scripts": {
    "type-check": "tsc --noEmit",
    "type-check:watch": "tsc --noEmit --watch",
    "type-check:build": "tsc --build"
  }
}
```

## Phase 5: Execute Full Verification Gate

Run the complete 6-tier verification suite (see [post-migration-verification-gate.md](post-migration-verification-gate.md)).
