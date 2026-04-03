# TypeBox Enum Patterns

## Three Ways to Define Enums

### 1. Union of Literals (Recommended)

```typescript
import { Type, type Static } from 'typebox'

const StatusSchema = Type.Union([
  Type.Literal('active'),
  Type.Literal('inactive'),
  Type.Literal('suspended'),
])
type Status = Static<typeof StatusSchema>
// => 'active' | 'inactive' | 'suspended'
```

JSON Schema output:
```json
{
  "anyOf": [
    { "const": "active" },
    { "const": "inactive" },
    { "const": "suspended" }
  ]
}
```

### 2. Type.Enum (for TypeScript native enums)

```typescript
enum Role {
  Admin = 'admin',
  User = 'user',
  Guest = 'guest',
}

const RoleSchema = Type.Enum(Role)
type RoleType = Static<typeof RoleSchema>
// => Role (Role.Admin | Role.User | Role.Guest)
```

JSON Schema output:
```json
{
  "anyOf": [
    { "const": "admin" },
    { "const": "user" },
    { "const": "guest" }
  ]
}
```

### 3. Type.Unsafe with enum keyword (direct JSON Schema)

```typescript
const PrioritySchema = Type.Unsafe<'low' | 'medium' | 'high'>({
  type: 'string',
  enum: ['low', 'medium', 'high'],
})
```

JSON Schema output:
```json
{ "type": "string", "enum": ["low", "medium", "high"] }
```

## Which to Use?

| Approach | Pros | Cons |
|----------|------|------|
| Union of Literals | Best TypeScript inference, composable | Verbose for many values |
| Type.Enum | Works with existing TS enums | TS enums have known quirks |
| Type.Unsafe + enum | Cleanest JSON Schema output | No type safety from TypeBox |

**Recommendation:** Use **Union of Literals** for new code. Use **Type.Enum** only when interfacing with existing TypeScript enums.

## Numeric Enums

```typescript
// TypeScript numeric enum
enum HttpStatus {
  OK = 200,
  Created = 201,
  BadRequest = 400,
  NotFound = 404,
}

const HttpStatusSchema = Type.Enum(HttpStatus)
// Matches: 200, 201, 400, 404

// Union of Literal numbers
const StatusCode = Type.Union([
  Type.Literal(200),
  Type.Literal(201),
  Type.Literal(400),
  Type.Literal(404),
])
```

## Helper: Enum from Array

Create a union of literals from a constant array:

```typescript
function StringEnum<T extends string[]>(values: [...T]) {
  return Type.Union(
    values.map(v => Type.Literal(v)) as { [K in keyof T]: ReturnType<typeof Type.Literal<T[K]>> }
  )
}

// Usage
const StatusSchema = StringEnum(['active', 'inactive', 'pending'])
type Status = Static<typeof StatusSchema>
// => 'active' | 'inactive' | 'pending'

// Reusable values constant
const ROLES = ['admin', 'user', 'viewer'] as const
const RoleSchema = Type.Union(ROLES.map(r => Type.Literal(r)))
```

## Discriminated Unions

Use a literal "type" or "kind" field to discriminate between union members:

```typescript
const TextMessage = Type.Object({
  type: Type.Literal('text'),
  content: Type.String(),
})

const ImageMessage = Type.Object({
  type: Type.Literal('image'),
  url: Type.String({ format: 'uri' }),
  altText: Type.Optional(Type.String()),
})

const FileMessage = Type.Object({
  type: Type.Literal('file'),
  filename: Type.String(),
  size: Type.Integer({ minimum: 0 }),
  mimeType: Type.String(),
})

const MessageSchema = Type.Union([TextMessage, ImageMessage, FileMessage])
type Message = Static<typeof MessageSchema>

// TypeScript narrows the type based on the discriminant
function renderMessage(msg: Message) {
  switch (msg.type) {
    case 'text':
      return msg.content               // string
    case 'image':
      return `<img src="${msg.url}" />` // url is string
    case 'file':
      return `Download: ${msg.filename} (${msg.size} bytes)`
  }
}
```

## Discriminated Union for API Responses

```typescript
const SuccessResponse = Type.Object({
  status: Type.Literal('success'),
  data: Type.Unknown(),
})

const ErrorResponse = Type.Object({
  status: Type.Literal('error'),
  error: Type.Object({
    code: Type.String(),
    message: Type.String(),
  }),
})

const ApiResponse = Type.Union([SuccessResponse, ErrorResponse])
type ApiResponse = Static<typeof ApiResponse>

function handleResponse(res: ApiResponse) {
  if (res.status === 'success') {
    console.log(res.data)       // narrowed to SuccessResponse
  } else {
    console.error(res.error)    // narrowed to ErrorResponse
  }
}
```

## Discriminated Unions for Polymorphic Entities

```typescript
const CreditPayment = Type.Object({
  method: Type.Literal('credit_card'),
  cardLast4: Type.String({ pattern: '^\\d{4}$' }),
  expiryMonth: Type.Integer({ minimum: 1, maximum: 12 }),
  expiryYear: Type.Integer({ minimum: 2024 }),
})

const BankPayment = Type.Object({
  method: Type.Literal('bank_transfer'),
  accountNumber: Type.String(),
  routingNumber: Type.String(),
})

const CryptoPayment = Type.Object({
  method: Type.Literal('crypto'),
  walletAddress: Type.String(),
  network: Type.Union([Type.Literal('ethereum'), Type.Literal('bitcoin')]),
})

const PaymentMethod = Type.Union([CreditPayment, BankPayment, CryptoPayment])
type PaymentMethod = Static<typeof PaymentMethod>
```

## Enum Validation

```typescript
import { Value } from 'typebox/value'

const StatusSchema = Type.Union([
  Type.Literal('active'),
  Type.Literal('inactive'),
])

Value.Check(StatusSchema, 'active')    // true
Value.Check(StatusSchema, 'invalid')   // false
Value.Check(StatusSchema, 123)         // false

// Error messages
const errors = [...Value.Errors(StatusSchema, 'invalid')]
// Errors will indicate none of the union members matched
```

## Enums in Query Parameters

```typescript
fastify.get('/users', {
  schema: {
    querystring: Type.Object({
      status: Type.Optional(Type.Union([
        Type.Literal('active'),
        Type.Literal('inactive'),
        Type.Literal('all'),
      ], { default: 'all' })),
      role: Type.Optional(Type.Union([
        Type.Literal('admin'),
        Type.Literal('user'),
      ])),
      // Multiple enum values via comma-separated string
      sortBy: Type.Optional(Type.Union([
        Type.Literal('name'),
        Type.Literal('email'),
        Type.Literal('createdAt'),
      ], { default: 'createdAt' })),
      sortOrder: Type.Optional(Type.Union([
        Type.Literal('asc'),
        Type.Literal('desc'),
      ], { default: 'desc' })),
    }),
  },
}, handler)
```

## Extracting Enum Values at Runtime

```typescript
const STATUS_VALUES = ['active', 'inactive', 'pending'] as const

// Schema from the array
const StatusSchema = Type.Union(STATUS_VALUES.map(v => Type.Literal(v)))

// Use the array at runtime too
function isValidStatus(value: string): boolean {
  return (STATUS_VALUES as readonly string[]).includes(value)
}

// This keeps the runtime values and the schema in sync
```
