# Fastify Routes

## Basic Route with TypeBox

```typescript
import { Type, type Static } from '@sinclair/typebox'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import Fastify from 'fastify'

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()

const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
})

app.get('/users', {
  schema: {
    response: { 200: Type.Array(UserSchema) },
  },
}, async () => {
  return [{ id: '...', name: 'John', email: 'john@example.com' }]
})
```

## Params, Query, Body, Headers

```typescript
const CreateUserBody = Type.Object({
  name: Type.String({ minLength: 1, maxLength: 100 }),
  email: Type.String({ format: 'email' }),
  age: Type.Optional(Type.Integer({ minimum: 0 })),
})

const UserParams = Type.Object({
  id: Type.String({ format: 'uuid' }),
})

const PaginationQuery = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1 }),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
  sort: Type.Optional(Type.String()),
})

const ApiKeyHeaders = Type.Object({
  'x-api-key': Type.String({ minLength: 32 }),
})

// GET with params + query
app.get('/users/:id', {
  schema: {
    params: UserParams,
    querystring: Type.Object({
      include: Type.Optional(Type.Union([
        Type.Literal('posts'),
        Type.Literal('comments'),
      ])),
    }),
    response: { 200: UserSchema },
  },
}, async (request) => {
  const { id } = request.params        // typed: { id: string }
  const { include } = request.query    // typed: 'posts' | 'comments' | undefined
  return { id, name: 'John', email: 'john@example.com' }
})

// POST with body + headers
app.post('/users', {
  schema: {
    headers: ApiKeyHeaders,
    body: CreateUserBody,
    response: { 201: UserSchema },
  },
}, async (request, reply) => {
  const { name, email } = request.body  // typed: { name: string; email: string; age?: number }
  reply.code(201)
  return { id: 'generated', name, email }
})
```

## Full Route Method

```typescript
app.route({
  method: 'PUT',
  url: '/users/:id',
  schema: {
    params: UserParams,
    body: Type.Object({
      name: Type.Optional(Type.String()),
      email: Type.Optional(Type.String({ format: 'email' })),
    }),
    response: { 200: UserSchema },
  },
  handler: async (request, reply) => {
    const { id } = request.params
    return { id, ...request.body, email: request.body.email ?? '' }
  },
})
```

## Route Constraints (Versioning)

```typescript
app.get('/users', {
  constraints: { version: '1.0.0' },
  schema: { response: { 200: Type.Array(UserSchema) } },
}, async () => {
  return [{ id: '1', name: 'v1', email: 'v1@example.com' }]
})

app.get('/users', {
  constraints: { version: '2.0.0' },
  schema: {
    response: {
      200: Type.Object({
        data: Type.Array(UserSchema),
        meta: Type.Object({ total: Type.Integer() }),
      }),
    },
  },
}, async () => {
  return { data: [], meta: { total: 0 } }
})
// Client sends Accept-Version: 2.0.0
```

## Route Prefixing with Register

```typescript
app.register(async function userRoutes(fastify) {
  const app = fastify.withTypeProvider<TypeBoxTypeProvider>()

  app.get('/', {
    schema: { response: { 200: Type.Array(UserSchema) } },
  }, async () => [])

  app.get('/:id', {
    schema: {
      params: UserParams,
      response: { 200: UserSchema },
    },
  }, async (request) => {
    return { id: request.params.id, name: 'User', email: 'user@example.com' }
  })
}, { prefix: '/api/v1/users' })
// Results in: GET /api/v1/users and GET /api/v1/users/:id
```

## Multiple HTTP Methods

```typescript
app.route({
  method: ['GET', 'HEAD'],
  url: '/resource',
  schema: {
    response: { 200: Type.Object({ data: Type.String() }) },
  },
  handler: async () => ({ data: 'resource' }),
})
```

## 404 Not Found Handler

```typescript
app.setNotFoundHandler(async (request, reply) => {
  reply.code(404)
  return {
    statusCode: 404,
    error: 'Not Found',
    message: `Route ${request.method} ${request.url} not found`,
  }
})
```

## Route Organization by Feature

```
src/
  routes/
    users/
      index.ts       # Route definitions
      schemas.ts     # TypeBox schemas
    posts/
      index.ts
      schemas.ts
```

```typescript
// routes/users/schemas.ts
import { Type } from '@sinclair/typebox'

export const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
})

export const CreateUserSchema = Type.Object({
  name: Type.String({ minLength: 1 }),
  email: Type.String({ format: 'email' }),
})

// routes/users/index.ts
import type { FastifyPluginAsync } from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { UserSchema, CreateUserSchema } from './schemas.js'

const userRoutes: FastifyPluginAsync = async (fastify) => {
  const app = fastify.withTypeProvider<TypeBoxTypeProvider>()

  app.get('/', {
    schema: { response: { 200: Type.Array(UserSchema) } },
  }, async () => fastify.db.users.findAll())

  app.post('/', {
    schema: {
      body: CreateUserSchema,
      response: { 201: UserSchema },
    },
  }, async (request, reply) => {
    reply.code(201)
    return fastify.db.users.create(request.body)
  })
}

export default userRoutes
```

## Route-Level Hooks

```typescript
const adminOnly = async (request, reply) => {
  if (request.user?.role !== 'admin') {
    reply.code(403).send({ error: 'Forbidden' })
  }
}

app.get('/admin/settings', {
  preHandler: [adminOnly],
  schema: {
    response: { 200: Type.Object({ settings: Type.Unknown() }) },
  },
}, async () => ({ settings: {} }))
```

## Route-Level Config

```typescript
app.get('/slow', {
  config: {
    rateLimit: { max: 10, timeWindow: '1 minute' },
  },
  schema: {
    response: { 200: Type.Object({ result: Type.String() }) },
  },
}, async () => ({ result: 'done' }))
```
