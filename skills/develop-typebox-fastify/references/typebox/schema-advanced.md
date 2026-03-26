# TypeBox Advanced Schema Patterns

## Recursive Schemas

Use `Type.Recursive` for self-referencing structures like trees and linked lists:

```typescript
import { Type, type Static } from 'typebox'

// Tree node that contains children of the same type
const TreeNode = Type.Recursive(This =>
  Type.Object({
    id: Type.String(),
    label: Type.String(),
    children: Type.Array(This),
  })
)
type TreeNode = Static<typeof TreeNode>
// => { id: string; label: string; children: TreeNode[] }

// Linked list
const LinkedList = Type.Recursive(This =>
  Type.Object({
    value: Type.Number(),
    next: Type.Optional(This),
  })
)

// JSON-like value (recursive union)
const JsonValue = Type.Recursive(This =>
  Type.Union([
    Type.String(),
    Type.Number(),
    Type.Boolean(),
    Type.Null(),
    Type.Array(This),
    Type.Record(Type.String(), This),
  ])
)
type JsonValue = Static<typeof JsonValue>
```

## Ref — Schema References

Use `$id` and `Type.Ref` for cross-referencing schemas in shared registries:

```typescript
const AddressSchema = Type.Object({
  street: Type.String(),
  city: Type.String(),
  zip: Type.String(),
}, { $id: 'Address' })

const PersonSchema = Type.Object({
  name: Type.String(),
  home: Type.Ref(AddressSchema),
  work: Type.Optional(Type.Ref(AddressSchema)),
}, { $id: 'Person' })

// When using with Fastify, add both to shared schema:
// fastify.addSchema(AddressSchema)
// fastify.addSchema(PersonSchema)
```

## Transform Schemas

Transform schemas let you define encode/decode pipelines. The schema validates the input, then a function transforms the value:

```typescript
import { Type, type Static, type StaticDecode, type StaticEncode } from 'typebox'

// Parse ISO date string into Date object
const DateTransform = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(value => new Date(value))    // string → Date (on input)
  .Encode(value => value.toISOString()) // Date → string (on output)

type DateInput = StaticEncode<typeof DateTransform>  // string
type DateOutput = StaticDecode<typeof DateTransform>  // Date

// Parse comma-separated string into array
const CsvTransform = Type.Transform(Type.String())
  .Decode(value => value.split(',').map(s => s.trim()))
  .Encode(value => value.join(','))

// Lowercase email normalization
const EmailTransform = Type.Transform(Type.String({ format: 'email' }))
  .Decode(value => value.toLowerCase().trim())
  .Encode(value => value)
```

## Type.Unsafe — Escape Hatch

When TypeBox cannot express a JSON Schema construct, use `Type.Unsafe`:

```typescript
// Custom JSON Schema that TypeBox doesn't support natively
const RegexPattern = Type.Unsafe<string>({
  type: 'string',
  pattern: '^[A-Z]{2}\\d{4}$',
})

// Complex conditional schema
const ConditionalSchema = Type.Unsafe<{ type: 'a'; value: string } | { type: 'b'; count: number }>({
  oneOf: [
    {
      type: 'object',
      properties: { type: { const: 'a' }, value: { type: 'string' } },
      required: ['type', 'value'],
    },
    {
      type: 'object',
      properties: { type: { const: 'b' }, count: { type: 'number' } },
      required: ['type', 'count'],
    },
  ],
})
```

> **Warning:** `Type.Unsafe` bypasses TypeBox's type checking. The generic parameter is trusted, not verified. Use sparingly.

## Discriminated Unions

Model tagged/discriminated unions for polymorphic APIs:

```typescript
const CircleSchema = Type.Object({
  kind: Type.Literal('circle'),
  radius: Type.Number({ minimum: 0 }),
})

const RectangleSchema = Type.Object({
  kind: Type.Literal('rectangle'),
  width: Type.Number({ minimum: 0 }),
  height: Type.Number({ minimum: 0 }),
})

const TriangleSchema = Type.Object({
  kind: Type.Literal('triangle'),
  base: Type.Number({ minimum: 0 }),
  height: Type.Number({ minimum: 0 }),
})

const ShapeSchema = Type.Union([CircleSchema, RectangleSchema, TriangleSchema])
type Shape = Static<typeof ShapeSchema>

// TypeScript narrows correctly:
function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle': return Math.PI * shape.radius ** 2
    case 'rectangle': return shape.width * shape.height
    case 'triangle': return 0.5 * shape.base * shape.height
  }
}
```

## Generic Schema Functions

Create reusable parameterized schemas using functions:

```typescript
// Generic paginated response
function PaginatedResponse<T extends TSchema>(itemSchema: T) {
  return Type.Object({
    items: Type.Array(itemSchema),
    total: Type.Integer({ minimum: 0 }),
    page: Type.Integer({ minimum: 1 }),
    pageSize: Type.Integer({ minimum: 1, maximum: 100 }),
    hasMore: Type.Boolean(),
  })
}

const UserListResponse = PaginatedResponse(UserSchema)
type UserListResponse = Static<typeof UserListResponse>

// Generic API response wrapper
function ApiResponse<T extends TSchema>(dataSchema: T) {
  return Type.Object({
    success: Type.Literal(true),
    data: dataSchema,
    meta: Type.Optional(Type.Object({
      requestId: Type.String(),
      duration: Type.Number(),
    })),
  })
}

// Generic error response
function ApiError(codes: string[]) {
  return Type.Object({
    success: Type.Literal(false),
    error: Type.Object({
      code: Type.Union(codes.map(c => Type.Literal(c))),
      message: Type.String(),
      details: Type.Optional(Type.Array(Type.Object({
        field: Type.String(),
        message: Type.String(),
      }))),
    }),
  })
}
```

You need the `TSchema` import for generic constraints:

```typescript
import { Type, type Static, type TSchema } from 'typebox'
```

## Conditional / If-Then-Else (via Unsafe)

JSON Schema's `if/then/else` isn't natively supported, but you can use Unsafe:

```typescript
const PaymentSchema = Type.Unsafe<
  | { method: 'card'; cardNumber: string; cvv: string }
  | { method: 'bank'; accountNumber: string; routingNumber: string }
>({
  type: 'object',
  properties: {
    method: { type: 'string', enum: ['card', 'bank'] },
  },
  required: ['method'],
  if: { properties: { method: { const: 'card' } } },
  then: {
    properties: {
      cardNumber: { type: 'string' },
      cvv: { type: 'string' },
    },
    required: ['cardNumber', 'cvv'],
  },
  else: {
    properties: {
      accountNumber: { type: 'string' },
      routingNumber: { type: 'string' },
    },
    required: ['accountNumber', 'routingNumber'],
  },
})
```

> **Prefer discriminated unions** (Type.Union with Literal discriminant) over if/then/else. They are simpler, well-supported, and TypeScript can narrow the types.

## Mapped Types with Type.Mapped

```typescript
import { Type, type TSchema } from 'typebox'

// Create a schema where every property is wrapped in Optional
const Keys = Type.Union([Type.Literal('a'), Type.Literal('b'), Type.Literal('c')])
const Mapped = Type.Mapped(Keys, K => Type.Optional(Type.String()))
```

## Not — Negation

```typescript
const NotEmpty = Type.Not(Type.String({ maxLength: 0 }))
// Matches any value that is NOT an empty string
```
