# Fastify Testing

## inject() for Request Testing (No Network Overhead)

```typescript
import { describe, it, before, after } from 'node:test'
import Fastify from 'fastify'
import { buildApp } from './app.js'

describe('User API', () => {
  let app

  before(async () => {
    app = await buildApp({ logger: false })
    await app.ready()
  })

  after(async () => {
    await app.close()
  })

  it('should return users list', async (t) => {
    const response = await app.inject({
      method: 'GET',
      url: '/users',
    })

    t.assert.equal(response.statusCode, 200)
    t.assert.equal(response.headers['content-type'], 'application/json; charset=utf-8')
    const body = response.json()
    t.assert.ok(Array.isArray(body.users))
  })

  it('should create a user', async (t) => {
    const response = await app.inject({
      method: 'POST',
      url: '/users',
      payload: { name: 'John Doe', email: 'john@example.com' },
    })

    t.assert.equal(response.statusCode, 201)
    t.assert.ok(response.json().id)
  })
})
```

## Using Vitest

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { buildApp } from './app.js'

describe('User API', () => {
  let app: ReturnType<typeof Fastify>

  beforeAll(async () => {
    app = await buildApp({ logger: false })
    await app.ready()
  })

  afterAll(async () => {
    await app.close()
  })

  it('should return users list', async () => {
    const response = await app.inject({
      method: 'GET',
      url: '/users',
    })

    expect(response.statusCode).toBe(200)
    expect(response.json().users).toBeInstanceOf(Array)
  })

  it('should validate request body', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/users',
      payload: { name: 'John', email: 'not-an-email' },
    })

    expect(response.statusCode).toBe(400)
    expect(response.json().message).toContain('email')
  })
})
```

## Testing with Authentication

```typescript
describe('Protected Routes', () => {
  let app
  let authToken

  before(async () => {
    app = await buildApp({ logger: false })
    await app.ready()

    const loginResponse = await app.inject({
      method: 'POST',
      url: '/auth/login',
      payload: { email: 'test@example.com', password: 'password123' },
    })
    authToken = loginResponse.json().token
  })

  after(async () => { await app.close() })

  it('should reject unauthenticated requests', async (t) => {
    const response = await app.inject({ method: 'GET', url: '/profile' })
    t.assert.equal(response.statusCode, 401)
  })

  it('should return profile for authenticated user', async (t) => {
    const response = await app.inject({
      method: 'GET',
      url: '/profile',
      headers: { authorization: `Bearer ${authToken}` },
    })
    t.assert.equal(response.statusCode, 200)
    t.assert.equal(response.json().email, 'test@example.com')
  })
})
```

## Testing Query Parameters

```typescript
it('should filter users by status', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/users',
    query: { status: 'active', page: '1', limit: '10' },
  })

  t.assert.equal(response.statusCode, 200)
})

// Or with URL string
it('should search users', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/users?q=john&sort=name',
  })
  t.assert.equal(response.statusCode, 200)
})
```

## Testing Validation Errors

```typescript
describe('Validation', () => {
  it('should reject missing required fields', async (t) => {
    const response = await app.inject({
      method: 'POST',
      url: '/users',
      payload: { name: 'John' }, // missing email
    })
    t.assert.equal(response.statusCode, 400)
  })

  it('should reject invalid format', async (t) => {
    const response = await app.inject({
      method: 'POST',
      url: '/users',
      payload: { name: 'John', email: 'not-an-email' },
    })
    t.assert.equal(response.statusCode, 400)
    t.assert.ok(response.json().message.includes('email'))
  })
})
```

## Mock Dependencies

```typescript
import { describe, it, before, after, mock } from 'node:test'

describe('User Service', () => {
  let app

  before(async () => {
    const mockDb = {
      users: {
        findAll: mock.fn(async () => [
          { id: '1', name: 'User 1' },
          { id: '2', name: 'User 2' },
        ]),
        findById: mock.fn(async (id) => id === '1' ? { id: '1', name: 'User 1' } : null),
        create: mock.fn(async (data) => ({ id: 'new-id', ...data })),
      },
    }

    app = Fastify({ logger: false })
    app.decorate('db', mockDb)
    app.register(import('./routes/users.js'))
    await app.ready()
  })

  after(async () => { await app.close() })

  it('should call findAll', async (t) => {
    const response = await app.inject({ method: 'GET', url: '/users' })
    t.assert.equal(response.statusCode, 200)
    t.assert.equal(app.db.users.findAll.mock.calls.length, 1)
  })
})
```

## Test Factory Pattern

```typescript
// test/helper.ts
import Fastify, { type FastifyInstance } from 'fastify'

interface TestContext {
  app: FastifyInstance
  inject: FastifyInstance['inject']
}

export async function buildTestApp(opts = {}): Promise<TestContext> {
  const app = Fastify({ logger: false, ...opts })

  app.register(import('../src/plugins/database.js'), {
    connectionString: process.env.TEST_DATABASE_URL,
  })
  app.register(import('../src/routes/index.js'))

  await app.ready()

  return { app, inject: app.inject.bind(app) }
}

// Usage in tests
describe('API Tests', () => {
  let ctx: TestContext

  before(async () => { ctx = await buildTestApp() })
  after(async () => { await ctx.app.close() })

  it('should work', async (t) => {
    const response = await ctx.inject({ method: 'GET', url: '/health' })
    t.assert.equal(response.statusCode, 200)
  })
})
```

## Testing Plugins in Isolation

```typescript
import cachePlugin from './plugins/cache.js'

describe('Cache Plugin', () => {
  let app

  before(async () => {
    app = Fastify()
    app.register(cachePlugin, { ttl: 1000 })
    await app.ready()
  })

  after(async () => { await app.close() })

  it('should decorate fastify with cache', (t) => {
    t.assert.ok(app.hasDecorator('cache'))
    t.assert.equal(typeof app.cache.get, 'function')
  })

  it('should cache and retrieve values', (t) => {
    app.cache.set('key', 'value')
    t.assert.equal(app.cache.get('key'), 'value')
  })
})
```

## Testing Hooks

```typescript
describe('Hooks', () => {
  it('should add request id header', async (t) => {
    const response = await app.inject({ method: 'GET', url: '/health' })
    t.assert.ok(response.headers['x-request-id'])
  })

  it('should log request timing', async (t) => {
    const logs = []
    const app = Fastify({
      logger: {
        level: 'info',
        stream: { write: (msg) => logs.push(JSON.parse(msg)) },
      },
    })
    app.register(import('./app.js'))
    await app.ready()

    await app.inject({ method: 'GET', url: '/health' })
    const responseLog = logs.find((l) => l.msg?.includes('completed'))
    t.assert.ok(responseLog)

    await app.close()
  })
})
```

## Database Testing with Transactions

```typescript
describe('Database Integration', () => {
  let app, transaction

  before(async () => { app = await buildApp(); await app.ready() })
  after(async () => { await app.close() })

  beforeEach(async () => {
    transaction = await app.db.beginTransaction()
    app.db.setTransaction(transaction)
  })

  afterEach(async () => { await transaction.rollback() })

  it('should create user and rollback', async (t) => {
    const response = await app.inject({
      method: 'POST',
      url: '/users',
      payload: { name: 'Test', email: 'test@example.com' },
    })
    t.assert.equal(response.statusCode, 201)
  })
})
```

## Running Tests

```bash
# node:test
node --test
node --test src/**/*.test.ts
node --test --experimental-test-coverage

# vitest
npx vitest run
npx vitest run --coverage
npx vitest --watch
```
