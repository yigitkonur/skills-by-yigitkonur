# Graceful Shutdown

## Overview

Graceful shutdown ensures in-flight requests complete before the server exits. This prevents
data corruption, broken connections, and failed responses during deployments and scaling.

## close-with-grace

The `close-with-grace` package handles the shutdown lifecycle:

```bash
npm install close-with-grace
```

```typescript
// src/server.ts
import Fastify from 'fastify'
import closeWithGrace from 'close-with-grace'
import { buildApp } from './app.js'

async function start() {
  const app = await buildApp()

  // Graceful shutdown handler
  closeWithGrace(
    {
      delay: 10_000 // Allow 10 seconds for cleanup before force-killing
    },
    async ({ signal, err }) => {
      if (err) {
        app.log.error(err, 'Server closing due to error')
      } else {
        app.log.info(`Received ${signal}, shutting down gracefully...`)
      }

      await app.close()
      app.log.info('Server closed')
    }
  )

  await app.listen({
    port: Number(process.env.PORT ?? 3000),
    host: '0.0.0.0' // Required for Docker/Kubernetes
  })

  app.log.info('Server started')
}

start()
```

## Fastify onClose Hooks

Register cleanup in plugins:

```typescript
// Database plugin
import fp from 'fastify-plugin'

export default fp(async (app) => {
  const db = createDatabaseConnection()
  app.decorate('db', db)

  // Runs during app.close()
  app.addHook('onClose', async (instance) => {
    instance.log.info('Closing database connection...')
    await db.end()
    instance.log.info('Database connection closed')
  })
})

// Redis plugin
export default fp(async (app) => {
  const redis = new Redis(app.config.REDIS_URL)
  app.decorate('redis', redis)

  app.addHook('onClose', async () => {
    app.log.info('Closing Redis connection...')
    await redis.quit()
    app.log.info('Redis connection closed')
  })
})
```

## Kubernetes Readiness During Shutdown

Stop accepting new traffic before shutting down:

```typescript
// src/plugins/health.ts
import fp from 'fastify-plugin'
import { Type } from '@sinclair/typebox'

export default fp(async (app) => {
  let isShuttingDown = false

  // Mark as shutting down before closing
  app.addHook('onClose', async () => {
    isShuttingDown = true
  })

  app.get('/health/ready', {
    schema: {
      response: {
        200: Type.Object({ status: Type.Literal('ready') }),
        503: Type.Object({ status: Type.Literal('shutting_down') })
      }
    }
  }, async (request, reply) => {
    if (isShuttingDown) {
      reply.status(503)
      return { status: 'shutting_down' as const }
    }
    return { status: 'ready' as const }
  })
})
```

## Full Shutdown Sequence

```typescript
// src/app.ts
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

export async function buildApp() {
  const app = Fastify({
    logger: true,
    // Stop accepting connections before closing
    forceCloseConnections: 'idle',
    // Timeout for completing in-flight requests
    connectionTimeout: 10_000
  }).withTypeProvider<TypeBoxTypeProvider>()

  // Register plugins in order of cleanup priority
  await app.register(databasePlugin)    // Closes last (most critical)
  await app.register(redisPlugin)
  await app.register(healthPlugin)
  await app.register(routes)

  return app
}
```

## Docker SIGTERM Handling

Docker sends SIGTERM on container stop. Ensure Node.js receives it:

```dockerfile
# Use exec form of CMD so Node.js receives signals directly
CMD ["node", "dist/server.js"]

# NOT shell form (signal goes to /bin/sh, not Node.js)
# CMD node dist/server.js  # BAD
```

## Background Job Cleanup

```typescript
// src/plugins/workers.ts
import fp from 'fastify-plugin'

export default fp(async (app) => {
  const intervalId = setInterval(processQueue, 5000)
  let isProcessing = false

  async function processQueue() {
    if (isProcessing) return
    isProcessing = true
    try {
      await processNextBatch()
    } finally {
      isProcessing = false
    }
  }

  app.addHook('onClose', async () => {
    clearInterval(intervalId)

    // Wait for current batch to complete
    const maxWait = 5000
    const start = Date.now()
    while (isProcessing && Date.now() - start < maxWait) {
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    if (isProcessing) {
      app.log.warn('Background job did not complete before shutdown')
    }
  })
})
```

## Shutdown Order

1. Stop accepting new connections (Fastify handles this)
2. Health endpoint returns 503 (Kubernetes stops sending traffic)
3. Wait for in-flight requests to complete
4. Close application resources (workers, queues)
5. Close external connections (Redis, database)
6. Exit process

## Key Points

- Use `close-with-grace` for signal handling and timeout
- Register `onClose` hooks in every plugin that owns a resource
- Set `host: '0.0.0.0'` for containerized environments
- Use Docker `CMD` exec form so Node.js receives SIGTERM
- Kubernetes: return 503 from readiness probe during shutdown
- Set a reasonable delay (10-30 seconds) before force-killing
- `onClose` hooks run in reverse registration order (LIFO)
