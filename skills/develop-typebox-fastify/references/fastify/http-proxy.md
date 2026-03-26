# Fastify HTTP Proxy

## @fastify/http-proxy for Simple Reverse Proxy

```typescript
import Fastify from 'fastify'
import httpProxy from '@fastify/http-proxy'
import { Type } from '@sinclair/typebox'

const app = Fastify({ logger: true })

// Proxy all /api/* requests to another service
app.register(httpProxy, {
  upstream: 'http://backend-service:3001',
  prefix: '/api',
  rewritePrefix: '/v1',
  http2: false,
})

// With authentication before proxying
app.register(httpProxy, {
  upstream: 'http://internal-api:3002',
  prefix: '/internal',
  preHandler: async (request, reply) => {
    if (!request.headers.authorization) {
      reply.code(401).send({ error: 'Unauthorized' })
    }
  },
})

await app.listen({ port: 3000 })
```

## @fastify/reply-from for Fine-Grained Control

```typescript
import Fastify from 'fastify'
import replyFrom from '@fastify/reply-from'

const app = Fastify({ logger: true })

app.register(replyFrom, {
  base: 'http://backend-service:3001',
  http2: false,
})

// Proxy with request/response manipulation
app.get('/users/:id', async (request, reply) => {
  const { id } = request.params as { id: string }

  return reply.from(`/api/users/${id}`, {
    rewriteRequestHeaders: (originalReq, headers) => ({
      ...headers,
      'x-request-id': request.id,
      'x-forwarded-for': request.ip,
    }),
    onResponse: (request, reply, res) => {
      reply.header('x-proxy', 'fastify')
      reply.send(res)
    },
  })
})
```

## Conditional Routing

```typescript
app.all('/api/*', async (request, reply) => {
  const upstream = selectUpstream(request)
  return reply.from(request.url, { base: upstream })
})

function selectUpstream(request) {
  if (request.headers['x-beta']) return 'http://beta-backend:3001'
  return 'http://stable-backend:3001'
}
```

## API Gateway Pattern

Route to multiple backend services:

```typescript
import replyFrom from '@fastify/reply-from'

const services = {
  users: 'http://users-service:3001',
  orders: 'http://orders-service:3002',
  products: 'http://products-service:3003',
}

app.register(replyFrom)

// Route to user service
app.register(async function (fastify) {
  fastify.all('/*', async (request, reply) => {
    return reply.from(request.url.replace('/users', ''), {
      base: services.users,
    })
  })
}, { prefix: '/users' })

// Route to orders service
app.register(async function (fastify) {
  fastify.all('/*', async (request, reply) => {
    return reply.from(request.url.replace('/orders', ''), {
      base: services.orders,
    })
  })
}, { prefix: '/orders' })

// Route to products service
app.register(async function (fastify) {
  fastify.all('/*', async (request, reply) => {
    return reply.from(request.url.replace('/products', ''), {
      base: services.products,
    })
  })
}, { prefix: '/products' })
```

## Request Body Forwarding

```typescript
app.post('/api/data', async (request, reply) => {
  return reply.from('/data', {
    body: request.body,
    contentType: request.headers['content-type'],
  })
})

// Stream large bodies
app.post('/upload', async (request, reply) => {
  return reply.from('/upload', {
    body: request.raw,
    contentType: request.headers['content-type'],
  })
})
```

## Error Handling

```typescript
app.register(replyFrom, {
  base: 'http://backend:3001',
  onError: (reply, error) => {
    reply.log.error({ err: error }, 'Proxy error')
    reply.code(502).send({
      error: 'Bad Gateway',
      message: 'Upstream service unavailable',
    })
  },
})

// Per-route error handling
app.get('/data', async (request, reply) => {
  try {
    return await reply.from('/data')
  } catch (error) {
    request.log.error({ err: error }, 'Failed to proxy')
    return reply.code(503).send({
      error: 'Service Unavailable',
      retryAfter: 30,
    })
  }
})
```

## WebSocket Proxying

```typescript
app.register(httpProxy, {
  upstream: 'http://ws-backend:3001',
  prefix: '/ws',
  websocket: true,
})
```

## Timeout Configuration

```typescript
app.register(replyFrom, {
  base: 'http://backend:3001',
  http: {
    requestOptions: {
      timeout: 30000, // 30 seconds
    },
  },
})
```

## Caching Proxied Responses

```typescript
import { createCache } from 'async-cache-dedupe'

const cache = createCache({
  ttl: 60,
  storage: { type: 'memory' },
})

cache.define('proxyGet', async (url: string) => {
  const response = await fetch(`http://backend:3001${url}`)
  return response.json()
})

app.get('/cached/*', {
  schema: { response: { 200: Type.Unknown() } },
}, async (request) => cache.proxyGet(request.url))
```

## Authentication Gateway

```typescript
app.register(async function gatewayRoutes(fastify) {
  // Verify JWT before proxying
  fastify.addHook('onRequest', async (request, reply) => {
    try {
      await request.jwtVerify()
    } catch {
      reply.code(401).send({ error: 'Unauthorized' })
    }
  })

  // Forward user info to upstream
  fastify.register(replyFrom, { base: 'http://backend:3001' })

  fastify.all('/*', async (request, reply) => {
    return reply.from(request.url, {
      rewriteRequestHeaders: (req, headers) => ({
        ...headers,
        'x-user-id': request.user.id,
        'x-user-role': request.user.role,
      }),
    })
  })
}, { prefix: '/api' })
```

## Service Discovery with Health Checks

```typescript
const backends = [
  { url: 'http://backend-1:3001', healthy: true },
  { url: 'http://backend-2:3001', healthy: true },
]

// Health check loop
setInterval(async () => {
  for (const backend of backends) {
    try {
      const res = await fetch(`${backend.url}/health`, { signal: AbortSignal.timeout(2000) })
      backend.healthy = res.ok
    } catch {
      backend.healthy = false
    }
  }
}, 10000)

let nextBackend = 0

function getHealthyBackend(): string {
  const healthy = backends.filter((b) => b.healthy)
  if (healthy.length === 0) throw new Error('No healthy backends')
  nextBackend = (nextBackend + 1) % healthy.length
  return healthy[nextBackend].url
}

app.all('/api/*', async (request, reply) => {
  return reply.from(request.url, { base: getHealthyBackend() })
})
```

## Key Rules

- Use `@fastify/http-proxy` for simple reverse proxy
- Use `@fastify/reply-from` when you need request/response manipulation
- Always configure timeouts for upstream services
- Handle upstream errors gracefully (return 502/503)
- Forward request IDs for distributed tracing
- Use health checks for backend discovery
