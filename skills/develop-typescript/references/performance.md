# Performance

Optimizing TypeScript compilation speed, type-level performance, and runtime efficiency.

## Measuring Compilation Performance

```bash
# Extended diagnostics — shows time for each phase
tsc --noEmit --extendedDiagnostics --incremental false

# Output includes:
# Files:              1234
# Lines of Library:   45678
# Lines of Definitions: 12345
# Lines of TypeScript:  67890
# Check time:         4.52s    ← type checking
# Emit time:          0.31s
# Total time:         5.83s

# Generate trace for deep analysis
tsc --generateTrace ./trace --incremental false
npx @typescript/analyze-trace ./trace

# Type coverage
npx type-coverage --detail --strict --at-least 95
```

---

## Type-Level Performance

### Prefer interfaces over intersections

```typescript
// SLOW — intersection creates a fresh type object every time
type UserWithPermissions = User & Permissions & Timestamps & Metadata;

// FAST — interface extends is cached
interface UserWithPermissions extends User, Permissions, Timestamps, Metadata {}
```

**Why**: Interfaces are named and cached in the type checker. Intersections create anonymous types that must be recomputed.

### Avoid deep conditional type chains

```typescript
// SLOW — deeply recursive conditional
type DeepGet<T, Path extends string> =
  Path extends `${infer Head}.${infer Tail}`
    ? Head extends keyof T
      ? DeepGet<T[Head], Tail>
      : never
    : Path extends keyof T
      ? T[Path]
      : never;

// FASTER — limit recursion depth
type DeepGet<T, Path extends string, Depth extends unknown[] = []> =
  Depth['length'] extends 10
    ? unknown // bail out at depth 10
    : Path extends `${infer Head}.${infer Tail}`
      ? Head extends keyof T
        ? DeepGet<T[Head], Tail, [...Depth, unknown]>
        : never
      : Path extends keyof T
        ? T[Path]
        : never;
```

### Break large unions into groups

```typescript
// SLOW — TypeScript checks each member sequentially
type Status =
  | 'pending' | 'processing' | 'approved' | 'rejected'
  | 'cancelled' | 'expired' | 'archived' | 'deleted'
  | 'draft' | 'review' | 'published' | 'unpublished'
  // ... 50+ more

// FASTER — grouped discriminated unions
type Status =
  | { phase: 'initial'; value: 'pending' | 'draft' | 'review' }
  | { phase: 'active'; value: 'processing' | 'approved' | 'published' }
  | { phase: 'terminal'; value: 'rejected' | 'cancelled' | 'expired' | 'archived' | 'deleted' };
```

### Use `type` aliases to name intermediate types

```typescript
// SLOW — complex inline type repeated everywhere
function process(
  input: Record<string, { value: string; metadata: Record<string, unknown> }>,
): Record<string, { value: string; metadata: Record<string, unknown> }> {
  // ...
}

// FAST — named once, reused
type DataMap = Record<string, { value: string; metadata: Record<string, unknown> }>;

function process(input: DataMap): DataMap {
  // ...
}
```

---

## Compilation Speed Optimization

### Enable incremental compilation

```json
{
  "compilerOptions": {
    "incremental": true,
    "tsBuildInfoFile": ".tsbuildinfo"
  }
}
```

Subsequent builds only recheck changed files and their dependents. Typically 2-10x faster.

### Use `skipLibCheck`

```json
{
  "compilerOptions": {
    "skipLibCheck": true
  }
}
```

Skips type checking of `.d.ts` files in `node_modules`. Safe for most projects — library types are already checked by their maintainers.

### Use project references for monorepos

```json
// Root tsconfig.json
{
  "files": [],
  "references": [
    { "path": "packages/shared" },
    { "path": "packages/api" },
    { "path": "packages/web" }
  ]
}

// Package tsconfig.json
{
  "compilerOptions": {
    "composite": true,
    "declaration": true,
    "declarationMap": true,
    "outDir": "dist"
  }
}
```

```bash
# Build respects dependency order, only rebuilds changed packages
tsc --build

# Build with verbose output to see what gets rebuilt
tsc --build --verbose

# Force clean rebuild
tsc --build --clean
```

### Use `isolatedModules`

```json
{
  "compilerOptions": {
    "isolatedModules": true
  }
}
```

Ensures each file can be transpiled independently. Required for `esbuild`, `swc`, `tsx`. Also helps catch patterns that break with single-file transpilation:

```typescript
// ERROR with isolatedModules — can't re-export type without 'type'
export { User } from './types'; // Error if User is only a type
export type { User } from './types'; // OK
```

---

## Avoiding Circular Dependencies

Circular imports slow down both the type checker and runtime.

### Detection

```bash
# Using madge
npx madge --circular --extensions ts src/

# Using dpdm
npx dpdm --circular --tree false src/index.ts
```

### Common fix patterns

```typescript
// BAD — circular: user.ts imports order.ts, order.ts imports user.ts

// user.ts
import { Order } from './order';
interface User {
  orders: Order[];
}

// order.ts
import { User } from './user';
interface Order {
  buyer: User;
}

// GOOD — extract shared types to a third file

// types.ts (shared)
interface User {
  id: string;
  name: string;
}

interface Order {
  id: string;
  buyerId: string;
}

interface UserWithOrders extends User {
  orders: Order[];
}

interface OrderWithBuyer extends Order {
  buyer: User;
}
```

### Architectural approach

```
Dependency flow (one direction only):
  types/ ← shared interfaces (no imports from other layers)
  utils/ ← pure functions (imports types only)
  services/ ← business logic (imports types, utils)
  routes/ ← entry points (imports services, types)
```

---

## Memory Optimization

### For large projects exceeding default heap

```bash
# Increase Node.js heap size
NODE_OPTIONS='--max-old-space-size=8192' tsc --noEmit

# Or in package.json
{
  "scripts": {
    "typecheck": "NODE_OPTIONS='--max-old-space-size=8192' tsc --noEmit"
  }
}
```

### Reduce files processed

```json
{
  "include": ["src"],
  "exclude": [
    "node_modules",
    "dist",
    "**/*.test.ts",
    "**/*.spec.ts",
    "**/__tests__/**"
  ]
}
```

### Separate test tsconfig

```json
// tsconfig.test.json — only for test files
{
  "extends": "./tsconfig.json",
  "include": ["src/**/*.test.ts", "src/**/*.spec.ts", "test/**/*.ts"],
  "compilerOptions": {
    "noEmit": true
  }
}
```

---

## Bundle Size Optimization

### Use `import type` consistently

```typescript
// BAD — bundler may include the module even though only types are used
import { User, UserService } from './user';

// GOOD — types stripped at compile time, only values remain
import type { User } from './user';
import { UserService } from './user';

// BEST — inline type imports
import { UserService, type User } from './user';
```

### Avoid barrel exports in large codebases

```typescript
// BAD — imports everything from the barrel
import { oneFunction } from './utils'; // Loads all of utils/index.ts

// GOOD — import directly
import { oneFunction } from './utils/string-helpers';
```

### Tree-shaking friendly patterns

```typescript
// BAD — class with static methods (can't tree-shake individual methods)
class MathUtils {
  static add(a: number, b: number) { return a + b; }
  static multiply(a: number, b: number) { return a * b; }
}

// GOOD — named exports (bundler can tree-shake unused functions)
export function add(a: number, b: number) { return a + b; }
export function multiply(a: number, b: number) { return a * b; }
```

### Use `as const` for enum-like values

```typescript
// BAD — enum generates runtime code, can't be tree-shaken
enum Direction { Up, Down, Left, Right }

// GOOD — const object is inlined, tree-shakeable
const Direction = {
  Up: 'up',
  Down: 'down',
  Left: 'left',
  Right: 'right',
} as const;
type Direction = typeof Direction[keyof typeof Direction];
```

---

## Watch Mode Performance

```json
// tsconfig.json — optimize watch mode
{
  "watchOptions": {
    "watchFile": "useFsEvents",
    "watchDirectory": "useFsEvents",
    "fallbackPolling": "dynamicPriorityPolling",
    "excludeDirectories": ["node_modules", "dist"]
  }
}
```

```bash
# Fast watch with incremental
tsc --watch --incremental

# With preserveWatchOutput (don't clear terminal)
tsc --watch --preserveWatchOutput
```

---

## Performance Checklist

```
□ Enable incremental: true
□ Enable skipLibCheck: true
□ Use isolatedModules: true
□ Use project references for monorepos (tsc --build)
□ Check for circular dependencies (madge --circular)
□ Use import type for type-only imports
□ Avoid barrel exports in large codebases
□ Name complex types instead of inlining
□ Prefer interface extends over intersections
□ Limit recursive type depth
□ Exclude test files from main tsconfig
□ Profile with --extendedDiagnostics and --generateTrace
```
