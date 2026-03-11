# Actual Findings: ky Type Safety Audit

These are real type-safety issues discovered in sindresorhus/ky during the derailment test.
They validate that the skill, despite its friction points, produces real value.

## Critical findings

### 1. `merge.ts` — 5 `any` annotations
- `target: any`, `source: any`, `returnValue: any`, `searchParameters: any`
- Existing TODO: "Make this strongly-typed (no any)"
- Recommendation: Use generics with `Record<string, unknown>` constraint

### 2. Type guards use `as any` for cross-realm checks
- `type-guards.ts` lines 53, 75, 102
- Pattern: `(error as any)?.name === ErrorClass.name`
- Should be: `(error as {name?: string})?.name === ErrorClass.name`

### 3. Zero `satisfies` usage
- `responseTypes` in `constants.ts` — maps response types to MIME types
- `kyOptionKeys` registry — validates known option keys
- Both would benefit from `satisfies` to validate exhaustiveness without widening

### 4. XO disables 6 safety-critical lint rules
- `@typescript-eslint/no-unsafe-argument`
- `@typescript-eslint/no-unsafe-assignment`
- `@typescript-eslint/no-unsafe-return`
- `@typescript-eslint/no-unsafe-call`
- `@typescript-eslint/ban-ts-comment`
- `@typescript-eslint/no-unnecessary-type-assertion`

### 5. Retry function types use `any`
- `Ky.ts` ~line 676/684: `(...arguments_: any) => Promise<any>`
- Should use proper generic signature

### 6. 3x `@ts-expect-error` for outdated Web API types
- Acceptable but should track upstream type fixes
