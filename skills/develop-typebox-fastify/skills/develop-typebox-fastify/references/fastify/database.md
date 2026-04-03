# Fastify Database Integration

## PostgreSQL with @fastify/postgres

```typescript
import Fastify from 'fastify'
import fastifyPostgres from '@fastify/postgres'
import { Type } from '@sinclair/typebox'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify({ logger: true }).withTypeProvider<TypeBoxTypeProvider>()

app.register(fastifyPostgres, {
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
})

app.get('/users', {
  schema: {
    response: {
      200: Type.Array(Type.Object({
        id: Type.String(),
        name: Type.String(),
        email: Type.String(),
      })),
    },
  },
}, async () => {
  const { rows } = await app.pg.query('SELECT id, name, email FROM users')
  return rows
})

// With client checkout for multiple queries
app.get('/users/:id', {
  schema: {
    params: Type.Object({ id: Type.String() }),
    response: { 200: Type.Object({ id: Type.String(), name: Type.String(), email: Type.String() }) },
  },
}, async (request) => {
  const client = await app.pg.connect()
  try {
    const { rows } = await client.query('SELECT * FROM users WHERE id = $1', [request.params.id])
    return rows[0]
  } finally {
    client.release()
  }
})
```

## Transactions

```typescript
app.post('/transfer', {
  schema: {
    body: Type.Object({
      fromId: Type.String(),
      toId: Type.String(),
      amount: Type.Number({ minimum: 0.01 }),
    }),
    response: { 200: Type.Object({ success: Type.Boolean() }) },
  },
}, async (request) => {
  const { fromId, toId, amount } = request.body
  const client = await app.pg.connect()

  try {
    await client.query('BEGIN')
    await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, fromId])
    await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, toId])
    await client.query('COMMIT')
    return { success: true }
  } catch (error) {
    await client.query('ROLLBACK')
    throw error
  } finally {
    client.release()
  }
})
```

## MySQL with @fastify/mysql

```typescript
import fastifyMysql from '@fastify/mysql'

app.register(fastifyMysql, {
  promise: true,
  connectionString: process.env.MYSQL_URL,
})

app.get('/users', async () => {
  const connection = await app.mysql.getConnection()
  try {
    const [rows] = await connection.query('SELECT * FROM users')
    return rows
  } finally {
    connection.release()
  }
})
```

## MongoDB with @fastify/mongodb

```typescript
import fastifyMongo from '@fastify/mongodb'

app.register(fastifyMongo, { url: process.env.MONGODB_URL })

app.get('/users', {
  schema: { response: { 200: Type.Array(Type.Object({ _id: Type.String(), name: Type.String() })) } },
}, async () => {
  return app.mongo.db.collection('users').find({}).toArray()
})

app.post('/users', {
  schema: {
    body: Type.Object({ name: Type.String(), email: Type.String() }),
    response: { 201: Type.Object({ id: Type.String() }) },
  },
}, async (request, reply) => {
  const result = await app.mongo.db.collection('users').insertOne(request.body)
  reply.code(201)
  return { id: result.insertedId.toString() }
})
```

## Redis with @fastify/redis

```typescript
import fastifyRedis from '@fastify/redis'

app.register(fastifyRedis, { url: process.env.REDIS_URL })

app.get('/data/:key', {
  schema: {
    params: Type.Object({ key: Type.String() }),
    response: { 200: Type.Unknown() },
  },
}, async (request) => {
  const cached = await app.redis.get(`cache:${request.params.key}`)
  if (cached) return JSON.parse(cached)

  const data = await fetchFromDatabase(request.params.key)
  await app.redis.setex(`cache:${request.params.key}`, 300, JSON.stringify(data))
  return data
})
```

## Database as Plugin

```typescript
import fp from 'fastify-plugin'
import fastifyPostgres from '@fastify/postgres'

export default fp(async function databasePlugin(fastify) {
  await fastify.register(fastifyPostgres, {
    connectionString: fastify.config.DATABASE_URL,
  })

  fastify.decorate('checkDatabaseHealth', async () => {
    try {
      await fastify.pg.query('SELECT 1')
      return true
    } catch {
      return false
    }
  })
}, {
  name: 'database',
  dependencies: ['config'],
})
```

## Repository Pattern

```typescript
import fp from 'fastify-plugin'
import { Type, type Static } from '@sinclair/typebox'
import type { FastifyInstance } from 'fastify'

export const UserSchema = Type.Object({
  id: Type.String(),
  email: Type.String(),
  name: Type.String(),
})

type User = Static<typeof UserSchema>

function createUserRepository(app: FastifyInstance) {
  return {
    async findById(id: string): Promise<User | null> {
      const { rows } = await app.pg.query('SELECT * FROM users WHERE id = $1', [id])
      return rows[0] || null
    },

    async findByEmail(email: string): Promise<User | null> {
      const { rows } = await app.pg.query('SELECT * FROM users WHERE email = $1', [email])
      return rows[0] || null
    },

    async create(data: Omit<User, 'id'>): Promise<User> {
      const { rows } = await app.pg.query(
        'INSERT INTO users (email, name) VALUES ($1, $2) RETURNING *',
        [data.email, data.name],
      )
      return rows[0]
    },

    async update(id: string, data: Partial<User>): Promise<User | null> {
      const fields = Object.keys(data)
      const values = Object.values(data)
      const setClause = fields.map((f, i) => `${f} = $${i + 2}`).join(', ')
      const { rows } = await app.pg.query(
        `UPDATE users SET ${setClause} WHERE id = $1 RETURNING *`,
        [id, ...values],
      )
      return rows[0] || null
    },

    async delete(id: string): Promise<boolean> {
      const { rowCount } = await app.pg.query('DELETE FROM users WHERE id = $1', [id])
      return rowCount > 0
    },
  }
}

declare module 'fastify' {
  interface FastifyInstance {
    repositories: { users: ReturnType<typeof createUserRepository> }
  }
}

export default fp(async function repositoriesPlugin(fastify) {
  fastify.decorate('repositories', {
    users: createUserRepository(fastify),
  })
}, {
  name: 'repositories',
  dependencies: ['database'],
})
```

## Using Repositories in Routes

```typescript
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { UserSchema } from '../repositories/user.js'

export default async function userRoutes(fastify) {
  const app = fastify.withTypeProvider<TypeBoxTypeProvider>()

  app.get('/users/:id', {
    schema: {
      params: Type.Object({ id: Type.String() }),
      response: { 200: UserSchema, 404: ErrorSchema },
    },
  }, async (request, reply) => {
    const user = await fastify.repositories.users.findById(request.params.id)
    if (!user) { reply.code(404); return { error: 'Not found' } }
    return user
  })
}
```

## Testing with Database Transactions

```typescript
describe('User API', () => {
  let app, client

  beforeEach(async () => {
    app = await buildApp()
    client = await app.pg.connect()
    await client.query('BEGIN')
  })

  afterEach(async () => {
    await client.query('ROLLBACK')
    client.release()
    await app.close()
  })

  it('should create a user', async (t) => {
    const response = await app.inject({
      method: 'POST',
      url: '/users',
      payload: { email: 'test@example.com', name: 'Test' },
    })
    t.assert.equal(response.statusCode, 201)
  })
})
```
