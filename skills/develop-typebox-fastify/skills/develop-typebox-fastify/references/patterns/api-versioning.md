# API Versioning Patterns

## Overview

Versioning ensures breaking changes do not affect existing clients. Two main strategies:
URL prefix versioning (simple, explicit) and header-based versioning (cleaner URLs).

## URL Prefix Versioning

The most common and straightforward approach:

```typescript
// src/routes/v1/users.ts
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'

const UserV1 = Type.Object({
  id: Type.String(),
  name: Type.String(),
  email: Type.String()
})

const usersV1: FastifyPluginAsyncTypebox = async (app) => {
  app.get('/users', {
    schema: { response: { 200: Type.Array(UserV1) } }
  }, async () => {
    return db.users.findMany()
  })
}

export default usersV1
```

```typescript
// src/routes/v2/users.ts
const UserV2 = Type.Object({
  id: Type.String(),
  firstName: Type.String(),    // Breaking: split name into first/last
  lastName: Type.String(),
  email: Type.String(),
  avatar: Type.Optional(Type.String({ format: 'uri' }))
})

const usersV2: FastifyPluginAsyncTypebox = async (app) => {
  app.get('/users', {
    schema: { response: { 200: Type.Array(UserV2) } }
  }, async () => {
    const users = await db.users.findMany()
    return users.map(u => ({
      id: u.id,
      firstName: u.firstName,
      lastName: u.lastName,
      email: u.email,
      avatar: u.avatarUrl
    }))
  })
}

export default usersV2
```

### Registration

```typescript
// src/app.ts
import usersV1 from './routes/v1/users.js'
import usersV2 from './routes/v2/users.js'

app.register(usersV1, { prefix: '/api/v1' })
app.register(usersV2, { prefix: '/api/v2' })
```

## Header-Based Versioning

Clients specify version via `Accept` or custom header:

```typescript
// src/plugins/api-version.ts
import fp from 'fastify-plugin'
import { Type } from '@sinclair/typebox'

declare module 'fastify' {
  interface FastifyRequest {
    apiVersion: number
  }
}

export default fp(async (app) => {
  app.decorateRequest('apiVersion', 0)

  app.addHook('onRequest', async (request, reply) => {
    // Accept: application/vnd.myapi.v2+json
    const accept = request.headers.accept ?? ''
    const versionMatch = accept.match(/vnd\.myapi\.v(\d+)\+json/)

    // Or: X-API-Version: 2
    const headerVersion = request.headers['x-api-version']

    if (versionMatch) {
      request.apiVersion = parseInt(versionMatch[1], 10)
    } else if (headerVersion) {
      request.apiVersion = parseInt(headerVersion as string, 10)
    } else {
      request.apiVersion = 2 // Default to latest
    }

    // Validate version range
    if (request.apiVersion < 1 || request.apiVersion > 2) {
      reply.status(400).send({
        statusCode: 400,
        error: 'Bad Request',
        message: `API version ${request.apiVersion} is not supported. Use v1 or v2.`
      })
    }
  })
})
```

### Version-Aware Route Handler

```typescript
app.get('/users/:id', {
  schema: {
    params: Type.Object({ id: Type.String({ format: 'uuid' }) })
  }
}, async (request) => {
  const user = await db.users.findById(request.params.id)

  if (request.apiVersion === 1) {
    return {
      id: user.id,
      name: `${user.firstName} ${user.lastName}`,
      email: user.email
    }
  }

  // v2 (default)
  return {
    id: user.id,
    firstName: user.firstName,
    lastName: user.lastName,
    email: user.email,
    avatar: user.avatarUrl
  }
})
```

## Version-Specific Schema Selection

```typescript
const ResponseSchemas = {
  1: Type.Object({
    id: Type.String(),
    name: Type.String(),
    email: Type.String()
  }),
  2: Type.Object({
    id: Type.String(),
    firstName: Type.String(),
    lastName: Type.String(),
    email: Type.String(),
    avatar: Type.Optional(Type.String())
  })
}
```

## Deprecation Headers

Signal upcoming deprecation to clients:

```typescript
// src/plugins/deprecation.ts
app.addHook('onSend', async (request, reply) => {
  if (request.url.startsWith('/api/v1')) {
    reply.header('Deprecation', 'true')
    reply.header('Sunset', 'Sat, 01 Jan 2026 00:00:00 GMT')
    reply.header('Link', '</api/v2>; rel="successor-version"')
  }
})
```

## Version Routing Plugin

Encapsulate version routing cleanly:

```typescript
// src/routes/users/index.ts
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import v1Routes from './v1.js'
import v2Routes from './v2.js'

const userRoutes: FastifyPluginAsyncTypebox = async (app) => {
  await app.register(v1Routes, { prefix: '/v1/users' })
  await app.register(v2Routes, { prefix: '/v2/users' })
}

export default userRoutes
```

## Recommended Directory Structure

```
src/
  routes/
    v1/
      users.ts
      products.ts
    v2/
      users.ts        # Only routes with breaking changes
      products.ts
  schemas/
    v1/
      user.ts
    v2/
      user.ts
```

## Key Points

- URL prefix versioning is simplest and most explicit
- Header-based versioning keeps URLs clean but adds complexity
- Only create a new version for breaking changes
- Non-breaking changes (adding fields) do not need a new version
- Add `Deprecation` and `Sunset` headers to old versions
- Default to the latest version for clients that do not specify
- Keep version-specific schemas separate for clarity
- Maintain backward compatibility as long as possible
