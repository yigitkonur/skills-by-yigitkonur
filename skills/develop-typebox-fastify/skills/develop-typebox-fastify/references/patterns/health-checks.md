# Health Checks: Liveness and Readiness Probes

## Overview

Health check endpoints tell orchestrators (Kubernetes, ECS, load balancers) whether the
service is alive and ready to handle traffic. Two separate endpoints serve different purposes.

## TypeBox Schemas

```typescript
// src/schemas/health.ts
import { Type } from '@sinclair/typebox'

export const LivenessResponse = Type.Object({
  status: Type.Union([Type.Literal('ok'), Type.Literal('error')]),
  timestamp: Type.String({ format: 'date-time' }),
  uptime: Type.Number({ description: 'Process uptime in seconds' })
})

export const ReadinessResponse = Type.Object({
  status: Type.Union([Type.Literal('ready'), Type.Literal('degraded'), Type.Literal('not_ready')]),
  timestamp: Type.String({ format: 'date-time' }),
  checks: Type.Object({
    database: Type.Object({
      status: Type.Union([Type.Literal('up'), Type.Literal('down')]),
      latencyMs: Type.Optional(Type.Number())
    }),
    redis: Type.Object({
      status: Type.Union([Type.Literal('up'), Type.Literal('down')]),
      latencyMs: Type.Optional(Type.Number())
    })
  })
})
```

## Health Check Plugin

```typescript
// src/plugins/health.ts
import fp from 'fastify-plugin'
import { Type } from '@sinclair/typebox'
import { LivenessResponse, ReadinessResponse } from '../schemas/health.js'

export default fp(async (app) => {
  let shuttingDown = false

  app.addHook('onClose', async () => {
    shuttingDown = true
  })

  // Liveness: Is the process alive and responding?
  // Kubernetes restarts the pod if this fails
  app.get('/health/live', {
    schema: {
      tags: ['Health'],
      summary: 'Liveness probe',
      response: { 200: LivenessResponse }
    },
    config: { rateLimit: false } // Exempt from rate limiting
  }, async () => {
    return {
      status: 'ok' as const,
      timestamp: new Date().toISOString(),
      uptime: process.uptime()
    }
  })

  // Readiness: Can the service handle requests?
  // Kubernetes stops routing traffic if this fails
  app.get('/health/ready', {
    schema: {
      tags: ['Health'],
      summary: 'Readiness probe',
      response: {
        200: ReadinessResponse,
        503: ReadinessResponse
      }
    },
    config: { rateLimit: false }
  }, async (request, reply) => {
    if (shuttingDown) {
      reply.status(503)
      return {
        status: 'not_ready' as const,
        timestamp: new Date().toISOString(),
        checks: {
          database: { status: 'down' as const },
          redis: { status: 'down' as const }
        }
      }
    }

    const [dbCheck, redisCheck] = await Promise.allSettled([
      checkDatabase(app),
      checkRedis(app)
    ])

    const dbResult = dbCheck.status === 'fulfilled' ? dbCheck.value : { status: 'down' as const }
    const redisResult = redisCheck.status === 'fulfilled' ? redisCheck.value : { status: 'down' as const }

    const allUp = dbResult.status === 'up' && redisResult.status === 'up'
    const allDown = dbResult.status === 'down' && redisResult.status === 'down'

    const status = allUp ? 'ready' : allDown ? 'not_ready' : 'degraded'
    const statusCode = status === 'not_ready' ? 503 : 200

    reply.status(statusCode)
    return {
      status: status as 'ready' | 'degraded' | 'not_ready',
      timestamp: new Date().toISOString(),
      checks: {
        database: dbResult,
        redis: redisResult
      }
    }
  })
})

async function checkDatabase(app: any): Promise<{ status: 'up' | 'down'; latencyMs: number }> {
  const start = performance.now()
  try {
    await app.db.execute(sql`SELECT 1`)
    return { status: 'up', latencyMs: Math.round(performance.now() - start) }
  } catch {
    return { status: 'down', latencyMs: Math.round(performance.now() - start) }
  }
}

async function checkRedis(app: any): Promise<{ status: 'up' | 'down'; latencyMs: number }> {
  const start = performance.now()
  try {
    await app.redis.ping()
    return { status: 'up', latencyMs: Math.round(performance.now() - start) }
  } catch {
    return { status: 'down', latencyMs: Math.round(performance.now() - start) }
  }
}
```

## Kubernetes Configuration

```yaml
# k8s/deployment.yaml
spec:
  containers:
    - name: api
      livenessProbe:
        httpGet:
          path: /health/live
          port: 3000
        initialDelaySeconds: 5
        periodSeconds: 10
        timeoutSeconds: 3
        failureThreshold: 3     # Restart after 3 consecutive failures
      readinessProbe:
        httpGet:
          path: /health/ready
          port: 3000
        initialDelaySeconds: 10
        periodSeconds: 5
        timeoutSeconds: 3
        failureThreshold: 2     # Remove from service after 2 failures
      startupProbe:
        httpGet:
          path: /health/live
          port: 3000
        initialDelaySeconds: 2
        periodSeconds: 5
        failureThreshold: 30    # Allow up to 150s for slow startups
```

## Deep Health Check (Admin Only)

```typescript
app.get('/health/deep', {
  onRequest: app.requireRole('admin'),
  schema: {
    tags: ['Health'],
    summary: 'Deep health check with diagnostics',
    response: {
      200: Type.Object({
        status: Type.String(),
        version: Type.String(),
        nodeVersion: Type.String(),
        memory: Type.Object({
          rss: Type.Number(),
          heapUsed: Type.Number(),
          heapTotal: Type.Number()
        }),
        uptime: Type.Number(),
        checks: Type.Record(Type.String(), Type.Object({
          status: Type.String(),
          latencyMs: Type.Number()
        }))
      })
    }
  }
}, async () => {
  const mem = process.memoryUsage()
  return {
    status: 'ok',
    version: process.env.APP_VERSION ?? 'unknown',
    nodeVersion: process.version,
    memory: {
      rss: Math.round(mem.rss / 1024 / 1024),
      heapUsed: Math.round(mem.heapUsed / 1024 / 1024),
      heapTotal: Math.round(mem.heapTotal / 1024 / 1024)
    },
    uptime: process.uptime(),
    checks: { /* ... dependency checks */ }
  }
})
```

## Key Points

- Liveness: lightweight, checks if the process can respond (no dependency checks)
- Readiness: checks all critical dependencies (DB, cache, external services)
- Return 503 during shutdown so orchestrators stop routing traffic
- Use `Promise.allSettled` so one failing check does not block others
- Exempt health endpoints from rate limiting and authentication
- Include latency in check results for monitoring dashboards
- Keep deep health checks behind authentication (exposes internals)
