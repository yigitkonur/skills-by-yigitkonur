# TypeBox Nullable and Optional Patterns

## The Distinction

- **Optional**: The property may be absent from the object (`key?: T`)
- **Nullable**: The property must be present but its value may be `null` (`key: T | null`)
- **Optional + Nullable**: The property may be absent or may be `null`

These are different concepts in JSON Schema and TypeScript. TypeBox handles them distinctly.

## Type.Optional — Property May Be Missing

```typescript
import { Type, type Static } from 'typebox'

const UserSchema = Type.Object({
  name: Type.String(),
  bio: Type.Optional(Type.String()),
})
type User = Static<typeof UserSchema>
// => { name: string; bio?: string }

// JSON Schema:
// {
//   "type": "object",
//   "properties": {
//     "name": { "type": "string" },
//     "bio": { "type": "string" }
//   },
//   "required": ["name"]          ← bio NOT in required
// }
```

Valid values:
```typescript
{ name: 'Alice' }                    // OK — bio is absent
{ name: 'Alice', bio: 'Hello' }      // OK — bio is present
{ name: 'Alice', bio: undefined }    // OK in TS, but JSON has no undefined
{ name: 'Alice', bio: null }         // INVALID — null is not string
```

## Nullable — Value May Be Null

TypeBox doesn't have a `Type.Nullable()` helper. Use `Type.Union` with `Type.Null()`:

```typescript
const NullableString = Type.Union([Type.String(), Type.Null()])

const UserSchema = Type.Object({
  name: Type.String(),
  bio: Type.Union([Type.String(), Type.Null()]),
})
type User = Static<typeof UserSchema>
// => { name: string; bio: string | null }

// JSON Schema:
// {
//   "type": "object",
//   "properties": {
//     "name": { "type": "string" },
//     "bio": { "anyOf": [{ "type": "string" }, { "type": "null" }] }
//   },
//   "required": ["name", "bio"]    ← bio IS required
// }
```

Valid values:
```typescript
{ name: 'Alice', bio: 'Hello' }  // OK
{ name: 'Alice', bio: null }     // OK
{ name: 'Alice' }                // INVALID — bio is required
```

## Optional + Nullable

```typescript
const UserSchema = Type.Object({
  name: Type.String(),
  bio: Type.Optional(Type.Union([Type.String(), Type.Null()])),
})
type User = Static<typeof UserSchema>
// => { name: string; bio?: string | null }
```

Valid values:
```typescript
{ name: 'Alice' }                // OK — bio absent
{ name: 'Alice', bio: 'Hello' }  // OK
{ name: 'Alice', bio: null }     // OK
```

## Helper Function: Nullable

Create a reusable `Nullable` utility:

```typescript
import { Type, type TSchema } from 'typebox'

function Nullable<T extends TSchema>(schema: T) {
  return Type.Union([schema, Type.Null()])
}

// Usage
const UserSchema = Type.Object({
  name: Type.String(),
  deletedAt: Nullable(Type.String({ format: 'date-time' })),
  bio: Type.Optional(Nullable(Type.String())),
})
```

## Database Model Patterns

### SQL NULL columns

SQL `NULL` maps to nullable (not optional) — the column exists, value is NULL:

```typescript
// Matches: SELECT id, name, deleted_at FROM users
const UserRow = Type.Object({
  id: Type.Integer(),
  name: Type.String(),
  deleted_at: Type.Union([Type.String({ format: 'date-time' }), Type.Null()]),
})
```

### API Response (include nulls explicitly)

```typescript
// Response always includes all fields, some may be null
const UserResponse = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  avatar: Type.Union([Type.String({ format: 'uri' }), Type.Null()]),
  lastLoginAt: Type.Union([Type.String({ format: 'date-time' }), Type.Null()]),
})
```

### API Request Body (omit optional fields)

```typescript
// Client may omit fields they don't want to update
const UpdateUserBody = Type.Object({
  name: Type.Optional(Type.String({ minLength: 1 })),
  avatar: Type.Optional(Type.Union([Type.String({ format: 'uri' }), Type.Null()])),
  // null means "clear the avatar", absent means "don't change"
})
```

## PATCH Semantics: Absent vs Null vs Value

A common API pattern where absent, null, and a value all mean different things:

```typescript
// In a PATCH request:
// - absent key → don't change this field
// - null value → clear this field (set to NULL in DB)
// - string value → update to this value

const PatchUserBody = Type.Object({
  name: Type.Optional(Type.String({ minLength: 1 })),
  bio: Type.Optional(Type.Union([Type.String(), Type.Null()])),
  avatar: Type.Optional(Type.Union([Type.String({ format: 'uri' }), Type.Null()])),
})

// Handler logic
fastify.patch('/users/:id', {
  schema: { body: PatchUserBody },
}, async (request) => {
  const updates: Record<string, unknown> = {}
  const body = request.body

  // Only include fields that were explicitly sent
  if ('name' in body) updates.name = body.name
  if ('bio' in body) updates.bio = body.bio       // could be null
  if ('avatar' in body) updates.avatar = body.avatar // could be null

  await db.users.update(request.params.id, updates)
})
```

## Fastify Serialization Caveat

Fastify's response serialization may strip `null` values if the response schema doesn't include `Type.Null()`:

```typescript
// If schema says Type.String() but handler returns null:
// Fastify may serialize it as "" or omit it

// Always match your response schema to actual values:
const ResponseSchema = Type.Object({
  name: Type.String(),
  deletedAt: Type.Union([Type.String({ format: 'date-time' }), Type.Null()]),
})
```

## Quick Reference

| Pattern | TypeBox | TypeScript | JSON valid |
|---------|---------|------------|------------|
| Required | `Type.String()` | `string` | `"hello"` |
| Optional | `Type.Optional(Type.String())` | `string?` | `"hello"` or absent |
| Nullable | `Type.Union([Type.String(), Type.Null()])` | `string \| null` | `"hello"` or `null` |
| Optional+Nullable | `Type.Optional(Type.Union([Type.String(), Type.Null()]))` | `string \| null \| undefined` | `"hello"`, `null`, or absent |
