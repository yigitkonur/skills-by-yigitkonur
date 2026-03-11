---
name: develop-typescript
description: Use skill if you are writing, reviewing, or refactoring TypeScript code and need strict types, anti-patterns, or configuration guidance.
---

# Develop TypeScript

Strict, type-safe TypeScript for any codebase — frontend, backend, libraries, CLIs. Covers TypeScript 5.0–5.8, modern tooling, and production patterns.

## Decision tree

```
What do you need?
│
├── Writing or reviewing code
│   ├── Type system guidance ──────────────► references/type-system.md
│   │   (generics, conditionals, mapped types, template literals,
│   │    branded types, recursive types, variance annotations)
│   │
│   ├── Common patterns ───────────────────► references/patterns.md
│   │   (Result type, discriminated unions, builder pattern, const
│   │    assertions, function overloads, module augmentation,
│   │    state machines, type-safe event emitter, pipe/compose)
│   │
│   ├── Error handling ────────────────────► references/error-handling.md
│   │   (Result<T,E>, custom error hierarchy, Zod validation,
│   │    exhaustive error handling, error boundaries, safe catch)
│   │
│   ├── Anti-patterns to avoid ────────────► references/anti-patterns.md
│   │   (any usage, unsafe assertions, numeric enums, mutation,
│   │    module resolution mistakes, generic misuse, barrel exports,
│   │    circular deps, unsafe narrowing, floating promises)
│   │
│   └── Testing types & code ──────────────► references/testing.md
│       (expect-type, @ts-expect-error tests, vitest type testing,
│        mock typing, dependency injection, snapshot testing)
│
├── Setting up or configuring a project
│   ├── tsconfig.json setup ───────────────► references/strict-config.md
│   │   (strict flags, module resolution, Node/browser/library
│   │    templates, project references, path aliases, watch options,
│   │    isolatedDeclarations, verbatimModuleSyntax, erasableSyntaxOnly)
│   │
│   ├── Build tools & linting ─────────────► references/tooling.md
│   │   (tsc, tsup, tsx, esbuild comparison, ESLint flat config
│   │    with typescript-eslint v8, Biome, Prettier, monorepo
│   │    setup with Turborepo, pre-commit hooks)
│   │
│   └── Performance optimization ──────────► references/performance.md
│       (type-level perf, incremental builds, circular deps,
│        bundle size, tree-shaking, watch mode, memory tuning)
│
├── Migrating or upgrading
│   ├── JS → TS migration ────────────────► references/migration.md
│   │   (step-by-step guide, gradual strictness, any→unknown,
│   │    CJS→ESM migration, declaration files for untyped packages)
│   │
│   └── Using new TS features ─────────────► references/modern-features.md
│       (satisfies, const type params, decorators, NoInfer<T>,
│        using/Disposable, inferred predicates, import attributes,
│        isolatedDeclarations, variance annotations, regex checking)
│
└── Quick answers
    ├── type vs interface? ────────────────► Core rules below
    ├── Error handling strategy? ──────────► Core rules below
    └── When to use generics? ────────────► Core rules below
```

## When to activate

- Writing or modifying `.ts` or `.tsx` files
- Reviewing TypeScript code for quality
- Refactoring JavaScript to TypeScript
- Debugging type errors or inference failures
- Setting up or auditing `tsconfig.json`
- Configuring build tools, linting, or formatting
- Publishing a TypeScript library to npm
- Optimizing type-checking or build performance

## Core rules

### NEVER

- Use `any` — use `unknown` and narrow with type guards
- Use `as` type assertions without runtime validation
- Use `@ts-ignore` — use `@ts-expect-error` with a reason comment
- Use numeric enums — use `as const` objects or string unions
- Mutate function arguments — return new objects/arrays
- Throw non-Error objects — always `throw new Error()` or a custom error class
- Skip `strictNullChecks` — handle `null`/`undefined` explicitly
- Use barrel exports (`export *`) in performance-sensitive code
- Import types as values — use `import type` for type-only imports
- Use `!` non-null assertion without a runtime check preceding it

### ALWAYS

- Enable `"strict": true` in `tsconfig.json`
- Annotate function parameters and return types for exports
- Let TypeScript infer local variables — don't over-annotate
- Use discriminated unions with a `type` or `kind` field for state
- Use `readonly` for data that should not be mutated
- Use `as const` for literal objects and arrays
- Prefer `interface` for object shapes that may be extended; `type` for unions, intersections, utilities
- Handle errors with typed catch blocks — check `instanceof Error`
- Use `Promise.all` for independent async operations
- Write exhaustive `switch` statements with `never` default
- Use `satisfies` to validate expressions without widening types
- Use `import type` or inline `type` for type-only imports
- Enable `verbatimModuleSyntax` and `isolatedModules`

## Quick reference

### `type` vs `interface`

```
Need union, intersection, or utility?   → type
Need declaration merging or extends?    → interface
Data shape for objects?                 → interface (default)
Mapped type or conditional type?        → type
Everything else?                        → type
```

### Error handling strategy

```
External input (API, user, file)?       → Validate with Zod schema
Internal function failure?              → Return Result<T, E> discriminated union
Unrecoverable state?                    → throw new CustomError()
Multiple failure modes in one call?     → Return AsyncResult<T, AppError>
Must handle all error types?            → Discriminated union + never default
```

### When to use generics

```
Used with multiple types?               → Generic with constraints
Used with one type?                     → Concrete type (don't over-abstract)
Generic parameter unused in body?       → Remove it — it's unnecessary
Need literal type inference?            → const type parameter
Inference should not come from an arg?  → NoInfer<T>
```

### Module resolution

```
Using Vite, webpack, esbuild, Bun?      → "moduleResolution": "bundler"
Node.js ESM application?               → "moduleResolution": "node16"
Publishing a library?                   → "moduleResolution": "bundler"
Uncertain?                              → "bundler" (safest default)
```

## Key patterns

### Result type for error handling

```typescript
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

function parseConfig(raw: string): Result<Config> {
  try {
    return { success: true, data: JSON.parse(raw) };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err : new Error(String(err)) };
  }
}

const result = parseConfig(input);
if (result.success) {
  console.log(result.data); // Config
} else {
  console.error(result.error); // Error
}
```

### Discriminated union for state

```typescript
type LoadingState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function render(state: LoadingState<User>): string {
  switch (state.status) {
    case 'idle': return 'Click to load';
    case 'loading': return 'Loading...';
    case 'success': return state.data.name;
    case 'error': return state.error.message;
  }
}
```

### Const object instead of enum

```typescript
const Status = {
  Pending: 'pending',
  Active: 'active',
  Done: 'done',
} as const;

type Status = typeof Status[keyof typeof Status];
// 'pending' | 'active' | 'done'
```

### Branded types for nominal safety

```typescript
type UserId = string & { readonly __brand: 'UserId' };
type OrderId = string & { readonly __brand: 'OrderId' };

function UserId(raw: string): UserId { return raw as UserId; }

function getUser(id: UserId): User { /* ... */ }
getUser(UserId('usr_123')); // OK
// getUser('raw-string');    // Error — not a UserId
```

### Zod schema for boundary validation

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(['admin', 'user']),
});
type User = z.infer<typeof UserSchema>;

function handleApiResponse(data: unknown): User {
  return UserSchema.parse(data);
}
```

## Modern TypeScript features (5.0+)

| Feature | Version | One-liner |
|---------|---------|-----------|
| `satisfies` | 5.0 | Validate type match without widening inference |
| `const` type params | 5.0 | Infer literal types in generic calls |
| TC39 Decorators | 5.0 | Standard `@decorator` syntax (not legacy) |
| Variance (`in`/`out`) | 5.0 | Explicit covariance/contravariance on type params |
| `verbatimModuleSyntax` | 5.0 | What you write is what gets emitted |
| `using` declarations | 5.2 | Auto resource cleanup via `Symbol.dispose` |
| Import attributes | 5.3 | `import x from 'y' with { type: 'json' }` |
| `NoInfer<T>` | 5.4 | Block inference from specific generic arguments |
| Inferred predicates | 5.5 | Auto type guards for `.filter()` callbacks |
| `isolatedDeclarations` | 5.5 | Fast `.d.ts` generation without full type check |
| Regex checking | 5.5 | Compile-time regex syntax validation |
| `erasableSyntaxOnly` | 5.8 | Only allow type-erasable syntax |

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| `any` everywhere from JS migration | Use `unknown` + type guards; add Zod at boundaries |
| `as User` without runtime check | Write a type guard or use Zod `parse()` |
| `moduleResolution: "node"` in Vite app | Use `"bundler"` for bundled apps |
| Missing `"type": "module"` with node16 | Add to package.json for ESM |
| `Object.keys()` returns `string[]` | Use typed helper or `Object.entries()` |
| `{}` used as "empty object" type | Use `Record<string, unknown>` instead |
| Non-null assertion `!` without proof | Add runtime check before the assertion |
| Floating promises (no `await`) | Always `await` or use `void` for fire-and-forget |
| Barrel exports slow builds | Import directly from source modules |
| Circular imports cause `undefined` | Extract shared types to a separate module |
| `interface` for unions/utilities | Use `type` — `interface` can't do unions |
| Over-annotating inferred types | Let TS infer locals; annotate exports and params |
| `target: "ES5"` in modern project | Use `"ES2022"` — matches Node 18+ and modern browsers |
| Missing `skipLibCheck: true` | Enable it — speeds up compilation significantly |
| Catch variable typed as `any` | Enable `strict: true` — defaults catch to `unknown` |

## Minimal reading sets

### "I need to write type-safe TypeScript code"

- `references/anti-patterns.md`
- `references/type-system.md`
- `references/patterns.md`

### "I need to handle errors properly"

- `references/error-handling.md`
- `references/patterns.md` (Result type, custom errors)

### "I need to set up a new TypeScript project"

- `references/strict-config.md`
- `references/tooling.md`

### "I need to set up a new library for npm publishing"

- `references/strict-config.md` (library template)
- `references/tooling.md` (tsup config, package.json exports)
- `references/performance.md` (bundle size, tree-shaking)

### "I need to migrate JavaScript to TypeScript"

- `references/migration.md`
- `references/strict-config.md` (migration flags)
- `references/anti-patterns.md` (common mistakes during migration)

### "I need to use modern TypeScript features"

- `references/modern-features.md`
- `references/type-system.md` (variance, satisfies, const params)

### "I need to optimize TypeScript performance"

- `references/performance.md`
- `references/strict-config.md` (incremental, project references)
- `references/tooling.md` (build tool comparison)

### "I need to test TypeScript types"

- `references/testing.md`
- `references/patterns.md` (type-only testing section)

### "I need to set up linting and formatting"

- `references/tooling.md` (ESLint flat config, Biome, Prettier)

### "I need to set up a monorepo"

- `references/strict-config.md` (project references, base config)
- `references/tooling.md` (Turborepo, tsc --build)
- `references/performance.md` (incremental builds, circular deps)

## Final reminder

This skill is split into focused reference files by topic. Do not load everything at once. Start with the smallest relevant reading set above, then expand into neighboring references only when the task requires them. Every reference file is explicitly routed from the decision tree.
