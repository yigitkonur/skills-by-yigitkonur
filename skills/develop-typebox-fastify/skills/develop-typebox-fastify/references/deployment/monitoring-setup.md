# Monitoring Setup: Logging, Error Tracking, and Metrics

## Overview

Production APIs need three pillars of observability: structured logging (Pino), error
tracking (Sentry), and application metrics (Prometheus/Datadog). This covers integration
with Fastify + TypeBox.

## Pino Logging (Built Into Fastify)

Fastify uses Pino by default. Configure it for production:

```typescript
import Fastify from 'fastify'

const app = Fastify({
  logger: {
    level: process.env.LOG_LEVEL ?? 'info',

    // Redact sensitive fields from logs
    redact: {
      paths: [
        'req.headers.authorization',
        'req.headers["x-api-key"]',
        'req.headers.cookie',
        'body.password',
        'body.token',
        'body.creditCard'
      ],
      censor: '[REDACTED]'
    },

    // Custom serializers
    serializers: {
      req(request) {
        return {
          method: request.method,
          url: request.url,
          hostname: request.hostname,
          remoteAddress: request.ip,
          requestId: request.id
        }
      },
      res(reply) {
        return {
          statusCode: reply.statusCode
        }
      }
    }
  }
})
```

## Pino Transports for Log Destinations

```typescript
// Production: Send logs to multiple destinations
const app = Fastify({
  logger: {
    level: 'info',
    transport: {
      targets: [
        // Stdout (for container log collectors)
        {
          target: 'pino/file',
          options: { destination: 1 }, // stdout
          level: 'info'
        },
        // File for local debugging
        {
          target: 'pino/file',
          options: { destination: '/var/log/app/api.log' },
          level: 'warn'
        }
      ]
    }
  }
})

// Development: Pretty printing
const devApp = Fastify({
  logger: {
    level: 'debug',
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'HH:MM:ss.l',
        ignore: 'pid,hostname'
      }
    }
  }
})
```

## Request Logging Hook

```typescript
// src/plugins/request-logger.ts
import fp from 'fastify-plugin'

export default fp(async (app) => {
  app.addHook('onResponse', async (request, reply) => {
    request.log.info({
      requestId: request.id,
      method: request.method,
      url: request.url,
      statusCode: reply.statusCode,
      responseTime: reply.elapsedTime,
      userAgent: request.headers['user-agent'],
      userId: request.user?.id
    }, 'request completed')
  })
})
```

## Sentry Error Tracking

```bash
npm install @sentry/node
```

```typescript
// src/plugins/sentry.ts
import fp from 'fastify-plugin'
import * as Sentry from '@sentry/node'

export default fp(async (app) => {
  if (!app.config.SENTRY_DSN) {
    app.log.info('Sentry DSN not configured, skipping')
    return
  }

  Sentry.init({
    dsn: app.config.SENTRY_DSN,
    environment: app.config.NODE_ENV,
    release: process.env.APP_VERSION,
    tracesSampleRate: app.config.NODE_ENV === 'production' ? 0.1 : 1.0,
    integrations: [
      Sentry.httpIntegration(),
    ]
  })

  // Capture unhandled errors
  app.addHook('onError', async (request, reply, error) => {
    // Only report 5xx errors to Sentry
    if (!reply.statusCode || reply.statusCode >= 500) {
      Sentry.withScope(scope => {
        scope.setTag('requestId', request.id)
        scope.setTag('method', request.method)
        scope.setTag('url', request.url)
        scope.setUser({
          id: request.user?.id,
          email: request.user?.email
        })
        scope.setContext('request', {
          params: request.params,
          query: request.query,
          // Do not send body -- may contain sensitive data
        })
        Sentry.captureException(error)
      })
    }
  })

  // Flush on shutdown
  app.addHook('onClose', async () => {
    await Sentry.close(2000)
  })
})
```

## Prometheus Metrics

```bash
npm install fastify-metrics prom-client
```

```typescript
// src/plugins/metrics.ts
import fp from 'fastify-plugin'
import metricsPlugin from 'fastify-metrics'

export default fp(async (app) => {
  await app.register(metricsPlugin, {
    endpoint: '/metrics',          // Prometheus scrape endpoint
    defaultMetrics: { enabled: true },
    routeMetrics: {
      enabled: true,
      overrides: {
        histogram: {
          name: 'http_request_duration_seconds',
          help: 'Request duration in seconds',
          labelNames: ['method', 'route', 'status_code'],
          buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        }
      }
    }
  })
})
```

## Custom Business Metrics

```typescript
// src/plugins/business-metrics.ts
import fp from 'fastify-plugin'
import { Counter, Histogram, Gauge } from 'prom-client'

export default fp(async (app) => {
  const ordersCreated = new Counter({
    name: 'orders_created_total',
    help: 'Total number of orders created',
    labelNames: ['status']
  })

  const orderProcessingDuration = new Histogram({
    name: 'order_processing_duration_seconds',
    help: 'Time to process an order',
    buckets: [0.1, 0.5, 1, 5, 10, 30]
  })

  const activeConnections = new Gauge({
    name: 'db_active_connections',
    help: 'Number of active database connections'
  })

  app.decorate('metrics', {
    ordersCreated,
    orderProcessingDuration,
    activeConnections
  })
})

// Usage in routes:
app.post('/orders', handler, async (request) => {
  const timer = app.metrics.orderProcessingDuration.startTimer()
  try {
    const order = await processOrder(request.body)
    app.metrics.ordersCreated.inc({ status: 'success' })
    return order
  } catch (err) {
    app.metrics.ordersCreated.inc({ status: 'failure' })
    throw err
  } finally {
    timer()
  }
})
```

## Health Check Schema for Monitoring

```typescript
import { Type } from '@sinclair/typebox'

const MetricsHealthSchema = Type.Object({
  status: Type.String(),
  uptime: Type.Number(),
  memory: Type.Object({
    rss: Type.Number({ description: 'Resident Set Size in MB' }),
    heapUsed: Type.Number({ description: 'Heap used in MB' }),
    heapTotal: Type.Number({ description: 'Heap total in MB' })
  }),
  eventLoopLag: Type.Number({ description: 'Event loop lag in ms' })
})
```

## Alerting Rules (Prometheus Example)

```yaml
# prometheus/alerts.yml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_request_duration_seconds_count{status_code=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High 5xx error rate"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency above 2 seconds"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes > 500e6
        for: 10m
        labels:
          severity: warning
```

## Key Points

- Pino is built into Fastify -- configure level, redaction, and transports
- Redact sensitive fields (auth headers, passwords, tokens) from all logs
- Send only 5xx errors to Sentry (4xx are client errors, not bugs)
- Expose `/metrics` endpoint for Prometheus scraping
- Track both HTTP metrics (latency, error rate) and business metrics (orders, signups)
- Set alert rules on error rate, latency percentiles, and resource usage
- Use `request.id` as correlation ID across logs, metrics, and error reports
- Flush Sentry on shutdown to avoid losing error reports
