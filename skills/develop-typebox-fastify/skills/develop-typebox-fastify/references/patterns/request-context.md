# Request Context: Correlation IDs and Request-Scoped Decorators

## Overview

Request context provides per-request metadata like correlation IDs, authenticated user info,
and timing data. Fastify decorators + TypeBox schemas make this type-safe.

## Correlation IDs

Track requests across services with a unique ID:

```typescript
// src/plugins/request-context.ts
import fp from 'fastify-plugin'
import { randomUUID } from 'node:crypto'

declare module 'fastify' {
  interface FastifyRequest {
    requestId: string
    startTime: bigint
  }
}

export default fp(async (app) => {
  app.decorateRequest('requestId', '')
  app.decorateRequest('startTime', 0n)

  app.addHook('onRequest', async (request, reply) => {
    // Use client-provided ID or generate one
    request.requestId = (request.headers['x-request-id'] as string) ?? randomUUID()
    request.startTime = process.hrtime.bigint()

    // Echo the ID back in the response
    reply.header('x-request-id', request.requestId)
  })

  app.addHook('onResponse', async (request, reply) => {
    const duration = Number(process.hrtime.bigint() - request.startTime) / 1e6
    request.log.info({
      requestId: request.requestId,
      method: request.method,
      url: request.url,
      statusCode: reply.statusCode,
      durationMs: Math.round(duration * 100) / 100
    }, 'request completed')
  })
})
```

## Request Header Schema with Correlation ID

```typescript
import { Type } from '@sinclair/typebox'

const TracingHeaders = Type.Object({
  'x-request-id': Type.Optional(Type.String({ format: 'uuid' })),
  'x-correlation-id': Type.Optional(Type.String()),
  'x-forwarded-for': Type.Optional(Type.String())
})
```

## Authenticated User Context

```typescript
// src/plugins/auth-context.ts
import fp from 'fastify-plugin'
import { Type, type Static } from '@sinclair/typebox'

const UserContext = Type.Object({
  id: Type.String({ format: 'uuid' }),
  email: Type.String(),
  role: Type.Union([Type.Literal('admin'), Type.Literal('user')]),
  tenantId: Type.Optional(Type.String())
})

type UserContextType = Static<typeof UserContext>

declare module 'fastify' {
  interface FastifyRequest {
    user: UserContextType | null
  }
}

export default fp(async (app) => {
  app.decorateRequest('user', null)

  app.addHook('onRequest', async (request) => {
    const token = request.headers.authorization?.replace('Bearer ', '')
    if (!token) return

    try {
      const payload = await verifyJWT(token)
      request.user = {
        id: payload.sub,
        email: payload.email,
        role: payload.role,
        tenantId: payload.tenantId
      }
    } catch {
      // Token invalid -- leave user as null
    }
  })
})
```

## Route Guard Using Context

```typescript
// src/plugins/guards.ts
import fp from 'fastify-plugin'
import { UnauthorizedError, ForbiddenError } from '../errors.js'

export default fp(async (app) => {
  // Require authentication
  app.decorate('requireAuth', async (request: FastifyRequest) => {
    if (!request.user) {
      throw new UnauthorizedError('Authentication required')
    }
  })

  // Require specific role
  app.decorate('requireRole', (role: string) => {
    return async (request: FastifyRequest) => {
      if (!request.user) {
        throw new UnauthorizedError()
      }
      if (request.user.role !== role) {
        throw new ForbiddenError(`Role '${role}' required`)
      }
    }
  })
})

declare module 'fastify' {
  interface FastifyInstance {
    requireAuth: (request: FastifyRequest) => Promise<void>
    requireRole: (role: string) => (request: FastifyRequest) => Promise<void>
  }
}
```

## Using Guards in Routes

```typescript
const routes: FastifyPluginAsyncTypebox = async (app) => {
  // Any authenticated user
  app.get('/profile', {
    onRequest: app.requireAuth,
    schema: {
      response: { 200: UserProfileSchema }
    }
  }, async (request) => {
    return app.userRepo.findById(request.user!.id)
  })

  // Admin only
  app.delete('/users/:id', {
    onRequest: app.requireRole('admin'),
    schema: {
      params: Type.Object({ id: Type.String({ format: 'uuid' }) })
    }
  }, async (request, reply) => {
    await app.userRepo.delete(request.params.id)
    reply.status(204)
  })
}
```

## AsyncLocalStorage for Deep Context Access

For service layers that do not have access to the request object:

```typescript
// src/context.ts
import { AsyncLocalStorage } from 'node:async_hooks'

interface RequestContext {
  requestId: string
  userId?: string
  tenantId?: string
}

export const asyncContext = new AsyncLocalStorage<RequestContext>()

// Plugin to set context
export default fp(async (app) => {
  app.addHook('onRequest', async (request) => {
    // Store will be available in any code called during this request
    asyncContext.enterWith({
      requestId: request.requestId,
      userId: request.user?.id,
      tenantId: request.user?.tenantId
    })
  })
})

// Usage in a service (no request object needed)
export function getRequestId(): string {
  return asyncContext.getStore()?.requestId ?? 'unknown'
}
```

## Key Points

- Use `decorateRequest` to add typed fields to the request object
- Generate or forward `x-request-id` for distributed tracing
- Echo `x-request-id` in response headers for client-side correlation
- Use hooks (`onRequest`) for auth context, not per-route middleware
- Use `AsyncLocalStorage` when services need request context without passing request
- Always declare types with `declare module 'fastify'` for full type safety
- Decorate with initial values (empty string, null) before assigning in hooks
