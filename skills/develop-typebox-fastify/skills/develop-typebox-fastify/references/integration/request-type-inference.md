# Request Type Inference from TypeBox Schemas

## Overview

When using `@fastify/type-provider-typebox`, Fastify infers TypeScript types for
`request.params`, `request.query`, `request.body`, and `request.headers` directly
from the TypeBox schemas you provide. No manual type annotations needed.

## How Inference Works

TypeBox schemas are both runtime JSON Schema objects and TypeScript type constructors.
The type provider extracts `Static<T>` from each schema slot:

```typescript
import { Type, type Static } from '@sinclair/typebox'

const QuerySchema = Type.Object({
  search: Type.Optional(Type.String()),
  page: Type.Integer({ default: 1 })
})

// Static<typeof QuerySchema> = { search?: string; page: number }

app.get('/items', {
  schema: { querystring: QuerySchema }
}, async (request) => {
  // TypeScript knows:
  // request.query.search -> string | undefined
  // request.query.page   -> number
  const { search, page } = request.query
})
```

## Inference for Each Schema Slot

### Params

```typescript
app.get('/users/:id/posts/:postId', {
  schema: {
    params: Type.Object({
      id: Type.String({ format: 'uuid' }),
      postId: Type.Integer()
    })
  }
}, async (request) => {
  request.params.id      // string
  request.params.postId  // number
})
```

### Body

```typescript
const CreatePostBody = Type.Object({
  title: Type.String({ minLength: 1, maxLength: 200 }),
  content: Type.String(),
  tags: Type.Array(Type.String(), { maxItems: 10 }),
  draft: Type.Boolean({ default: false })
})

app.post('/posts', {
  schema: { body: CreatePostBody }
}, async (request) => {
  request.body.title   // string
  request.body.tags    // string[]
  request.body.draft   // boolean
})
```

### Headers

```typescript
app.get('/protected', {
  schema: {
    headers: Type.Object({
      authorization: Type.String(),
      'x-tenant-id': Type.Optional(Type.String())
    })
  }
}, async (request) => {
  request.headers.authorization  // string
  request.headers['x-tenant-id'] // string | undefined
})
```

### Response

Response schemas also infer the expected return type from the handler:

```typescript
app.get('/health', {
  schema: {
    response: {
      200: Type.Object({
        status: Type.Union([Type.Literal('ok'), Type.Literal('degraded')]),
        uptime: Type.Number()
      })
    }
  }
}, async () => {
  // TypeScript enforces this return shape
  return { status: 'ok' as const, uptime: process.uptime() }
})
```

## Extracting Types for External Use

Use `Static` to extract types from schemas for use outside route handlers:

```typescript
import { type Static } from '@sinclair/typebox'

const UserSchema = Type.Object({
  id: Type.String(),
  name: Type.String(),
  email: Type.String({ format: 'email' })
})

// Extract the type for use in service layers
type User = Static<typeof UserSchema>
// { id: string; name: string; email: string }

// Use in a service function
async function createUser(data: User): Promise<User> {
  // ...
}
```

## Union and Intersection Inference

```typescript
const AdminUser = Type.Intersect([
  Type.Object({ id: Type.String(), name: Type.String() }),
  Type.Object({ role: Type.Literal('admin'), permissions: Type.Array(Type.String()) })
])

type AdminUser = Static<typeof AdminUser>
// { id: string; name: string; role: 'admin'; permissions: string[] }
```

## Nullable and Optional Patterns

```typescript
const UpdateUserBody = Type.Partial(Type.Object({
  name: Type.String(),
  email: Type.String({ format: 'email' }),
  bio: Type.Union([Type.String(), Type.Null()])
}))

type UpdateUserBody = Static<typeof UpdateUserBody>
// { name?: string; email?: string; bio?: string | null }
```

## Generic Route Factories

Create typed route factories that preserve inference:

```typescript
import { TSchema, type Static } from '@sinclair/typebox'
import { FastifyInstance } from 'fastify'

function createGetById<T extends TSchema>(
  app: FastifyInstance,
  path: string,
  responseSchema: T,
  fetcher: (id: string) => Promise<Static<T> | null>
) {
  app.get(path, {
    schema: {
      params: Type.Object({ id: Type.String() }),
      response: { 200: responseSchema }
    }
  }, async (request, reply) => {
    const result = await fetcher((request.params as { id: string }).id)
    if (!result) { reply.status(404); return { error: 'Not found' } }
    return result
  })
}
```

## Key Points

- Inference is automatic when `withTypeProvider<TypeBoxTypeProvider>()` is applied
- Use `Static<typeof Schema>` to extract types for service layers
- `Type.Optional()` infers `T | undefined`
- `Type.Union([Type.String(), Type.Null()])` infers `string | null`
- Response schemas infer the handler return type for each status code
- All inference is compile-time only -- zero runtime overhead
