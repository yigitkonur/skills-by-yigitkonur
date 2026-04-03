# Route Schemas with TypeBox

## Overview

Fastify routes accept a `schema` object with keys for `params`, `querystring`, `body`,
`headers`, and `response`. TypeBox schemas in each slot give you validation + type inference.

## Params Schema

```typescript
import { Type } from '@sinclair/typebox'

app.get('/users/:id', {
  schema: {
    params: Type.Object({
      id: Type.String({ format: 'uuid' })
    })
  }
}, async (request) => {
  const { id } = request.params // string
  return { id }
})
```

## Querystring Schema

```typescript
const PaginationQuery = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1 }),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
  search: Type.Optional(Type.String({ minLength: 1 })),
  sort: Type.Optional(Type.Union([
    Type.Literal('name'),
    Type.Literal('createdAt'),
    Type.Literal('updatedAt')
  ]))
})

app.get('/users', {
  schema: { querystring: PaginationQuery }
}, async (request) => {
  const { page, limit, search, sort } = request.query
  // page: number, limit: number, search: string | undefined
})
```

## Body Schema

```typescript
const CreateUserBody = Type.Object({
  name: Type.String({ minLength: 2, maxLength: 100 }),
  email: Type.String({ format: 'email' }),
  role: Type.Union([Type.Literal('admin'), Type.Literal('user')]),
  metadata: Type.Optional(Type.Record(Type.String(), Type.Unknown()))
})

app.post('/users', {
  schema: { body: CreateUserBody }
}, async (request, reply) => {
  const { name, email, role } = request.body
  // All typed, all validated before handler runs
  reply.status(201)
  return { id: 'new-id', name, email, role }
})
```

## Headers Schema

```typescript
const AuthHeaders = Type.Object({
  'x-api-key': Type.String({ minLength: 32 }),
  'x-request-id': Type.Optional(Type.String({ format: 'uuid' }))
})

app.get('/protected', {
  schema: { headers: AuthHeaders }
}, async (request) => {
  const apiKey = request.headers['x-api-key'] // string
})
```

## Response Schema

Response schemas serve two purposes: type-checking your handler return value and
serializing the response via fast-json-stringify (stripping unknown fields).

```typescript
const UserResponse = Type.Object({
  id: Type.String(),
  name: Type.String(),
  email: Type.String(),
  createdAt: Type.String({ format: 'date-time' })
})

const ErrorResponse = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String()
})

app.get('/users/:id', {
  schema: {
    params: Type.Object({ id: Type.String() }),
    response: {
      200: UserResponse,
      404: ErrorResponse,
      500: ErrorResponse
    }
  }
}, async (request, reply) => {
  const user = await findUser(request.params.id)
  if (!user) {
    reply.status(404)
    return { statusCode: 404, error: 'Not Found', message: 'User not found' }
  }
  return user // Must match UserResponse shape
})
```

## Complete Route Example

```typescript
const CreateOrderSchema = {
  params: Type.Object({
    userId: Type.String({ format: 'uuid' })
  }),
  querystring: Type.Object({
    dryRun: Type.Optional(Type.Boolean({ default: false }))
  }),
  body: Type.Object({
    items: Type.Array(Type.Object({
      productId: Type.String(),
      quantity: Type.Integer({ minimum: 1 })
    }), { minItems: 1 }),
    shippingAddress: Type.Object({
      street: Type.String(),
      city: Type.String(),
      zip: Type.String()
    })
  }),
  response: {
    201: Type.Object({
      orderId: Type.String(),
      total: Type.Number(),
      status: Type.Literal('pending')
    })
  }
} as const

app.post('/users/:userId/orders', {
  schema: CreateOrderSchema
}, async (request, reply) => {
  const { userId } = request.params
  const { items, shippingAddress } = request.body
  const { dryRun } = request.query
  reply.status(201)
  return { orderId: 'ord-123', total: 59.99, status: 'pending' as const }
})
```

## Key Points

- Define schemas as `const` objects or standalone variables for reuse
- `Type.Optional()` makes a field optional in both validation and types
- `default` values in schemas are applied during validation if the field is missing
- Response schemas strip any extra fields not defined in the schema
- Use `Type.Ref()` for shared sub-schemas registered with `addSchema()`
