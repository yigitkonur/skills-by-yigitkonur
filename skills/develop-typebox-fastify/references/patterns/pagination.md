# Pagination Patterns

## Overview

Two main approaches: offset-based (page/limit) for simple UIs and cursor-based for
infinite scroll, real-time feeds, and large datasets. Both are defined with TypeBox schemas.

## Offset-Based Pagination

Simple, familiar, works well for smaller datasets:

```typescript
import { Type, type Static } from '@sinclair/typebox'

const OffsetPaginationQuery = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1, description: 'Page number' }),
  limit: Type.Integer({
    minimum: 1,
    maximum: 100,
    default: 20,
    description: 'Items per page'
  })
})

const PaginationMeta = Type.Object({
  page: Type.Integer(),
  limit: Type.Integer(),
  total: Type.Integer({ description: 'Total matching items' }),
  totalPages: Type.Integer(),
  hasNext: Type.Boolean(),
  hasPrev: Type.Boolean()
})

// Generic paginated response factory
function PaginatedResponse<T extends TSchema>(itemSchema: T) {
  return Type.Object({
    data: Type.Array(itemSchema),
    pagination: PaginationMeta
  })
}
```

### Route Implementation

```typescript
import { TSchema } from '@sinclair/typebox'

app.get('/users', {
  schema: {
    querystring: OffsetPaginationQuery,
    response: { 200: PaginatedResponse(UserSchema) }
  }
}, async (request) => {
  const { page, limit } = request.query
  const offset = (page - 1) * limit

  const [users, total] = await Promise.all([
    db.select().from(usersTable).limit(limit).offset(offset),
    db.select({ count: sql<number>`count(*)` }).from(usersTable)
  ])

  const totalPages = Math.ceil(total / limit)

  return {
    data: users,
    pagination: {
      page,
      limit,
      total,
      totalPages,
      hasNext: page < totalPages,
      hasPrev: page > 1
    }
  }
})
```

## Cursor-Based Pagination

Better for large datasets, real-time data, and infinite scroll:

```typescript
const CursorPaginationQuery = Type.Object({
  cursor: Type.Optional(Type.String({
    description: 'Opaque cursor from previous response'
  })),
  limit: Type.Integer({
    minimum: 1,
    maximum: 100,
    default: 20,
    description: 'Items per page'
  }),
  direction: Type.Optional(Type.Union([
    Type.Literal('forward'),
    Type.Literal('backward')
  ], { default: 'forward' }))
})

const CursorPaginationMeta = Type.Object({
  nextCursor: Type.Union([Type.String(), Type.Null()]),
  prevCursor: Type.Union([Type.String(), Type.Null()]),
  hasMore: Type.Boolean()
})

function CursorPaginatedResponse<T extends TSchema>(itemSchema: T) {
  return Type.Object({
    data: Type.Array(itemSchema),
    pagination: CursorPaginationMeta
  })
}
```

### Cursor Implementation

```typescript
import { gt, lt, desc, asc } from 'drizzle-orm'

// Encode/decode cursor as base64 JSON
function encodeCursor(id: string, sortValue: string): string {
  return Buffer.from(JSON.stringify({ id, sortValue })).toString('base64url')
}

function decodeCursor(cursor: string): { id: string; sortValue: string } {
  return JSON.parse(Buffer.from(cursor, 'base64url').toString())
}

app.get('/posts', {
  schema: {
    querystring: CursorPaginationQuery,
    response: { 200: CursorPaginatedResponse(PostSchema) }
  }
}, async (request) => {
  const { cursor, limit } = request.query

  let query = db.select().from(postsTable).orderBy(desc(postsTable.createdAt))

  if (cursor) {
    const { id, sortValue } = decodeCursor(cursor)
    query = query.where(
      sql`(${postsTable.createdAt}, ${postsTable.id}) < (${sortValue}, ${id})`
    )
  }

  // Fetch one extra to check if there are more results
  const posts = await query.limit(limit + 1)
  const hasMore = posts.length > limit
  const data = hasMore ? posts.slice(0, limit) : posts

  const lastItem = data[data.length - 1]
  const firstItem = data[0]

  return {
    data,
    pagination: {
      nextCursor: hasMore && lastItem
        ? encodeCursor(lastItem.id, lastItem.createdAt)
        : null,
      prevCursor: cursor && firstItem
        ? encodeCursor(firstItem.id, firstItem.createdAt)
        : null,
      hasMore
    }
  }
})
```

## Link Header Pattern (RFC 8288)

Add pagination links in HTTP headers:

```typescript
app.get('/items', {
  schema: { querystring: OffsetPaginationQuery }
}, async (request, reply) => {
  const { page, limit } = request.query
  const total = await countItems()
  const totalPages = Math.ceil(total / limit)

  const links: string[] = []
  const base = `${request.protocol}://${request.hostname}/items`

  if (page < totalPages) {
    links.push(`<${base}?page=${page + 1}&limit=${limit}>; rel="next"`)
  }
  if (page > 1) {
    links.push(`<${base}?page=${page - 1}&limit=${limit}>; rel="prev"`)
  }
  links.push(`<${base}?page=1&limit=${limit}>; rel="first"`)
  links.push(`<${base}?page=${totalPages}&limit=${limit}>; rel="last"`)

  reply.header('Link', links.join(', '))
  reply.header('X-Total-Count', total.toString())

  return { data: items }
})
```

## Key Points

- Offset pagination: simple, allows jumping to pages, degrades on large datasets
- Cursor pagination: stable under inserts/deletes, efficient for large datasets
- Always use `limit + 1` trick to determine `hasMore` without a COUNT query
- Encode cursors as opaque base64 strings (clients should not parse them)
- Include pagination metadata in the response body, not just headers
- Set a reasonable `maximum` on limit (100 is a safe default)
- Use compound cursors `(sortField, id)` for deterministic ordering
