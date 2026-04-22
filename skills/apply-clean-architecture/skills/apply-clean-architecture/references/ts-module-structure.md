---
title: Structure TypeScript Modules with Path Aliases and Enforced Layer Boundaries
impact: MEDIUM
impactDescription: enforces import direction and sanctioned import paths
tags: ts, modules, paths, imports
---

## Structure TypeScript Modules with Path Aliases and Enforced Layer Boundaries

Path aliases (`@domain/*`, `@application/*`) replace brittle relative imports with intent-revealing absolute paths. Avoid barrel files (`index.ts`) in application code — they cause cascade loading and circular dependencies. Use aliases for direct file imports inside the app, and reserve single-entry-point exports for real package boundaries only.

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
      patterns: [
        {
          group: ['*/index'],
          message: 'Import directly from the source file, not the barrel index.',
        },
        {
          group: ['@domain/internal/*', '@application/internal/*'],
          message: 'Import only from sanctioned layer paths or package entry points.',
        }
      ],
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

**Correct (path aliases with direct file imports):**

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
      "@adapters/*": ["src/adapters/*"],
      "@infrastructure/*": ["src/infrastructure/*"],
      "@shared/*": ["src/shared/*"]
    }
  }
}

// src/adapters/http/OrderController.ts
import type { Order } from '@domain/entities/Order'
import { CreateOrderUseCase } from '@application/use-cases/CreateOrderUseCase'
// ✅ Clean, stable, intent-revealing imports
// ✅ No barrel traversal or hidden module loading
// ✅ Lint rules can still block forbidden paths

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

**Alternative (real package boundary with a single entry point):**

```typescript
// packages/domain/package.json — domain is its own package now
{
  "name": "@myapp/domain",
  "exports": {
    ".": "./src/index.ts"
  }
}

// packages/domain/src/index.ts — package entry point only
export { Order } from './entities/Order'
export type { OrderRepository } from './ports/OrderRepository'

// Now imports outside the package go through the package boundary:
import { Order } from '@myapp/domain'
// Internal app code inside the same package still uses direct file imports.
```

**When NOT to use this pattern:**
- Projects with fewer than 10 source files — aliases add config overhead without benefit
- When using a framework with its own module conventions (e.g., Next.js app directory)
- When package boundaries do not exist — do not invent pseudo-packages just to justify barrels

**Benefits:**
- Moving files within a layer doesn't break imports in other layers
- Direct file imports keep dependency flow explicit and avoid barrel cascades
- Path aliases make the architecture visible in every import statement
- Real package boundaries can expose a single entry point when you truly need one
- Linting tools can enforce allowed alias roots and package entry points

Reference: [TypeScript Path Mapping](https://www.typescriptlang.org/docs/handbook/modules/reference.html#paths) | [TypeScript Project References](https://www.typescriptlang.org/docs/handbook/project-references.html)
