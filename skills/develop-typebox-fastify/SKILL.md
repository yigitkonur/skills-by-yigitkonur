---
name: develop-typebox-fastify
description: Use skill if you are building Fastify REST APIs with TypeBox schemas, type-provider-typebox, route validation, OpenAPI generation, plugins, hooks, inject() testing, or Drizzle/Prisma database integration.
---

# TypeBox + Fastify Development

## Scope

- Fastify v5+ with TypeBox schemas and `@fastify/type-provider-typebox`
- Type-safe route definitions with automatic request/response type inference
- OpenAPI 3.0 generation from TypeBox schemas via `@fastify/swagger`
- Plugin architecture, hooks lifecycle, decorators
- Testing with `inject()`, database integration, auth, deployment

Does NOT cover: Frontend frameworks, GraphQL, Express migration (beyond basic guidance), non-TypeBox schema libraries as primary.

## When to use

- Building or modifying Fastify REST APIs
- Defining TypeBox schemas for validation or serialization
- Configuring Fastify plugins, hooks, or decorators
- Writing tests for Fastify routes
- Setting up OpenAPI/Swagger documentation
- Integrating databases (Drizzle, Prisma) with Fastify
- Implementing authentication (JWT, OAuth, API keys) in Fastify
- Optimizing Fastify performance

## When NOT to use

- General TypeScript questions without Fastify context
- Frontend development or React/Vue/Angular work
- Express.js applications (different middleware model)
- GraphQL servers (use dedicated GraphQL tools)
- Edge/serverless with strict bundle size constraints

## Critical rules

1. **Always use TypeBoxTypeProvider**: `fastify.withTypeProvider<TypeBoxTypeProvider>()`
2. **Always define response schemas**: enables fast-json-stringify (2-3x faster) AND prevents data leaks
3. **Wrap shared plugins with fastify-plugin**: exposes decorators to parent scope
4. **Never use reference types as decorator initial values**: shared across ALL requests (security risk)
5. **Use `typebox` package** (not `@sinclair/typebox` which is deprecated — though many existing projects still use it)

## Quick start

```typescript
import Fastify from 'fastify'
import { Type, TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify({ logger: true }).withTypeProvider<TypeBoxTypeProvider>()

const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String({ minLength: 1 }),
  email: Type.String({ format: 'email' }),
})

app.get('/:id', {
  schema: {
    params: Type.Object({ id: Type.String({ format: 'uuid' }) }),
    response: { 200: UserSchema },
  },
}, async (request) => {
  // request.params.id is typed as string
  return { id: request.params.id, name: 'User', email: 'user@example.com' }
})
```

## Decision tree

### What are you building?

**New Fastify project** → Read: `references/project-structure/recommended-layout.md`, `references/fastify/server-setup.md`, `references/integration/type-provider-setup.md`

**Adding routes** → Read: `references/integration/route-schemas.md`, `references/patterns/crud-routes.md`

**TypeBox schemas** → Read: `references/typebox/schema-basics.md`, then `schema-composition.md` or `schema-advanced.md` as needed

**Plugin development** → Read: `references/fastify/plugins.md`, `references/fastify/decorators.md`

**Authentication** → Read: `references/fastify/authentication.md`

**Database integration** → Read: `references/database/drizzle-integration.md` or `references/database/prisma-integration.md`

**OpenAPI/Swagger** → Read: `references/openapi/swagger-setup.md`, `references/openapi/schema-to-openapi.md`

**Testing** → Read: `references/fastify/testing.md`

**Performance** → Read: `references/fastify/performance.md`, `references/typebox/performance-tips.md`

**Error handling** → Read: `references/fastify/error-handling.md`, `references/patterns/error-responses.md`

**WebSockets** → Read: `references/fastify/websockets.md`

**Going to production** → Read: `references/deployment/production-checklist.md`, `references/patterns/graceful-shutdown.md`

## Hook lifecycle (reference)

```
Incoming Request
  → onRequest        (auth, timing, request ID)
  → preParsing       (transform request stream)
  → preValidation    (normalize data before schema validation)
  → preHandler       (authorization, load related data)
  → Handler          (business logic)
  → preSerialization (transform response object)
  → onSend           (modify serialized payload, add headers)
  → onResponse       (metrics, logging — cannot modify response)
  → onError          (error logging, cleanup — on error only)
```

## Critical gotchas (from research)

1. **Transform types do NOT work with Ajv** — TypeBox Transform (encode/decode) schemas are incompatible with Fastify's Ajv validator. Use `TypeBoxValidatorCompiler` or apply `Value.Decode`/`Value.Encode` manually.
2. **Value.Parse pipeline** — The recommended safe parsing order is: Clone → Default → Convert → Clean → Decode. Use this for environment variables and untrusted input.
3. **Response schemas strip extra properties** — This is a security feature of fast-json-stringify, not a bug. It prevents leaking database fields like passwords.
4. **Registration order is critical** — Register shared schemas before routes, infrastructure plugins before feature plugins, CORS/helmet before everything else.
5. **TypeBox outputs standard JSON Schema (Draft 7)** — This is why it integrates seamlessly with Fastify, unlike Zod which requires adapters.

## Red flags to watch for

| Red flag | Why it matters | Fix |
|---|---|---|
| No `withTypeProvider<TypeBoxTypeProvider>()` | No compile-time type safety | Add to server setup |
| Missing response schemas | Loses 2-3x serialization perf, risks data leaks | Define for all status codes |
| Shared plugin without `fastify-plugin` | Decorators invisible to other plugins | Wrap with `fp()` |
| Reference type in `decorateRequest()` | Shared mutable state across requests | Use `null`, set in hook |
| No error handler configured | Stack traces exposed to clients | Add `setErrorHandler` |
| Missing `await server.ready()` in tests | Plugins may not be loaded | Always await before inject() |
| Mixing async/await with done callback | Double-completion bugs | Pick one pattern per hook |
| Rate limiting without Redis backend | Bypassed in distributed deployments | Use Redis store |

## Reference routing

### Core references
| File | Read when |
|---|---|
| `references/core/quick-reference.md` | Need a cheat sheet for TypeBox + Fastify patterns |
| `references/core/package-ecosystem.md` | Setting up dependencies, choosing packages |

### TypeBox schemas
| File | Read when |
|---|---|
| `references/typebox/schema-basics.md` | Defining basic TypeBox schemas |
| `references/typebox/schema-composition.md` | Composing, extending, picking, omitting schemas |
| `references/typebox/schema-advanced.md` | Recursive types, transforms, discriminated unions |
| `references/typebox/schema-formats.md` | Custom formats, format validators |
| `references/typebox/value-operations.md` | Value.Check, Value.Cast, Value.Clean, etc. |
| `references/typebox/value-decode-encode.md` | Type transformations (wire → domain) |
| `references/typebox/type-compiler.md` | High-performance compiled validation |
| `references/typebox/typemap-standard-schema.md` | Standard Schema support via TypeMap |
| `references/typebox/json-schema-mapping.md` | TypeBox ↔ JSON Schema, $id/$ref |
| `references/typebox/schema-patterns.md` | Pagination, error, CRUD schema patterns |
| `references/typebox/nullable-optional.md` | Optional vs nullable patterns |
| `references/typebox/type-inference.md` | Static type extraction |
| `references/typebox/schema-organization.md` | File organization for schemas |
| `references/typebox/migration-guide.md` | Migrating from @sinclair/typebox, Zod |
| `references/typebox/validation-patterns.md` | Custom and cross-field validation |
| `references/typebox/coercion-defaults.md` | Type coercion, default values |
| `references/typebox/enum-patterns.md` | Enums, literals, discriminated unions |
| `references/typebox/date-handling.md` | Date schemas and transforms |
| `references/typebox/common-mistakes.md` | Top TypeBox mistakes to avoid |
| `references/typebox/performance-tips.md` | Compilation, caching, benchmarks |

### Fastify core
| File | Read when |
|---|---|
| `references/fastify/server-setup.md` | Creating Fastify instance |
| `references/fastify/routes.md` | Defining routes, params, query, body |
| `references/fastify/plugins.md` | Plugin system and encapsulation |
| `references/fastify/hooks-lifecycle.md` | Request lifecycle hooks |
| `references/fastify/error-handling.md` | Error handlers and custom errors |
| `references/fastify/decorators.md` | Extending Fastify/Request/Reply |
| `references/fastify/serialization.md` | Response serialization |
| `references/fastify/authentication.md` | JWT, OAuth, API keys, sessions |
| `references/fastify/testing.md` | inject() testing patterns |
| `references/fastify/performance.md` | Performance optimization |
| `references/fastify/logging.md` | Pino logging |
| `references/fastify/cors-security.md` | CORS, helmet, CSRF, rate limiting |
| `references/fastify/websockets.md` | WebSocket support |
| `references/fastify/database.md` | Database adapters |
| `references/fastify/file-uploads.md` | Multipart uploads |
| `references/fastify/configuration.md` | @fastify/env, config validation |
| `references/fastify/deployment.md` | Graceful shutdown, Docker, cluster |
| `references/fastify/content-type.md` | Content type parsing |
| `references/fastify/http-proxy.md` | HTTP proxy patterns |
| `references/fastify/typescript-setup.md` | TypeScript configuration |

### Integration (TypeBox + Fastify together)
| File | Read when |
|---|---|
| `references/integration/type-provider-setup.md` | Setting up type provider |
| `references/integration/route-schemas.md` | TypeBox schemas in route definitions |
| `references/integration/schema-registration.md` | addSchema() with $id/$ref |
| `references/integration/request-type-inference.md` | How request types are inferred |
| `references/integration/response-serialization.md` | TypeBox + fast-json-stringify |

### OpenAPI
| File | Read when |
|---|---|
| `references/openapi/swagger-setup.md` | Setting up Swagger/OpenAPI |
| `references/openapi/schema-to-openapi.md` | TypeBox → OpenAPI mapping |
| `references/openapi/openapi-codegen.md` | Client SDK generation |

### Database
| File | Read when |
|---|---|
| `references/database/drizzle-integration.md` | Drizzle ORM + Fastify |
| `references/database/prisma-integration.md` | Prisma + Fastify |
| `references/database/repository-pattern.md` | Repository abstraction |
| `references/database/migration-patterns.md` | Schema migrations |

### Middleware
| File | Read when |
|---|---|
| `references/middleware/rate-limiting.md` | @fastify/rate-limit |
| `references/middleware/cors-setup.md` | @fastify/cors |
| `references/middleware/compression.md` | @fastify/compress |
| `references/middleware/helmet-security.md` | @fastify/helmet |

### Patterns
| File | Read when |
|---|---|
| `references/patterns/crud-routes.md` | Full CRUD with TypeBox |
| `references/patterns/pagination.md` | Cursor/offset pagination |
| `references/patterns/error-responses.md` | Standardized errors |
| `references/patterns/request-context.md` | Correlation IDs, context |
| `references/patterns/graceful-shutdown.md` | Shutdown handling |
| `references/patterns/health-checks.md` | Liveness/readiness probes |
| `references/patterns/api-versioning.md` | API version strategies |
| `references/patterns/batch-operations.md` | Bulk operations |

### Project structure
| File | Read when |
|---|---|
| `references/project-structure/recommended-layout.md` | Directory organization |
| `references/project-structure/module-patterns.md` | ESM, imports, barrel files |
| `references/project-structure/environment-config.md` | Env config with TypeBox |
| `references/project-structure/docker-setup.md` | Docker for Fastify |

### Deployment
| File | Read when |
|---|---|
| `references/deployment/production-checklist.md` | Pre-production audit |
| `references/deployment/monitoring-setup.md` | Logging, metrics, tracing |

## Guardrails

- Always import Type from `@fastify/type-provider-typebox` or `typebox` (not `@sinclair/typebox` in new projects)
- Always define response schemas for every route in production
- Never skip `fastify-plugin` wrapping for plugins that expose decorators
- Never use `express.Router()` patterns — use Fastify's plugin system instead
- Never configure rate limiting with in-memory store for production (use Redis)
- Test with `inject()` — never start an actual HTTP server in tests
