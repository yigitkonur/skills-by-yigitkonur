# Standardized Error Responses

## Overview

A consistent error format across all endpoints makes APIs predictable and debuggable.
Define error schemas with TypeBox and use Fastify's error handler to enforce them.

## Error Schema

```typescript
// src/schemas/error.ts
import { Type, type Static } from '@sinclair/typebox'

export const ErrorResponse = Type.Object({
  statusCode: Type.Integer({ description: 'HTTP status code' }),
  error: Type.String({ description: 'HTTP error name' }),
  message: Type.String({ description: 'Human-readable error description' }),
  code: Type.Optional(Type.String({
    description: 'Machine-readable error code (e.g., USER_NOT_FOUND)'
  })),
  details: Type.Optional(Type.Array(Type.Object({
    field: Type.String(),
    message: Type.String(),
    value: Type.Optional(Type.Unknown())
  }), { description: 'Field-level validation errors' }))
}, { $id: 'ErrorResponse' })

export type ErrorResponseType = Static<typeof ErrorResponse>
```

## Custom Error Classes

```typescript
// src/errors.ts
export class AppError extends Error {
  constructor(
    public statusCode: number,
    public error: string,
    message: string,
    public code?: string,
    public details?: Array<{ field: string; message: string; value?: unknown }>
  ) {
    super(message)
    this.name = 'AppError'
  }

  toJSON() {
    return {
      statusCode: this.statusCode,
      error: this.error,
      message: this.message,
      ...(this.code && { code: this.code }),
      ...(this.details && { details: this.details })
    }
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(404, 'Not Found', `${resource} with id '${id}' not found`, 'RESOURCE_NOT_FOUND')
  }
}

export class ConflictError extends AppError {
  constructor(message: string, code?: string) {
    super(409, 'Conflict', message, code ?? 'CONFLICT')
  }
}

export class ForbiddenError extends AppError {
  constructor(message = 'Insufficient permissions') {
    super(403, 'Forbidden', message, 'FORBIDDEN')
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Authentication required') {
    super(401, 'Unauthorized', message, 'UNAUTHORIZED')
  }
}

export class ValidationError extends AppError {
  constructor(details: Array<{ field: string; message: string; value?: unknown }>) {
    super(400, 'Bad Request', 'Validation failed', 'VALIDATION_ERROR', details)
  }
}
```

## Global Error Handler

```typescript
// src/plugins/error-handler.ts
import fp from 'fastify-plugin'
import { AppError } from '../errors.js'

export default fp(async (app) => {
  app.setErrorHandler((error, request, reply) => {
    // Application errors
    if (error instanceof AppError) {
      return reply.status(error.statusCode).send(error.toJSON())
    }

    // Fastify validation errors (from TypeBox schemas)
    if (error.validation) {
      return reply.status(400).send({
        statusCode: 400,
        error: 'Bad Request',
        message: 'Request validation failed',
        code: 'VALIDATION_ERROR',
        details: error.validation.map(v => ({
          field: v.instancePath || v.params?.missingProperty || 'unknown',
          message: v.message ?? 'Invalid value'
        }))
      })
    }

    // Unexpected errors
    request.log.error(error, 'Unhandled error')

    const statusCode = error.statusCode ?? 500
    return reply.status(statusCode).send({
      statusCode,
      error: statusCode >= 500 ? 'Internal Server Error' : 'Error',
      message: statusCode >= 500
        ? 'An unexpected error occurred'  // Don't leak internals
        : error.message
    })
  })

  // Handle 404 for undefined routes
  app.setNotFoundHandler((request, reply) => {
    reply.status(404).send({
      statusCode: 404,
      error: 'Not Found',
      message: `Route ${request.method} ${request.url} not found`
    })
  })
})
```

## Using Errors in Routes

```typescript
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'
import { ErrorResponse } from '../schemas/error.js'
import { NotFoundError, ConflictError } from '../errors.js'

const routes: FastifyPluginAsyncTypebox = async (app) => {
  app.post('/users', {
    schema: {
      body: Type.Object({
        email: Type.String({ format: 'email' }),
        name: Type.String({ minLength: 2 })
      }),
      response: {
        201: UserSchema,
        400: ErrorResponse,
        409: ErrorResponse
      }
    }
  }, async (request, reply) => {
    const existing = await app.userRepo.findByEmail(request.body.email)
    if (existing) {
      throw new ConflictError('Email already registered', 'EMAIL_EXISTS')
    }

    const user = await app.userRepo.create(request.body)
    reply.status(201)
    return user
  })

  app.get('/users/:id', {
    schema: {
      params: Type.Object({ id: Type.String({ format: 'uuid' }) }),
      response: {
        200: UserSchema,
        404: ErrorResponse
      }
    }
  }, async (request) => {
    const user = await app.userRepo.findById(request.params.id)
    if (!user) {
      throw new NotFoundError('User', request.params.id)
    }
    return user
  })
}
```

## Example Error Responses

```json
// 400 Validation Error
{
  "statusCode": 400,
  "error": "Bad Request",
  "message": "Request validation failed",
  "code": "VALIDATION_ERROR",
  "details": [
    { "field": "/email", "message": "must match format \"email\"" },
    { "field": "/name", "message": "must NOT have fewer than 2 characters" }
  ]
}

// 404 Not Found
{
  "statusCode": 404,
  "error": "Not Found",
  "message": "User with id '550e8400-...' not found",
  "code": "RESOURCE_NOT_FOUND"
}

// 500 Internal Server Error (no details leaked)
{
  "statusCode": 500,
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

## Key Points

- Define a single `ErrorResponse` schema used across all error responses
- Use custom error classes with `throw` -- the error handler catches them
- Never expose internal error details in 500 responses
- Map Fastify validation errors to your standardized format
- Include machine-readable `code` fields for client-side error handling
- Register the error handler plugin before route plugins
