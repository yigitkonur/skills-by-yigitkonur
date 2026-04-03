# Fastify Serialization

## Response Schemas Enable fast-json-stringify

Defining response schemas provides 2-3x faster serialization AND automatic security filtering:

```typescript
import { Type, type Static } from '@sinclair/typebox'

const UserResponse = Type.Object({
  id: Type.String(),
  name: Type.String(),
  email: Type.String(),
})

// FAST: uses fast-json-stringify + strips unlisted properties
app.get('/users', {
  schema: {
    response: {
      200: Type.Array(UserResponse),
    },
  },
}, async () => {
  return db.users.findAll()
  // Even if db returns password_hash, it is NOT serialized
})

// SLOW: uses JSON.stringify, no filtering
app.get('/users-slow', async () => {
  return db.users.findAll() // password_hash would leak!
})
```

## Multiple Status Code Schemas

```typescript
const ErrorResponse = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String(),
})

app.get('/users/:id', {
  schema: {
    params: Type.Object({ id: Type.String() }),
    response: {
      200: UserResponse,
      404: ErrorResponse,
    },
  },
}, async (request, reply) => {
  const user = await db.users.findById(request.params.id)
  if (!user) {
    reply.code(404)
    return { statusCode: 404, error: 'Not Found', message: 'User not found' }
  }
  return user
})
```

## Wildcard Status Code Schemas

```typescript
app.get('/resource', {
  schema: {
    response: {
      200: ResourceSchema,
      '4xx': ErrorResponse,  // Covers all 4xx codes
      '5xx': Type.Object({
        statusCode: Type.Integer(),
        error: Type.String(),
      }),
    },
  },
}, handler)
```

## Nullable Fields with TypeBox

```typescript
const ProfileResponse = Type.Object({
  name: Type.String(),
  bio: Type.Union([Type.String(), Type.Null()]),
  avatar: Type.Optional(Type.Union([
    Type.String({ format: 'uri' }),
    Type.Null(),
  ])),
})

app.get('/profile', {
  schema: { response: { 200: ProfileResponse } },
}, async () => ({
  name: 'John',
  bio: null,
  avatar: null,
}))
```

## Type Coercion in Serialization

fast-json-stringify coerces types to match the schema:

```typescript
app.get('/data', {
  schema: {
    response: {
      200: Type.Object({
        count: Type.Integer(),     // '5' -> 5
        active: Type.Boolean(),    // 'true' -> true
        tags: Type.Array(Type.String()), // [1, 2] -> ['1', '2']
      }),
    },
  },
}, async () => ({
  count: '5',      // coerced to integer
  active: 'true',  // coerced to boolean
  tags: [1, 2, 3], // coerced to strings
}))
```

## Nested Objects and References

```typescript
const AddressSchema = Type.Object({
  street: Type.String(),
  city: Type.String(),
  country: Type.String(),
})

const ContactSchema = Type.Object({
  type: Type.String(),
  value: Type.String(),
})

const UserDetailSchema = Type.Object({
  name: Type.String(),
  address: AddressSchema,
  contacts: Type.Array(ContactSchema),
})

app.get('/user-detail', {
  schema: { response: { 200: UserDetailSchema } },
}, async () => ({
  name: 'John',
  address: { street: '123 Main', city: 'Boston', country: 'USA' },
  contacts: [
    { type: 'email', value: 'john@example.com' },
    { type: 'phone', value: '+1234567890' },
  ],
}))
```

## Date Serialization

```typescript
const EventSchema = Type.Object({
  name: Type.String(),
  date: Type.String({ format: 'date-time' }),
})

app.get('/events', {
  schema: { response: { 200: Type.Array(EventSchema) } },
}, async () => {
  const events = await db.events.findAll()
  return events.map((e) => ({
    ...e,
    date: e.date.toISOString(), // Convert Date to string
  }))
})
```

## Additional Properties Control

```typescript
// Default: extra properties are STRIPPED (security!)
app.get('/strict', {
  schema: {
    response: {
      200: Type.Object({
        id: Type.String(),
        name: Type.String(),
      }), // TypeBox objects have additionalProperties: false by default
    },
  },
}, async () => {
  return { id: '1', name: 'John', secret: 'hidden' }
  // Output: { "id": "1", "name": "John" } -- secret stripped
})

// Allow additional properties
app.get('/flexible', {
  schema: {
    response: {
      200: Type.Object({
        id: Type.String(),
      }, { additionalProperties: true }),
    },
  },
}, async () => {
  return { id: '1', extra: 'included' }
  // Output: { "id": "1", "extra": "included" }
})
```

## Stream Responses (Bypass Serialization)

```typescript
import { createReadStream } from 'node:fs'

app.get('/file', async (request, reply) => {
  const stream = createReadStream('./data.json')
  reply.type('application/json')
  return reply.send(stream)
})

// Streaming JSON array from database cursor
app.get('/export', async (request, reply) => {
  reply.type('application/json')
  const cursor = db.users.findCursor()

  reply.raw.write('[')
  let first = true
  for await (const user of cursor) {
    if (!first) reply.raw.write(',')
    reply.raw.write(JSON.stringify(user))
    first = false
  }
  reply.raw.write(']')
  reply.raw.end()
})
```

## Pre-Serialization Hook

Modify data before serialization:

```typescript
app.addHook('preSerialization', async (request, reply, payload) => {
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    return {
      ...payload,
      _links: { self: request.url },
    }
  }
  return payload
})
```

## Custom Serializer

```typescript
app.get('/custom', {
  schema: {
    response: {
      200: Type.Object({ value: Type.String() }),
    },
  },
  serializerCompiler: ({ schema }) => {
    return (data) => {
      return JSON.stringify({ value: String(data.value).toUpperCase() })
    }
  },
}, async () => ({ value: 'hello' }))
```

## Key Rules

- Always define response schemas for production APIs
- Response schemas enable fast-json-stringify (2-3x faster)
- Properties NOT in the schema are automatically stripped (prevents data leaks)
- TypeBox objects default to `additionalProperties: false`
- Compile schemas at startup, never at request time
