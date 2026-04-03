# TypeBox + Fastify Quick Reference

## TypeBox type constructors

```typescript
import { Type, type Static } from '@fastify/type-provider-typebox'
// or: import { Type, type Static } from '@sinclair/typebox'
// or: import { Type, type Static } from 'typebox'

// Primitives
Type.String()                                    // { type: 'string' }
Type.String({ minLength: 1, maxLength: 100 })   // with constraints
Type.String({ format: 'email' })                 // with format
Type.String({ format: 'uuid' })                  // UUID format
Type.Number()                                    // { type: 'number' }
Type.Integer()                                   // { type: 'integer' }
Type.Integer({ minimum: 0, maximum: 100 })       // with range
Type.Boolean()                                   // { type: 'boolean' }
Type.Null()                                      // { type: 'null' }

// Objects
Type.Object({                                    // { type: 'object', properties: {...} }
  name: Type.String(),
  age: Type.Optional(Type.Integer()),
})

// Arrays
Type.Array(Type.String())                        // { type: 'array', items: { type: 'string' } }
Type.Array(Type.String(), { minItems: 1 })       // non-empty array

// Optional (omittable, not nullable)
Type.Optional(Type.String())                     // can be missing from object

// Nullable (present but null)
Type.Union([Type.String(), Type.Null()])          // string | null

// Enums
Type.Union([
  Type.Literal('active'),
  Type.Literal('inactive'),
])                                                // 'active' | 'inactive'

// Composition
Type.Intersect([SchemaA, SchemaB])               // A & B
Type.Pick(Schema, ['id', 'name'])                // Pick<T, 'id' | 'name'>
Type.Omit(Schema, ['password'])                  // Omit<T, 'password'>
Type.Partial(Schema)                             // Partial<T>
Type.Required(Schema)                            // Required<T>
Type.Record(Type.String(), Type.Unknown())       // Record<string, unknown>

// Type extraction
type User = Static<typeof UserSchema>            // TypeScript type from schema
```

## Fastify + TypeBox setup

```typescript
import Fastify from 'fastify'
import { Type, TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify({ logger: true })
  .withTypeProvider<TypeBoxTypeProvider>()
```

## Route with full schema

```typescript
app.post('/users', {
  schema: {
    body: Type.Object({
      name: Type.String({ minLength: 1 }),
      email: Type.String({ format: 'email' }),
    }),
    response: {
      201: Type.Object({
        id: Type.String({ format: 'uuid' }),
        name: Type.String(),
        email: Type.String(),
      }),
      400: Type.Object({
        statusCode: Type.Integer(),
        error: Type.String(),
        message: Type.String(),
      }),
    },
  },
}, async (request, reply) => {
  // request.body is typed: { name: string; email: string }
  const user = await createUser(request.body)
  reply.code(201)
  return user
})
```

## Plugin pattern

```typescript
import fp from 'fastify-plugin'
import type { FastifyPluginAsync } from 'fastify'

// For shared plugins (decorators visible everywhere)
const myPlugin: FastifyPluginAsync = async (fastify) => {
  fastify.decorate('myService', new MyService())
}
export default fp(myPlugin, { name: 'my-plugin' })

// For route plugins (encapsulated)
const routes: FastifyPluginAsync = async (fastify) => {
  fastify.get('/', async () => ({ status: 'ok' }))
}
export default routes
```

## Testing

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest'

let app: FastifyInstance

beforeAll(async () => {
  app = buildApp()
  await app.ready()
})

afterAll(() => app.close())

it('should return 200', async () => {
  const res = await app.inject({ method: 'GET', url: '/health' })
  expect(res.statusCode).toBe(200)
})
```

## Hook lifecycle order

```
onRequest → preParsing → preValidation → preHandler → Handler
→ preSerialization → onSend → onResponse
(onError on failure)
```

## Common hooks

```typescript
// Auth check (runs before body parsing)
app.addHook('onRequest', async (request, reply) => {
  const token = request.headers.authorization?.replace('Bearer ', '')
  if (!token) return reply.code(401).send({ error: 'Unauthorized' })
  request.user = await verifyToken(token)
})

// Authorization (runs after validation)
app.addHook('preHandler', async (request, reply) => {
  if (request.user.role !== 'admin')
    return reply.code(403).send({ error: 'Forbidden' })
})
```

## Error handling

```typescript
import createError from '@fastify/error'

const NotFoundError = createError('NOT_FOUND', '%s not found', 404)

app.setErrorHandler((error, request, reply) => {
  if (error.validation) {
    return reply.code(400).send({
      statusCode: 400,
      error: 'Validation Error',
      details: error.validation,
    })
  }
  const status = error.statusCode ?? 500
  reply.code(status).send({
    statusCode: status,
    error: error.code ?? 'INTERNAL_ERROR',
    message: status >= 500 ? 'Internal Server Error' : error.message,
  })
})
```

## OpenAPI

```typescript
import fastifySwagger from '@fastify/swagger'
import fastifySwaggerUi from '@fastify/swagger-ui'

await app.register(fastifySwagger, {
  openapi: { info: { title: 'My API', version: '1.0.0' } },
})
await app.register(fastifySwaggerUi, { routePrefix: '/docs' })
```
