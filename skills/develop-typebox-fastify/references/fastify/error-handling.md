# Fastify Error Handling

## Custom Error Classes with @fastify/error

```typescript
import createError from '@fastify/error'

const NotFoundError = createError('NOT_FOUND', '%s not found', 404)
const UnauthorizedError = createError('UNAUTHORIZED', 'Authentication required', 401)
const ForbiddenError = createError('FORBIDDEN', 'Access denied: %s', 403)
const ValidationError = createError('VALIDATION_ERROR', '%s', 400)
const ConflictError = createError('CONFLICT', '%s already exists', 409)

// Usage in routes
app.get('/users/:id', async (request) => {
  const user = await findUser(request.params.id)
  if (!user) throw new NotFoundError('User')
  return user
})

app.post('/users', async (request) => {
  const exists = await userExists(request.body.email)
  if (exists) throw new ConflictError('Email')
  return createUser(request.body)
})
```

## Custom Error Handler

```typescript
import Fastify from 'fastify'
import { Type } from '@sinclair/typebox'
import type { FastifyError, FastifyRequest, FastifyReply } from 'fastify'

const app = Fastify({ logger: true })

app.setErrorHandler((error: FastifyError, request: FastifyRequest, reply: FastifyReply) => {
  request.log.error({ err: error }, 'Request error')

  // Handle validation errors specially
  if (error.validation) {
    return reply.code(400).send({
      statusCode: 400,
      error: 'Validation Error',
      message: 'Request validation failed',
      details: error.validation.map((err) => ({
        field: err.instancePath?.slice(1).replace(/\//g, '.') || err.params?.missingProperty || 'unknown',
        message: err.message,
      })),
    })
  }

  // Known errors with status codes
  const statusCode = error.statusCode ?? 500
  const message = statusCode >= 500 && process.env.NODE_ENV === 'production'
    ? 'Internal Server Error'
    : error.message

  return reply.code(statusCode).send({
    statusCode,
    error: error.code ?? 'INTERNAL_ERROR',
    message,
  })
})
```

## Error Response Schema with TypeBox

```typescript
const ErrorResponse = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String(),
  details: Type.Optional(Type.Array(Type.Object({
    field: Type.String(),
    message: Type.String(),
  }))),
})

// Use in route schemas
app.get('/users/:id', {
  schema: {
    params: Type.Object({ id: Type.String({ format: 'uuid' }) }),
    response: {
      200: UserSchema,
      404: ErrorResponse,
      500: ErrorResponse,
    },
  },
}, async (request, reply) => {
  const user = await findUser(request.params.id)
  if (!user) {
    reply.code(404)
    return { statusCode: 404, error: 'NOT_FOUND', message: 'User not found' }
  }
  return user
})
```

## Reply Helpers with @fastify/sensible

```typescript
import fastifySensible from '@fastify/sensible'

app.register(fastifySensible)

app.get('/users/:id', async (request, reply) => {
  const user = await findUser(request.params.id)
  if (!user) return reply.notFound('User not found')
  if (!hasAccess(request.user, user)) return reply.forbidden('Access denied')
  return user
})

// Available: reply.badRequest(), reply.unauthorized(), reply.forbidden(),
// reply.notFound(), reply.conflict(), reply.tooManyRequests(),
// reply.internalServerError(), reply.serviceUnavailable()
```

## Async Error Handling

Errors in async handlers are automatically caught:

```typescript
app.get('/users', async () => {
  const users = await db.users.findAll() // if this throws, error handler catches it
  return users
})

// Wrap external errors with context
app.get('/users/:id', async (request, reply) => {
  try {
    return await db.users.findById(request.params.id)
  } catch (error) {
    if (error.code === 'CONNECTION_ERROR') {
      request.log.error({ err: error }, 'Database connection failed')
      return reply.code(503).send({ error: 'Service temporarily unavailable' })
    }
    throw error // re-throw for error handler
  }
})
```

## Error Cause Chain

```typescript
import createError from '@fastify/error'

const DatabaseError = createError('DATABASE_ERROR', 'Database operation failed: %s', 500)

app.get('/users/:id', async (request) => {
  try {
    return await db.users.findById(request.params.id)
  } catch (error) {
    throw new DatabaseError(error.message, { cause: error })
  }
})

// Log the full chain in error handler
app.setErrorHandler((error, request, reply) => {
  let current = error
  const chain = []
  while (current) {
    chain.push({ message: current.message, code: current.code })
    current = current.cause
  }
  request.log.error({ errorChain: chain }, 'Request failed')
  reply.code(error.statusCode || 500).send({ error: error.message })
})
```

## Plugin-Scoped Error Handlers

```typescript
app.register(async function apiRoutes(fastify) {
  // Error handler only for routes in this plugin
  fastify.setErrorHandler((error, request, reply) => {
    reply.code(error.statusCode || 500).send({
      error: { code: error.code || 'API_ERROR', message: error.message },
    })
  })

  fastify.get('/data', async () => {
    throw new Error('API-specific error')
  })
}, { prefix: '/api' })
```

## Graceful Error Recovery

```typescript
app.get('/dashboard', {
  schema: {
    response: {
      200: Type.Object({
        primary: Type.Unknown(),
        secondary: Type.Union([Type.Unknown(), Type.Null()]),
        warnings: Type.Array(Type.String()),
      }),
    },
  },
}, async () => {
  const results = await Promise.allSettled([
    fetchPrimaryData(),
    fetchSecondaryData(),
  ])

  const [primary, secondary] = results

  if (primary.status === 'rejected') {
    throw new Error('Primary data unavailable')
  }

  return {
    primary: primary.value,
    secondary: secondary.status === 'fulfilled' ? secondary.value : null,
    warnings: results
      .filter((r) => r.status === 'rejected')
      .map((r) => r.reason.message),
  }
})
```

## Custom Not Found Handler

```typescript
app.setNotFoundHandler(async (request, reply) => {
  reply.code(404)
  return {
    statusCode: 404,
    error: 'Not Found',
    message: `Route ${request.method} ${request.url} not found`,
  }
})
```

## Validation Error Customization

```typescript
app.setErrorHandler((error, request, reply) => {
  if (error.validation) {
    const details = error.validation.map((err) => ({
      field: err.instancePath ? err.instancePath.slice(1) : err.params?.missingProperty || 'unknown',
      message: err.message,
      context: error.validationContext, // 'body', 'querystring', 'params', 'headers'
    }))

    return reply.code(400).send({
      statusCode: 400,
      error: 'Validation Error',
      message: `Invalid ${error.validationContext}: ${details.map(d => d.field).join(', ')}`,
      details,
    })
  }

  throw error
})
```
