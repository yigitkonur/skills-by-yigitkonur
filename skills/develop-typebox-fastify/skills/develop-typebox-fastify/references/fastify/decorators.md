# Fastify Decorators

## Three Decorator Types

```typescript
import Fastify from 'fastify'

const app = Fastify()

// Instance decorator - on fastify instance (services, config)
app.decorate('config', { apiVersion: '1.0.0' })
app.decorate('db', databaseConnection)

// Request decorator - on each request object
app.decorateRequest('user', null)
app.decorateRequest('startTime', 0)

// Reply decorator - on each reply object
app.decorateReply('sendError', function (code: number, message: string) {
  return this.code(code).send({ error: message })
})
```

## CRITICAL: Never Use Reference Types as Initial Values

Reference types (objects, arrays) are shared across ALL requests. Mutations persist and accumulate:

```typescript
// WRONG: Shared mutable state across requests
app.decorateRequest('userData', { name: '', permissions: [] })
app.addHook('preHandler', async (request) => {
  request.userData.name = 'John'           // MUTATES SHARED OBJECT
  request.userData.permissions.push('read') // ACCUMULATES ACROSS REQUESTS
})

// CORRECT: Use null and initialize per-request in a hook
app.decorateRequest('userData', null)
app.addHook('preHandler', async (request) => {
  request.userData = { name: 'John', permissions: ['read'] }
})

// Primitives (number, string, boolean) are safe as defaults
app.decorateRequest('startTime', 0)
app.addHook('onRequest', async (request) => {
  request.startTime = Date.now()
})
```

## TypeScript Declaration Merging

```typescript
declare module 'fastify' {
  interface FastifyInstance {
    config: {
      apiVersion: string
      environment: string
    }
    db: DatabaseClient
    cache: CacheClient
  }

  interface FastifyRequest {
    user: { id: string; email: string; role: string } | null
    startTime: number
    requestId: string
  }

  interface FastifyReply {
    sendError: (code: number, message: string) => void
    success: (data: unknown) => void
  }
}

// Register decorators
app.decorate('config', { apiVersion: '1.0.0', environment: process.env.NODE_ENV })
app.decorateRequest('user', null)
app.decorateRequest('startTime', 0)
app.decorateReply('sendError', function (code, message) {
  this.code(code).send({ error: message })
})
```

## Dependency Injection Pattern

```typescript
import fp from 'fastify-plugin'

// Database plugin
export default fp(async function databasePlugin(fastify, options) {
  const db = await createDatabaseConnection(options.connectionString)
  fastify.decorate('db', db)
  fastify.addHook('onClose', async () => { await db.close() })
})

// User service plugin - depends on db
export default fp(async function userServicePlugin(fastify) {
  if (!fastify.hasDecorator('db')) {
    throw new Error('Database plugin must be registered first')
  }

  const userService = {
    findById: (id: string) => fastify.db.query('SELECT * FROM users WHERE id = $1', [id]),
    create: (data) => fastify.db.query('INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *', [data.name, data.email]),
  }

  fastify.decorate('userService', userService)
}, {
  dependencies: ['database-plugin'],
})
```

## Request Context Pattern

Build a rich per-request context:

```typescript
import { Type } from '@sinclair/typebox'

interface RequestContext {
  traceId: string
  user: User | null
  permissions: Set<string>
  startTime: number
}

declare module 'fastify' {
  interface FastifyRequest {
    ctx: RequestContext
  }
}

app.decorateRequest('ctx', null) // null = will be set per-request

app.addHook('onRequest', async (request) => {
  request.ctx = {
    traceId: request.headers['x-trace-id']?.toString() || crypto.randomUUID(),
    user: null,
    permissions: new Set(),
    startTime: Date.now(),
  }
})

app.addHook('preHandler', async (request) => {
  const token = request.headers.authorization
  if (token) {
    const user = await verifyToken(token)
    request.ctx.user = user
    request.ctx.permissions = new Set(user.permissions)
  }
})

app.get('/profile', {
  schema: { response: { 200: Type.Object({ id: Type.String(), email: Type.String() }) } },
}, async (request, reply) => {
  if (!request.ctx.user) return reply.code(401).send({ error: 'Unauthorized' })
  if (!request.ctx.permissions.has('read:profile')) return reply.code(403).send({ error: 'Forbidden' })
  return request.ctx.user
})
```

## Reply Helpers

```typescript
declare module 'fastify' {
  interface FastifyReply {
    ok: (data?: unknown) => void
    created: (data: unknown) => void
    noContent: () => void
    notFound: (resource?: string) => void
  }
}

app.decorateReply('ok', function (data) {
  this.code(200).send(data ?? { success: true })
})

app.decorateReply('created', function (data) {
  this.code(201).send(data)
})

app.decorateReply('noContent', function () {
  this.code(204).send()
})

app.decorateReply('notFound', function (resource = 'Resource') {
  this.code(404).send({ statusCode: 404, error: 'Not Found', message: `${resource} not found` })
})

// Usage
app.get('/users/:id', async (request, reply) => {
  const user = await db.users.findById(request.params.id)
  if (!user) return reply.notFound('User')
  return reply.ok(user)
})
```

## Checking Decorator Existence

```typescript
app.register(async function (fastify) {
  if (!fastify.hasDecorator('db')) throw new Error('Database decorator required')
  if (!fastify.hasRequestDecorator('user')) throw new Error('User request decorator required')
  if (!fastify.hasReplyDecorator('sendError')) throw new Error('sendError reply decorator required')
})
```

## Decorator Encapsulation

Decorators respect plugin encapsulation by default:

```typescript
app.register(async function pluginA(fastify) {
  fastify.decorate('pluginAUtil', () => 'A')
  // Only available inside pluginA and its children
})

app.register(async function pluginB(fastify) {
  // fastify.pluginAUtil is undefined here (encapsulated)
})

// Use fastify-plugin to share decorators with parent/siblings
```

## Decorator vs Hook Decision

| Need | Use |
|------|-----|
| Utility/service available to all requests | `decorate()` on FastifyInstance |
| Per-request state | `decorateRequest()` + hook to populate |
| Response helper methods | `decorateReply()` |
| Cross-cutting behavior (auth, logging) | `addHook()` |
| One-time setup | Run in plugin registration function |
