# TypeBox Schema Organization

## Recommended Project Structure

```
src/
  schemas/
    common/
      pagination.ts      # PaginationQuery, PaginatedResponse<T>
      errors.ts          # ErrorResponse, ValidationError, NotFound
      formats.ts         # Reusable format schemas (uuid, email, etc.)
      base.ts            # Timestamps, SoftDelete, BaseEntity
    users/
      user.schema.ts     # User, CreateUser, UpdateUser, UserList
      user.routes.ts     # Route definitions
      user.service.ts    # Business logic (uses types from schema)
    products/
      product.schema.ts
      product.routes.ts
      product.service.ts
    orders/
      order.schema.ts
      order.routes.ts
      order.service.ts
    index.ts             # Re-exports shared schemas
```

## Domain-Based Schema Modules

Each domain module exports its schemas and derived types:

```typescript
// schemas/users/user.schema.ts
import { Type, type Static } from 'typebox'
import { Timestamps } from '../common/base'
import { Nullable } from '../common/formats'

// --- Base schema ---
const UserFields = Type.Object({
  name: Type.String({ minLength: 1, maxLength: 100 }),
  email: Type.String({ format: 'email' }),
  role: Type.Union([Type.Literal('admin'), Type.Literal('user'), Type.Literal('viewer')]),
  avatar: Type.Optional(Nullable(Type.String({ format: 'uri' }))),
})

// --- CRUD variants ---
export const UserSchema = Type.Intersect([
  Type.Object({ id: Type.String({ format: 'uuid' }) }),
  UserFields,
  Timestamps,
], { $id: 'User' })
export type User = Static<typeof UserSchema>

export const CreateUserBody = Type.Omit(UserFields, [])
export type CreateUserBody = Static<typeof CreateUserBody>

export const UpdateUserBody = Type.Partial(UserFields)
export type UpdateUserBody = Static<typeof UpdateUserBody>

// --- Query schemas ---
export const UserQuerystring = Type.Object({
  role: Type.Optional(Type.Union([
    Type.Literal('admin'),
    Type.Literal('user'),
    Type.Literal('viewer'),
  ])),
  search: Type.Optional(Type.String({ minLength: 1 })),
  page: Type.Integer({ minimum: 1, default: 1 }),
  pageSize: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
})
export type UserQuerystring = Static<typeof UserQuerystring>

// --- Params ---
export const UserParams = Type.Object({
  id: Type.String({ format: 'uuid' }),
})
export type UserParams = Static<typeof UserParams>
```

## Common / Shared Schemas

```typescript
// schemas/common/base.ts
import { Type } from 'typebox'

export const Timestamps = Type.Object({
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' }),
})

export const SoftDelete = Type.Object({
  deletedAt: Type.Union([Type.String({ format: 'date-time' }), Type.Null()]),
})

export const IdParam = Type.Object({
  id: Type.String({ format: 'uuid' }),
})
```

```typescript
// schemas/common/formats.ts
import { Type, type TSchema } from 'typebox'

export function Nullable<T extends TSchema>(schema: T) {
  return Type.Union([schema, Type.Null()])
}

export const Formats = {
  uuid: () => Type.String({ format: 'uuid' }),
  email: () => Type.String({ format: 'email' }),
  uri: () => Type.String({ format: 'uri' }),
  dateTime: () => Type.String({ format: 'date-time' }),
  date: () => Type.String({ format: 'date' }),
} as const
```

```typescript
// schemas/common/pagination.ts
import { Type, type Static, type TSchema } from 'typebox'

export const PaginationQuery = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1 }),
  pageSize: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
})
export type PaginationQuery = Static<typeof PaginationQuery>

export function PaginatedResponse<T extends TSchema>(itemSchema: T) {
  return Type.Object({
    items: Type.Array(itemSchema),
    total: Type.Integer({ minimum: 0 }),
    page: Type.Integer({ minimum: 1 }),
    pageSize: Type.Integer({ minimum: 1 }),
  })
}
```

```typescript
// schemas/common/errors.ts
import { Type, type Static } from 'typebox'

export const ErrorResponse = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String(),
})
export type ErrorResponse = Static<typeof ErrorResponse>
```

## Barrel Files

```typescript
// schemas/index.ts — re-export for convenience
export * from './common/base'
export * from './common/formats'
export * from './common/pagination'
export * from './common/errors'

// Domain schemas
export * from './users/user.schema'
export * from './products/product.schema'
export * from './orders/order.schema'
```

## Route Registration Pattern

```typescript
// schemas/users/user.routes.ts
import { type FastifyInstance } from 'fastify'
import {
  UserSchema, CreateUserBody, UpdateUserBody,
  UserParams, UserQuerystring,
} from './user.schema'
import { PaginatedResponse } from '../common/pagination'
import { ErrorResponse } from '../common/errors'

export async function userRoutes(fastify: FastifyInstance) {
  fastify.get('/users', {
    schema: {
      querystring: UserQuerystring,
      response: {
        200: PaginatedResponse(UserSchema),
      },
    },
  }, async (request) => {
    // ...
  })

  fastify.post('/users', {
    schema: {
      body: CreateUserBody,
      response: {
        201: UserSchema,
        400: ErrorResponse,
      },
    },
  }, async (request, reply) => {
    // ...
  })

  fastify.patch('/users/:id', {
    schema: {
      params: UserParams,
      body: UpdateUserBody,
      response: {
        200: UserSchema,
        404: ErrorResponse,
      },
    },
  }, async (request) => {
    // ...
  })
}
```

## Shared Schema Registration (for $ref)

If using `$ref`, register shared schemas at app startup:

```typescript
// app.ts
import { UserSchema } from './schemas/users/user.schema'
import { ErrorResponse } from './schemas/common/errors'

export async function buildApp() {
  const fastify = Fastify().withTypeProvider<TypeBoxTypeProvider>()

  // Register shared schemas for $ref resolution
  fastify.addSchema(UserSchema)       // has $id: 'User'
  fastify.addSchema(ErrorResponse)    // has $id: 'Error'

  await fastify.register(userRoutes, { prefix: '/api' })
  return fastify
}
```

## Naming Conventions

| Schema purpose | Naming pattern | Example |
|---|---|---|
| Full entity | `{Entity}Schema` or just `{Entity}` | `UserSchema`, `Product` |
| Create body | `Create{Entity}Body` | `CreateUserBody` |
| Update body | `Update{Entity}Body` | `UpdateUserBody` |
| Patch body | `Patch{Entity}Body` | `PatchUserBody` |
| Route params | `{Entity}Params` | `UserParams` |
| Query string | `{Entity}Querystring` | `UserQuerystring` |
| List response | `{Entity}ListResponse` | `UserListResponse` |

## Tips

1. Keep schemas close to the routes that use them (same directory)
2. Extract truly shared schemas (pagination, errors, timestamps) to `common/`
3. Export both the schema constant and the derived type with the same name
4. Use `$id` on schemas you plan to reference via `$ref` or register with Fastify
5. Prefer composition (Intersect, Pick, Omit) over copying fields between schemas
