# TypeBox to JSON Schema Mapping

## Core Principle

Every TypeBox schema IS a JSON Schema object. There is no conversion step — TypeBox constructs standard JSON Schema at definition time.

```typescript
import { Type } from 'typebox'

const schema = Type.Object({
  name: Type.String(),
  age: Type.Integer(),
})

console.log(JSON.stringify(schema, null, 2))
// {
//   "type": "object",
//   "properties": {
//     "name": { "type": "string" },
//     "age": { "type": "integer" }
//   },
//   "required": ["name", "age"]
// }
```

## Complete Mapping Table

| TypeBox | JSON Schema |
|---------|-------------|
| `Type.String()` | `{ "type": "string" }` |
| `Type.Number()` | `{ "type": "number" }` |
| `Type.Boolean()` | `{ "type": "boolean" }` |
| `Type.Integer()` | `{ "type": "integer" }` |
| `Type.Null()` | `{ "type": "null" }` |
| `Type.Array(T)` | `{ "type": "array", "items": T }` |
| `Type.Object({...})` | `{ "type": "object", "properties": {...}, "required": [...] }` |
| `Type.Optional(T)` | removes key from `required` array |
| `Type.Literal('x')` | `{ "const": "x" }` |
| `Type.Union([A,B])` | `{ "anyOf": [A, B] }` |
| `Type.Intersect([A,B])` | `{ "allOf": [A, B] }` |
| `Type.Record(K,V)` | `{ "type": "object", "patternProperties": {...} }` |
| `Type.Tuple([A,B])` | `{ "type": "array", "items": [A,B], "minItems": 2, "maxItems": 2 }` |
| `Type.Enum(E)` | `{ "anyOf": [{ "const": v1 }, { "const": v2 }, ...] }` |
| `Type.Not(T)` | `{ "not": T }` |
| `Type.Any()` | `{}` |
| `Type.Unknown()` | `{}` |
| `Type.Never()` | `{ "not": {} }` |
| `Type.Ref(T)` | `{ "$ref": "T.$id" }` |
| `Type.Recursive(fn)` | `{ "$ref": "#", ... }` (self-referencing) |

## Schema Annotations

All JSON Schema annotations pass through directly:

```typescript
const ProductSchema = Type.Object({
  name: Type.String({
    minLength: 1,
    maxLength: 200,
    description: 'Product name',
    examples: ['Widget', 'Gadget'],
  }),
  price: Type.Number({
    minimum: 0,
    exclusiveMinimum: 0,
    multipleOf: 0.01,
    description: 'Price in USD',
  }),
  tags: Type.Array(Type.String(), {
    minItems: 1,
    maxItems: 10,
    uniqueItems: true,
  }),
}, {
  $id: 'Product',
  title: 'Product',
  description: 'A product in the catalog',
  additionalProperties: false,
})
```

## $id and $ref — Schema References

### Defining Reusable Schemas

```typescript
const AddressSchema = Type.Object({
  street: Type.String(),
  city: Type.String(),
  state: Type.String(),
  zip: Type.String(),
}, { $id: 'Address' })

// Reference it
const PersonSchema = Type.Object({
  name: Type.String(),
  home: Type.Ref(AddressSchema),       // { "$ref": "Address" }
  work: Type.Optional(Type.Ref(AddressSchema)),
}, { $id: 'Person' })
```

### In Fastify: addSchema + $ref

```typescript
import Fastify from 'fastify'

const fastify = Fastify()

// Register shared schemas
fastify.addSchema(Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
}, { $id: 'User' }))

fastify.addSchema(Type.Object({
  message: Type.String(),
  code: Type.Integer(),
}, { $id: 'Error' }))

// Reference in route schemas
fastify.get('/users/:id', {
  schema: {
    params: Type.Object({
      id: Type.String({ format: 'uuid' }),
    }),
    response: {
      200: Type.Ref(Type.Object({}, { $id: 'User' })),
      404: Type.Ref(Type.Object({}, { $id: 'Error' })),
    },
  },
}, handler)

// Or use the Fastify shorthand $ref syntax:
fastify.get('/users/:id', {
  schema: {
    response: {
      200: { $ref: 'User#' },
      404: { $ref: 'Error#' },
    },
  },
}, handler)
```

## OpenAPI / Swagger Generation

TypeBox schemas produce JSON Schema that `@fastify/swagger` converts to OpenAPI:

```typescript
import swagger from '@fastify/swagger'
import swaggerUI from '@fastify/swagger-ui'

await fastify.register(swagger, {
  openapi: {
    info: { title: 'My API', version: '1.0.0' },
  },
})
await fastify.register(swaggerUI, { routePrefix: '/docs' })
```

### Tips for Clean OpenAPI Output

```typescript
// Use $id for named definitions in OpenAPI
const UserSchema = Type.Object({...}, { $id: 'User', title: 'User' })

// Use additionalProperties: false for strict schemas
const StrictSchema = Type.Object({...}, { additionalProperties: false })

// Use description on every field for documentation
const DocumentedSchema = Type.Object({
  name: Type.String({ description: 'User display name' }),
  role: Type.Union([
    Type.Literal('admin'),
    Type.Literal('user'),
  ], { description: 'User role in the system' }),
})

// Prefer Union of Literals over Type.Enum for OpenAPI compatibility
// Type.Enum generates anyOf which some OpenAPI tools misrender
```

## Gotchas

### additionalProperties

By default, TypeBox objects allow additional properties (JSON Schema default). Set `additionalProperties: false` explicitly:

```typescript
// Allows extra properties (default)
Type.Object({ name: Type.String() })

// Rejects extra properties
Type.Object({ name: Type.String() }, { additionalProperties: false })
```

### Fastify's removeAdditional

Fastify's Ajv can be configured to strip extra properties instead of rejecting:

```typescript
const fastify = Fastify({
  ajv: {
    customOptions: {
      removeAdditional: 'all',  // strips unknown properties
    },
  },
})
```

### Transform Schemas and JSON Schema

Transform schemas produce standard JSON Schema for the **wire** (encoded) type. The Decode/Encode functions are TypeBox runtime features, not part of the JSON Schema output.

```typescript
const DateSchema = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(v => new Date(v))
  .Encode(v => v.toISOString())

console.log(JSON.stringify(DateSchema))
// { "type": "string", "format": "date-time" }
// The Transform is invisible in JSON Schema
```

## Extracting JSON Schema for External Use

```typescript
// TypeBox schemas are already JSON Schema — just serialize
const jsonSchema = JSON.stringify(ProductSchema, null, 2)

// Write to file for non-TypeScript consumers
import { writeFileSync } from 'fs'
writeFileSync('schemas/product.json', jsonSchema)
```
