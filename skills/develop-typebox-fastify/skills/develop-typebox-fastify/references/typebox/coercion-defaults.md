# TypeBox Coercion and Default Values

## The Problem: Query Strings Are Always Strings

HTTP query parameters and some headers arrive as strings. A schema expecting `Type.Integer()` will fail if the raw value is `"42"` instead of `42`.

```typescript
// GET /users?page=2&active=true
// request.query = { page: "2", active: "true" }  ← all strings!
```

## Fastify's Built-in Coercion

Fastify uses Ajv with `coerceTypes` enabled by default for query strings and params. This means basic type coercion works automatically:

```typescript
import Fastify from 'fastify'
import { Type } from 'typebox'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const fastify = Fastify().withTypeProvider<TypeBoxTypeProvider>()

fastify.get('/users', {
  schema: {
    querystring: Type.Object({
      page: Type.Integer({ minimum: 1, default: 1 }),
      active: Type.Boolean(),
      search: Type.Optional(Type.String()),
    }),
  },
}, async (request) => {
  // Fastify coerces automatically:
  // "2" → 2 (Integer)
  // "true" → true (Boolean)
  request.query.page    // number (not string)
  request.query.active  // boolean (not string)
})
```

## What Fastify Coerces Automatically

| Schema Type | String Input | Coerced Output |
|------------|--------------|----------------|
| `Type.Integer()` | `"42"` | `42` |
| `Type.Number()` | `"3.14"` | `3.14` |
| `Type.Boolean()` | `"true"` / `"false"` | `true` / `false` |
| `Type.Boolean()` | `"1"` / `"0"` | `true` / `false` |
| `Type.Null()` | `"null"` | `null` |
| `Type.Array(Type.String())` | `"a"` (single item) | `["a"]` |

## Ajv Coercion Settings

Customize coercion behavior in Fastify:

```typescript
const fastify = Fastify({
  ajv: {
    customOptions: {
      // Default: true for querystring/params, false for body
      coerceTypes: true,

      // 'array' mode: also wrap single values in arrays
      // coerceTypes: 'array',

      // Remove properties not in schema
      removeAdditional: true,
      // Options: true, 'all', 'failing'

      // Use schema defaults for missing properties
      useDefaults: true,
    },
  },
})
```

## Default Values

### Schema-level Defaults

```typescript
const ConfigSchema = Type.Object({
  host: Type.String({ default: 'localhost' }),
  port: Type.Integer({ default: 3000 }),
  debug: Type.Boolean({ default: false }),
  logLevel: Type.Union([
    Type.Literal('debug'),
    Type.Literal('info'),
    Type.Literal('warn'),
    Type.Literal('error'),
  ], { default: 'info' }),
  maxRetries: Type.Integer({ minimum: 0, default: 3 }),
  tags: Type.Array(Type.String(), { default: [] }),
})
```

### How Defaults Work in Fastify

With `useDefaults: true` (Fastify's default), Ajv inserts default values for missing properties during validation:

```typescript
fastify.post('/config', {
  schema: {
    body: ConfigSchema,
  },
}, async (request) => {
  // If client sends: { host: 'myhost' }
  // request.body will be:
  // {
  //   host: 'myhost',        ← provided
  //   port: 3000,            ← default applied
  //   debug: false,          ← default applied
  //   logLevel: 'info',      ← default applied
  //   maxRetries: 3,         ← default applied
  //   tags: [],              ← default applied
  // }
})
```

### Default with Optional

```typescript
// Optional with default — field is filled if missing, but can be explicitly omitted
const Schema = Type.Object({
  limit: Type.Optional(Type.Integer({ default: 20 })),
})
// Missing → 20 (default applied by Ajv)
// Present → uses provided value
```

> **Note:** There's a subtlety — `Type.Optional` removes the field from `required`, and `default` fills it if absent. Together they mean "if you don't send it, you get the default."

## Value.Default — Runtime Defaults

Outside Fastify, use `Value.Default` to apply defaults:

```typescript
import { Value } from 'typebox/value'

const schema = Type.Object({
  host: Type.String({ default: 'localhost' }),
  port: Type.Integer({ default: 3000 }),
})

const partial = { host: 'myhost' }
Value.Default(schema, partial)
// partial is now { host: 'myhost', port: 3000 }
```

## Value.Convert — Manual Type Coercion

```typescript
import { Value } from 'typebox/value'

const schema = Type.Object({
  port: Type.Integer(),
  debug: Type.Boolean(),
  ratio: Type.Number(),
})

// Simulates what Fastify does for querystrings
const converted = Value.Convert(schema, {
  port: '8080',
  debug: 'true',
  ratio: '0.75',
})
// { port: 8080, debug: true, ratio: 0.75 }
```

## Common Pipeline: Convert → Default → Clean → Check

```typescript
function parseQuerystring<T extends TSchema>(schema: T, raw: Record<string, string>): Static<T> {
  // Step 1: Convert string values to proper types
  const converted = Value.Convert(schema, raw)

  // Step 2: Apply defaults for missing values
  Value.Default(schema, converted)

  // Step 3: Remove unexpected properties
  const cleaned = Value.Clean(schema, converted)

  // Step 4: Validate
  if (!Value.Check(schema, cleaned)) {
    const errors = [...Value.Errors(schema, cleaned)]
    throw new Error(`Invalid query: ${errors[0]?.message}`)
  }

  return cleaned as Static<T>
}
```

## Array Coercion for Query Params

Query strings with repeated keys create arrays, but a single value stays a string. Use Ajv's `coerceTypes: 'array'` or handle it:

```typescript
// GET /search?tag=a&tag=b → { tag: ['a', 'b'] }
// GET /search?tag=a       → { tag: 'a' }  ← not an array!

// Solution 1: Ajv array coercion
const fastify = Fastify({
  ajv: {
    customOptions: {
      coerceTypes: 'array',  // wraps single values in arrays
    },
  },
})

// Solution 2: Use Transform to always normalize to array
const TagsParam = Type.Transform(
  Type.Union([Type.String(), Type.Array(Type.String())])
)
  .Decode(v => Array.isArray(v) ? v : [v])
  .Encode(v => v)
```

## Environment Variable Parsing

```typescript
const EnvSchema = Type.Object({
  PORT: Type.Integer({ default: 3000 }),
  HOST: Type.String({ default: '0.0.0.0' }),
  DATABASE_URL: Type.String(),
  DEBUG: Type.Boolean({ default: false }),
  LOG_LEVEL: Type.Union([
    Type.Literal('debug'),
    Type.Literal('info'),
    Type.Literal('warn'),
    Type.Literal('error'),
  ], { default: 'info' }),
  MAX_CONNECTIONS: Type.Integer({ minimum: 1, default: 10 }),
})

function loadEnv() {
  const converted = Value.Convert(EnvSchema, process.env)
  Value.Default(EnvSchema, converted)
  const cleaned = Value.Clean(EnvSchema, converted)

  if (!Value.Check(EnvSchema, cleaned)) {
    const errors = [...Value.Errors(EnvSchema, cleaned)]
    console.error('Invalid environment:', errors.map(e => `${e.path}: ${e.message}`))
    process.exit(1)
  }

  return cleaned as Static<typeof EnvSchema>
}

export const env = loadEnv()
```
