# TypeBox Type Provider Setup

## Overview

The `@fastify/type-provider-typebox` package bridges TypeBox schemas with Fastify's type system,
giving you full request/response type inference from your schemas with zero runtime overhead.

## Installation

```bash
npm install fastify @sinclair/typebox @fastify/type-provider-typebox
```

## Basic Setup with withTypeProvider

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

// Create the Fastify instance and apply the type provider
const app = Fastify({
  logger: true
}).withTypeProvider<TypeBoxTypeProvider>()

// Now all route schemas produce TypeBox-inferred types
app.get('/hello', {
  schema: {
    querystring: Type.Object({
      name: Type.String()
    }),
    response: {
      200: Type.Object({
        greeting: Type.String()
      })
    }
  }
}, async (request, reply) => {
  // request.query.name is typed as string
  return { greeting: `Hello, ${request.query.name}` }
})
```

## Plugin Pattern with FastifyPluginAsyncTypebox

For encapsulated plugins, use `FastifyPluginAsyncTypebox` to carry the type provider
through without re-declaring it:

```typescript
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'

const userRoutes: FastifyPluginAsyncTypebox = async (app) => {
  // app already has TypeBoxTypeProvider — no withTypeProvider needed

  app.get('/users/:id', {
    schema: {
      params: Type.Object({
        id: Type.String({ format: 'uuid' })
      }),
      response: {
        200: Type.Object({
          id: Type.String(),
          name: Type.String(),
          email: Type.String({ format: 'email' })
        })
      }
    }
  }, async (request) => {
    const { id } = request.params // typed as { id: string }
    return { id, name: 'Alice', email: 'alice@example.com' }
  })
}

export default userRoutes
```

## Registering Plugins

```typescript
// server.ts
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import userRoutes from './routes/users.js'

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()

// Register the plugin — type provider flows through
app.register(userRoutes, { prefix: '/api' })

await app.listen({ port: 3000 })
```

## TypeBoxValidatorCompiler (Ajv Alternative)

By default Fastify uses Ajv. The type provider package also exports a dedicated
validator compiler that uses TypeBox's own `TypeCompiler` for faster validation:

```typescript
import Fastify from 'fastify'
import {
  TypeBoxTypeProvider,
  TypeBoxValidatorCompiler
} from '@fastify/type-provider-typebox'

const app = Fastify()
  .withTypeProvider<TypeBoxTypeProvider>()
  .setValidatorCompiler(TypeBoxValidatorCompiler)
```

This gives ~2-3x faster validation than Ajv for most schemas, because TypeBox compiles
schemas to optimized validation functions at startup.

## Shared App Type

Export a reusable app type for use in route files:

```typescript
// types/app.ts
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()
export type FastifyApp = typeof app
```

## Key Points

- Always call `.withTypeProvider<TypeBoxTypeProvider>()` on the root instance
- Use `FastifyPluginAsyncTypebox` for plugin files to avoid repeating the generic
- The type provider is compile-time only -- zero runtime cost
- Combine with `TypeBoxValidatorCompiler` for fastest schema validation
- TypeBox schemas double as both validation and TypeScript types
