---
name: develop-typescript
description: Use skill if you are writing or reviewing framework-agnostic TypeScript and need strict typing, tsconfig/lint decisions, safer refactors, or guidance on generics, unions, and typed boundaries.
---

# Develop TypeScript

Language-level steering for TypeScript work. Use this skill to decide how code should be typed, modeled, configured, and reviewed. Keep framework-specific architecture out of this skill.

## Trigger boundary

### Activate when

- Writing, refactoring, or reviewing `.ts`, `.tsx`, `.mts`, `.cts`, or `.d.ts`
- Debugging compiler errors, inference failures, overload problems, or module-resolution mismatches
- Tightening `tsconfig.json`, TypeScript-aware linting, or library type-check/build setup
- Migrating JavaScript or loose TypeScript toward strict mode
- Choosing between unions, overloads, generics, branded types, type guards, schema validation, or newer TS 5.x features

### Do not activate when

- The main task is framework-specific app structure, routing, server actions, or component architecture
- The main task is broad PR review across many languages or files
- The main task is runtime debugging without a TypeScript typing or configuration question
- The task only needs formatting, naming, or style cleanup

## Default workflow

1. **Classify the job first and load the smallest relevant reference set.**
   - Type modeling, inference, advanced types → `references/type-system.md`
   - Unsafe code, brittle review findings, common mistakes → `references/anti-patterns.md`
   - Result/state/validation patterns → `references/patterns.md`
   - Error hierarchy, safe catch, boundary validation → `references/error-handling.md`
   - `tsconfig.json`, strict flags, module settings → `references/strict-config.md`
   - Build, lint, runtime, library packaging → `references/tooling.md`
   - JS to TS or CJS to ESM migration → `references/migration.md`
   - Slow type checking, circular deps, watch performance → `references/performance.md`
   - Type tests and `@ts-expect-error` usage → `references/testing.md`
   - TS 5.x feature selection → `references/modern-features.md`

2. **Establish the safe baseline before changing code.**
   - Treat external input, JSON, DOM data, env vars, and API responses as `unknown`
   - Keep strictness on; do not fix errors by weakening compiler settings first
   - Annotate exported function parameters and return types
   - Let TypeScript infer local variables unless an annotation communicates an invariant
   - Prefer the repo's existing toolchain; when choosing defaults, follow this skill

3. **Choose the simplest type mechanism that preserves the invariant.**
   - Reach for concrete types before generics
   - Reach for built-in utility types before custom mapped/conditional types
   - Reach for discriminated unions before boolean flags or optional-property bags
   - Reach for `satisfies` before whole-object annotations that widen literals
   - Reach for branded types only when structural typing is causing accidental compatibility

4. **Remove unsafe shortcuts before polishing.**
   - Block `any`, unchecked `as`, `@ts-ignore`, bare `!`, floating promises, numeric enums, and legacy `moduleResolution: "node"` in modern bundled apps
   - In review mode, prioritize correctness, boundary safety, async behavior, and config mismatches before style notes

5. **Verify with the actual type system.**
   - If the repo already has TypeScript or lint commands, run them
   - Always separate type checking from transpilation: `tsx`, `tsup`, `esbuild`, and `swc` do not replace `tsc --noEmit`
   - If the first pass still feels uncertain, read one adjacent reference, not the whole folder

## Do this, not that

| Need | Do this | Not that | Route |
|---|---|---|---|
| Unknown boundary data | `unknown` plus a type guard or schema validator | `data as Foo` | `references/patterns.md`, `references/error-handling.md`, `references/anti-patterns.md` |
| Shared object contract or declaration merging | `interface` | Using `interface` for unions, mapped types, or conditional transforms | `references/type-system.md`, `references/anti-patterns.md` |
| Union, mapped, conditional, or template-literal transform | `type` alias | Forcing `interface` to model non-object logic | `references/type-system.md` |
| Finite states or API variants | Discriminated union with an explicit `type` or `status` field | Boolean flags or bags of optional props | `references/patterns.md`, `references/type-system.md` |
| Same primitive, different domain meaning | Branded types plus validated constructors | Plain `string` aliases for IDs or validated values | `references/type-system.md`, `references/patterns.md` |
| Exhaustive keyed object without widening | `satisfies Record<Union, ...>` | Annotating the whole object and losing literal inference | `references/type-system.md`, `references/modern-features.md`, `references/patterns.md` |
| Literal inference inside a generic helper | `const` type parameters | Repeated call-site `as const` or wide generic helpers | `references/type-system.md`, `references/modern-features.md` |
| Inference should come from one argument only | `NoInfer<T>` | Duplicate generics or cleanup casts after the fact | `references/type-system.md`, `references/modern-features.md` |
| Multiple call shapes with distinct outputs | Specific-first overloads or a discriminated union | Boolean switches or overly abstract generic wrappers | `references/anti-patterns.md`, `references/patterns.md` |
| Recoverable internal failure | `Result` or another tagged outcome type | String throws or catch-all exceptions | `references/error-handling.md`, `references/patterns.md` |
| Broken invariant or impossible state | Throw an `Error` subclass | Throwing strings, objects, or silent `undefined` | `references/error-handling.md`, `references/anti-patterns.md` |

## Strictness and tooling defaults

### Compiler baseline

Start from `strict: true`, then prefer these defaults unless the repo has a deliberate reason otherwise:

- `noUncheckedIndexedAccess`
- `noImplicitReturns`
- `noFallthroughCasesInSwitch`
- `noImplicitOverride`
- `forceConsistentCasingInFileNames`
- `verbatimModuleSyntax`
- `isolatedModules`
- `skipLibCheck`

Add these deliberately rather than blindly:

- `exactOptionalPropertyTypes` when “absent” and “present but undefined” mean different things
- `isolatedDeclarations` for libraries that emit `.d.ts`
- `erasableSyntaxOnly` only when targeting strip-types runtimes or erasable-only syntax

### Module and output choices

| Situation | Choose | Notes | Route |
|---|---|---|---|
| Bundled app (Vite, webpack, esbuild, Bun) | `moduleResolution: "bundler"`, `module: "ESNext"` | Often paired with `noEmit: true` | `references/strict-config.md` |
| Node.js ESM app | `moduleResolution: "node16"`, `module: "node16"` | Requires `"type": "module"` in `package.json` | `references/strict-config.md`, `references/migration.md` |
| Published library | `moduleResolution: "bundler"` plus declarations | Prefer `isolatedDeclarations` for fast `.d.ts` workflows | `references/strict-config.md`, `references/tooling.md` |
| Modern transpiler (`esbuild`, `swc`, `tsx`, `tsup`) | `isolatedModules: true` and `verbatimModuleSyntax: true` | Keep `tsc --noEmit` as the separate type-check step | `references/strict-config.md`, `references/tooling.md` |
| Path aliases | Only if bundler/runtime also resolves them | `tsc` alone does not make aliases work at runtime | `references/strict-config.md` |

### Tool defaults

- `tsc` is the source of truth for type errors and diagnostics
- `tsup` is a strong default for simple library bundling
- `tsx` is for execution and dev scripts, not for type checking
- Type-aware ESLint should catch `no-explicit-any`, `no-floating-promises`, `consistent-type-imports`, and exhaustive switch gaps
- If the repo already uses Biome or another formatter/linter stack, extend it instead of layering redundant tooling

## Anti-derail guardrails

- Do not cargo-cult advanced type tricks. If a concrete type or built-in utility solves it, use that.
- Do not add a generic parameter unless it relates multiple values or affects the return type.
- Do not silence errors with `as`, `!`, `@ts-ignore`, or looser compiler flags before asking what invariant is missing.
- Do not use classes for plain data shapes when interfaces plus objects are simpler.
- Do not use `enum`, namespaces, or value-bearing type imports when `as const`, modules, and `import type` are clearer.
- Do not load every reference file; route narrowly and expand only when the task still needs more detail.
- Do not drift into framework rules, API design style, or testing strategy unless there is a TypeScript reason to do so.

## Recovery paths

- **Inference is too wide** → add explicit export return types, use `satisfies`, or switch to `const` type parameters. Start with `references/type-system.md`, then `references/modern-features.md`.
- **Boundary data is untrusted** → replace unchecked `as` with `unknown` plus a type guard or Zod schema. Read `references/patterns.md`, `references/error-handling.md`, and `references/anti-patterns.md`.
- **Strict flags surface too much at once** → tighten in order: `noImplicitAny` → `strictNullChecks` → `strict` → `noUncheckedIndexedAccess` → `exactOptionalPropertyTypes`. Read `references/migration.md` and `references/strict-config.md`.
- **Build works but imports or emitted code behave oddly** → inspect `verbatimModuleSyntax`, `import type`, `isolatedModules`, and `moduleResolution`. Read `references/strict-config.md` and `references/anti-patterns.md`.
- **Type checking is slow** → simplify intersections and conditional chains, group large unions, generate diagnostics or traces, and check for circular deps. Read `references/type-system.md` and `references/performance.md`.
- **Async code feels unsafe** → eliminate floating promises, choose `Result` versus exceptions deliberately, and narrow caught errors explicitly. Read `references/anti-patterns.md`, `references/error-handling.md`, and `references/testing.md`.

## Smallest useful reading sets

- **Make this code strict and safe** → `references/anti-patterns.md` + `references/type-system.md`
- **Choose between union, overload, generic, brand, or `satisfies`** → `references/type-system.md` + `references/patterns.md` + `references/modern-features.md`
- **Set up or audit `tsconfig.json`** → `references/strict-config.md` + `references/tooling.md`
- **Migrate JS or CJS safely** → `references/migration.md` + `references/strict-config.md` + `references/anti-patterns.md`
- **Speed up type checking or builds** → `references/performance.md` + `references/strict-config.md` + `references/tooling.md`
- **Validate boundary data or design error flow** → `references/error-handling.md` + `references/patterns.md`
- **Write or review type tests** → `references/testing.md` + `references/patterns.md`

## Final reminder

This skill should steer decisions, not dump tutorials. Start with one small reading set, make the smallest safe change, verify with the compiler and existing lint/test workflow, then expand only if the task still needs more detail.
