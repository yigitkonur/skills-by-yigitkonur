# TypeBox Performance Tips

## 1. Always Use TypeCompiler for Repeated Validation

The single most impactful optimization. `Value.Check` recompiles on every call; `TypeCompiler.Compile` compiles once and reuses.

```typescript
import { TypeCompiler } from 'typebox/compiler'
import { Value } from 'typebox/value'
import { Type } from 'typebox'

const schema = Type.Object({
  name: Type.String(),
  email: Type.String({ format: 'email' }),
  age: Type.Integer({ minimum: 0 }),
})

// SLOW: ~2M ops/sec (recompiles each call)
Value.Check(schema, data)

// FAST: ~150-200M ops/sec (compiled once)
const compiled = TypeCompiler.Compile(schema)
compiled.Check(data)
```

**Rule:** Use `Value.Check` only for one-off validations (tests, scripts). Use `TypeCompiler.Compile` for anything called repeatedly.

## 2. Compile at Module Level, Not Per Request

```typescript
// schemas/user.ts
import { TypeCompiler } from 'typebox/compiler'
import { Type } from 'typebox'

export const UserSchema = Type.Object({
  name: Type.String(),
  email: Type.String({ format: 'email' }),
})

// Compile once when module loads
export const UserValidator = TypeCompiler.Compile(UserSchema)

// routes/users.ts
import { UserValidator } from '../schemas/user'

// Reuse on every request — no recompilation
function handleRequest(data: unknown) {
  if (UserValidator.Check(data)) {
    // ...
  }
}
```

## 3. Fastify Already Compiles Schemas via Ajv

Fastify compiles route schemas with Ajv at startup. You do NOT need to also use TypeCompiler for request validation in route handlers — Fastify handles it.

TypeCompiler is valuable for:
- Validation outside Fastify routes (message queues, WebSockets, cron jobs)
- Transform schema Decode/Encode
- Custom validation pipelines

```typescript
// Fastify handles this automatically — no TypeCompiler needed
fastify.post('/users', {
  schema: { body: UserSchema },  // Compiled by Ajv at startup
}, handler)

// Use TypeCompiler here — outside Fastify's validation
async function processQueueMessage(raw: string) {
  const data = JSON.parse(raw)
  if (UserValidator.Check(data)) { ... }
}
```

## 4. Use Response Schemas for Fast Serialization

Fastify uses response schemas to generate fast serialization functions (via `fast-json-stringify`). This is significantly faster than `JSON.stringify`.

```typescript
fastify.get('/users', {
  schema: {
    response: {
      200: Type.Object({
        users: Type.Array(Type.Object({
          id: Type.String(),
          name: Type.String(),
          email: Type.String(),
        })),
        total: Type.Integer(),
      }),
    },
  },
}, async () => {
  // Response is serialized ~2-5x faster than JSON.stringify
  return { users: [...], total: 100 }
})
```

Without a response schema, Fastify falls back to standard `JSON.stringify`.

## 5. Prefer Flat Schemas Over Deep Nesting

Deeply nested schemas are slower to validate. Flatten when possible.

```typescript
// Slower: deeply nested
const DeepSchema = Type.Object({
  level1: Type.Object({
    level2: Type.Object({
      level3: Type.Object({
        value: Type.String(),
      }),
    }),
  }),
})

// Faster: flat
const FlatSchema = Type.Object({
  'level1.level2.level3.value': Type.String(),
})

// Or restructure your data model to be shallower
```

## 6. Avoid Union of Many Complex Objects

Large unions require checking each member until one matches. This is O(n) in the number of members.

```typescript
// Slow for validation — checks each of 20 schemas
const BigUnion = Type.Union([
  Type.Object({ type: Type.Literal('a'), /* ... many fields */ }),
  Type.Object({ type: Type.Literal('b'), /* ... many fields */ }),
  // ... 18 more
])

// Faster: use a discriminator to route manually
function validateMessage(data: { type: string }) {
  const validators: Record<string, ReturnType<typeof TypeCompiler.Compile>> = {
    a: TypeCompiler.Compile(TypeA),
    b: TypeCompiler.Compile(TypeB),
    // ...
  }
  const validator = validators[data.type]
  if (!validator) return false
  return validator.Check(data)
}
```

## 7. Use $ref for Shared Schemas in Fastify

When the same schema is used in multiple routes, register it once with `addSchema` and reference it with `$ref`. Fastify compiles it once.

```typescript
// Register once
fastify.addSchema(Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
}, { $id: 'User' }))

// Reference everywhere — compiled once
fastify.get('/users/:id', {
  schema: { response: { 200: { $ref: 'User#' } } },
}, handler)

fastify.get('/users', {
  schema: { response: { 200: Type.Array({ $ref: 'User#' } as any) } },
}, handler)
```

## 8. Minimize Use of allErrors

Ajv's `allErrors: true` continues validation after the first error. This is slower for invalid data.

```typescript
// Faster (default) — stops at first error
const fastify = Fastify()

// Slower — collects all errors
const fastify = Fastify({
  ajv: {
    customOptions: {
      allErrors: true,  // Only enable if you need all error details
    },
  },
})
```

Use `allErrors: true` only in development or when you need detailed error reports.

## 9. Cache Schema Definitions

Don't recreate schemas inside functions:

```typescript
// BAD: creates new schema objects on every call
function getHandler(request) {
  const schema = Type.Object({ name: Type.String() })  // new object every time
  const validator = TypeCompiler.Compile(schema)          // recompiles every time
  return validator.Check(request.body)
}

// GOOD: define schemas at module level
const BodySchema = Type.Object({ name: Type.String() })
const bodyValidator = TypeCompiler.Compile(BodySchema)

function getHandler(request) {
  return bodyValidator.Check(request.body)
}
```

## 10. Generic Schema Functions: Memoize Results

If you use generic functions to create schemas, cache the results:

```typescript
const paginatedCache = new Map<string, TSchema>()

function PaginatedResponse<T extends TSchema>(itemSchema: T) {
  const key = JSON.stringify(itemSchema)
  if (paginatedCache.has(key)) return paginatedCache.get(key)!

  const schema = Type.Object({
    items: Type.Array(itemSchema),
    total: Type.Integer({ minimum: 0 }),
    page: Type.Integer({ minimum: 1 }),
    pageSize: Type.Integer({ minimum: 1 }),
  })

  paginatedCache.set(key, schema)
  return schema
}
```

## 11. Use additionalProperties: false

When `additionalProperties` is false, Ajv skips checking extra properties. This can be faster for objects with many unknown keys:

```typescript
const StrictSchema = Type.Object({
  name: Type.String(),
  email: Type.String(),
}, { additionalProperties: false })
```

## 12. Benchmark Your Schemas

Use the compiled validator's `Code()` method to inspect generated code:

```typescript
const validator = TypeCompiler.Compile(MySchema)
console.log(validator.Code())
// See the actual validation function — useful for spotting expensive checks
```

## Performance Summary

| Technique | Impact | Effort |
|-----------|--------|--------|
| TypeCompiler.Compile | 100x faster than Value.Check | Low |
| Response schemas | 2-5x faster serialization | Low |
| Compile at module level | Avoids per-request compilation | Low |
| $ref for shared schemas | Reduces memory and compile time | Medium |
| Flat schemas over deep nesting | 10-30% faster validation | Medium |
| Manual discriminated union routing | 5-20x for large unions | Medium |
| allErrors: false (default) | Faster on invalid data | Low |
| additionalProperties: false | Marginal improvement | Low |
