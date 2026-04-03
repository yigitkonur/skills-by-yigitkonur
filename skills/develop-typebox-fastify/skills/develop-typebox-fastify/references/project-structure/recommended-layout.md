# Recommended Directory Layout

## Overview

A well-organized project structure separates concerns (routes, schemas, services, plugins)
and scales from small APIs to large microservices.

## Standard Layout

```
project-root/
  src/
    app.ts                  # App factory (buildApp function)
    server.ts               # Entry point (listen + graceful shutdown)
    config.ts               # Environment config schema

    schemas/                # TypeBox schemas (shared across layers)
      common.ts             # Pagination, error, timestamp schemas
      user.ts               # User-related schemas
      product.ts            # Product-related schemas

    routes/                 # Fastify route plugins
      index.ts              # Route registration (prefix mapping)
      users.ts              # /users routes
      products.ts           # /products routes
      health.ts             # /health routes

    plugins/                # Fastify plugins (infrastructure)
      database.ts           # DB connection + decorator
      redis.ts              # Redis connection + decorator
      auth.ts               # Authentication hooks
      error-handler.ts      # Global error handler
      request-context.ts    # Correlation IDs, request decorators

    services/               # Business logic (no Fastify dependency)
      user.service.ts
      product.service.ts
      email.service.ts

    repositories/           # Data access layer
      types.ts              # Repository interfaces
      user.repository.ts
      product.repository.ts

    db/                     # Database-specific
      schema.ts             # Drizzle table definitions (or prisma/)
      migrations/           # SQL migration files

    utils/                  # Shared utilities
      logger.ts
      crypto.ts

  test/
    helpers/
      setup.ts              # Test app builder
      fixtures.ts           # Test data factories
    routes/
      users.test.ts
      products.test.ts
    services/
      user.service.test.ts

  drizzle/                  # Drizzle migrations output
  prisma/                   # Or Prisma schema + migrations

  Dockerfile
  docker-compose.yml
  tsconfig.json
  package.json
  .env.example
```

## App Factory Pattern

```typescript
// src/app.ts
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

// Plugins
import configPlugin from './config.js'
import databasePlugin from './plugins/database.js'
import redisPlugin from './plugins/redis.js'
import authPlugin from './plugins/auth.js'
import errorHandlerPlugin from './plugins/error-handler.js'
import requestContextPlugin from './plugins/request-context.js'

// Routes
import routes from './routes/index.js'

export async function buildApp(opts = {}) {
  const app = Fastify({
    logger: true,
    ...opts
  }).withTypeProvider<TypeBoxTypeProvider>()

  // Infrastructure plugins (order matters)
  await app.register(configPlugin)
  await app.register(errorHandlerPlugin)
  await app.register(requestContextPlugin)
  await app.register(databasePlugin)
  await app.register(redisPlugin)
  await app.register(authPlugin)

  // Routes
  await app.register(routes, { prefix: '/api' })

  return app
}
```

```typescript
// src/server.ts
import closeWithGrace from 'close-with-grace'
import { buildApp } from './app.js'

const app = await buildApp()

closeWithGrace({ delay: 10_000 }, async ({ signal, err }) => {
  if (err) app.log.error(err)
  await app.close()
})

await app.listen({ port: 3000, host: '0.0.0.0' })
```

## Route Registration

```typescript
// src/routes/index.ts
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import healthRoutes from './health.js'
import userRoutes from './users.js'
import productRoutes from './products.js'

const routes: FastifyPluginAsyncTypebox = async (app) => {
  await app.register(healthRoutes)                        // /api/health
  await app.register(userRoutes, { prefix: '/users' })    // /api/users
  await app.register(productRoutes, { prefix: '/products' }) // /api/products
}

export default routes
```

## Schema Organization

```typescript
// src/schemas/common.ts
import { Type, type TSchema } from '@sinclair/typebox'

export const IdParams = Type.Object({
  id: Type.String({ format: 'uuid' })
})

export const PaginationQuery = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1 }),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 })
})

export const ErrorResponse = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String()
}, { $id: 'ErrorResponse' })

export const TimestampFields = Type.Object({
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' })
})

// Generic paginated response
export function Paginated<T extends TSchema>(schema: T) {
  return Type.Object({
    data: Type.Array(schema),
    pagination: Type.Object({
      page: Type.Integer(),
      limit: Type.Integer(),
      total: Type.Integer(),
      totalPages: Type.Integer()
    })
  })
}
```

## Test Structure

```typescript
// test/helpers/setup.ts
import { buildApp } from '../../src/app.js'

export async function buildTestApp() {
  const app = await buildApp({ logger: false })
  await app.ready()
  return app
}

// test/routes/users.test.ts
import { describe, it, beforeAll, afterAll, expect } from 'vitest'
import { buildTestApp } from '../helpers/setup.js'

describe('GET /api/users', () => {
  let app: Awaited<ReturnType<typeof buildTestApp>>

  beforeAll(async () => { app = await buildTestApp() })
  afterAll(async () => { await app.close() })

  it('returns paginated users', async () => {
    const res = await app.inject({ method: 'GET', url: '/api/users' })
    expect(res.statusCode).toBe(200)
    expect(res.json()).toHaveProperty('data')
    expect(res.json()).toHaveProperty('pagination')
  })
})
```

## Key Points

- Use the app factory pattern (`buildApp`) for testability
- Separate `app.ts` (configuration) from `server.ts` (listening)
- Group by concern: schemas/, routes/, plugins/, services/, repositories/
- Register plugins in dependency order (config first, then DB, then auth)
- Keep schemas in a dedicated directory, not mixed with routes
- Services contain business logic and do not depend on Fastify types
- Tests mirror the src/ structure for easy navigation
