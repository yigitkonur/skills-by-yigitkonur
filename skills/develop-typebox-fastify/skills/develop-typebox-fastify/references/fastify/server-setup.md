# Fastify Server Setup

## Instance Creation with TypeBox

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
    transport: process.env.NODE_ENV === 'development'
      ? { target: 'pino-pretty', options: { colorize: true } }
      : undefined,
  },
  trustProxy: true,
  bodyLimit: 1048576, // 1MB default
  connectionTimeout: 30000,
  keepAliveTimeout: 72000,
  requestTimeout: 30000,
  requestIdHeader: 'x-request-id',
  requestIdLogLabel: 'reqId',
  caseSensitive: true,
}).withTypeProvider<TypeBoxTypeProvider>()
```

## Minimal Server

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'

const app = Fastify({ logger: true }).withTypeProvider<TypeBoxTypeProvider>()

app.get('/health', {
  schema: {
    response: {
      200: Type.Object({
        status: Type.String(),
        timestamp: Type.String({ format: 'date-time' }),
      }),
    },
  },
}, async () => {
  return { status: 'ok', timestamp: new Date().toISOString() }
})

await app.listen({ port: 3000, host: '0.0.0.0' })
```

## App Factory Pattern (Recommended)

Separate app building from server start for testability:

```typescript
// src/app.ts
import Fastify, { type FastifyInstance } from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import closeWithGrace from 'close-with-grace'

export async function buildApp(opts = {}): Promise<FastifyInstance> {
  const app = Fastify({
    logger: opts.logger ?? true,
    trustProxy: true,
    bodyLimit: 1048576,
    ...opts,
  }).withTypeProvider<TypeBoxTypeProvider>()

  // Register plugins in order
  await app.register(import('./plugins/config.js'))
  await app.register(import('./plugins/database.js'))
  await app.register(import('./routes/index.js'))

  return app
}

// src/server.ts
import { buildApp } from './app.js'

const app = await buildApp()

closeWithGrace({ delay: 10000 }, async ({ signal, err }) => {
  if (err) app.log.error({ err }, 'Closing due to error')
  await app.close()
})

await app.listen({
  port: parseInt(process.env.PORT || '3000', 10),
  host: '0.0.0.0',
})
```

## Request ID Generation

```typescript
import { randomUUID } from 'node:crypto'

const app = Fastify({
  logger: true,
  requestIdHeader: 'x-request-id',
  genReqId: (request) => {
    return request.headers['x-request-id']?.toString() || randomUUID()
  },
})
```

## Custom Ajv Options

Configure the JSON Schema validator with TypeBox-compatible settings:

```typescript
const app = Fastify({
  ajv: {
    customOptions: {
      removeAdditional: 'all',
      useDefaults: true,
      coerceTypes: true,
      allErrors: true,
    },
    plugins: [require('ajv-formats')],
  },
})
```

## TypeBox Type Provider on Plugin Level

When defining routes inside plugins, re-apply the type provider:

```typescript
import { Type } from '@sinclair/typebox'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import type { FastifyPluginAsync } from 'fastify'

const routes: FastifyPluginAsync = async (fastify) => {
  const app = fastify.withTypeProvider<TypeBoxTypeProvider>()

  app.get('/items', {
    schema: {
      response: {
        200: Type.Array(Type.Object({ id: Type.String(), name: Type.String() })),
      },
    },
  }, async () => {
    return [{ id: '1', name: 'Item 1' }]
  })
}

export default routes
```

## Key Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `logger` | `false` | Pino logger config or boolean |
| `trustProxy` | `false` | Trust X-Forwarded-* headers |
| `bodyLimit` | `1048576` | Max body size in bytes (1MB) |
| `connectionTimeout` | `0` | Connection timeout in ms |
| `keepAliveTimeout` | `72000` | Keep-alive timeout in ms |
| `requestTimeout` | `0` | Request timeout in ms |
| `caseSensitive` | `true` | Case-sensitive routing |
| `disableRequestLogging` | `false` | Disable automatic request logging |
