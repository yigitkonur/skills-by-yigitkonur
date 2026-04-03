# Drizzle ORM + Fastify + TypeBox Integration

## Overview

Drizzle ORM is a lightweight, type-safe SQL toolkit that pairs well with Fastify and TypeBox.
The pattern: define Drizzle schemas for database operations, TypeBox schemas for API
validation, and map between them cleanly.

## Installation

```bash
npm install drizzle-orm postgres
npm install -D drizzle-kit
```

## Drizzle Schema Definition

```typescript
// src/db/schema.ts
import { pgTable, uuid, varchar, text, timestamp, integer, boolean } from 'drizzle-orm/pg-core'

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  name: varchar('name', { length: 100 }).notNull(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  role: varchar('role', { length: 20 }).notNull().default('user'),
  bio: text('bio'),
  active: boolean('active').notNull().default(true),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow()
})

export const posts = pgTable('posts', {
  id: uuid('id').primaryKey().defaultRandom(),
  title: varchar('title', { length: 200 }).notNull(),
  content: text('content').notNull(),
  authorId: uuid('author_id').notNull().references(() => users.id),
  published: boolean('published').notNull().default(false),
  createdAt: timestamp('created_at').notNull().defaultNow()
})
```

## Database Connection Plugin

```typescript
// src/plugins/database.ts
import fp from 'fastify-plugin'
import { drizzle } from 'drizzle-orm/postgres-js'
import postgres from 'postgres'
import * as schema from '../db/schema.js'

declare module 'fastify' {
  interface FastifyInstance {
    db: ReturnType<typeof drizzle<typeof schema>>
  }
}

export default fp(async (app) => {
  const client = postgres(app.config.DATABASE_URL)
  const db = drizzle(client, { schema })

  app.decorate('db', db)

  app.addHook('onClose', async () => {
    await client.end()
  })
})
```

## TypeBox Schemas for API Layer

```typescript
// src/schemas/user.ts
import { Type, type Static } from '@sinclair/typebox'

export const UserResponse = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
  role: Type.String(),
  bio: Type.Union([Type.String(), Type.Null()]),
  active: Type.Boolean(),
  createdAt: Type.String({ format: 'date-time' })
}, { $id: 'UserResponse' })

export const CreateUserBody = Type.Object({
  name: Type.String({ minLength: 2, maxLength: 100 }),
  email: Type.String({ format: 'email' }),
  role: Type.Optional(Type.Union([Type.Literal('admin'), Type.Literal('user')])),
  bio: Type.Optional(Type.String())
})

export const UpdateUserBody = Type.Partial(
  Type.Object({
    name: Type.String({ minLength: 2, maxLength: 100 }),
    email: Type.String({ format: 'email' }),
    bio: Type.Union([Type.String(), Type.Null()])
  })
)

export type CreateUserInput = Static<typeof CreateUserBody>
```

## Route with Drizzle Queries

```typescript
// src/routes/users.ts
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'
import { eq } from 'drizzle-orm'
import { users } from '../db/schema.js'
import { UserResponse, CreateUserBody, UpdateUserBody } from '../schemas/user.js'

const userRoutes: FastifyPluginAsyncTypebox = async (app) => {
  app.get('/users', {
    schema: {
      response: { 200: Type.Array(UserResponse) }
    }
  }, async (request) => {
    const result = await app.db.select().from(users).where(eq(users.active, true))
    return result.map(u => ({
      ...u,
      createdAt: u.createdAt.toISOString()
    }))
  })

  app.post('/users', {
    schema: {
      body: CreateUserBody,
      response: { 201: UserResponse }
    }
  }, async (request, reply) => {
    const [user] = await app.db.insert(users).values(request.body).returning()
    reply.status(201)
    return { ...user, createdAt: user.createdAt.toISOString() }
  })

  app.patch('/users/:id', {
    schema: {
      params: Type.Object({ id: Type.String({ format: 'uuid' }) }),
      body: UpdateUserBody,
      response: { 200: UserResponse }
    }
  }, async (request) => {
    const [user] = await app.db
      .update(users)
      .set({ ...request.body, updatedAt: new Date() })
      .where(eq(users.id, request.params.id))
      .returning()
    return { ...user, createdAt: user.createdAt.toISOString() }
  })
}

export default userRoutes
```

## Drizzle Kit Configuration

```typescript
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  schema: './src/db/schema.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!
  }
})
```

```bash
# Generate migrations
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate

# Open Drizzle Studio
npx drizzle-kit studio
```

## Key Points

- Drizzle schema defines database structure; TypeBox schema defines API contracts
- Decorate the Fastify instance with the Drizzle client via a plugin
- Convert Date objects to ISO strings when returning from routes (for serialization)
- Use `drizzle-kit` for migrations and studio for visual DB management
- Keep Drizzle schemas in `src/db/` and TypeBox schemas in `src/schemas/`
