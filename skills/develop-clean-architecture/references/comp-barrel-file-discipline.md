---
title: Avoid Barrel Files in Application Code — Use Direct Imports
impact: HIGH
impactDescription: prevents circular dependencies, avoids 3x+ module loading overhead
tags: comp, barrel-files, imports, performance
---

## Avoid Barrel Files in Application Code — Use Direct Imports

Barrel files (`index.ts`) re-export from multiple modules, creating hidden coupling and serious build performance issues. Importing ONE thing from a barrel loads ALL modules it re-exports. Atlassian found barrels caused 11,000 modules loaded vs 3,500 without.

**Incorrect (cascading barrels — importing one thing loads everything):**

```typescript
// src/domain/entities/index.ts — barrel re-exports everything
export { Order } from './Order';
export { Customer } from './Customer';
export { Product } from './Product';

// src/domain/index.ts — top-level barrel
export * from './entities';
export * from './events';
export * from './services';

// Importing ONE entity loads ALL domain modules
import { Order } from '../domain';
// Forces: domain/index.ts → entities/index.ts → ALL entities + events + services

// Circular dependency trap:
// src/domain/entities/Order.ts
import { OrderLine } from './';  // imports from index.ts INSIDE same folder
// Order.ts → index.ts → Order.ts → circular!
```

**Correct (direct imports — fast, explicit, no circular risk):**

```typescript
// Direct imports: fast, clear, no barrel traversal
import { Order } from '../domain/entities/Order';
import { Customer } from '../domain/entities/Customer';
// LSP resolves these instantly

// Barrels acceptable ONLY for published library public API
// @myorg/order-domain/src/index.ts (the library entry point only)
export { Order } from './entities/Order';
export { Money } from './value-objects/Money';
export type { OrderRepository } from './ports/OrderRepository';
```

**ESLint enforcement:**

```javascript
// eslint.config.js
module.exports = {
  rules: {
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

**When barrel files ARE acceptable:**
- Published npm package entry point (`package.json` "main" field)
- Monorepo package boundaries where the barrel IS the public API
- Generated code barrel that acts as a single import point

**Benefits:**
- No circular dependency risk from barrel re-export chains
- Build and LSP performance: only the needed module is loaded
- Import paths make the source file unambiguous
- `import/no-cycle` ESLint rule catches any remaining circular issues

Reference: [Atlassian — Barrel File Performance](https://blog.myriad.ai/barrel-files-in-typescript) | [TypeScript Performance Wiki](https://github.com/microsoft/TypeScript/wiki/Performance)
