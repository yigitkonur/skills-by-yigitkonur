# Rate Limiting with @fastify/rate-limit

## Overview

Rate limiting is REQUIRED for production APIs. `@fastify/rate-limit` provides per-route
or global rate limiting with Redis-backed storage for multi-instance deployments.

## Installation

```bash
npm install @fastify/rate-limit
# For production (multi-instance):
npm install ioredis
```

## Basic Setup

```typescript
import Fastify from 'fastify'
import rateLimit from '@fastify/rate-limit'

const app = Fastify()

await app.register(rateLimit, {
  max: 100,            // 100 requests
  timeWindow: '1 minute', // per minute
  ban: 3               // After 3 limit violations, ban for the rest of the window
})
```

## Redis-Backed Rate Limiting (Production)

In-memory rate limiting only works for single instances. Use Redis for production:

```typescript
import rateLimit from '@fastify/rate-limit'
import Redis from 'ioredis'

const redis = new Redis({
  host: process.env.REDIS_HOST ?? 'localhost',
  port: Number(process.env.REDIS_PORT ?? 6379),
  password: process.env.REDIS_PASSWORD,
  maxRetriesPerRequest: 3,
  enableReadyCheck: true
})

await app.register(rateLimit, {
  max: 100,
  timeWindow: '1 minute',
  redis,
  // Identify users by API key header, falling back to IP
  keyGenerator: (request) => {
    return request.headers['x-api-key'] as string ?? request.ip
  },
  // Custom error response
  errorResponseBuilder: (request, context) => ({
    statusCode: 429,
    error: 'Too Many Requests',
    message: `Rate limit exceeded. Retry in ${context.after}`,
    retryAfter: context.after
  })
})
```

## Per-Route Rate Limits

Override global limits on specific routes:

```typescript
import { Type } from '@sinclair/typebox'

// Strict limit on auth endpoints
app.post('/auth/login', {
  config: {
    rateLimit: {
      max: 5,
      timeWindow: '15 minutes'
    }
  },
  schema: {
    body: Type.Object({
      email: Type.String({ format: 'email' }),
      password: Type.String()
    })
  }
}, async (request) => {
  // Login logic
})

// Higher limit for read-heavy endpoints
app.get('/products', {
  config: {
    rateLimit: {
      max: 500,
      timeWindow: '1 minute'
    }
  },
  schema: {
    querystring: Type.Object({
      category: Type.Optional(Type.String())
    })
  }
}, async (request) => {
  // Product listing
})

// Disable rate limiting for health checks
app.get('/health', {
  config: { rateLimit: false }
}, async () => {
  return { status: 'ok' }
})
```

## Tiered Rate Limits by User Role

```typescript
await app.register(rateLimit, {
  max: async (request, key) => {
    // Check user tier from JWT or API key
    const user = request.user
    if (!user) return 30     // Anonymous: 30/min
    switch (user.tier) {
      case 'free': return 100
      case 'pro': return 1000
      case 'enterprise': return 10000
      default: return 100
    }
  },
  timeWindow: '1 minute',
  redis,
  keyGenerator: (request) => {
    return request.user?.id ?? request.ip
  }
})
```

## Response Headers

Rate limit info is automatically included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
Retry-After: 30  (only on 429 responses)
```

Customize headers:

```typescript
await app.register(rateLimit, {
  max: 100,
  timeWindow: '1 minute',
  addHeadersOnExceeding: {
    'x-ratelimit-limit': true,
    'x-ratelimit-remaining': true,
    'x-ratelimit-reset': true
  },
  addHeaders: {
    'x-ratelimit-limit': true,
    'x-ratelimit-remaining': true,
    'x-ratelimit-reset': true,
    'retry-after': true
  }
})
```

## TypeBox Schema for Rate Limit Errors

```typescript
const RateLimitErrorSchema = Type.Object({
  statusCode: Type.Literal(429),
  error: Type.Literal('Too Many Requests'),
  message: Type.String(),
  retryAfter: Type.String()
})

// Add to route response schemas
app.post('/api/expensive', {
  schema: {
    response: {
      200: SuccessSchema,
      429: RateLimitErrorSchema
    }
  }
}, handler)
```

## Key Points

- ALWAYS use rate limiting in production -- no exceptions
- Use Redis storage for multi-instance deployments
- Set stricter limits on auth endpoints (login, register, password reset)
- Use `keyGenerator` to rate-limit by API key or user ID, not just IP
- Disable rate limiting only for health check endpoints
- Return `Retry-After` header to help clients back off correctly
- Tier rate limits by user plan for SaaS applications
