---
title: Structure TypeScript Modules with Path Aliases and Enforced Layer Boundaries
impact: MEDIUM
impactDescription: enforces import direction, creates explicit public APIs per layer
tags: ts, modules, paths, imports
---

## Structure TypeScript Modules with Path Aliases and Enforced Layer Boundaries

Path aliases (`@domain/*`, `@application/*`) replace brittle relative imports with intent-revealing absolute paths. Avoid barrel files (`index.ts`) in application code — they cause cascade loading and circular dependencies. Use ESLint `import/no-restricted-paths` to enforce the Dependency Rule at lint time.

**ESLint enforcement of the Dependency Rule:**

```javascript
// eslint.config.js — enforces inward-only dependencies via linting
module.exports = {
  rules: {
    'import/no-restricted-paths': ['error', {
      zones: [
        // Domain must not import from outer layers
        { target: './src/domain', from: './src/application' },
        { target: './src/domain', from: './src/adapters' },
        { target: './src/domain', from: './src/infrastructure' },
        // Application must not import from adapters or infrastructure
        { target: './src/application', from: './src/adapters' },
        { target: './src/application', from: './src/infrastructure' },
      ],
    }],
    'import/no-cycle': 'error',
    'no-restricted-imports': ['error', {
      patterns: [{
        group: ['*/index'],
        message: 'Import directly from the source file, not the barrel index.',
      }],
    }],
  },
};
```

**Warning on barrel files:** Avoid barrels in application code. Importing ONE thing from a barrel loads ALL modules it re-exports. Use direct imports instead. See `comp-barrel-file-discipline` for the full analysis.

**Incorrect (relative imports cross layers with no boundary control):**

```typescript
// src/infrastructure/api/controllers/OrderController.ts
import { Order } from '../../../domain/entities/Order'
import { OrderItem } from '../../../domain/entities/OrderItem'
import { OrderValidator } from '../../../domain/services/OrderValidator'
import { CreateOrderUseCase } from '../../../application/use-cases/CreateOrderUseCase'
import { OrderCreatedEvent } from '../../../domain/events/OrderCreatedEvent'
// ^^^^ Fragile: moving any file breaks every import chain
// ^^^^ No boundary: controller can import any internal domain file

// src/application/use-cases/CreateOrderUseCase.ts
import { OrderItemPriceCalculator } from '../../domain/services/internal/OrderItemPriceCalculator'
// ^^^^ Violation: importing an internal module that shouldn't be exposed

// tsconfig.json — no path aliases
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "outDir": "dist"
  }
}
```

**Correct (path aliases with barrel files as public API gates):**

```typescript
// tsconfig.json — path aliases mirror architecture layers
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "outDir": "dist",
    "baseUrl": ".",
    "paths": {
      "@domain/*": ["src/domain/*"],
      "@application/*": ["src/application/*"],
      "@infrastructure/*": ["src/infrastructure/*"],
      "@shared/*": ["src/shared/*"]
    }
  }
}

// src/domain/entities/index.ts — barrel file: public API of domain entities
export { Order } from './Order'
export { OrderItem } from './OrderItem'
export type { OrderProps, OrderStatus } from './Order'
// OrderItemPriceCalculator is NOT exported — internal implementation detail

// src/domain/index.ts — top-level domain barrel
export * from './entities'
export * from './events'
export * from './ports'
// services/internal/* deliberately excluded from exports

// src/application/index.ts — public use cases
export { CreateOrderUseCase } from './use-cases/CreateOrderUseCase'
export { GetOrderUseCase } from './use-cases/GetOrderUseCase'
export type { CreateOrderInput, CreateOrderOutput } from './use-cases/CreateOrderUseCase'

// src/infrastructure/api/controllers/OrderController.ts
import { Order, OrderItem } from '@domain/entities'
import { CreateOrderUseCase } from '@application/use-cases/CreateOrderUseCase'
// ✅ Clean, stable, intent-revealing imports
// ✅ Cannot import internal domain modules not exported from barrel

// For monorepos: TypeScript project references
// tsconfig.json
{
  "references": [
    { "path": "./packages/domain" },
    { "path": "./packages/application" },
    { "path": "./packages/infrastructure" }
  ]
}
```

**Alternative (module-level package.json for stricter encapsulation):**

```typescript
// src/domain/package.json — treats domain as a separate package
{
  "name": "@myapp/domain",
  "main": "index.ts",
  "types": "index.ts"
}

// Now imports outside domain MUST go through the barrel:
import { Order } from '@myapp/domain'
// Direct deep imports fail:
import { OrderItemPriceCalculator } from '@myapp/domain/services/internal/calc'  // ❌ Error
```

**When NOT to use this pattern:**
- Projects with fewer than 10 source files — aliases add config overhead without benefit
- When using a framework with its own module conventions (e.g., Next.js app directory)
- Barrel files that re-export everything — defeats the purpose; be selective

**Benefits:**
- Moving files within a layer doesn't break imports in other layers
- Barrel files create explicit public APIs — internal refactoring is invisible to consumers
- Path aliases make the architecture visible in every import statement
- Project references enable incremental builds in monorepos
- Linting tools can enforce "only import from barrel files" rules

Reference: [TypeScript Path Mapping](https://www.typescriptlang.org/docs/handbook/modules/reference.html#paths) | [TypeScript Project References](https://www.typescriptlang.org/docs/handbook/project-references.html)
