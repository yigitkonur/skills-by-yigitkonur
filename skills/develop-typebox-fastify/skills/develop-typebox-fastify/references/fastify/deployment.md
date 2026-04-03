# Fastify Deployment

## Graceful Shutdown with close-with-grace

```typescript
import Fastify from 'fastify'
import closeWithGrace from 'close-with-grace'
import { Type } from '@sinclair/typebox'

const app = Fastify({ logger: true })

await app.register(import('./plugins/index.js'))
await app.register(import('./routes/index.js'))

closeWithGrace({ delay: 10000 }, async ({ signal, err }) => {
  if (err) {
    app.log.error({ err }, 'Server closing due to error')
  } else {
    app.log.info({ signal }, 'Server closing due to signal')
  }
  await app.close()
})

await app.listen({
  port: parseInt(process.env.PORT || '3000', 10),
  host: '0.0.0.0',
})
```

## Health Check Endpoints

```typescript
app.get('/health', {
  schema: {
    response: {
      200: Type.Object({
        status: Type.String(),
        timestamp: Type.String({ format: 'date-time' }),
      }),
    },
  },
}, async () => ({ status: 'ok', timestamp: new Date().toISOString() }))

app.get('/health/live', async () => ({ status: 'ok' }))

app.get('/health/ready', {
  schema: {
    response: {
      200: Type.Object({
        status: Type.Union([Type.Literal('ok'), Type.Literal('degraded')]),
        checks: Type.Object({
          database: Type.Boolean(),
          cache: Type.Boolean(),
        }),
      }),
    },
  },
}, async (request, reply) => {
  const checks = { database: false, cache: false }

  try { await app.pg.query('SELECT 1'); checks.database = true } catch {}
  try { await app.redis.ping(); checks.cache = true } catch {}

  const allHealthy = Object.values(checks).every(Boolean)
  if (!allHealthy) reply.code(503)

  return { status: allHealthy ? 'ok' : 'degraded', checks }
})
```

## Docker Configuration

```dockerfile
# Build stage
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

# Production stage
FROM node:22-alpine
WORKDIR /app

RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001

COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/src ./src
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

USER nodejs
EXPOSE 3000

ENV NODE_ENV=production
ENV PORT=3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "src/server.ts"]
```

## Docker Compose

```yaml
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://user:pass@db:5432/app
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=app
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastify-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastify-api
  template:
    metadata:
      labels:
        app: fastify-api
    spec:
      containers:
        - name: api
          image: my-registry/fastify-api:latest
          ports:
            - containerPort: 3000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: api-secrets
                  key: database-url
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health/live
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]
```

## Production Logger Configuration

```typescript
const app = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
    formatters: {
      level: (label) => ({ level: label }),
      bindings: (bindings) => ({
        pid: bindings.pid,
        hostname: bindings.hostname,
        service: 'fastify-api',
        version: process.env.APP_VERSION,
      }),
    },
    timestamp: () => `,"time":"${new Date().toISOString()}"`,
    redact: {
      paths: ['req.headers.authorization', 'req.headers.cookie', '*.password', '*.token'],
      censor: '[REDACTED]',
    },
  },
})
```

## Production Timeouts

```typescript
const app = Fastify({
  connectionTimeout: 30000,
  keepAliveTimeout: 72000,  // longer than ALB 60s
  requestTimeout: 30000,
  bodyLimit: 1048576,
  trustProxy: true,
})
```

## Prometheus Metrics

```typescript
import { register, collectDefaultMetrics, Counter, Histogram } from 'prom-client'

collectDefaultMetrics()

const httpDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests',
  labelNames: ['method', 'route', 'status'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 5],
})

const httpTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status'],
})

app.addHook('onResponse', (request, reply, done) => {
  const labels = {
    method: request.method,
    route: request.routeOptions.url || request.url,
    status: reply.statusCode,
  }
  httpDuration.observe(labels, reply.elapsedTime / 1000)
  httpTotal.inc(labels)
  done()
})

app.get('/metrics', async (request, reply) => {
  reply.header('Content-Type', register.contentType)
  return register.metrics()
})
```

## Static File Serving

```typescript
import fastifyStatic from '@fastify/static'
import { join } from 'node:path'

app.register(fastifyStatic, {
  root: join(import.meta.dirname, '..', 'public'),
  prefix: '/static/',
  maxAge: '1d',
  immutable: true,
  etag: true,
  lastModified: true,
})
```

## Compression

```typescript
import fastifyCompress from '@fastify/compress'

app.register(fastifyCompress, {
  global: true,
  threshold: 1024,
  encodings: ['gzip', 'deflate'],
})
```

## Zero-Downtime Rolling Updates

```typescript
closeWithGrace({ delay: 30000 }, async ({ signal }) => {
  app.log.info({ signal }, 'Received shutdown signal')
  // Stop accepting new connections; existing connections continue
  await app.close()
  app.log.info('Server closed')
})
```

## Checklist Before Deploying

- [ ] close-with-grace configured
- [ ] Health endpoints (/health, /health/live, /health/ready)
- [ ] Logger configured for production (JSON, redact secrets)
- [ ] trustProxy enabled for reverse proxy
- [ ] Body limits set
- [ ] Timeouts configured
- [ ] onClose hooks for cleanup (db, redis, connections)
- [ ] Response schemas defined on all routes
- [ ] Error handler configured
- [ ] No sensitive data in error responses
- [ ] Compression enabled
- [ ] Metrics endpoint for monitoring
