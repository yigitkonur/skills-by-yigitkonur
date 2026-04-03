# TypeBox to OpenAPI Mapping

## Overview

TypeBox schemas produce JSON Schema that maps directly to OpenAPI 3.1 schema objects.
Adding descriptions, examples, and metadata in TypeBox options flows through to the
generated OpenAPI specification automatically.

## Basic Type Mapping

```typescript
import { Type } from '@sinclair/typebox'

// TypeBox                         -> OpenAPI type
Type.String()                      // { type: "string" }
Type.Number()                      // { type: "number" }
Type.Integer()                     // { type: "integer" }
Type.Boolean()                     // { type: "boolean" }
Type.Null()                        // { type: "null" }
Type.Array(Type.String())          // { type: "array", items: { type: "string" } }
Type.Object({ name: Type.String()}) // { type: "object", properties: { name: { type: "string" } } }
```

## Adding Descriptions

Pass `description` in schema options -- it appears in OpenAPI field docs:

```typescript
const CreateProductBody = Type.Object({
  name: Type.String({
    description: 'Product display name',
    minLength: 1,
    maxLength: 200
  }),
  sku: Type.String({
    description: 'Stock Keeping Unit - unique product identifier',
    pattern: '^[A-Z]{3}-\\d{6}$'
  }),
  price: Type.Number({
    description: 'Price in USD cents (e.g., 1999 = $19.99)',
    minimum: 0,
    examples: [1999, 4500]
  }),
  category: Type.Union([
    Type.Literal('electronics'),
    Type.Literal('clothing'),
    Type.Literal('food')
  ], {
    description: 'Product category for catalog organization'
  }),
  inStock: Type.Boolean({
    description: 'Whether the product is currently available',
    default: true
  })
}, {
  description: 'Payload for creating a new product',
  $id: 'CreateProduct'
})
```

## Examples in Schemas

```typescript
const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid', examples: ['550e8400-e29b-41d4-a716-446655440000'] }),
  name: Type.String({ examples: ['Jane Doe'] }),
  email: Type.String({ format: 'email', examples: ['jane@example.com'] }),
  age: Type.Optional(Type.Integer({ minimum: 0, maximum: 150, examples: [28] }))
}, {
  $id: 'User',
  description: 'A user in the system',
  examples: [{
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Jane Doe',
    email: 'jane@example.com',
    age: 28
  }]
})
```

## Enum Mapping

```typescript
// TypeBox Union of Literals -> OpenAPI enum
const StatusEnum = Type.Union([
  Type.Literal('pending'),
  Type.Literal('active'),
  Type.Literal('suspended'),
  Type.Literal('deleted')
], {
  description: 'Account status',
  default: 'pending'
})

// Produces: { type: "string", enum: ["pending","active","suspended","deleted"] }
```

## Tags and Route Grouping

Tags are set at the route level, not on the schema itself:

```typescript
app.get('/products', {
  schema: {
    tags: ['Products'],
    summary: 'List products',
    description: 'Returns a paginated list of products with optional filtering.',
    querystring: Type.Object({
      category: Type.Optional(Type.String({ description: 'Filter by category' })),
      minPrice: Type.Optional(Type.Integer({ description: 'Minimum price in cents' })),
      maxPrice: Type.Optional(Type.Integer({ description: 'Maximum price in cents' }))
    }),
    response: {
      200: Type.Object({
        data: Type.Array(Type.Ref(ProductSchema)),
        total: Type.Integer({ description: 'Total matching products' })
      }, { description: 'Successful product listing' })
    }
  }
}, handler)
```

## Nullable Fields (OpenAPI 3.1)

```typescript
// OpenAPI 3.1 supports "type" arrays for nullable
const ProfileSchema = Type.Object({
  bio: Type.Union([Type.String(), Type.Null()], {
    description: 'User biography, null if not set'
  }),
  website: Type.Optional(Type.Union([Type.String({ format: 'uri' }), Type.Null()]))
})
```

## Deprecated Fields

```typescript
const LegacyEndpoint = Type.Object({
  oldField: Type.String({
    description: 'Use newField instead',
    deprecated: true
  }),
  newField: Type.String()
})

// Mark entire route as deprecated
app.get('/v1/legacy', {
  schema: {
    deprecated: true,
    tags: ['Legacy'],
    summary: 'Deprecated - use /v2/modern instead'
  }
}, handler)
```

## additionalProperties Control

```typescript
// Strict object (no extra properties) -- default for TypeBox
const StrictBody = Type.Object({
  name: Type.String()
}) // additionalProperties: false

// Allow extra properties
const FlexibleBody = Type.Object({
  name: Type.String()
}, { additionalProperties: true })

// Typed additional properties
const MetadataBody = Type.Object({
  name: Type.String(),
  metadata: Type.Record(Type.String(), Type.String())
})
```

## Discriminated Unions

```typescript
const NotificationSchema = Type.Union([
  Type.Object({
    type: Type.Literal('email'),
    to: Type.String({ format: 'email' }),
    subject: Type.String()
  }),
  Type.Object({
    type: Type.Literal('sms'),
    phone: Type.String(),
    message: Type.String({ maxLength: 160 })
  }),
  Type.Object({
    type: Type.Literal('push'),
    deviceToken: Type.String(),
    title: Type.String()
  })
], {
  description: 'Notification payload, discriminated by type field'
})
```

## Key Points

- TypeBox options (`description`, `examples`, `deprecated`) map directly to OpenAPI fields
- Use `$id` on schemas to create reusable OpenAPI components
- Union of Literals becomes OpenAPI enum
- `Type.Optional()` removes the field from `required` in OpenAPI
- Tags, summary, and security are route-level schema properties, not TypeBox properties
- OpenAPI 3.1 aligns with JSON Schema draft 2020-12, matching TypeBox output
