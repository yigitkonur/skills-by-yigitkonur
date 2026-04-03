# Repository Pattern with TypeBox Contracts

## Overview

The repository pattern abstracts database operations behind a typed interface. TypeBox
schemas define the input/output contracts, making repositories swappable between
implementations (Drizzle, Prisma, in-memory) without changing route handlers.

## Define Contracts with TypeBox

```typescript
// src/contracts/user.ts
import { Type, type Static } from '@sinclair/typebox'

export const UserEntity = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
  role: Type.Union([Type.Literal('admin'), Type.Literal('user')]),
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' })
})

export const CreateUserInput = Type.Object({
  name: Type.String({ minLength: 2 }),
  email: Type.String({ format: 'email' }),
  role: Type.Optional(Type.Union([Type.Literal('admin'), Type.Literal('user')]))
})

export const UpdateUserInput = Type.Partial(
  Type.Object({
    name: Type.String({ minLength: 2 }),
    email: Type.String({ format: 'email' }),
    role: Type.Union([Type.Literal('admin'), Type.Literal('user')])
  })
)

export const ListUsersFilter = Type.Object({
  role: Type.Optional(Type.String()),
  search: Type.Optional(Type.String()),
  page: Type.Integer({ minimum: 1, default: 1 }),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 })
})

export type User = Static<typeof UserEntity>
export type CreateUser = Static<typeof CreateUserInput>
export type UpdateUser = Static<typeof UpdateUserInput>
export type ListFilter = Static<typeof ListUsersFilter>
```

## Repository Interface

```typescript
// src/repositories/types.ts
import type { User, CreateUser, UpdateUser, ListFilter } from '../contracts/user.js'

export interface PaginatedResult<T> {
  data: T[]
  total: number
  page: number
  limit: number
}

export interface UserRepository {
  findById(id: string): Promise<User | null>
  findByEmail(email: string): Promise<User | null>
  list(filter: ListFilter): Promise<PaginatedResult<User>>
  create(input: CreateUser): Promise<User>
  update(id: string, input: UpdateUser): Promise<User | null>
  delete(id: string): Promise<boolean>
}
```

## Drizzle Implementation

```typescript
// src/repositories/drizzle-user.repository.ts
import { eq, ilike, sql, and } from 'drizzle-orm'
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js'
import { users } from '../db/schema.js'
import type { UserRepository, PaginatedResult } from './types.js'
import type { User, CreateUser, UpdateUser, ListFilter } from '../contracts/user.js'

export class DrizzleUserRepository implements UserRepository {
  constructor(private db: PostgresJsDatabase) {}

  async findById(id: string): Promise<User | null> {
    const [user] = await this.db.select().from(users).where(eq(users.id, id))
    return user ? this.serialize(user) : null
  }

  async findByEmail(email: string): Promise<User | null> {
    const [user] = await this.db.select().from(users).where(eq(users.email, email))
    return user ? this.serialize(user) : null
  }

  async list(filter: ListFilter): Promise<PaginatedResult<User>> {
    const conditions = []
    if (filter.role) conditions.push(eq(users.role, filter.role))
    if (filter.search) conditions.push(ilike(users.name, `%${filter.search}%`))

    const where = conditions.length ? and(...conditions) : undefined
    const offset = (filter.page - 1) * filter.limit

    const [data, [{ count }]] = await Promise.all([
      this.db.select().from(users).where(where).limit(filter.limit).offset(offset),
      this.db.select({ count: sql<number>`count(*)` }).from(users).where(where)
    ])

    return {
      data: data.map(u => this.serialize(u)),
      total: Number(count),
      page: filter.page,
      limit: filter.limit
    }
  }

  async create(input: CreateUser): Promise<User> {
    const [user] = await this.db.insert(users).values(input).returning()
    return this.serialize(user)
  }

  async update(id: string, input: UpdateUser): Promise<User | null> {
    const [user] = await this.db.update(users).set(input).where(eq(users.id, id)).returning()
    return user ? this.serialize(user) : null
  }

  async delete(id: string): Promise<boolean> {
    const result = await this.db.delete(users).where(eq(users.id, id)).returning()
    return result.length > 0
  }

  private serialize(row: typeof users.$inferSelect): User {
    return {
      ...row,
      bio: row.bio ?? undefined,
      createdAt: row.createdAt.toISOString(),
      updatedAt: row.updatedAt.toISOString()
    } as User
  }
}
```

## Fastify Plugin to Wire Repository

```typescript
// src/plugins/repositories.ts
import fp from 'fastify-plugin'
import { DrizzleUserRepository } from '../repositories/drizzle-user.repository.js'
import type { UserRepository } from '../repositories/types.js'

declare module 'fastify' {
  interface FastifyInstance {
    userRepo: UserRepository
  }
}

export default fp(async (app) => {
  const userRepo = new DrizzleUserRepository(app.db)
  app.decorate('userRepo', userRepo)
})
```

## Route Using Repository

```typescript
// src/routes/users.ts
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import { UserEntity, CreateUserInput, ListUsersFilter } from '../contracts/user.js'

const routes: FastifyPluginAsyncTypebox = async (app) => {
  app.get('/users', {
    schema: {
      querystring: ListUsersFilter,
      response: { 200: Type.Object({
        data: Type.Array(UserEntity),
        total: Type.Integer(),
        page: Type.Integer(),
        limit: Type.Integer()
      })}
    }
  }, async (request) => {
    return app.userRepo.list(request.query)
  })

  app.post('/users', {
    schema: { body: CreateUserInput, response: { 201: UserEntity } }
  }, async (request, reply) => {
    const existing = await app.userRepo.findByEmail(request.body.email)
    if (existing) { reply.status(409); return { error: 'Email taken' } }
    reply.status(201)
    return app.userRepo.create(request.body)
  })
}
```

## Key Points

- TypeBox schemas define the contract between API and repository layers
- Repository interface uses `Static<>` types extracted from TypeBox schemas
- Implementations handle DB-specific concerns (date conversion, query building)
- Decorate Fastify instance with repository for easy access in routes
- Swap implementations (Drizzle -> Prisma -> in-memory) without changing routes
- In-memory implementations are ideal for unit testing
