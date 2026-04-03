# Production Checklist

## Overview

Before deploying a Fastify + TypeBox API to production, verify every item on this checklist.
Each item addresses a real failure mode observed in production systems.

## Security

```typescript
// 1. Helmet security headers
import helmet from '@fastify/helmet'
await app.register(helmet, {
  contentSecurityPolicy: false, // For APIs
  strictTransportSecurity: { maxAge: 31536000, includeSubDomains: true }
})

// 2. Rate limiting with Redis
import rateLimit from '@fastify/rate-limit'
await app.register(rateLimit, {
  max: 100,
  timeWindow: '1 minute',
  redis: redisClient // Multi-instance safe
})

// 3. CORS with explicit origins
import cors from '@fastify/cors'
await app.register(cors, {
  origin: ['https://app.example.com'],
  credentials: true
})

// 4. Request size limits
const app = Fastify({
  bodyLimit: 1_048_576, // 1MB max body
  maxParamLength: 200
})
```

**Checklist:**
- [ ] Helmet registered with appropriate CSP
- [ ] Rate limiting enabled with Redis backend
- [ ] CORS configured with specific origins (no wildcard)
- [ ] Body size limit set (default 1MB, adjust if needed)
- [ ] JWT secrets are 32+ characters from secrets manager
- [ ] No sensitive data in error responses (500s return generic messages)
- [ ] API keys and tokens validated on every protected route
- [ ] SQL injection prevented (parameterized queries via ORM)

## Performance

```typescript
// 5. Response schemas for fast-json-stringify
app.get('/users', {
  schema: {
    response: {
      200: Type.Array(UserSchema) // Enables fast serialization
    }
  }
}, handler)

// 6. Connection pooling
const pool = postgres(DATABASE_URL, {
  max: 20,           // Max connections
  idle_timeout: 30,  // Close idle connections after 30s
  connect_timeout: 5 // Fail fast on connection timeout
})

// 7. TypeBox validator compiler (faster than Ajv)
import { TypeBoxValidatorCompiler } from '@fastify/type-provider-typebox'
app.setValidatorCompiler(TypeBoxValidatorCompiler)
```

**Checklist:**
- [ ] Response schemas defined on all routes (enables fast-json-stringify)
- [ ] TypeBoxValidatorCompiler set for faster validation
- [ ] Database connection pooling configured
- [ ] Redis connection pooling configured
- [ ] Compression enabled (`@fastify/compress`)
- [ ] No N+1 queries (use `include`/`join` appropriately)
- [ ] Pagination enforced on list endpoints (max 100 items)

## Reliability

```typescript
// 8. Graceful shutdown
import closeWithGrace from 'close-with-grace'

closeWithGrace({ delay: 10_000 }, async ({ signal, err }) => {
  if (err) app.log.error(err)
  await app.close()
})

// 9. Health checks
app.get('/health/live', handler)  // Liveness
app.get('/health/ready', handler) // Readiness (checks dependencies)

// 10. Structured logging
const app = Fastify({
  logger: {
    level: process.env.LOG_LEVEL ?? 'info',
    // Pino transports for production
    transport: process.env.NODE_ENV === 'production'
      ? undefined // Use pino-pretty only in dev
      : { target: 'pino-pretty' }
  }
})
```

**Checklist:**
- [ ] Graceful shutdown with `close-with-grace` (10-30s timeout)
- [ ] Liveness and readiness health check endpoints
- [ ] `onClose` hooks for all connections (DB, Redis, external services)
- [ ] Host set to `0.0.0.0` (required for containers)
- [ ] Structured JSON logging in production (no pino-pretty)
- [ ] Error handler catches all errors and logs them
- [ ] Process manager or container orchestrator for restarts

## Configuration

```typescript
// 11. Validate all config at startup
import fastifyEnv from '@fastify/env'

await app.register(fastifyEnv, {
  schema: ConfigSchema, // TypeBox schema
  dotenv: false         // Use real env vars in production
})
```

**Checklist:**
- [ ] All environment variables validated at startup
- [ ] Secrets loaded from secrets manager (not .env files)
- [ ] NODE_ENV set to "production"
- [ ] Database migrations run before deployment (not at startup)
- [ ] `.env` files not in Docker image or version control

## Observability

**Checklist:**
- [ ] Request IDs (correlation IDs) in all log lines
- [ ] Request duration logged for every response
- [ ] Error tracking (Sentry or equivalent) configured
- [ ] Metrics endpoint or push-based metrics
- [ ] Alert rules for error rate spikes and latency
- [ ] Log aggregation (ELK, Datadog, etc.)

## Deployment

**Checklist:**
- [ ] Docker image uses multi-stage build (small final image)
- [ ] Running as non-root user in container
- [ ] `CMD ["node", "dist/server.js"]` (exec form for signals)
- [ ] Memory and CPU limits set on container
- [ ] Horizontal scaling tested (stateless API, Redis for state)
- [ ] Database connection limit accounts for replica count
- [ ] TLS termination at load balancer
- [ ] CI/CD pipeline runs tests before deployment
- [ ] Rollback strategy documented and tested

## API Quality

**Checklist:**
- [ ] OpenAPI spec generated and validated
- [ ] All routes have TypeBox schemas for params, body, and response
- [ ] Error responses follow consistent format
- [ ] API versioning strategy in place
- [ ] Deprecation headers on old endpoints
- [ ] Client SDK generated from OpenAPI spec (if applicable)

## Key Points

- Fail fast: validate config and connections at startup, not at first request
- Defense in depth: helmet + CORS + rate limiting + auth + input validation
- Every response schema enables fast-json-stringify (performance) and field stripping (security)
- Structured logging with correlation IDs is non-negotiable for debugging
- Test graceful shutdown: `kill -SIGTERM <pid>` and verify in-flight requests complete
