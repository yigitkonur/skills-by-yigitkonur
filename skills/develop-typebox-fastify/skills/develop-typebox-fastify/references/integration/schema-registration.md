# Schema Registration with addSchema and $ref

## Overview

Fastify's `addSchema()` lets you register reusable TypeBox schemas that can be referenced
via `$ref` across routes. This avoids schema duplication and enables shared definitions
in OpenAPI output.

## Defining Schemas with $id

```typescript
import { Type, type Static } from '@sinclair/typebox'

// Give each schema a unique $id for referencing
const AddressSchema = Type.Object({
  street: Type.String(),
  city: Type.String(),
  state: Type.String({ minLength: 2, maxLength: 2 }),
  zip: Type.String({ pattern: '^\\d{5}(-\\d{4})?$' })
}, { $id: 'Address' })

const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
  address: Type.Ref(AddressSchema),
  createdAt: Type.String({ format: 'date-time' })
}, { $id: 'User' })

type User = Static<typeof UserSchema>
```

## Registering Schemas

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()

// Register shared schemas before routes
app.addSchema(AddressSchema)
app.addSchema(UserSchema)
```

## Using $ref in Routes

Once registered, you can reference schemas by their $id using `Type.Ref()`:

```typescript
app.post('/users', {
  schema: {
    body: Type.Object({
      name: Type.String(),
      email: Type.String({ format: 'email' }),
      address: Type.Ref(AddressSchema) // References the registered schema
    }),
    response: {
      201: Type.Ref(UserSchema) // Full user object from registered schema
    }
  }
}, async (request, reply) => {
  reply.status(201)
  return {
    id: crypto.randomUUID(),
    name: request.body.name,
    email: request.body.email,
    address: request.body.address,
    createdAt: new Date().toISOString()
  }
})
```

## Schema Registration Plugin Pattern

Organize schemas into a dedicated plugin that registers them all:

```typescript
// schemas/index.ts
import { FastifyPluginAsync } from 'fastify'
import { Type } from '@sinclair/typebox'

export const PaginationSchema = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1 }),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
  total: Type.Integer({ minimum: 0 })
}, { $id: 'Pagination' })

export const ErrorSchema = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String()
}, { $id: 'HttpError' })

export const TimestampsSchema = Type.Object({
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' })
}, { $id: 'Timestamps' })

const schemaPlugin: FastifyPluginAsync = async (app) => {
  app.addSchema(PaginationSchema)
  app.addSchema(ErrorSchema)
  app.addSchema(TimestampsSchema)
}

export default schemaPlugin
```

```typescript
// server.ts
import schemaPlugin from './schemas/index.js'

app.register(schemaPlugin) // Registers all shared schemas
app.register(userRoutes, { prefix: '/api/users' })
```

## Composing Registered Schemas

Build complex schemas from registered components:

```typescript
const PaginatedUsersResponse = Type.Object({
  data: Type.Array(Type.Ref(UserSchema)),
  pagination: Type.Ref(PaginationSchema)
}, { $id: 'PaginatedUsers' })

app.addSchema(PaginatedUsersResponse)

app.get('/users', {
  schema: {
    response: {
      200: Type.Ref(PaginatedUsersResponse)
    }
  }
}, async (request) => {
  return {
    data: [],
    pagination: { page: 1, limit: 20, total: 0 }
  }
})
```

## Retrieving Registered Schemas

```typescript
// Get all registered schemas
const schemas = app.getSchemas()
// { Address: {...}, User: {...}, Pagination: {...}, ... }

// Get a specific schema by $id
const addressSchema = app.getSchema('Address')
```

## Key Points

- Every `$id` must be unique across the entire Fastify instance
- Register schemas before registering route plugins that reference them
- `Type.Ref()` creates a JSON Schema `$ref` that Fastify resolves at validation time
- Registered schemas appear as components in OpenAPI output
- Use a dedicated schema-registration plugin to centralize all shared schemas
- Schema registration respects Fastify's encapsulation -- child contexts inherit parent schemas
