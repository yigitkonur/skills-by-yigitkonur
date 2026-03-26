# Prisma + Fastify + TypeBox Integration

## Overview

Prisma provides a powerful ORM with schema-first design, auto-generated client, and
migrations. With TypeBox handling API validation and Prisma handling DB operations,
you get full type safety across the entire stack.

## Installation

```bash
npm install @prisma/client
npm install -D prisma
npx prisma init
```

## Prisma Schema

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(uuid())
  name      String
  email     String   @unique
  role      Role     @default(USER)
  bio       String?
  posts     Post[]
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  @@map("users")
}

model Post {
  id        String   @id @default(uuid())
  title     String
  content   String
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  String   @map("author_id")
  createdAt DateTime @default(now()) @map("created_at")

  @@map("posts")
}

enum Role {
  ADMIN
  USER
}
```

## Prisma Plugin for Fastify

```typescript
// src/plugins/prisma.ts
import fp from 'fastify-plugin'
import { PrismaClient } from '@prisma/client'

declare module 'fastify' {
  interface FastifyInstance {
    prisma: PrismaClient
  }
}

export default fp(async (app) => {
  const prisma = new PrismaClient({
    log: app.config.NODE_ENV === 'development'
      ? ['query', 'warn', 'error']
      : ['error']
  })

  await prisma.$connect()
  app.decorate('prisma', prisma)

  app.addHook('onClose', async () => {
    await prisma.$disconnect()
  })
})
```

## TypeBox Schemas Alongside Prisma

```typescript
// src/schemas/user.ts
import { Type, type Static } from '@sinclair/typebox'

export const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  email: Type.String({ format: 'email' }),
  role: Type.Union([Type.Literal('ADMIN'), Type.Literal('USER')]),
  bio: Type.Union([Type.String(), Type.Null()]),
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' })
}, { $id: 'User' })

export const CreateUserBody = Type.Object({
  name: Type.String({ minLength: 2, maxLength: 100 }),
  email: Type.String({ format: 'email' }),
  role: Type.Optional(Type.Union([Type.Literal('ADMIN'), Type.Literal('USER')])),
  bio: Type.Optional(Type.String({ maxLength: 500 }))
})

export const UserWithPostsSchema = Type.Intersect([
  UserSchema,
  Type.Object({
    posts: Type.Array(Type.Object({
      id: Type.String(),
      title: Type.String(),
      published: Type.Boolean()
    }))
  })
])

export type CreateUserInput = Static<typeof CreateUserBody>
```

## Routes with Prisma Queries

```typescript
// src/routes/users.ts
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'
import { UserSchema, CreateUserBody, UserWithPostsSchema } from '../schemas/user.js'

// Helper to convert Prisma dates to ISO strings
function serializeUser(user: any) {
  return {
    ...user,
    createdAt: user.createdAt.toISOString(),
    updatedAt: user.updatedAt.toISOString()
  }
}

const routes: FastifyPluginAsyncTypebox = async (app) => {
  app.get('/users', {
    schema: {
      querystring: Type.Object({
        role: Type.Optional(Type.Union([Type.Literal('ADMIN'), Type.Literal('USER')])),
        search: Type.Optional(Type.String())
      }),
      response: { 200: Type.Array(UserSchema) }
    }
  }, async (request) => {
    const users = await app.prisma.user.findMany({
      where: {
        role: request.query.role,
        name: request.query.search
          ? { contains: request.query.search, mode: 'insensitive' }
          : undefined
      },
      orderBy: { createdAt: 'desc' }
    })
    return users.map(serializeUser)
  })

  app.get('/users/:id', {
    schema: {
      params: Type.Object({ id: Type.String({ format: 'uuid' }) }),
      response: { 200: UserWithPostsSchema }
    }
  }, async (request, reply) => {
    const user = await app.prisma.user.findUnique({
      where: { id: request.params.id },
      include: { posts: { select: { id: true, title: true, published: true } } }
    })
    if (!user) { reply.status(404); return { error: 'Not found' } }
    return serializeUser(user)
  })

  app.post('/users', {
    schema: {
      body: CreateUserBody,
      response: { 201: UserSchema }
    }
  }, async (request, reply) => {
    const user = await app.prisma.user.create({ data: request.body })
    reply.status(201)
    return serializeUser(user)
  })
}

export default routes
```

## Prisma Migrations

```bash
# Create a migration
npx prisma migrate dev --name add_users_table

# Apply migrations in production
npx prisma migrate deploy

# Reset database (development only)
npx prisma migrate reset

# Generate Prisma client
npx prisma generate
```

## Key Points

- Prisma schema defines database models; TypeBox schemas define API validation
- Decorate Fastify with PrismaClient and disconnect on close
- Convert Prisma Date objects to ISO strings for TypeBox response serialization
- Use `select` and `include` in Prisma queries to match TypeBox response schemas
- Run `prisma generate` after schema changes to update the client
- Keep Prisma schema in `prisma/` and TypeBox schemas in `src/schemas/`
