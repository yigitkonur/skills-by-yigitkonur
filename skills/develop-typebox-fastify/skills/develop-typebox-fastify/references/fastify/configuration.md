# Fastify Configuration

## env-schema with TypeBox (Recommended)

```typescript
import Fastify from 'fastify'
import envSchema from 'env-schema'
import { Type, type Static } from '@sinclair/typebox'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const schema = Type.Object({
  PORT: Type.Number({ default: 3000 }),
  HOST: Type.String({ default: '0.0.0.0' }),
  DATABASE_URL: Type.String(),
  JWT_SECRET: Type.String({ minLength: 32 }),
  LOG_LEVEL: Type.Union([
    Type.Literal('trace'),
    Type.Literal('debug'),
    Type.Literal('info'),
    Type.Literal('warn'),
    Type.Literal('error'),
    Type.Literal('fatal'),
  ], { default: 'info' }),
  REDIS_URL: Type.Optional(Type.String()),
})

type Config = Static<typeof schema>

const config = envSchema<Config>({
  schema,
  dotenv: true, // loads from .env file
})

const app = Fastify({
  logger: { level: config.LOG_LEVEL },
}).withTypeProvider<TypeBoxTypeProvider>()

app.decorate('config', config)

declare module 'fastify' {
  interface FastifyInstance {
    config: Config
  }
}

await app.listen({ port: config.PORT, host: config.HOST })
```

## Configuration as Plugin

```typescript
import fp from 'fastify-plugin'
import envSchema from 'env-schema'
import { Type, type Static } from '@sinclair/typebox'

const schema = Type.Object({
  PORT: Type.Number({ default: 3000 }),
  HOST: Type.String({ default: '0.0.0.0' }),
  DATABASE_URL: Type.String(),
  JWT_SECRET: Type.String({ minLength: 32 }),
  LOG_LEVEL: Type.String({ default: 'info' }),
  CORS_ORIGINS: Type.Optional(Type.String()),
})

type Config = Static<typeof schema>

declare module 'fastify' {
  interface FastifyInstance {
    config: Config
  }
}

export default fp(async function configPlugin(fastify) {
  const config = envSchema<Config>({
    schema,
    dotenv: true,
  })

  fastify.decorate('config', config)
}, {
  name: 'config',
})
```

## Feature Flags

```typescript
const schema = Type.Object({
  // ... core config
  FEATURE_NEW_DASHBOARD: Type.Boolean({ default: false }),
  FEATURE_BETA_API: Type.Boolean({ default: false }),
  FEATURE_RATE_LIMIT: Type.Boolean({ default: true }),
})

type Config = Static<typeof schema>

// Usage in routes
app.get('/dashboard', {
  schema: { response: { 200: Type.Object({ version: Type.String(), data: Type.Unknown() }) } },
}, async () => {
  if (app.config.FEATURE_NEW_DASHBOARD) {
    return { version: 'v2', data: await getNewDashboardData() }
  }
  return { version: 'v1', data: await getOldDashboardData() }
})
```

## Secrets Management

```typescript
// Never log secrets
const app = Fastify({
  logger: {
    level: config.LOG_LEVEL,
    redact: ['req.headers.authorization', '*.password', '*.secret', '*.apiKey'],
  },
})

// For production, use secret managers (AWS Secrets Manager, Vault, etc.)
// Pass secrets through environment variables - NEVER commit them
```

## Anti-Patterns to AVOID

### NEVER use configuration files

```typescript
// WRONG: configuration files are an anti-pattern
import config from './config/production.json'

// WRONG: per-environment config files
const env = process.env.NODE_ENV || 'development'
const config = await import(`./config/${env}.js`)
```

Configuration files lead to security risks, deployment complexity, and difficult secret rotation.

### NEVER use per-environment conditionals

```typescript
// WRONG
const configs = {
  development: { logLevel: 'debug' },
  production: { logLevel: 'info' },
}
const config = configs[process.env.NODE_ENV]

// CORRECT: single config source, environment controls values
const config = envSchema<Config>({ schema, dotenv: true })
```

### Prefer explicit flags over NODE_ENV

```typescript
// AVOID
if (process.env.NODE_ENV === 'production') { /* ... */ }

// BETTER
if (app.config.ENABLE_DETAILED_LOGGING) { /* ... */ }
```

## Dynamic Configuration

For config that changes without restart:

```typescript
import { Type } from '@sinclair/typebox'

interface DynamicConfig {
  rateLimit: number
  maintenanceMode: boolean
}

let dynamicConfig: DynamicConfig = { rateLimit: 100, maintenanceMode: false }

async function refreshConfig() {
  try {
    const newConfig = await fetchConfigFromService()
    dynamicConfig = newConfig
    app.log.info('Configuration refreshed')
  } catch (error) {
    app.log.error({ err: error }, 'Failed to refresh config')
  }
}

setInterval(refreshConfig, 60000)

app.addHook('onRequest', async (request, reply) => {
  if (dynamicConfig.maintenanceMode && !request.url.startsWith('/health')) {
    reply.code(503).send({ error: 'Service under maintenance' })
  }
})
```

## @fastify/env Alternative

```typescript
import fastifyEnv from '@fastify/env'
import { Type } from '@sinclair/typebox'

const schema = Type.Object({
  PORT: Type.Number({ default: 3000 }),
  HOST: Type.String({ default: '0.0.0.0' }),
  DATABASE_URL: Type.String(),
})

await app.register(fastifyEnv, {
  schema,
  dotenv: true,
  confKey: 'config',
})

// Access via app.config.PORT, app.config.DATABASE_URL, etc.
```

## Testing Configuration

```typescript
import { describe, it } from 'node:test'
import { buildApp } from './app.js'

describe('App Config', () => {
  it('should start with valid config', async (t) => {
    process.env.DATABASE_URL = 'postgres://localhost/test'
    process.env.JWT_SECRET = 'a-very-long-secret-for-testing-purposes-only'

    const app = await buildApp({ logger: false })
    await app.ready()

    t.assert.ok(app.config.DATABASE_URL)
    t.assert.ok(app.config.JWT_SECRET)

    await app.close()
  })
})
```

## Key Rules

- Use `env-schema` with TypeBox for validated, typed configuration
- Environment variables are the single source of truth
- NEVER commit secrets (use .env for development, secret managers for production)
- Use feature flags instead of NODE_ENV conditionals
- Validate all config at startup (fail fast on invalid config)
