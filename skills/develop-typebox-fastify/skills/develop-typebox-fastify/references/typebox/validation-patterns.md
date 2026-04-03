# TypeBox Validation Patterns

## Request Validation in Fastify

Fastify validates requests automatically when you provide schemas:

```typescript
import Fastify from 'fastify'
import { Type } from 'typebox'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const fastify = Fastify().withTypeProvider<TypeBoxTypeProvider>()

fastify.post('/users', {
  schema: {
    body: Type.Object({
      name: Type.String({ minLength: 1 }),
      email: Type.String({ format: 'email' }),
    }),
    querystring: Type.Object({
      dryRun: Type.Optional(Type.Boolean()),
    }),
    params: Type.Object({
      // (for /users/:id routes)
    }),
    headers: Type.Object({
      'x-api-key': Type.String(),
    }),
  },
}, async (request) => {
  // All validated and typed. If validation fails, Fastify returns 400 automatically
  const { name, email } = request.body
  return { name, email }
})
```

## Custom Error Formatting

Override Fastify's default validation error response:

```typescript
const fastify = Fastify({
  ajv: {
    customOptions: {
      allErrors: true,  // collect all errors, not just the first
    },
  },
})

// Custom error handler for validation errors
fastify.setErrorHandler((error, request, reply) => {
  if (error.validation) {
    return reply.status(400).send({
      statusCode: 400,
      error: 'Validation Error',
      message: 'Request validation failed',
      details: error.validation.map(err => ({
        field: err.instancePath.replace(/^\//, '').replace(/\//g, '.') || err.params?.missingProperty || 'unknown',
        message: err.message || 'Invalid value',
        constraint: err.keyword,
      })),
    })
  }

  // Handle other errors
  reply.status(error.statusCode || 500).send({
    statusCode: error.statusCode || 500,
    error: error.name,
    message: error.message,
  })
})
```

## Schema-level Validation with Ajv Keywords

Add custom validation keywords for cross-field logic:

```typescript
import Fastify from 'fastify'

const fastify = Fastify({
  ajv: {
    plugins: [
      function addCustomKeywords(ajv) {
        // Cross-field: password confirmation
        ajv.addKeyword({
          keyword: 'passwordMatch',
          type: 'object',
          validate: function validatePasswordMatch(
            schema: boolean,
            data: { password?: string; confirmPassword?: string }
          ) {
            if (!schema) return true
            return data.password === data.confirmPassword
          },
          error: {
            message: 'Passwords must match',
          },
        })
      },
    ],
  },
})

// Use in schema via Type.Unsafe for the custom keyword
const RegisterBody = Type.Intersect([
  Type.Object({
    email: Type.String({ format: 'email' }),
    password: Type.String({ minLength: 8 }),
    confirmPassword: Type.String(),
  }),
  Type.Unsafe({ passwordMatch: true }),
])
```

## Validation Outside Route Handlers

Use TypeCompiler for validation in services, workers, or tests:

```typescript
import { TypeCompiler } from 'typebox/compiler'
import { Type, type Static } from 'typebox'

const EventSchema = Type.Object({
  type: Type.String(),
  payload: Type.Unknown(),
  timestamp: Type.String({ format: 'date-time' }),
})
type Event = Static<typeof EventSchema>

const eventValidator = TypeCompiler.Compile(EventSchema)

// In a message queue consumer
async function processMessage(raw: string): void {
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    logger.error('Invalid JSON')
    return
  }

  if (!eventValidator.Check(parsed)) {
    const errors = [...eventValidator.Errors(parsed)]
    logger.warn('Invalid event', { errors: errors.map(e => ({ path: e.path, message: e.message })) })
    return
  }

  // parsed is now typed as Event
  await handleEvent(parsed as Event)
}
```

## Validation Pipeline Pattern

```typescript
import { Value } from 'typebox/value'
import { TypeCompiler } from 'typebox/compiler'
import { type TSchema, type Static } from 'typebox'

class Validator<T extends TSchema> {
  private compiled

  constructor(private schema: T) {
    this.compiled = TypeCompiler.Compile(schema)
  }

  check(data: unknown): data is Static<T> {
    return this.compiled.Check(data)
  }

  parse(data: unknown): Static<T> {
    // Apply defaults
    Value.Default(this.schema, data)
    // Convert types (string → number, etc.)
    const converted = Value.Convert(this.schema, data)
    // Clean extra properties
    const cleaned = Value.Clean(this.schema, converted)
    // Validate
    if (!this.compiled.Check(cleaned)) {
      const errors = [...this.compiled.Errors(cleaned)]
      throw new ValidationError(errors)
    }
    return cleaned as Static<T>
  }

  errors(data: unknown) {
    return [...this.compiled.Errors(data)]
  }
}

// Usage
const userValidator = new Validator(UserSchema)
const user = userValidator.parse(rawInput)
```

## Conditional Validation in Handlers

Sometimes you need validation logic that goes beyond JSON Schema:

```typescript
fastify.post('/transfers', {
  schema: {
    body: Type.Object({
      fromAccount: Type.String(),
      toAccount: Type.String(),
      amount: Type.Number({ minimum: 0.01 }),
      currency: Type.String({ minLength: 3, maxLength: 3 }),
    }),
  },
}, async (request, reply) => {
  const { fromAccount, toAccount, amount } = request.body

  // Business rule: can't transfer to yourself
  if (fromAccount === toAccount) {
    return reply.status(422).send({
      statusCode: 422,
      error: 'Unprocessable Entity',
      message: 'Cannot transfer to the same account',
    })
  }

  // Business rule: daily limit check (requires DB)
  const dailyTotal = await getDailyTransferTotal(fromAccount)
  if (dailyTotal + amount > 10000) {
    return reply.status(422).send({
      statusCode: 422,
      error: 'Unprocessable Entity',
      message: 'Daily transfer limit exceeded',
    })
  }

  // Proceed with transfer
})
```

## Pre-validation Hook

Validate or transform data before it reaches the route handler:

```typescript
fastify.addHook('preValidation', async (request) => {
  // Normalize headers before validation
  if (request.headers['content-type']?.includes('application/json')) {
    // Already handled by Fastify
  }
})

fastify.addHook('preHandler', async (request, reply) => {
  // Additional validation after schema validation passes
  // Useful for auth checks, rate limiting, etc.
})
```

## Response Validation

Fastify can also validate responses (useful in development):

```typescript
fastify.get('/users/:id', {
  schema: {
    response: {
      200: Type.Object({
        id: Type.String(),
        name: Type.String(),
        email: Type.String(),
      }),
    },
  },
}, handler)

// Response validation serializes output — it REMOVES fields not in the schema
// This acts as a security filter, preventing accidental data leaks (e.g., password hash)
```

## Shared Validation Schemas

```typescript
// Common validation schemas that can be reused across routes
export const IdParam = Type.Object({
  id: Type.String({ format: 'uuid' }),
})

export const SlugParam = Type.Object({
  slug: Type.String({ pattern: '^[a-z0-9]+(?:-[a-z0-9]+)*$' }),
})

export const SearchQuery = Type.Object({
  q: Type.Optional(Type.String({ minLength: 1, maxLength: 200 })),
  page: Type.Integer({ minimum: 1, default: 1 }),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
})
```
