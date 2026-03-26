# TypeBox Common Schema Patterns

Reusable schema patterns for building REST APIs with Fastify.

## Pagination

```typescript
import { Type, type Static, type TSchema } from 'typebox'

// Query parameters for paginated endpoints
const PaginationQuery = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1 }),
  pageSize: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
  sortBy: Type.Optional(Type.String()),
  sortOrder: Type.Optional(Type.Union([
    Type.Literal('asc'),
    Type.Literal('desc'),
  ], { default: 'desc' })),
})
type PaginationQuery = Static<typeof PaginationQuery>

// Generic paginated response wrapper
function PaginatedResponse<T extends TSchema>(itemSchema: T) {
  return Type.Object({
    items: Type.Array(itemSchema),
    pagination: Type.Object({
      page: Type.Integer(),
      pageSize: Type.Integer(),
      total: Type.Integer({ minimum: 0 }),
      totalPages: Type.Integer({ minimum: 0 }),
      hasNext: Type.Boolean(),
      hasPrev: Type.Boolean(),
    }),
  })
}

// Usage
const UserListResponse = PaginatedResponse(UserSchema)
type UserListResponse = Static<typeof UserListResponse>
```

## Error Responses

```typescript
// Standard error detail
const ErrorDetail = Type.Object({
  field: Type.Optional(Type.String()),
  message: Type.String(),
  code: Type.Optional(Type.String()),
})

// Standard error response
const ErrorResponse = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String(),
  details: Type.Optional(Type.Array(ErrorDetail)),
})
type ErrorResponse = Static<typeof ErrorResponse>

// HTTP-specific error factories
const NotFoundError = Type.Object({
  statusCode: Type.Literal(404),
  error: Type.Literal('Not Found'),
  message: Type.String(),
})

const ValidationError = Type.Object({
  statusCode: Type.Literal(400),
  error: Type.Literal('Bad Request'),
  message: Type.String(),
  details: Type.Array(ErrorDetail),
})

const UnauthorizedError = Type.Object({
  statusCode: Type.Literal(401),
  error: Type.Literal('Unauthorized'),
  message: Type.String(),
})

// Use in route schemas
fastify.get('/users/:id', {
  schema: {
    params: Type.Object({ id: Type.String({ format: 'uuid' }) }),
    response: {
      200: UserSchema,
      404: NotFoundError,
      401: UnauthorizedError,
    },
  },
}, handler)
```

## CRUD Schema Set

```typescript
// Base fields (shared between create and read)
const ProductFields = Type.Object({
  name: Type.String({ minLength: 1, maxLength: 200 }),
  description: Type.String({ maxLength: 5000 }),
  price: Type.Number({ minimum: 0 }),
  categoryId: Type.String({ format: 'uuid' }),
  tags: Type.Array(Type.String(), { maxItems: 20, default: [] }),
  active: Type.Boolean({ default: true }),
})

// CREATE
const CreateProductBody = ProductFields
type CreateProductBody = Static<typeof CreateProductBody>

// READ (includes server-generated fields)
const Product = Type.Intersect([
  Type.Object({ id: Type.String({ format: 'uuid' }) }),
  ProductFields,
  Type.Object({
    createdAt: Type.String({ format: 'date-time' }),
    updatedAt: Type.String({ format: 'date-time' }),
  }),
])
type Product = Static<typeof Product>

// UPDATE (full replacement)
const UpdateProductBody = ProductFields

// PATCH (partial update)
const PatchProductBody = Type.Partial(ProductFields)
type PatchProductBody = Static<typeof PatchProductBody>

// Common params
const IdParam = Type.Object({
  id: Type.String({ format: 'uuid' }),
})
```

## Search and Filter

```typescript
const SearchQuery = Type.Object({
  q: Type.Optional(Type.String({ minLength: 1, maxLength: 200, description: 'Search query' })),
  status: Type.Optional(Type.Union([
    Type.Literal('active'),
    Type.Literal('inactive'),
    Type.Literal('draft'),
  ])),
  categoryId: Type.Optional(Type.String({ format: 'uuid' })),
  minPrice: Type.Optional(Type.Number({ minimum: 0 })),
  maxPrice: Type.Optional(Type.Number({ minimum: 0 })),
  createdAfter: Type.Optional(Type.String({ format: 'date-time' })),
  createdBefore: Type.Optional(Type.String({ format: 'date-time' })),
  tags: Type.Optional(Type.Array(Type.String())),
  ...PaginationQuery.properties,
})
type SearchQuery = Static<typeof SearchQuery>
```

## Batch Operations

```typescript
const BatchDeleteBody = Type.Object({
  ids: Type.Array(Type.String({ format: 'uuid' }), {
    minItems: 1,
    maxItems: 100,
  }),
})

const BatchUpdateBody = Type.Object({
  items: Type.Array(
    Type.Intersect([
      Type.Object({ id: Type.String({ format: 'uuid' }) }),
      Type.Partial(ProductFields),
    ]),
    { minItems: 1, maxItems: 50 }
  ),
})

const BatchResult = Type.Object({
  succeeded: Type.Integer({ minimum: 0 }),
  failed: Type.Integer({ minimum: 0 }),
  errors: Type.Array(Type.Object({
    id: Type.String(),
    error: Type.String(),
  })),
})
```

## File Upload Metadata

```typescript
const FileUploadMeta = Type.Object({
  filename: Type.String({ minLength: 1 }),
  mimeType: Type.String({ pattern: '^[a-z]+/[a-z0-9.+-]+$' }),
  size: Type.Integer({ minimum: 1, maximum: 50 * 1024 * 1024 }), // 50MB
  checksum: Type.Optional(Type.String({ description: 'SHA-256 hex digest' })),
})

const UploadResponse = Type.Object({
  id: Type.String({ format: 'uuid' }),
  url: Type.String({ format: 'uri' }),
  expiresAt: Type.String({ format: 'date-time' }),
})
```

## Auth Tokens

```typescript
const LoginBody = Type.Object({
  email: Type.String({ format: 'email' }),
  password: Type.String({ minLength: 8 }),
})

const TokenResponse = Type.Object({
  accessToken: Type.String(),
  refreshToken: Type.String(),
  tokenType: Type.Literal('Bearer'),
  expiresIn: Type.Integer({ description: 'Seconds until access token expires' }),
})

const RefreshBody = Type.Object({
  refreshToken: Type.String(),
})
```

## Webhook Payload

```typescript
const WebhookPayload = Type.Object({
  id: Type.String({ format: 'uuid' }),
  event: Type.Union([
    Type.Literal('order.created'),
    Type.Literal('order.updated'),
    Type.Literal('order.cancelled'),
    Type.Literal('payment.succeeded'),
    Type.Literal('payment.failed'),
  ]),
  data: Type.Unknown(),
  timestamp: Type.String({ format: 'date-time' }),
  signature: Type.String(),
})
```

## Headers Schema

```typescript
const AuthHeaders = Type.Object({
  authorization: Type.String({ pattern: '^Bearer .+$' }),
  'x-request-id': Type.Optional(Type.String({ format: 'uuid' })),
})

// In route
fastify.get('/protected', {
  schema: {
    headers: AuthHeaders,
  },
}, handler)
```
