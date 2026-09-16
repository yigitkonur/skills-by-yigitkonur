# Compiler API (Strada) Removal & Migration

## Overview

In TypeScript 7.0 (Project Corsa), the compiler was completely rewritten from JavaScript into native Go. As a direct consequence, the legacy JavaScript-based Compiler API (internal codename "Strada") accessible via `import * as ts from "typescript"` has been removed from the primary compiler package.

The native Go binary does not evaluate JavaScript AST transformers or export the Node.js V8 AST inspection functions.

## Who Is Affected?

Tools and packages that perform AST manipulation, custom transformation, or programmatic type-checking:
- **AST Utilities**: `ts-morph`, `ts-query`, `ts-ast-viewer`
- **Custom Transformers**: `ts-loader` with custom `getCustomTransformers`, `ttypescript`, `ts-patch`
- **Certain ESLint Plugins**: Custom internal ESLint rules directly importing `typescript` to parse AST nodes
- **Code Generators**: Custom OpenAPI or GraphQL type generators that construct AST nodes via `ts.factory.*`

## Who Is NOT Affected?

- Projects that use TypeScript solely via CLI commands (`tsc`, `tsgo`).
- Projects using modern bundlers and transpilers: `Vite`, `Turbopack`, `esbuild`, `SWC`, `Rollup`, `Rolldown`.
- Modern runtime execution runners: `tsx`, `bun`, `deno`.
- Standard `@typescript-eslint` setups (version 8+).

## Remediation Strategies

### Strategy 1: The `@typescript/typescript6` Compatibility Bridge

For tools that strictly require the legacy JavaScript Compiler API, Microsoft provides the `@typescript/typescript6` compatibility package. This package re-exports the full TypeScript 6.0 Strada JS API alongside the `tsc6` binary.

```json
{
  "devDependencies": {
    "typescript": "^7.0.0",
    "@typescript/typescript6": "^6.0.4"
  }
}
```

In your AST manipulation script:
```ts
// Before (Broken in TS 7.0)
import * as ts from 'typescript';

// After (Using compatibility bridge)
import * as ts from '@typescript/typescript6';
```

### Strategy 2: Offload Transpilation to esbuild / SWC

If your project used `ts-loader` or `ttypescript` solely for transpilation and path mapping, replace them with modern native tools:
- Replace `ts-node` with `tsx` (`npm i -D tsx`).
- Replace `ts-loader` with `swc-loader` or `esbuild-loader`.
- Keep `tsc --noEmit` as a dedicated type-checking step.

### Strategy 3: Migrate to Official LSP / AST Tools

For AST analysis and linting, migrate to `@typescript-eslint/parser` v8+ or native linters (`Biome`, `Oxlint`) which interface with the native compiler outputs or independent parsers.
