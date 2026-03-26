# Response Serialization with TypeBox + fast-json-stringify

## Overview

Fastify uses `fast-json-stringify` to serialize responses when a response schema is provided.
This is 2-5x faster than `JSON.stringify()` and automatically strips fields not in the schema,
providing both performance gains and security (no accidental data leaks).

## How It Works

When you define a response schema, Fastify compiles it into a serialization function at startup:

```typescript
import { Type } from '@sinclair/typebox'

app.get('/users/:id', {
  schema: {
    params: Type.Object({ id: Type.String() }),
    response: {
      200: Type.Object({
        id: Type.String(),
        name: Type.String(),
        email: Type.String()
        // Note: no "passwordHash" field
      })
    }
  }
}, async (request) => {
  const user = await db.users.findById(request.params.id)
  // Even if `user` has passwordHash, internalNotes, etc.,
  // they are STRIPPED from the response automatically
  return user
})
```

## Field Stripping for Security

This is a critical security feature. Fields not in the response schema are removed:

```typescript
const PublicUserSchema = Type.Object({
  id: Type.String(),
  name: Type.String(),
  avatar: Type.Optional(Type.String())
})

app.get('/users/:id', {
  schema: {
    response: { 200: PublicUserSchema }
  }
}, async () => {
  // Database returns everything, but response only includes schema fields
  return {
    id: '123',
    name: 'Alice',
    avatar: 'https://example.com/avatar.jpg',
    email: 'alice@secret.com',       // STRIPPED
    passwordHash: '$2b$...',          // STRIPPED
    ssn: '123-45-6789'               // STRIPPED
  }
})
// Response: { "id": "123", "name": "Alice", "avatar": "https://..." }
```

## Multiple Status Code Schemas

Define different schemas for different status codes:

```typescript
const ItemSchema = Type.Object({
  id: Type.String(),
  name: Type.String(),
  price: Type.Number()
})

const ErrorSchema = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String()
})

app.get('/items/:id', {
  schema: {
    response: {
      200: ItemSchema,
      404: ErrorSchema,
      500: ErrorSchema
    }
  }
}, async (request, reply) => {
  const item = await findItem(request.params.id)
  if (!item) {
    reply.status(404)
    return { statusCode: 404, error: 'Not Found', message: 'Item not found' }
  }
  return item
})
```

## Serialization with Nested Objects

```typescript
const OrderResponse = Type.Object({
  id: Type.String(),
  status: Type.String(),
  items: Type.Array(Type.Object({
    productId: Type.String(),
    name: Type.String(),
    quantity: Type.Integer(),
    unitPrice: Type.Number()
  })),
  total: Type.Number(),
  shippingAddress: Type.Object({
    street: Type.String(),
    city: Type.String(),
    zip: Type.String()
  })
})
```

## Custom Serializer Compiler

Override the serializer compiler for custom behavior:

```typescript
import Fastify from 'fastify'

const app = Fastify({
  serializerOpts: {
    // Options passed to fast-json-stringify
    rounding: 'ceil',          // How to round integers
    mode: 'standalone'         // Generate standalone serializer
  }
})
```

## Date Handling

TypeBox `format: 'date-time'` fields are serialized as strings. Convert Date objects
before returning:

```typescript
const EventResponse = Type.Object({
  id: Type.String(),
  title: Type.String(),
  startTime: Type.String({ format: 'date-time' }),
  endTime: Type.String({ format: 'date-time' })
})

app.get('/events/:id', {
  schema: { response: { 200: EventResponse } }
}, async (request) => {
  const event = await db.events.findById(request.params.id)
  return {
    ...event,
    // Convert Date objects to ISO strings for serialization
    startTime: event.startTime.toISOString(),
    endTime: event.endTime.toISOString()
  }
})
```

## Performance Comparison

```
JSON.stringify:        ~50,000 ops/sec
fast-json-stringify:   ~150,000 ops/sec  (3x faster)
```

The speedup comes from generating code at startup that knows the exact shape of the
output, avoiding runtime type checks.

## Disabling Serialization for a Route

If you need raw `JSON.stringify` behavior (e.g., dynamic schemas):

```typescript
app.get('/raw', async (request, reply) => {
  // No response schema = no fast-json-stringify = no field stripping
  reply.send({ anything: 'goes', extra: 'fields included' })
})
```

## Key Points

- Response schemas enable fast-json-stringify (2-5x faster than JSON.stringify)
- Fields NOT in the schema are automatically stripped -- critical for security
- Each status code can have its own schema
- Date objects must be converted to strings before serialization
- No response schema = standard JSON.stringify behavior
- Serialization functions are compiled once at startup, not per-request
