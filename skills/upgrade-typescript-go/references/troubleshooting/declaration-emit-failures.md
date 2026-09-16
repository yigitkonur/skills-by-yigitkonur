# Declaration Emit Failures & Isolated Declarations

## Overview

When building npm libraries or composite monorepo packages, TypeScript must emit type declaration files (`.d.ts`).

In TypeScript 7.0, declaration emit uses the native engine, enforcing stricter validation to prevent leaking private types or un-exported inferred shapes.

## Common Declaration Emit Errors

### 1. TS4023 / TS4058: Exported variable has or is using name from external module but cannot be named

**Cause**: An exported function or constant returns an inferred type that depends on a non-exported or private type.

```ts
// ❌ Problematic
interface InternalOptions {
  apiKey: string;
}
// Return type is inferred as InternalOptions, which is not exported
export function createClient(opt: InternalOptions) {
  return { opt };
}

// ✅ Solution: Explicitly export the underlying interface or provide explicit return type
export interface InternalOptions {
  apiKey: string;
}
export interface ClientInstance {
  opt: InternalOptions;
}
export function createClient(opt: InternalOptions): ClientInstance {
  return { opt };
}
```

### 2. Isolated Declarations (`isolatedDeclarations: true`)

TypeScript 7.0 supports the `isolatedDeclarations` mode, which allows fast, parallel `.d.ts` generation by requiring explicit return types on all exported module boundaries.

If enabled in `tsconfig.json`:
```json
{
  "compilerOptions": {
    "isolatedDeclarations": true
  }
}
```
* **Rule**: Every exported function, method, and variable must have an explicit type annotation.

## Verifying Declaration Emit

Always test declaration emit explicitly for library packages:

```bash
# Verify declaration generation without emitting JS
tsc --declaration --emitDeclarationOnly --noEmit false --outDir ./dist/types
```
