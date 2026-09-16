# Vite, Vitest & Rolldown Integration

## Overview

Vite, Vitest, and Rolldown do not run `tsc` during development or bundling. They use native transpilers (esbuild / OXC / SWC) to strip type annotations and transform JSX/TSX syntax.

Type checking in Vite projects is typically handled in one of two ways:
1. As a separate CLI script (`"type-check": "tsc --noEmit"` or `"type-check": "tsgo --noEmit"`).
2. As a background dev overlay plugin (e.g. `vite-plugin-checker`).

## Vite Configuration

### 1. `vite.config.ts`
Vite works out-of-the-box with TypeScript 7.0 without changes. If using `vite-plugin-checker`:
```ts
import { defineConfig } from 'vite';
import checker from 'vite-plugin-checker';

export default defineConfig({
  plugins: [
    checker({
      typescript: true, // Will execute the project's native tsc binary
    }),
  ],
});
```

## Vitest Configuration

Vitest executes tests in worker threads using Vite's transformation pipeline.

### 1. Vitest Types & Globals
In `tsconfig.json`, include `vitest/globals` if using global test APIs (`describe`, `it`, `expect`):
```json
{
  "compilerOptions": {
    "types": ["vitest/globals", "node"]
  }
}
```

### 2. Mocking & Dynamic Imports
When testing dynamic imports or mocked modules with `vi.mock()` / `vi.doMock()`:
* Ensure strict return type annotations or cast with `typeof import(...)` to satisfy TypeScript 7.0's strict type inference.

## Rolldown & Build Optimization

If migrating to Rolldown (Rust-based Rollup replacement for Vite):
* Rolldown integrates seamlessly with TypeScript 7.0 types.
* Chunks and tree-shaking benefit from clean ESModule outputs with zero ambient module pollution.
