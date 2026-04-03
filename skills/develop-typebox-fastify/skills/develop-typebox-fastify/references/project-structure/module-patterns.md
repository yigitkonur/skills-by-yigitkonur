# Module Patterns: ESM, Package.json, and Imports

## Overview

Modern Fastify + TypeBox projects use ECMAScript Modules (ESM) with TypeScript. This covers
the correct configuration for module resolution, imports, and compatibility.

## package.json Configuration

```json
{
  "name": "my-api",
  "version": "1.0.0",
  "type": "module",
  "engines": {
    "node": ">=22.0.0"
  },
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "eslint src/",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "fastify": "^5.0.0",
    "@sinclair/typebox": "^0.34.0",
    "@fastify/type-provider-typebox": "^5.0.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "tsx": "^4.19.0",
    "vitest": "^2.1.0",
    "@types/node": "^22.0.0"
  }
}
```

## tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "test"]
}
```

## ESM Import Conventions

With `"module": "NodeNext"`, TypeScript requires `.js` extensions in imports (even for `.ts` files):

```typescript
// CORRECT: Use .js extension (TypeScript resolves to .ts at compile time)
import { buildApp } from './app.js'
import { UserSchema } from '../schemas/user.js'
import type { User } from '../contracts/user.js'

// WRONG: No extension or .ts extension
import { buildApp } from './app'        // Error in ESM
import { buildApp } from './app.ts'     // Only works with tsx/bun
```

## Re-Export Patterns

Barrel exports for clean imports:

```typescript
// src/schemas/index.ts
export { UserSchema, CreateUserBody, UpdateUserBody } from './user.js'
export { ProductSchema, CreateProductBody } from './product.js'
export { ErrorResponse, PaginationQuery, IdParams } from './common.js'

// Usage in routes:
import { UserSchema, CreateUserBody, ErrorResponse } from '../schemas/index.js'
```

## Plugin Export Pattern

```typescript
// src/plugins/database.ts
import fp from 'fastify-plugin'
import { FastifyPluginAsync } from 'fastify'

// Use fp() to break encapsulation (decorators visible to sibling plugins)
const databasePlugin: FastifyPluginAsync = async (app) => {
  // ...
}

export default fp(databasePlugin, {
  name: 'database',
  dependencies: ['config'] // Ensure config is registered first
})
```

```typescript
// src/routes/users.ts
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'

// Do NOT use fp() for routes (encapsulation is desired)
const userRoutes: FastifyPluginAsyncTypebox = async (app) => {
  // ...
}

export default userRoutes
```

## Type-Only Imports

Use `type` keyword for imports used only in type positions:

```typescript
import type { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify'
import type { Static } from '@sinclair/typebox'
import { Type } from '@sinclair/typebox'  // Runtime import

// Combined import
import { Type, type Static, type TSchema } from '@sinclair/typebox'
```

## Development with tsx

`tsx` runs TypeScript directly without a build step:

```json
{
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "dev:inspect": "tsx watch --inspect src/server.ts"
  }
}
```

## Path Aliases (Optional)

For deeply nested imports, configure path aliases:

```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "#schemas/*": ["./src/schemas/*"],
      "#plugins/*": ["./src/plugins/*"],
      "#services/*": ["./src/services/*"]
    }
  }
}
```

```json
// package.json
{
  "imports": {
    "#schemas/*": "./dist/schemas/*",
    "#plugins/*": "./dist/plugins/*",
    "#services/*": "./dist/services/*"
  }
}
```

```typescript
// Usage:
import { UserSchema } from '#schemas/user.js'
import type { UserRepository } from '#services/types.js'
```

## Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    root: '.',
    include: ['test/**/*.test.ts'],
    setupFiles: ['test/helpers/setup.ts'],
    pool: 'forks',        // Isolate tests
    testTimeout: 10_000,
    hookTimeout: 10_000
  }
})
```

## Key Points

- Always set `"type": "module"` in package.json for ESM
- Use `"module": "NodeNext"` and `"moduleResolution": "NodeNext"` in tsconfig
- Include `.js` extension in all relative imports
- Use `fp()` for infrastructure plugins, not for route plugins
- Use `type` imports for types to enable proper tree-shaking
- Use `tsx` for development (no build step needed)
- Use Node.js subpath imports (`#prefix`) for path aliases (native, no bundler needed)
