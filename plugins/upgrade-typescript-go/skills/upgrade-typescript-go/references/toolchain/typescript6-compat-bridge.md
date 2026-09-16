# TypeScript 6.0 Compatibility Bridge (`@typescript/typescript6`)

## Overview

When migrating large enterprise codebases to TypeScript 7.0, third-party libraries or internal tooling might still rely on the legacy JavaScript Compiler API. Microsoft publishes `@typescript/typescript6` to provide an in-place compatibility bridge without blocking the rest of the repository from adopting the native Go compiler.

## What `@typescript/typescript6` Provides

1. **Full JavaScript Compiler API**: Exports the exact `typescript@6.0.4` API (`ts.createProgram`, `ts.createSourceFile`, `ts.factory`, `ts.transform`, etc.).
2. **Dedicated Binary `tsc6`**: A standalone binary to invoke the legacy Node.js compiler if a specialized script requires it.

## Installation

```bash
# Using pnpm
pnpm add -D @typescript/typescript6

# Using npm
npm install -D @typescript/typescript6

# Using yarn
yarn add -D @typescript/typescript6
```

## Side-by-Side Coexistence Pattern

In `package.json`:
```json
{
  "scripts": {
    "type-check": "tsc --noEmit",
    "type-check:legacy-ast-audit": "node scripts/custom-ast-checker.mjs"
  },
  "devDependencies": {
    "typescript": "^7.0.0",
    "@typescript/typescript6": "^6.0.4"
  }
}
```

In your custom script (`scripts/custom-ast-checker.mjs`):
```js
// Import the bridge explicitly
import ts from '@typescript/typescript6';

const program = ts.createProgram(['src/index.ts'], {});
const sourceFile = program.getSourceFile('src/index.ts');
console.log('Parsed AST statements:', sourceFile.statements.length);
```

## Deprecation Roadmap

The `@typescript/typescript6` bridge is intended as a transitional tool. Projects should plan to replace custom AST manipulation scripts with modern static analysis tools (e.g. `@typescript-eslint/parser`, Biome, or Oxlint) as ecosystem support matures.
