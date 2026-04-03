# Fastify Hooks and Request Lifecycle

## Request Lifecycle Order

```
Incoming Request
       |
   onRequest         — before any processing
       |
   preParsing        — before body parsing
       |
   preValidation     — after parsing, before schema validation
       |
   preHandler        — after validation, before handler
       |
     Handler         — business logic
       |
   preSerialization  — modify response object
       |
    onSend           — modify serialized payload
       |
   onResponse        — after response sent (non-blocking)
```

## onRequest

First hook. Runs before body parsing. Use for auth checks, request ID, timing:

```typescript
import { Type } from '@sinclair/typebox'

app.addHook('onRequest', async (request, reply) => {
  request.startTime = Date.now()
  request.log.info({ url: request.url, method: request.method }, 'Request started')
})

// Authentication in onRequest
app.addHook('onRequest', async (request, reply) => {
  if (request.url.startsWith('/public')) return

  const token = request.headers.authorization?.replace('Bearer ', '')
  if (!token) {
    reply.code(401).send({ error: 'Unauthorized' })
    return // stops processing
  }
  request.user = await verifyToken(token)
})
```

## preParsing

Before body parsing. Can modify the payload stream:

```typescript
import zlib from 'node:zlib'

app.addHook('preParsing', async (request, reply, payload) => {
  if (request.headers['content-encoding'] === 'gzip') {
    return payload.pipe(zlib.createGunzip())
  }
  return payload
})
```

## preValidation

After parsing, before schema validation. Normalize data here:

```typescript
app.addHook('preValidation', async (request, reply) => {
  if (request.body && typeof request.body === 'object') {
    request.body.email = request.body.email?.toLowerCase().trim()
  }
})
```

## preHandler

After validation, before handler. Most common hook for auth and data loading:

```typescript
// Authorization check
app.addHook('preHandler', async (request, reply) => {
  const { userId } = request.params as { userId: string }
  if (request.user.id !== userId && !request.user.isAdmin) {
    reply.code(403).send({ error: 'Forbidden' })
  }
})

// Load related data
app.addHook('preHandler', async (request, reply) => {
  if (request.params?.projectId) {
    request.project = await db.projects.findById(request.params.projectId)
    if (!request.project) {
      reply.code(404).send({ error: 'Project not found' })
    }
  }
})
```

## preSerialization

Modify the response object before JSON serialization:

```typescript
app.addHook('preSerialization', async (request, reply, payload) => {
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    return {
      ...payload,
      _meta: {
        requestId: request.id,
        timestamp: new Date().toISOString(),
      },
    }
  }
  return payload
})
```

## onSend

After serialization. Payload is already a string/buffer. Add response headers:

```typescript
app.addHook('onSend', async (request, reply, payload) => {
  reply.header('X-Response-Time', Date.now() - request.startTime)
  return payload
})
```

## onResponse

After response is sent. Cannot modify response. Use for metrics and logging:

```typescript
app.addHook('onResponse', async (request, reply) => {
  request.log.info({
    method: request.method,
    url: request.url,
    statusCode: reply.statusCode,
    responseTime: reply.elapsedTime,
  }, 'Request completed')
})
```

## onError

Runs when an error is thrown. For logging and cleanup:

```typescript
app.addHook('onError', async (request, reply, error) => {
  request.log.error({ err: error, url: request.url }, 'Request error')

  if (request.transaction) {
    await request.transaction.rollback()
  }
})
```

## onTimeout and onRequestAbort

```typescript
app.addHook('onTimeout', async (request, reply) => {
  request.log.warn({ url: request.url }, 'Request timeout')
  if (request.abortController) request.abortController.abort()
})

app.addHook('onRequestAbort', async (request) => {
  request.log.info('Client aborted request')
  if (request.abortController) request.abortController.abort()
})
```

## Application Lifecycle Hooks

```typescript
app.addHook('onReady', async function () {
  this.log.info('Server is ready')
  await this.db.connect()
})

app.addHook('onClose', async function () {
  this.log.info('Server is closing')
  await this.db.close()
})

app.addHook('onRoute', (routeOptions) => {
  console.log(`Route registered: ${routeOptions.method} ${routeOptions.url}`)
})

app.addHook('onRegister', (instance, options) => {
  console.log(`Plugin registered with prefix: ${options.prefix}`)
})
```

## Scoped Hooks

Hooks respect plugin encapsulation:

```typescript
app.addHook('onRequest', async (request) => {
  // Runs for ALL routes
  request.log.info('Global hook')
})

app.register(async function adminRoutes(fastify) {
  // Only runs for routes in this plugin
  fastify.addHook('onRequest', async (request, reply) => {
    if (!request.user?.isAdmin) {
      reply.code(403).send({ error: 'Admin only' })
    }
  })

  fastify.get('/admin/users', async () => ({ users: [] }))
}, { prefix: '/admin' })
```

## Route-Level Hooks

```typescript
const validateApiKey = async (request, reply) => { /* ... */ }
const loadUser = async (request, reply) => { /* ... */ }
const checkQuota = async (request, reply) => { /* ... */ }

app.post('/orders', {
  preValidation: [validateApiKey],
  preHandler: [loadUser, checkQuota],
  schema: {
    body: Type.Object({ product: Type.String(), quantity: Type.Integer() }),
    response: { 201: Type.Object({ orderId: Type.String() }) },
  },
}, async (request, reply) => {
  reply.code(201)
  return { orderId: 'order-123' }
})
```

## Hook Execution Order

Multiple hooks of the same type execute in registration order:

```typescript
app.addHook('onRequest', async () => console.log('First'))
app.addHook('onRequest', async () => console.log('Second'))
app.addHook('onRequest', async () => console.log('Third'))
// Output: First, Second, Third
```

## Important Rules

- Always use `async` hooks (never mix async with done callback)
- Return `reply.send()` or `reply.code().send()` to stop further processing
- `onResponse` and `onError` hooks cannot modify the response
- `preSerialization` receives the JS object; `onSend` receives the serialized string

## Hook Decision Guide

| Need | Hook |
|------|------|
| Logging, request ID | `onRequest` |
| Transform raw stream | `preParsing` |
| Normalize before validation | `preValidation` |
| Auth, authorization, load data | `preHandler` |
| Transform response object | `preSerialization` |
| Compression, final headers | `onSend` |
| Metrics, cleanup (non-blocking) | `onResponse` |
| Error logging | `onError` |
