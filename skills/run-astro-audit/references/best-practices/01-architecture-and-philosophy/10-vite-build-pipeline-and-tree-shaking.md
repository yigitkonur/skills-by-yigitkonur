# Separate Server-Only Utilities From Client Bundles in the Vite Build Pipeline

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro orchestrates Vite across two distinct compilation targets: the **server build** (which compiles `.astro` components, endpoints, and SSR entrypoints) and the **client build** (which bundles hydrated islands and client scripts). Keeping server-only modules strictly decoupled from client modules ensures Rollup can effectively tree-shake dead code and prevents Node.js built-ins from crashing client builds.

## 2. How It Differs From Classic React / Next.js

In Next.js, barrel files (`index.ts`) frequently leak server-side code into client bundles unless guarded by the `server-only` package. In Astro, Vite processes client islands in an isolated browser environment. Importing a barrel file that touches server dependencies (e.g. `node:fs` or database drivers) will directly fail the client build.

## 3. Common Mistakes & Anti-Patterns

Creating a shared `src/lib/utils.ts` barrel file that exports both client string helpers and server database connection instances causes Vite's client bundling pass to pull in database drivers.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/lib/utils.ts
// Anti-pattern: Mixing server-only utilities and client helpers in a shared file
import { PrismaClient } from '@prisma/client'
export const db = new PrismaClient() // Server-only!

export function formatCurrency(amount: number) {
  // Client-safe helper
  return `$${amount.toFixed(2)}`
}
```

```jsx
// src/components/react/PriceDisplay.jsx
// Importing formatCurrency accidentally drags Prisma into the client bundle!
import { formatCurrency } from '../../lib/utils'
export default function PriceDisplay({ price }) {
  return <span>{formatCurrency(price)}</span>
}
```

### ✅ Best Practice / Idiomatic

```typescript
// src/lib/server/db.ts - Dedicated server-only boundary
import { PrismaClient } from '@prisma/client'
export const db = new PrismaClient()
```

```typescript
// src/lib/formatters.ts - Pure, zero-dependency browser-safe utilities
export function formatCurrency(amount: number) {
  return `$${amount.toFixed(2)}`
}
```

```jsx
// src/components/react/PriceDisplay.jsx
// Clean import: Vite bundles ONLY the tiny formatter function
import { formatCurrency } from '../../lib/formatters'

export default function PriceDisplay({ price }) {
  return <span>{formatCurrency(price)}</span>
}
```

## 4. Verification & Audit

Run a production build and inspect emitted client chunks:

```bash
npx astro build
# Verify that no server dependencies or node modules are bundled into client assets:
find dist/_astro/ -name "*.js" -exec grep -l "Prisma" {} + || echo "Clean client bundle."
```
