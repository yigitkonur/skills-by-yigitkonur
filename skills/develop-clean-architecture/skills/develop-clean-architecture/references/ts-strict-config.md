---
title: Enable All Strict TypeScript Compiler Options
impact: CRITICAL
impactDescription: catches 30-50% of common runtime bugs at compile time, enforces architectural boundaries at syntax level
tags: ts, config, strict, compiler, erasable-syntax
---

## Enable All Strict TypeScript Compiler Options

Every Clean Architecture principle depends on a fully strict TypeScript configuration. This is not optional. Beyond `strict: true`, additional flags enforce architectural boundaries, enable native TS execution, and close gaps in null safety.

**Incorrect (loose config allows runtime surprises):**

```typescript
// tsconfig.json — no strict options
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "outDir": "dist"
  }
}

// domain/entities/Product.ts — compiles cleanly, crashes at runtime
function getProductName(products: Record<string, Product>, id: string) {
  const product = products[id]
  return product.name.toUpperCase()  // Runtime crash: product is undefined
}

function calculateDiscount(price, percentage) {
  return price * percentage / 100  // price could be a string — NaN result
}
```

**Correct (full strict configuration with beyond-strict flags):**

```json
{
  "compilerOptions": {
    // Core strict bundle (enables 8 sub-flags)
    "strict": true,

    // Beyond strict (commonly missed)
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true,
    "forceConsistentCasingInFileNames": true,

    // Module resolution
    "moduleResolution": "bundler",
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,

    // Output
    "target": "ES2022",
    "lib": ["ES2022"]
  }
}
```

**The `strict` sub-flag matrix:**

| Flag (enabled by `strict: true`) | What it catches | Architecture Layer |
|---|---|---|
| `noImplicitAny` | Untyped variables/params | All |
| `strictNullChecks` | `null`/`undefined` misuse | Domain, Use Cases |
| `strictFunctionTypes` | Contravariant param checks | Ports/Adapters |
| `strictBindCallApply` | `bind`/`call`/`apply` safety | Infrastructure |
| `strictPropertyInitialization` | Uninitialised class props | Domain Entities |
| `noImplicitThis` | Unbound `this` context | Controllers |
| `alwaysStrict` | Emits `"use strict"` | All |
| `useUnknownInCatchVariables` | `catch(e)` -> `e: unknown` | Error boundaries |

**Beyond-strict flags for Clean Architecture:**

| Flag | Why it matters |
|---|---|
| `noUncheckedIndexedAccess` | Forces null guards on array/map access — enforces defensive domain logic |
| `exactOptionalPropertyTypes` | Closes gap between `undefined` and `absent` in DTOs |
| `verbatimModuleSyntax` | Forces `import type` for type-only imports — enforces layer boundaries at syntax level |
| `erasableSyntaxOnly` | Bans enums and namespaces — aligns with Node.js 22+ native TS stripping |

**When NOT to use this pattern:**
- Migrating a large JavaScript codebase — enable options incrementally
- Generated code (protobuf, GraphQL codegen) — exclude via tsconfig paths
- `erasableSyntaxOnly` conflicts with decorator-based DI (tsyringe, InversifyJS)

**Benefits:**
- Null/undefined crashes caught before tests even run
- `verbatimModuleSyntax` makes every import declare its architectural intent
- `erasableSyntaxOnly` enables Node.js 22+ to run TypeScript files directly
- Strict config compounds with branded types and discriminated unions

Reference: [TypeScript tsconfig Reference — Strict Checks](https://www.typescriptlang.org/tsconfig#strict)
