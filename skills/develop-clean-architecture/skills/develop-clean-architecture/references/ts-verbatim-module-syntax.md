---
title: Use verbatimModuleSyntax to Enforce Layer Boundaries at Import Level
impact: HIGH
impactDescription: forces import type for cross-layer type imports, prevents accidental infrastructure leaks
tags: ts, imports, boundaries, verbatim-module-syntax
---

## Use verbatimModuleSyntax to Enforce Layer Boundaries at Import Level

Setting `verbatimModuleSyntax: true` in tsconfig forces developers to explicitly mark type-only imports with `import type`. This makes architectural intent visible at the import level and prevents accidental runtime dependencies on outer layers.

**Incorrect (without verbatimModuleSyntax — intent is ambiguous):**

```typescript
// tsconfig.json
{ "compilerOptions": { /* no verbatimModuleSyntax */ } }

// application/usecases/PlaceOrder.ts
import { Order } from '../../domain/entities/Order';           // Value or type? Unclear
import { OrderRepository } from '../../application/ports/OrderRepository';  // Value or type?
import { PrismaOrderRepository } from '../../infrastructure/persistence/PrismaOrderRepo';
// No error — use case accidentally imports concrete infrastructure class
```

**Correct (verbatimModuleSyntax forces explicit intent):**

```typescript
// tsconfig.json
{
  "compilerOptions": {
    "verbatimModuleSyntax": true
  }
}

// application/usecases/PlaceOrder.ts
import type { Order } from '../../domain/entities/Order';              // Type only — zero runtime cost
import type { OrderRepository } from '../../application/ports/OrderRepository'; // Port interface
import { PlaceOrderCommand } from './PlaceOrder.command';              // Value — command class

// Accidentally importing concrete infra class as type-only:
// import type { PrismaOrderRepository } from '../../infrastructure/...';
// This forces you to ask: "Why does my use case need to know about Prisma?"
// If you try to USE it as a value, TS will error because it's type-only
```

**Combined with erasableSyntaxOnly (Node.js 22+ native TS stripping):**

```json
{
  "compilerOptions": {
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true
  }
}
```

`erasableSyntaxOnly` bans enums and namespaces — constructs that require non-trivial compilation. Combined with `verbatimModuleSyntax`, this enables Node.js 22+ to run TypeScript files directly without a build step while maintaining strict import discipline.

**When NOT to use this pattern:**
- Migrating a large codebase — enable incrementally with auto-fixers
- Generated code (protobuf, GraphQL codegen) that doesn't follow the convention

**Benefits:**
- Every import statement declares its architectural intent (type vs. value)
- Prevents accidental runtime dependencies from inner layers to outer layers
- Enables native TypeScript execution in Node.js 22+ with `erasableSyntaxOnly`
- LSP type-only imports resolve faster (skips value resolution)

Reference: [TypeScript 5.0 — verbatimModuleSyntax](https://www.typescriptlang.org/tsconfig#verbatimModuleSyntax) | [Node.js 22 — Type Stripping](https://nodejs.org/en/blog/release/v22.6.0)
