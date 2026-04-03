# Strict Configuration

TypeScript compiler configuration for maximum type safety.

The first snippet below is the **bundler-app baseline**. Use the Node.js or library baselines later in this file when they match the project better. Strictness is separate from module mode: keep the correct runtime mode, then tighten the safety flags inside that mode.

## Recommended `tsconfig.json`

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "module": "ESNext",
    "target": "ES2022",
    "lib": ["ES2022"]
  }
}
```

## What `strict: true` enables

| Flag | Effect |
|---|---|
| `strictNullChecks` | `null` and `undefined` are distinct types; must be handled explicitly |
| `strictFunctionTypes` | Function parameter types checked contravariantly |
| `strictBindCallApply` | `bind`, `call`, `apply` are type-checked |
| `strictPropertyInitialization` | Class properties must be initialized in constructor |
| `noImplicitAny` | Error on expressions with implied `any` type |
| `noImplicitThis` | Error on `this` with implied `any` type |
| `alwaysStrict` | Emits `"use strict"` in every output file |
| `useUnknownInCatchVariables` | Catch clause variables typed as `unknown` instead of `any` |

## Additional strict flags (not in `strict`)

| Flag | Effect | When to enable |
|---|---|---|
| `noUncheckedIndexedAccess` | Array/object index access returns `T \| undefined` | Always — prevents out-of-bounds access assumptions |
| `exactOptionalPropertyTypes` | `x?: string` cannot be set to `undefined` explicitly | When you need semantic difference between "absent" and "undefined" |
| `noImplicitReturns` | Error if a function code path doesn't return | Always |
| `noFallthroughCasesInSwitch` | Error on switch case fallthrough | Always |
| `noImplicitOverride` | Require `override` keyword for overridden methods | Always — catches rename bugs |

## Module Resolution

### For bundler-based projects (Vite, webpack, esbuild, Bun)

```json
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "module": "ESNext",
    "allowImportingTsExtensions": true,
    "noEmit": true
  }
}
```

### For Node.js projects (ESM)

```json
{
  "compilerOptions": {
    "moduleResolution": "node16",
    "module": "node16",
    "target": "ES2022"
  }
}
```

### Baseline selection rule

Pick the baseline by runtime, then compare strictness flags within that family:

| Project shape | Baseline |
|---|---|
| Vite / webpack / esbuild / Bun app | `moduleResolution: "bundler"` |
| Node.js ESM app or package | `moduleResolution: "node16"` or `"nodenext"` |
| Published library | Library baseline in this file |

Do not change module mode just because another example in this file is stricter. Change it only when the runtime/build target changes too.
In monorepos or solution-style repos, start with the package tsconfig that owns the edited files and then follow its `extends` chain. Do not compare only the root helper config.

### For library publishing

```json
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "module": "ESNext",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist"
  }
}
```

## Path Aliases

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/types/*": ["src/types/*"]
    }
  }
}
```

**Note**: path aliases require bundler or runtime support (e.g., `tsconfig-paths`). They are not resolved by `tsc` at runtime.

## Project References (Monorepos)

```json
// tsconfig.json (root)
{
  "references": [
    { "path": "packages/shared" },
    { "path": "packages/server" },
    { "path": "packages/client" }
  ]
}

// packages/shared/tsconfig.json
{
  "compilerOptions": {
    "composite": true,
    "declaration": true,
    "outDir": "dist"
  }
}
```

Build with: `tsc --build` (incremental, respects dependency order).

## Performance Optimization

### Compilation speed

```json
{
  "compilerOptions": {
    "incremental": true,
    "skipLibCheck": true,
    "composite": true
  }
}
```

### Memory issues

```bash
# Increase heap for large projects
node --max-old-space-size=8192 ./node_modules/typescript/lib/tsc.js --noEmit
```

### Diagnostics

```bash
# Extended diagnostics (check time, memory, file counts)
tsc --extendedDiagnostics --incremental false

# Type trace (find slow types)
tsc --generateTrace trace --incremental false
npx @typescript/analyze-trace trace

# Type checking only (no output)
tsc --noEmit

# Watch with performance
tsc --watch --incremental
```

## Common Migration Flags

When migrating from JavaScript or relaxed TypeScript:

```json
{
  "compilerOptions": {
    "allowJs": true,
    "checkJs": false,
    "strict": false,
    "noImplicitAny": false
  }
}
```

Tighten incrementally:
1. Enable `noImplicitAny` first — forces parameter annotations
2. Enable `strictNullChecks` — catches null/undefined bugs
3. Enable `strict` — turns on everything
4. Enable `noUncheckedIndexedAccess` — catches array access bugs
5. Enable `exactOptionalPropertyTypes` — strictest optional handling

Each step will surface type errors. Fix them before enabling the next flag.

## ESLint Integration

Key TypeScript-specific ESLint rules:

```json
{
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-non-null-assertion": "warn",
    "@typescript-eslint/prefer-nullish-coalescing": "error",
    "@typescript-eslint/prefer-optional-chain": "error",
    "@typescript-eslint/consistent-type-imports": ["error", { "prefer": "type-imports" }],
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/switch-exhaustiveness-check": "error"
  }
}
```

## Declaration Files

### When writing `.d.ts` files

```typescript
// global.d.ts — augment global types
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      DATABASE_URL: string;
      API_KEY: string;
      NODE_ENV: 'development' | 'production' | 'test';
    }
  }
}

export {}; // Make this a module (required for declare global)
```

### For untyped packages

```typescript
// types/untyped-lib.d.ts
declare module 'untyped-lib' {
  export function doSomething(input: string): Promise<string>;
  export interface Config {
    timeout: number;
    retries: number;
  }
}
```

**Prefer**: install `@types/package-name` from DefinitelyTyped when available. Write custom declarations only when no `@types` package exists.

---

## `verbatimModuleSyntax` (5.0+)

Simple rule: what you write is what gets emitted.

```json
{
  "compilerOptions": {
    "verbatimModuleSyntax": true
  }
}
```

### Effect on imports

```typescript
// Type-only import — stripped from output
import type { User } from './types';

// Value import — preserved in output
import { createUser } from './user';

// Mixed — types stripped, values preserved
import { createUser, type User } from './user';

// ERROR — using a type import as a value
import { User } from './types'; // Error if User is only a type
```

Replaces the older `importsNotUsedAsValues` and `preserveValueImports` options.

---

## `isolatedDeclarations` (5.5+)

Requires explicit return types on exported functions so tools other than `tsc` can generate `.d.ts` files.

```json
{
  "compilerOptions": {
    "isolatedDeclarations": true,
    "declaration": true
  }
}
```

```typescript
// ERROR — return type must be explicit for exports
export function add(a: number, b: number) {
  return a + b;
}

// OK — explicit return type
export function add(a: number, b: number): number {
  return a + b;
}

// OK — non-exported functions can use inference
function internal(x: number) {
  return x * 2;
}
```

**Why**: Enables `tsup`, `oxc`, and `swc` to generate declarations without running the full type checker. Useful for large monorepos where type-checking is slow.

For exported TSX components, use the repo's existing return-type convention. If the codebase has no convention yet, this is the most version-stable explicit form:

```tsx
import type { ReactElement } from 'react';

export function Toolbar(): ReactElement {
  return <div>...</div>;
}
```

This avoids depending on whether the global `JSX` namespace is available in the current React/TypeScript setup.

---

## `isolatedModules`

Ensures each file can be transpiled independently by tools like `esbuild` or `swc`.

```json
{
  "compilerOptions": {
    "isolatedModules": true
  }
}
```

### What it prohibits

```typescript
// ERROR — re-exporting types without 'type'
export { User } from './types'; // Error if User is only a type
export type { User } from './types'; // OK

// ERROR — const enum (requires cross-file analysis)
const enum Direction { Up, Down, Left, Right }
// Use regular enum or as const object instead

// ERROR — ambient module declarations with value exports
declare module 'foo' {
  export const bar: string; // Error in isolated modules
}
```

**Why**: Required for all modern transpilers (esbuild, swc, tsx, Vite). Always enable.

---

## `erasableSyntaxOnly` (5.8+)

Restricts TypeScript to syntax that can be erased (removed) to produce valid JavaScript, without requiring any transformation or code generation.

```json
{
  "compilerOptions": {
    "erasableSyntaxOnly": true
  }
}
```

### What it prohibits

```typescript
// ERROR — enums generate runtime code
enum Status { Active, Inactive }

// ERROR — namespaces generate runtime code
namespace Utils {
  export function helper() {}
}

// ERROR — parameter properties generate constructor assignments
class User {
  constructor(public name: string) {} // Error
}

// OK — these are all erased cleanly
type Status = 'active' | 'inactive';
interface User { name: string; }
import type { Config } from './config';
```

**Why**: Aligns with the TC39 Type Annotations proposal. If you plan to use Node.js `--experimental-strip-types` or Deno's built-in TypeScript support, this flag ensures compatibility.

---

## Watch Options

```json
{
  "watchOptions": {
    "watchFile": "useFsEvents",
    "watchDirectory": "useFsEvents",
    "fallbackPolling": "dynamicPriorityPolling",
    "excludeDirectories": ["node_modules", "dist", ".git"]
  }
}
```

| Option | Recommended | Why |
|--------|-------------|-----|
| `watchFile` | `useFsEvents` | Native file events, lower CPU |
| `watchDirectory` | `useFsEvents` | Native directory events |
| `fallbackPolling` | `dynamicPriorityPolling` | Adaptive frequency for non-native FS |
| `excludeDirectories` | `["node_modules", "dist"]` | Reduces watched files |

```bash
# Watch with incremental (fastest recompilation)
tsc --watch --incremental

# Watch without clearing terminal
tsc --watch --preserveWatchOutput
```

---

## Complete tsconfig Templates

### Node.js 20+ ESM Application

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "node16",
    "moduleResolution": "node16",
    "lib": ["ES2022"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "outDir": "dist",
    "rootDir": "src",
    "sourceMap": true,
    "declaration": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

Requires `"type": "module"` in package.json.

### Browser Application (Vite, Next.js)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "jsx": "react-jsx",
    "noEmit": true
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
```

### Library Publishing

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "isolatedDeclarations": true,
    "skipLibCheck": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist"
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### Monorepo Base Config

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "declaration": true,
    "declarationMap": true,
    "composite": true,
    "incremental": true,
    "sourceMap": true
  }
}
```


---

## Common tsconfig.json mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| `moduleResolution: "node"` with ESM | Import extensions not required, runtime crashes | Use `"node16"` or `"bundler"` |
| `target: "ES5"` for modern runtimes | Unnecessary downlevel transforms, larger bundles | Use `"ES2022"` or later |
| Missing `"type": "module"` in package.json | `.ts` files treated as CJS despite ESM syntax | Add to package.json |
| `paths` aliases without bundler support | TypeScript resolves, runtime crashes | Configure bundler/loader aliases to match |
| `strict: false` with individual strict flags | Confusing — some strict checks on, `strict` says off | Set `strict: true`, disable specific flags |
| Assuming `skipLibCheck: true` is enough while debugging dependency types | Third-party declaration regressions stay hidden | Keep it on for normal builds, but temporarily turn it off when investigating `@types/*` conflicts or library publish issues |

### Legacy `moduleResolution` — only `"node"` is legacy

Only bare `"node"` is legacy. `"node16"` and `"nodenext"` are modern and correct for Node.js ESM. `"bundler"` is correct for bundled applications. Do NOT flag `"node16"` as legacy.

```json
// LEGACY — avoid
{ "moduleResolution": "node" }

// MODERN — correct for different contexts
{ "moduleResolution": "node16" }    // Node.js ESM packages
{ "moduleResolution": "nodenext" }  // Node.js, tracks latest
{ "moduleResolution": "bundler" }   // Bundled applications (Vite, webpack, esbuild)
```

---

## Flag availability by TypeScript version

| Flag | Introduced | Notes |
|---|---|---|
| `strict` | 2.3 | Umbrella for all strict checks |
| `noUncheckedIndexedAccess` | 4.1 | Adds `undefined` to index signatures |
| `exactOptionalPropertyTypes` | 4.4 | Distinguishes `undefined` from missing |
| `moduleResolution: "node16"` | 4.7 | ESM-aware resolution for Node.js |
| `moduleResolution: "bundler"` | 5.0 | For bundled applications |
| `verbatimModuleSyntax` | 5.0 | Replaces `importsNotUsedAsValues` + `preserveValueImports` |
| `allowImportingTsExtensions` | 5.0 | Allows `.ts` in import specifiers |
| `rewriteRelativeImportExtensions` | 5.7 | Rewrites `.ts` to `.js` in output |
| `erasableSyntaxOnly` | 5.8 | Blocks enums, namespaces, parameter properties |

---

## When lint rules conflict with strict TypeScript

Projects may have ESLint/xo/Biome configs that disable safety rules the skill recommends. Resolution:

1. **Do NOT unilaterally re-enable rules** — the project may have valid reasons for disabling them
2. **Note the conflict** in your findings: "The project disables `@typescript-eslint/no-unsafe-assignment` — consider re-enabling"
3. **Classify as recommendation**, not blocking issue
4. **Explain the trade-off** — what the rule catches vs why it might be disabled (e.g., gradual migration from `any`)

The skill blocklist (no `any`, no `@ts-ignore`) takes precedence over lint config for *new* code. For *existing* code under review, follow the project lint config and flag conflicts as informational.
