# Environment Configuration with @fastify/env and TypeBox

## Overview

`@fastify/env` validates environment variables at startup using a JSON Schema. Combined with
TypeBox, you get type-safe config access throughout your application with validation errors
surfaced immediately rather than at runtime.

## Installation

```bash
npm install @fastify/env
```

## Define Config Schema with TypeBox

```typescript
// src/config.ts
import fp from 'fastify-plugin'
import fastifyEnv from '@fastify/env'
import { Type, type Static } from '@sinclair/typebox'

const ConfigSchema = Type.Object({
  NODE_ENV: Type.Union([
    Type.Literal('development'),
    Type.Literal('staging'),
    Type.Literal('production'),
    Type.Literal('test')
  ], { default: 'development' }),

  // Server
  PORT: Type.Integer({ default: 3000, minimum: 1, maximum: 65535 }),
  HOST: Type.String({ default: '0.0.0.0' }),
  LOG_LEVEL: Type.Union([
    Type.Literal('fatal'),
    Type.Literal('error'),
    Type.Literal('warn'),
    Type.Literal('info'),
    Type.Literal('debug'),
    Type.Literal('trace')
  ], { default: 'info' }),

  // Database
  DATABASE_URL: Type.String({ format: 'uri' }),
  DATABASE_POOL_SIZE: Type.Integer({ default: 10, minimum: 1, maximum: 100 }),

  // Redis
  REDIS_URL: Type.String({ default: 'redis://localhost:6379' }),

  // Auth
  JWT_SECRET: Type.String({ minLength: 32 }),
  JWT_EXPIRES_IN: Type.String({ default: '1h' }),

  // CORS
  CORS_ORIGINS: Type.String({ default: 'http://localhost:3000' }),

  // Rate Limiting
  RATE_LIMIT_MAX: Type.Integer({ default: 100 }),
  RATE_LIMIT_WINDOW: Type.String({ default: '1 minute' }),

  // External Services
  SMTP_HOST: Type.Optional(Type.String()),
  SMTP_PORT: Type.Optional(Type.Integer()),
  SENTRY_DSN: Type.Optional(Type.String({ format: 'uri' }))
})

export type AppConfig = Static<typeof ConfigSchema>

// Augment Fastify types
declare module 'fastify' {
  interface FastifyInstance {
    config: AppConfig
  }
}

export default fp(async (app) => {
  await app.register(fastifyEnv, {
    schema: ConfigSchema,
    dotenv: {
      path: `.env.${process.env.NODE_ENV ?? 'development'}`,
      debug: false
    },
    // Also load from .env as fallback
    data: process.env
  })
}, {
  name: 'config'
})
```

## Usage in Plugins

```typescript
// src/plugins/database.ts
import fp from 'fastify-plugin'

export default fp(async (app) => {
  // app.config is fully typed
  const pool = createPool({
    connectionString: app.config.DATABASE_URL,
    max: app.config.DATABASE_POOL_SIZE
  })

  app.decorate('db', pool)
}, {
  name: 'database',
  dependencies: ['config'] // Ensure config is loaded first
})
```

```typescript
// src/server.ts
const app = await buildApp()

await app.listen({
  port: app.config.PORT,
  host: app.config.HOST
})
```

## Environment Files

```bash
# .env.development
NODE_ENV=development
PORT=3000
DATABASE_URL=postgresql://localhost:5432/myapp_dev
JWT_SECRET=dev-secret-at-least-32-characters-long
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=debug
```

```bash
# .env.test
NODE_ENV=test
PORT=0
DATABASE_URL=postgresql://localhost:5432/myapp_test
JWT_SECRET=test-secret-at-least-32-characters-long
LOG_LEVEL=silent
```

```bash
# .env.production (DO NOT commit -- use secrets management)
NODE_ENV=production
PORT=3000
DATABASE_URL=postgresql://prod-host:5432/myapp
JWT_SECRET=${from_secrets_manager}
CORS_ORIGINS=https://app.example.com,https://admin.example.com
LOG_LEVEL=info
SENTRY_DSN=https://xxx@sentry.io/123
```

## .env.example (Commit This)

```bash
# .env.example -- Copy to .env.development and fill in values
NODE_ENV=development
PORT=3000
DATABASE_URL=postgresql://localhost:5432/myapp_dev
DATABASE_POOL_SIZE=10
REDIS_URL=redis://localhost:6379
JWT_SECRET=change-me-to-at-least-32-characters
JWT_EXPIRES_IN=1h
CORS_ORIGINS=http://localhost:5173
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW=1 minute
```

## Validation at Startup

If a required variable is missing or invalid, the app fails fast:

```
Error: env/DATABASE_URL must match format "uri"
Error: env must have required property 'JWT_SECRET'
```

This is much better than a runtime crash when the first request tries to use the DB.

## Conditional Config for Tests

```typescript
// test/helpers/setup.ts
import { buildApp } from '../../src/app.js'

export async function buildTestApp() {
  process.env.NODE_ENV = 'test'
  process.env.DATABASE_URL = 'postgresql://localhost:5432/myapp_test'
  process.env.JWT_SECRET = 'test-secret-that-is-at-least-32-chars'

  const app = await buildApp({ logger: false })
  await app.ready()
  return app
}
```

## Key Points

- Define config schema with TypeBox for type-safe `app.config` access
- `@fastify/env` validates all variables at startup (fail fast)
- Use `.env.development`, `.env.test`, `.env.production` for environment-specific files
- Commit `.env.example` but NEVER commit actual `.env` files with secrets
- Set `default` values for non-sensitive config (PORT, LOG_LEVEL, pool sizes)
- Make external service config `Type.Optional` if the feature is optional
- Register the config plugin first (other plugins depend on it)
