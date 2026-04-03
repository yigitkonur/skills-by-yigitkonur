# TypeMap and Standard Schema

## What is TypeMap?

`@sinclair/typemap` (TypeMap) bridges TypeBox with the Standard Schema specification. It provides a way to create schemas that are compatible with the evolving Standard Schema ecosystem while still generating TypeBox schemas under the hood.

```typescript
import { TypeMap } from '@sinclair/typemap'
```

## Standard Schema

Standard Schema is a shared interface that schema libraries (Zod, Valibot, ArkType, TypeBox) can implement, allowing frameworks to accept schemas from any compliant library.

TypeBox itself can participate via TypeMap.

## TypeMap Basics

TypeMap provides a mapping syntax that translates to TypeBox schemas:

```typescript
import { TypeMap } from '@sinclair/typemap'

// Define schemas using TypeMap's mapping syntax
const StringSchema = TypeMap.Map('string')           // → Type.String()
const NumberSchema = TypeMap.Map('number')           // → Type.Number()
const BooleanSchema = TypeMap.Map('boolean')         // → Type.Boolean()

// Objects
const UserSchema = TypeMap.Map({
  name: 'string',
  age: 'number',
  active: 'boolean',
})
// Equivalent to:
// Type.Object({ name: Type.String(), age: Type.Number(), active: Type.Boolean() })
```

## TypeMap Translation Functions

```typescript
import { TypeMap } from '@sinclair/typemap'

// From TypeBox to Standard Schema compatible representation
const schema = TypeMap.Map({
  id: 'string',
  email: 'string',
  count: 'number',
})

// The result is a standard TypeBox schema
// that can be used with TypeCompiler, Value.Check, Fastify, etc.
```

## Using TypeMap with Fastify

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { TypeMap } from '@sinclair/typemap'

const fastify = Fastify().withTypeProvider<TypeBoxTypeProvider>()

const CreateUserSchema = TypeMap.Map({
  name: 'string',
  email: 'string',
})

fastify.post('/users', {
  schema: {
    body: CreateUserSchema,
  },
}, async (request) => {
  // request.body is typed as { name: string; email: string }
  return { ok: true }
})
```

## TypeMap Syntax Reference

```typescript
// Primitives
TypeMap.Map('string')            // Type.String()
TypeMap.Map('number')            // Type.Number()
TypeMap.Map('boolean')           // Type.Boolean()
TypeMap.Map('integer')           // Type.Integer()
TypeMap.Map('null')              // Type.Null()
TypeMap.Map('undefined')         // Type.Undefined()
TypeMap.Map('unknown')           // Type.Unknown()
TypeMap.Map('any')               // Type.Any()

// Arrays
TypeMap.Map('string[]')          // Type.Array(Type.String())
TypeMap.Map('number[]')          // Type.Array(Type.Number())

// Unions
TypeMap.Map('string | number')   // Type.Union([Type.String(), Type.Number()])
TypeMap.Map("'a' | 'b' | 'c'")  // Type.Union([Type.Literal('a'), ...])

// Objects
TypeMap.Map({
  name: 'string',
  age: 'number',
  tags: 'string[]',
})

// Optional properties
TypeMap.Map({
  name: 'string',
  bio: 'string | undefined',     // optional
})

// Nested objects
TypeMap.Map({
  user: {
    name: 'string',
    address: {
      street: 'string',
      city: 'string',
    },
  },
})
```

## Standard Schema Interface

The Standard Schema spec defines a minimal interface that any schema library can implement:

```typescript
interface StandardSchemaV1<Input, Output> {
  readonly '~standard': {
    readonly version: 1
    readonly vendor: string
    readonly validate: (value: unknown) => StandardResult<Output>
    readonly types?: {
      readonly input: Input
      readonly output: Output
    }
  }
}
```

TypeBox schemas can be made Standard Schema compliant:

```typescript
import { Type } from 'typebox'
import { TypeCompiler } from 'typebox/compiler'

// A wrapper to make TypeBox schemas Standard Schema compatible
function toStandardSchema<T extends TSchema>(schema: T) {
  const compiled = TypeCompiler.Compile(schema)
  return {
    '~standard': {
      version: 1 as const,
      vendor: 'typebox',
      validate(value: unknown) {
        if (compiled.Check(value)) {
          return { value: value as Static<T> }
        }
        const issues = [...compiled.Errors(value)].map(e => ({
          message: e.message,
          path: e.path.split('/').filter(Boolean),
        }))
        return { issues }
      },
      types: undefined as unknown as {
        input: Static<T>
        output: Static<T>
      },
    },
  }
}
```

## When to Use TypeMap

Use TypeMap when:
- You want a more concise syntax for simple schemas
- You need Standard Schema compliance for framework interoperability
- You are building a library that should work with any schema library

Stick with direct `Type.*` when:
- You need advanced features (Transform, Recursive, Ref)
- You want full control over JSON Schema output
- You are building a Fastify API (Type.* integrates natively)

## Installation

```bash
npm install @sinclair/typemap
```

TypeMap is a separate package from TypeBox. It depends on TypeBox as a peer dependency.

## TypeMap with Validation

```typescript
import { TypeMap } from '@sinclair/typemap'
import { Value } from 'typebox/value'
import { TypeCompiler } from 'typebox/compiler'

const schema = TypeMap.Map({
  name: 'string',
  email: 'string',
  age: 'number',
})

// Works with all TypeBox validation methods
Value.Check(schema, { name: 'Alice', email: 'a@b.com', age: 30 })  // true

const compiled = TypeCompiler.Compile(schema)
compiled.Check({ name: 'Alice', email: 'a@b.com', age: 30 })       // true
```
