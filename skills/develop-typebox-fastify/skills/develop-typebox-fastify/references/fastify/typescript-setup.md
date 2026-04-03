# Fastify TypeScript Setup

## Node.js Type Stripping (Node.js 22.6+)

Run TypeScript directly without compilation:

```bash
# Node.js 22.6+
node --experimental-strip-types app.ts

# Node.js 23+
node app.ts
```

```json
// package.json
{
  "type": "module",
  "scripts": {
    "start": "node app.ts",
    "dev": "node --watch app.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

## tsconfig.json for Type Stripping

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,
    "noEmit": true,
    "strict": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "declaration": false
  }
}
```

## TypeBox Type Provider Setup

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'

// Configure type provider on the instance
const app = Fastify({ logger: true }).withTypeProvider<TypeBoxTypeProvider>()

// Now schemas provide automatic type inference
app.get('/users', {
  schema: {
    querystring: Type.Object({
      limit: Type.Optional(Type.Integer({ minimum: 1, maximum: 100 })),
    }),
    response: {
      200: Type.Array(Type.Object({
        id: Type.String(),
        name: Type.String(),
      })),
    },
  },
}, async (request) => {
  const limit = request.query.limit // typed: number | undefined
  return [{ id: '1', name: 'User' }]
})
```

## Re-Apply Type Provider in Plugins

The type provider must be re-applied inside plugin registration:

```typescript
import type { FastifyPluginAsync } from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'

const routes: FastifyPluginAsync = async (fastify) => {
  const app = fastify.withTypeProvider<TypeBoxTypeProvider>()

  app.get('/items', {
    schema: {
      response: {
        200: Type.Array(Type.Object({ id: Type.String() })),
      },
    },
  }, async () => [{ id: '1' }])
}

export default routes
```

## Declaration Merging for Decorators

```typescript
// types.ts
declare module 'fastify' {
  interface FastifyInstance {
    config: {
      port: number
      host: string
      databaseUrl: string
    }
    db: {
      query: (sql: string, params?: unknown[]) => Promise<unknown[]>
      close: () => Promise<void>
    }
  }

  interface FastifyRequest {
    user?: {
      id: string
      email: string
      role: 'admin' | 'user'
    }
    startTime: number
  }

  interface FastifyReply {
    sendSuccess: (data: unknown) => void
  }
}

export {} // Make it a module
```

## Typing Route Handlers

```typescript
import type { FastifyRequest, FastifyReply } from 'fastify'
import { Type, type Static } from '@sinclair/typebox'

const CreateUserBody = Type.Object({
  name: Type.String({ minLength: 1 }),
  email: Type.String({ format: 'email' }),
})

const UserParams = Type.Object({
  id: Type.String({ format: 'uuid' }),
})

// With type provider, types are inferred from schema:
app.post('/users', {
  schema: {
    body: CreateUserBody,
    response: { 201: UserSchema },
  },
}, async (request, reply) => {
  const { name, email } = request.body // typed automatically
  reply.code(201)
  return { id: 'generated', name, email }
})

// Without type provider, use generics:
app.get<{
  Params: Static<typeof UserParams>
  Querystring: { include?: string }
}>('/users/:id', async (request) => {
  const { id } = request.params // string
  return { id }
})
```

## Typing Plugins

```typescript
import fp from 'fastify-plugin'
import type { FastifyPluginAsync } from 'fastify'

interface DatabasePluginOptions {
  connectionString: string
  poolSize?: number
}

declare module 'fastify' {
  interface FastifyInstance {
    db: {
      query: (sql: string, params?: unknown[]) => Promise<unknown[]>
      close: () => Promise<void>
    }
  }
}

const databasePlugin: FastifyPluginAsync<DatabasePluginOptions> = async (fastify, options) => {
  const { connectionString, poolSize = 10 } = options
  const db = await createConnection(connectionString, poolSize)

  fastify.decorate('db', {
    query: (sql, params) => db.query(sql, params),
    close: () => db.end(),
  })

  fastify.addHook('onClose', async () => { await db.end() })
}

export default fp(databasePlugin, { name: 'database' })
```

## Typing Hooks

```typescript
import type {
  onRequestHookHandler,
  preHandlerHookHandler,
} from 'fastify'

const timingHook: onRequestHookHandler = async (request) => {
  request.startTime = Date.now()
}

const authHook: preHandlerHookHandler = async (request, reply) => {
  const token = request.headers.authorization
  if (!token) {
    reply.code(401).send({ error: 'Unauthorized' })
    return
  }
  request.user = await verifyToken(token)
}

app.addHook('onRequest', timingHook)
app.addHook('preHandler', authHook)
```

## Static Type Inference from TypeBox

```typescript
import { Type, type Static } from '@sinclair/typebox'

// Define schema
const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
  role: Type.Union([Type.Literal('admin'), Type.Literal('user')]),
  tags: Type.Array(Type.String()),
  address: Type.Optional(Type.Object({
    street: Type.String(),
    city: Type.String(),
  })),
})

// Infer TypeScript type
type User = Static<typeof UserSchema>
// Equivalent to:
// {
//   id: string
//   name: string
//   email: string
//   role: 'admin' | 'user'
//   tags: string[]
//   address?: { street: string; city: string }
// }
```

## Shared Types Organization

```typescript
// types/index.ts
import { Type, type Static } from '@sinclair/typebox'

export const PaginationQuery = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1 }),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
  sort: Type.Optional(Type.String()),
})

export type PaginationQueryType = Static<typeof PaginationQuery>

export const ErrorResponse = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String(),
})

export type ErrorResponseType = Static<typeof ErrorResponse>
```

## Type-Safe Route Registration

```typescript
import type { FastifyInstance } from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'

export default async function userRoutes(fastify: FastifyInstance) {
  const app = fastify.withTypeProvider<TypeBoxTypeProvider>()

  app.get('/', {
    schema: {
      querystring: PaginationQuery,
      response: {
        200: Type.Object({
          users: Type.Array(UserSchema),
          total: Type.Integer(),
        }),
      },
    },
  }, async (request) => {
    const { page, limit } = request.query // typed: { page: number; limit: number; sort?: string }
    return { users: [], total: 0 }
  })
}
```

## Type Checking Without Compilation

```bash
npx tsc --noEmit          # type check
npx tsc --noEmit --watch  # watch mode
```

```json
// package.json
{
  "scripts": {
    "start": "node app.ts",
    "typecheck": "tsc --noEmit",
    "test": "npm run typecheck && node --test"
  }
}
```

## Key Rules

- Always use `withTypeProvider<TypeBoxTypeProvider>()` on the Fastify instance
- Re-apply type provider inside plugin registration functions
- Use `declare module 'fastify'` for decorator types
- Use `type Static<typeof Schema>` to extract TypeScript types from TypeBox schemas
- Use `verbatimModuleSyntax: true` and `erasableSyntaxOnly: true` for type stripping
- Run `tsc --noEmit` for type checking (no compilation needed with Node.js type stripping)
- Avoid manual type assertions; let schemas infer types
