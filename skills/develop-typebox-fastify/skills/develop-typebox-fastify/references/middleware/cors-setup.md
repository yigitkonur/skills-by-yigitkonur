# CORS Configuration with @fastify/cors

## Overview

`@fastify/cors` handles Cross-Origin Resource Sharing headers for your Fastify API.
Required when frontend and backend are on different origins (different domain, port, or protocol).

## Installation

```bash
npm install @fastify/cors
```

## Basic Setup

```typescript
import Fastify from 'fastify'
import cors from '@fastify/cors'

const app = Fastify()

await app.register(cors, {
  origin: true // Allow all origins (development only!)
})
```

## Production Configuration

```typescript
await app.register(cors, {
  // Specific allowed origins
  origin: [
    'https://app.example.com',
    'https://admin.example.com',
    /\.example\.com$/  // Regex for subdomains
  ],

  // Allowed HTTP methods
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],

  // Headers the client can send
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Request-Id',
    'X-API-Key'
  ],

  // Headers the client can read from responses
  exposedHeaders: [
    'X-Total-Count',
    'X-RateLimit-Remaining',
    'X-Request-Id'
  ],

  // Allow cookies/auth headers
  credentials: true,

  // Cache preflight response for 24 hours
  maxAge: 86400,

  // Respond to preflight with 204 (no content)
  optionsSuccessStatus: 204
})
```

## Dynamic Origin Based on Environment

```typescript
import { Type, type Static } from '@sinclair/typebox'

const EnvSchema = Type.Object({
  NODE_ENV: Type.Union([
    Type.Literal('development'),
    Type.Literal('staging'),
    Type.Literal('production')
  ]),
  CORS_ORIGINS: Type.String({ description: 'Comma-separated allowed origins' })
})

await app.register(cors, {
  origin: (origin, callback) => {
    const allowedOrigins = process.env.CORS_ORIGINS?.split(',') ?? []

    // Allow requests with no origin (server-to-server, curl, mobile apps)
    if (!origin) return callback(null, true)

    // Development: allow all localhost
    if (process.env.NODE_ENV === 'development') {
      if (origin.startsWith('http://localhost')) {
        return callback(null, true)
      }
    }

    // Check against allowed list
    if (allowedOrigins.includes(origin)) {
      return callback(null, true)
    }

    callback(new Error('Not allowed by CORS'), false)
  },
  credentials: true
})
```

## Per-Route CORS Override

```typescript
// Specific route with different CORS policy
app.get('/public/data', {
  config: {
    cors: {
      origin: '*',         // Public endpoint -- allow all
      credentials: false
    }
  }
}, async () => {
  return { public: true }
})
```

## CORS with Fastify Hooks

For fine-grained control, use hooks instead of the plugin:

```typescript
app.addHook('onRequest', async (request, reply) => {
  const origin = request.headers.origin

  if (origin && isAllowedOrigin(origin)) {
    reply.header('Access-Control-Allow-Origin', origin)
    reply.header('Access-Control-Allow-Credentials', 'true')
  }

  // Handle preflight
  if (request.method === 'OPTIONS') {
    reply.header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE')
    reply.header('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    reply.header('Access-Control-Max-Age', '86400')
    reply.status(204).send()
  }
})
```

## Common Mistakes

```typescript
// BAD: origin: '*' with credentials: true -- browsers reject this
await app.register(cors, {
  origin: '*',
  credentials: true // This combination is INVALID
})

// GOOD: Specify exact origins when using credentials
await app.register(cors, {
  origin: ['https://app.example.com'],
  credentials: true
})

// BAD: Forgetting to expose custom headers
// Frontend cannot read X-Total-Count without this:
await app.register(cors, {
  origin: true,
  exposedHeaders: ['X-Total-Count'] // Required for frontend access
})
```

## Key Points

- Never use `origin: '*'` in production -- specify exact origins
- `credentials: true` requires explicit origins (not wildcard)
- Expose custom headers with `exposedHeaders` or browsers hide them
- Set `maxAge` to reduce preflight requests (OPTIONS)
- Register CORS before routes so preflight requests are handled
- Use dynamic origin callback for environment-based configuration
- Allow `null` origin for server-to-server and mobile requests
