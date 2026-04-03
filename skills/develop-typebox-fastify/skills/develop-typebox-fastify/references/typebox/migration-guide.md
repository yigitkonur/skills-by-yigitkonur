# TypeBox Migration Guide

## Package Rename: @sinclair/typebox → typebox

TypeBox was renamed from `@sinclair/typebox` to `typebox`. Both work, but new projects should use `typebox`.

### Import Changes

```typescript
// Before (legacy — still works)
import { Type, Static } from '@sinclair/typebox'
import { Value } from '@sinclair/typebox/value'
import { TypeCompiler } from '@sinclair/typebox/compiler'

// After (new package name)
import { Type, Static } from 'typebox'
import { Value } from 'typebox/value'
import { TypeCompiler } from 'typebox/compiler'
```

### Migration Steps

1. Install the new package:
```bash
npm install typebox
npm uninstall @sinclair/typebox
```

2. Find and replace imports:
```bash
# Find all files with old imports
grep -r "@sinclair/typebox" src/

# Replace (use your editor or sed)
# @sinclair/typebox/value → typebox/value
# @sinclair/typebox/compiler → typebox/compiler
# @sinclair/typebox → typebox
```

3. No API changes — the API is identical. Only the package name changed.

4. `@fastify/type-provider-typebox` works with both package names.

## Zod to TypeBox Migration

### Why Migrate?

- TypeBox generates standard JSON Schema (native Fastify integration)
- No serialization step needed for Fastify schemas
- TypeCompiler is faster than Zod's parse for validation
- Smaller bundle size
- Better Fastify DX (auto-inferred route types)

### Type Mapping: Zod → TypeBox

```typescript
// ─── Primitives ───
z.string()                    → Type.String()
z.number()                    → Type.Number()
z.boolean()                   → Type.Boolean()
z.null()                      → Type.Null()
z.undefined()                 → Type.Undefined()
z.any()                       → Type.Any()
z.unknown()                   → Type.Unknown()
z.never()                     → Type.Never()
z.void()                      → Type.Void()

// ─── String Constraints ───
z.string().min(1)             → Type.String({ minLength: 1 })
z.string().max(100)           → Type.String({ maxLength: 100 })
z.string().email()            → Type.String({ format: 'email' })
z.string().url()              → Type.String({ format: 'uri' })
z.string().uuid()             → Type.String({ format: 'uuid' })
z.string().datetime()         → Type.String({ format: 'date-time' })
z.string().regex(/pattern/)   → Type.String({ pattern: 'pattern' })

// ─── Number Constraints ───
z.number().min(0)             → Type.Number({ minimum: 0 })
z.number().max(100)           → Type.Number({ maximum: 100 })
z.number().int()              → Type.Integer()
z.number().positive()         → Type.Number({ exclusiveMinimum: 0 })
z.number().nonnegative()      → Type.Number({ minimum: 0 })

// ─── Objects ───
z.object({ name: z.string() })  → Type.Object({ name: Type.String() })
z.object({}).strict()            → Type.Object({}, { additionalProperties: false })
z.object({}).passthrough()       → Type.Object({})  // default behavior

// ─── Arrays ───
z.array(z.string())           → Type.Array(Type.String())
z.array(z.string()).min(1)    → Type.Array(Type.String(), { minItems: 1 })
z.array(z.string()).max(10)   → Type.Array(Type.String(), { maxItems: 10 })

// ─── Composition ───
z.union([z.string(), z.number()])     → Type.Union([Type.String(), Type.Number()])
z.intersection(schemaA, schemaB)      → Type.Intersect([schemaA, schemaB])
schema.pick({ name: true })           → Type.Pick(schema, ['name'])
schema.omit({ password: true })       → Type.Omit(schema, ['password'])
schema.partial()                      → Type.Partial(schema)
schema.required()                     → Type.Required(schema)

// ─── Optional / Nullable ───
z.string().optional()         → Type.Optional(Type.String())
z.string().nullable()         → Type.Union([Type.String(), Type.Null()])
z.string().nullish()          → Type.Optional(Type.Union([Type.String(), Type.Null()]))

// ─── Literals / Enums ───
z.literal('admin')            → Type.Literal('admin')
z.enum(['a', 'b', 'c'])      → Type.Union([Type.Literal('a'), Type.Literal('b'), Type.Literal('c')])
z.nativeEnum(MyEnum)          → Type.Enum(MyEnum)

// ─── Records / Maps ───
z.record(z.string(), z.number())  → Type.Record(Type.String(), Type.Number())

// ─── Tuples ───
z.tuple([z.string(), z.number()])  → Type.Tuple([Type.String(), Type.Number()])

// ─── Default Values ───
z.string().default('hello')   → Type.String({ default: 'hello' })

// ─── Type Inference ───
z.infer<typeof schema>        → Static<typeof schema>
```

### Validation: Zod → TypeBox

```typescript
// ─── Zod ───
const result = schema.safeParse(data)
if (!result.success) {
  console.log(result.error.issues)
}
const parsed = schema.parse(data) // throws on failure

// ─── TypeBox (quick) ───
import { Value } from 'typebox/value'
if (!Value.Check(schema, data)) {
  const errors = [...Value.Errors(schema, data)]
}

// ─── TypeBox (fast) ───
import { TypeCompiler } from 'typebox/compiler'
const validator = TypeCompiler.Compile(schema)
if (!validator.Check(data)) {
  const errors = [...validator.Errors(data)]
}
```

### Transforms: Zod → TypeBox

```typescript
// ─── Zod ───
const DateSchema = z.string().datetime().transform(v => new Date(v))

// ─── TypeBox ───
const DateSchema = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(v => new Date(v))
  .Encode(v => v.toISOString())
```

### Refinements: Zod → TypeBox

```typescript
// ─── Zod ───
const PasswordSchema = z.string().refine(
  v => v.length >= 8 && /[A-Z]/.test(v) && /\d/.test(v),
  'Password must be 8+ chars with uppercase and digit'
)

// ─── TypeBox ───
// Option 1: Use pattern constraint
const PasswordSchema = Type.String({
  minLength: 8,
  pattern: '(?=.*[A-Z])(?=.*\\d)',
})

// Option 2: Validate after schema check
const PasswordSchema = Type.String({ minLength: 8 })
// Then add custom validation in your handler/service
```

### Complete Migration Example

```typescript
// ─── Before: Zod ───
import { z } from 'zod'

const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).optional(),
  role: z.enum(['admin', 'user']).default('user'),
  tags: z.array(z.string()).max(10).default([]),
})
type CreateUser = z.infer<typeof CreateUserSchema>

// ─── After: TypeBox ───
import { Type, type Static } from 'typebox'

const CreateUserSchema = Type.Object({
  name: Type.String({ minLength: 1, maxLength: 100 }),
  email: Type.String({ format: 'email' }),
  age: Type.Optional(Type.Integer({ minimum: 0 })),
  role: Type.Union([Type.Literal('admin'), Type.Literal('user')], { default: 'user' }),
  tags: Type.Array(Type.String(), { maxItems: 10, default: [] }),
})
type CreateUser = Static<typeof CreateUserSchema>
```

## Key Behavioral Differences

| Behavior | Zod | TypeBox |
|----------|-----|---------|
| Strips unknown keys | `.strict()` rejects, default strips | Depends on Ajv `removeAdditional` setting |
| Coercion | `z.coerce.*` | Fastify/Ajv coercion or `Value.Convert` |
| Async validation | `schema.parseAsync()` | Not built-in (handle in app code) |
| Error format | `ZodError` with `issues[]` | Iterator of `ValueError` objects |
| Schema output | Not JSON Schema | IS JSON Schema |
