---
name: develop-typescript
description: Use skill if you are writing, reviewing, or refactoring TypeScript code and need strict types, anti-patterns, or configuration guidance.
---

# Develop TypeScript

Strict, type-safe TypeScript for any codebase — frontend, backend, libraries, CLIs.

## When to activate

- Writing or modifying `.ts` or `.tsx` files
- Reviewing TypeScript code for quality
- Refactoring JavaScript to TypeScript
- Debugging type errors or inference failures
- Setting up or auditing `tsconfig.json`

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

### ALWAYS

- Enable `"strict": true` in `tsconfig.json`
- Annotate function parameters and return types
- Let TypeScript infer local variables — don't over-annotate
- Use discriminated unions with a `type` or `kind` field for state
- Use `readonly` for data that should not be mutated
- Use `as const` for literal objects and arrays
- Prefer `interface` for object shapes that may be extended; `type` for unions, intersections, utilities
- Handle errors with typed catch blocks — check `instanceof Error`
- Use `Promise.all` for independent async operations
- Write exhaustive `switch` statements with `never` default

## Decision tree

### Choosing between `type` and `interface`

```
Need union, intersection, or utility?  → type
Need declaration merging or extends?   → interface
Data shape for objects?                → interface (default)
Everything else?                       → type
```

### Choosing error handling strategy

```
External input (API, user, file)?  → Validate at boundary with type guard or schema (Zod)
Internal function failure?         → Return Result<T, E> discriminated union
Unrecoverable state?               → throw new CustomError()
```

### Choosing between generics and concrete types

```
Used with multiple types?          → Generic with constraints
Used with one type?                → Concrete type (don't over-abstract)
Generic parameter unused in body?  → Remove it — it's unnecessary
```

## Reference routing

Load only the files relevant to the current task.

| File | When to read |
|---|---|
| `references/anti-patterns.md` | When writing new code, reviewing code, or refactoring. Contains the full catalog of mistakes with fixes. |
| `references/type-system.md` | When working with advanced types: generics, conditionals, mapped types, template literals, branded types, recursive types. |
| `references/patterns.md` | When implementing common TypeScript patterns: Result types, type guards, discriminated unions, builder pattern, const assertions. |
| `references/strict-config.md` | When setting up or auditing `tsconfig.json`, diagnosing type performance, or configuring module resolution. |
