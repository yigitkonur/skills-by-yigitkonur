# Common Migration Pitfalls & Solutions

## Overview

A curated catalogue of real-world edge cases encountered when migrating complex enterprise repositories to TypeScript 7.0 (Go Native).

## Pitfall 1: Retaining `baseUrl: "."` alongside Wildcard `paths`

**Symptom**: TS compiler reports deprecation errors or fails to resolve root packages.
**Solution**: Remove `baseUrl`. Prefix all paths in `paths` with `./` relative to the tsconfig location:
```json
// Fix:
"paths": {
  "@/*": ["./src/*"]
}
```

## Pitfall 2: Custom Code Generation Scripts Importing `typescript`

**Symptom**: `TypeError: ts.createSourceFile is not a function` or `Cannot find module 'typescript'`.
**Solution**:
1. Check if the script can be rewritten with template literals or code generation libraries.
2. If AST inspection is strictly necessary, install `@typescript/typescript6` and update imports to `from '@typescript/typescript6'`.

## Pitfall 3: Monorepo Symlinks and `preserveSymlinks`

**Symptom**: Types not resolving across pnpm workspace symlinks (`packages/a -> node_modules/@myorg/a`).
**Solution**: Ensure `"preserveSymlinks": false` (or omit) and configure path aliases in root `tsconfig.json` for internal packages.

## Pitfall 4: Conflicting Web Worker and DOM Types

**Symptom**: `Duplicate identifier 'ImageData'` or `Cannot redeclare block-scoped variable 'self'`.
**Solution**: In `tsconfig.json`, use isolated tsconfigs for web worker scripts, or enable `"skipLibCheck": true`.

## Pitfall 5: Stale Type Build Info Files

**Symptom**: Build succeeds locally but fails in CI, or reports errors on deleted files.
**Solution**: Clear stale `.tsbuildinfo` caches:
```bash
rm -rf .cache/tsc *.tsbuildinfo
```
