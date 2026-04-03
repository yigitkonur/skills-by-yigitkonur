# Swagger/OpenAPI Setup with TypeBox

## Overview

`@fastify/swagger` generates OpenAPI specs from your route schemas, and `@fastify/swagger-ui`
serves an interactive UI. Combined with TypeBox, your schemas become the single source of
truth for validation, types, and API documentation.

## Installation

```bash
npm install @fastify/swagger @fastify/swagger-ui
```

## Basic Setup

```typescript
import Fastify from 'fastify'
import swagger from '@fastify/swagger'
import swaggerUi from '@fastify/swagger-ui'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()

// Register swagger BEFORE routes
await app.register(swagger, {
  openapi: {
    openapi: '3.1.0',
    info: {
      title: 'My API',
      description: 'API documentation generated from TypeBox schemas',
      version: '1.0.0'
    },
    servers: [
      { url: 'http://localhost:3000', description: 'Development' },
      { url: 'https://api.example.com', description: 'Production' }
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT'
        },
        apiKey: {
          type: 'apiKey',
          in: 'header',
          name: 'X-API-Key'
        }
      }
    }
  }
})

await app.register(swaggerUi, {
  routePrefix: '/docs',
  uiConfig: {
    docExpansion: 'list',
    deepLinking: true,
    defaultModelsExpandDepth: 3
  }
})
```

## Route with Full OpenAPI Metadata

```typescript
import { Type } from '@sinclair/typebox'

app.post('/users', {
  schema: {
    summary: 'Create a new user',
    description: 'Creates a user account and returns the created user object.',
    tags: ['Users'],
    security: [{ bearerAuth: [] }],
    body: Type.Object({
      name: Type.String({ minLength: 2, description: 'Full name of the user' }),
      email: Type.String({ format: 'email', description: 'Email address' }),
      role: Type.Union([Type.Literal('admin'), Type.Literal('user')], {
        default: 'user',
        description: 'User role in the system'
      })
    }),
    response: {
      201: Type.Object({
        id: Type.String({ format: 'uuid' }),
        name: Type.String(),
        email: Type.String(),
        role: Type.String(),
        createdAt: Type.String({ format: 'date-time' })
      }, { description: 'User created successfully' }),
      409: Type.Object({
        statusCode: Type.Integer(),
        error: Type.String(),
        message: Type.String()
      }, { description: 'Email already exists' })
    }
  }
}, async (request, reply) => {
  reply.status(201)
  return { /* ... */ }
})
```

## Using Tags to Group Routes

```typescript
// Register tags in swagger config
await app.register(swagger, {
  openapi: {
    info: { title: 'My API', version: '1.0.0' },
    tags: [
      { name: 'Users', description: 'User management endpoints' },
      { name: 'Orders', description: 'Order processing endpoints' },
      { name: 'Admin', description: 'Administrative endpoints' }
    ]
  }
})

// Each route specifies its tag
app.get('/users', {
  schema: {
    tags: ['Users'],
    summary: 'List all users'
    // ...
  }
}, handler)
```

## Accessing the OpenAPI Spec Programmatically

```typescript
// After all routes are registered
await app.ready()

// Get the full OpenAPI spec as JSON
const spec = app.swagger()
console.log(JSON.stringify(spec, null, 2))

// Or expose it at an endpoint (done automatically by swagger-ui)
// GET /docs/json -> OpenAPI JSON
// GET /docs/yaml -> OpenAPI YAML
```

## Environment-Conditional Setup

```typescript
const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()

if (process.env.NODE_ENV !== 'production') {
  await app.register(swagger, {
    openapi: { info: { title: 'My API', version: '1.0.0' } }
  })
  await app.register(swaggerUi, { routePrefix: '/docs' })
}
```

## Key Points

- Register `@fastify/swagger` BEFORE any route plugins
- TypeBox schemas automatically map to OpenAPI schema objects
- Use `description` in TypeBox options to document individual fields
- Use `summary`, `tags`, `security` in the route schema for OpenAPI metadata
- Swagger UI is available at the configured `routePrefix` (e.g., `/docs`)
- Schemas registered with `addSchema()` appear as OpenAPI components
- Disable swagger-ui in production for security
