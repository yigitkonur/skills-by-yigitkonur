# Bundlers, Transpilers & Script Runners

## Overview

Modern web projects separate **type checking** from **code transpilation**. While `tsc` (or `tsgo`) performs authoritative type checking, high-throughput bundlers and transpilers strip types and emit runnable JavaScript.

## Compatibility by Tool

### 1. `tsx` (TypeScript Execute)
- **Status**:  **Recommended**
- `tsx` uses `esbuild` under the hood to execute `.ts` and `.mts` files instantaneously without invoking the TypeScript compiler.
- It is completely unaffected by TypeScript 7.0 changes.
- **Usage**: Replace any remaining `ts-node` references in `package.json` scripts with `tsx`.

```bash
npm install -D tsx
# Run scripts:
npx tsx scripts/my-script.mts
```

### 2. `esbuild`
- **Status**:  **Native & Compatible**
- Strips TypeScript annotations without type validation.
- Ensure `tsconfig.json` contains `"useDefineForClassFields": true` if targeting modern ESNext class fields.

### 3. `SWC` / Next.js Compiler
- **Status**:  **Native & Compatible**
- Handles all JSX/TSX transforms in Next.js.
- Fully compatible with TypeScript 7.0 type syntax.

### 4. `ts-node`
- **Status**: ⚠️ **Legacy / Deprecated**
- `ts-node` relies on the legacy Node.js compiler API.
- **Action**: Migrate to `tsx` or run scripts natively under `bun` / `node --loader` / `node --experimental-strip-types`.
