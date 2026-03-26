# Fastify Plugins

## Understanding Encapsulation

Each plugin creates its own context. Decorators, hooks, and plugins registered within it are isolated:

```typescript
import Fastify from 'fastify'

const app = Fastify()

// Encapsulated plugin - decorators NOT available to siblings
app.register(async function childPlugin(fastify) {
  fastify.decorate('privateUtil', () => 'only here')

  fastify.get('/child', async function () {
    return this.privateUtil() // works
  })
})

// This route CANNOT access privateUtil
app.get('/parent', async function () {
  // this.privateUtil is undefined
  return { status: 'ok' }
})
```

## Breaking Encapsulation with fastify-plugin

Use `fastify-plugin` to share decorators with the parent context:

```typescript
import fp from 'fastify-plugin'
import { Type, type Static } from '@sinclair/typebox'

interface DatabaseClient {
  query: (sql: string, params?: unknown[]) => Promise<unknown[]>
  close: () => Promise<void>
}

declare module 'fastify' {
  interface FastifyInstance {
    db: DatabaseClient
  }
}

export default fp(async function databasePlugin(fastify, options) {
  const db = await createConnection(options.connectionString)

  fastify.decorate('db', db)

  fastify.addHook('onClose', async () => {
    await db.close()
  })
}, {
  name: 'database-plugin',
  dependencies: [],
})
```

## Plugin Registration Order

Plugins load in order. Use `after()` for explicit sequencing:

```typescript
import databasePlugin from './plugins/database.js'
import authPlugin from './plugins/auth.js'
import routesPlugin from './routes/index.js'

const app = Fastify()

// Sequential: database -> auth -> routes
app.register(databasePlugin)
app.register(authPlugin)    // can access db
app.register(routesPlugin)  // can access db + auth

await app.ready()
```

## Plugin Options with TypeBox

```typescript
import fp from 'fastify-plugin'
import { Type, type Static } from '@sinclair/typebox'

const OptionsSchema = Type.Object({
  ttl: Type.Number({ minimum: 1 }),
  maxSize: Type.Optional(Type.Number({ default: 1000 })),
  prefix: Type.Optional(Type.String({ default: 'cache:' })),
})

type CachePluginOptions = Static<typeof OptionsSchema>

export default fp<CachePluginOptions>(async function cachePlugin(fastify, options) {
  const { ttl, maxSize = 1000, prefix = 'cache:' } = options

  const cache = new Map<string, { value: unknown; expires: number }>()

  fastify.decorate('cache', {
    get(key: string): unknown | undefined {
      const item = cache.get(prefix + key)
      if (!item || Date.now() > item.expires) return undefined
      return item.value
    },
    set(key: string, value: unknown): void {
      if (cache.size >= maxSize) cache.delete(cache.keys().next().value)
      cache.set(prefix + key, { value, expires: Date.now() + ttl })
    },
  })
}, {
  name: 'cache-plugin',
})
```

## Plugin Dependencies

Declare dependencies to ensure correct load order:

```typescript
import fp from 'fastify-plugin'

export default fp(async function authPlugin(fastify) {
  if (!fastify.hasDecorator('db')) {
    throw new Error('Auth plugin requires database plugin')
  }

  fastify.decorate('authenticate', async (request) => {
    return fastify.db.users.findByToken(request.headers.authorization)
  })
}, {
  name: 'auth-plugin',
  dependencies: ['database-plugin'],
})
```

## Scoped Plugins for Route Groups

Use encapsulation to scope auth or other hooks to specific routes:

```typescript
// Public routes - no auth
app.register(async function publicRoutes(fastify) {
  fastify.get('/health', async () => ({ status: 'ok' }))
  fastify.get('/docs', async () => ({ version: '1.0.0' }))
})

// Protected routes - auth required
app.register(async function protectedRoutes(fastify) {
  fastify.addHook('onRequest', async (request, reply) => {
    const token = request.headers.authorization
    if (!token) {
      reply.code(401).send({ error: 'Unauthorized' })
      return
    }
    request.user = await verifyToken(token)
  })

  fastify.get('/profile', async (request) => ({ user: request.user }))
  fastify.get('/settings', async (request) => ({ settings: await getSettings(request.user.id) }))
})
```

## Prefix Routes with Register

```typescript
app.register(import('./routes/users.js'), { prefix: '/api/v1/users' })
app.register(import('./routes/posts.js'), { prefix: '/api/v1/posts' })
```

## Autoload Plugins

```typescript
import autoload from '@fastify/autoload'
import { join } from 'node:path'

// Load all plugins from the plugins directory
app.register(autoload, {
  dir: join(import.meta.dirname, 'plugins'),
})

// Load all routes from the routes directory
app.register(autoload, {
  dir: join(import.meta.dirname, 'routes'),
  options: { prefix: '/api' },
})
```

Directory structure for autoload:

```
src/
  plugins/
    database.ts     # Loaded automatically
    auth.ts         # Loaded automatically
  routes/
    users/
      index.ts      # GET/POST /api/users
      _id/
        index.ts    # GET/PUT/DELETE /api/users/:id
    posts/
      index.ts      # GET/POST /api/posts
```

## Plugin Metadata

```typescript
export default fp(metricsPlugin, {
  name: 'metrics-plugin',
  fastify: '5.x',
  dependencies: ['pino-plugin'],
  decorators: {
    fastify: ['db'],  // Required instance decorators
    request: [],
    reply: [],
  },
})
```

## Testing Plugins in Isolation

```typescript
import { describe, it, before, after } from 'node:test'
import Fastify from 'fastify'
import cachePlugin from './plugins/cache.js'

describe('Cache Plugin', () => {
  let app

  before(async () => {
    app = Fastify()
    app.register(cachePlugin, { ttl: 1000 })
    await app.ready()
  })

  after(async () => {
    await app.close()
  })

  it('should decorate fastify with cache', (t) => {
    t.assert.ok(app.hasDecorator('cache'))
    t.assert.equal(typeof app.cache.get, 'function')
  })
})
```

## Key Rule: When to Use fastify-plugin

| Scenario | Use fastify-plugin? |
|----------|-------------------|
| Shared infrastructure (db, cache, logger) | Yes |
| Domain/feature module (routes) | No (keep encapsulated) |
| Adds decorators other plugins need | Yes |
| Scoped hooks for route groups | No |
| Default | No (encapsulation is safer) |
