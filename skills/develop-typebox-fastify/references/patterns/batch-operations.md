# Batch Operations: Bulk Create, Update, and Delete

## Overview

Batch endpoints let clients perform multiple operations in a single request, reducing
network round-trips. TypeBox schemas validate the batch payload and enforce limits.

## Batch Create

```typescript
import { Type, type Static } from '@sinclair/typebox'

const BatchCreateBody = Type.Object({
  items: Type.Array(
    Type.Object({
      name: Type.String({ minLength: 1, maxLength: 200 }),
      email: Type.String({ format: 'email' }),
      role: Type.Optional(Type.Union([Type.Literal('admin'), Type.Literal('user')]))
    }),
    {
      minItems: 1,
      maxItems: 100,
      description: 'Array of users to create (max 100 per request)'
    }
  )
})

const BatchCreateResponse = Type.Object({
  created: Type.Integer({ description: 'Number of successfully created items' }),
  failed: Type.Integer({ description: 'Number of failed items' }),
  results: Type.Array(Type.Union([
    Type.Object({
      index: Type.Integer(),
      status: Type.Literal('created'),
      data: UserSchema
    }),
    Type.Object({
      index: Type.Integer(),
      status: Type.Literal('failed'),
      error: Type.String()
    })
  ]))
})

app.post('/users/batch', {
  schema: {
    tags: ['Users'],
    summary: 'Batch create users',
    body: BatchCreateBody,
    response: { 200: BatchCreateResponse }
  }
}, async (request) => {
  const results = await Promise.allSettled(
    request.body.items.map((item, index) =>
      app.userRepo.create(item).then(
        data => ({ index, status: 'created' as const, data }),
        err => ({ index, status: 'failed' as const, error: err.message })
      )
    )
  )

  const resolved = results.map(r =>
    r.status === 'fulfilled' ? r.value : { index: -1, status: 'failed' as const, error: 'Unknown' }
  )

  return {
    created: resolved.filter(r => r.status === 'created').length,
    failed: resolved.filter(r => r.status === 'failed').length,
    results: resolved
  }
})
```

## Batch Update

```typescript
const BatchUpdateBody = Type.Object({
  items: Type.Array(
    Type.Object({
      id: Type.String({ format: 'uuid' }),
      data: Type.Partial(Type.Object({
        name: Type.String({ minLength: 1 }),
        email: Type.String({ format: 'email' }),
        role: Type.Union([Type.Literal('admin'), Type.Literal('user')])
      }))
    }),
    { minItems: 1, maxItems: 100 }
  )
})

const BatchUpdateResponse = Type.Object({
  updated: Type.Integer(),
  failed: Type.Integer(),
  results: Type.Array(Type.Union([
    Type.Object({ id: Type.String(), status: Type.Literal('updated') }),
    Type.Object({ id: Type.String(), status: Type.Literal('failed'), error: Type.String() })
  ]))
})

app.patch('/users/batch', {
  schema: {
    body: BatchUpdateBody,
    response: { 200: BatchUpdateResponse }
  }
}, async (request) => {
  const results = []

  // Use a transaction for atomicity
  await app.db.transaction(async (tx) => {
    for (const item of request.body.items) {
      try {
        await tx.update(users)
          .set({ ...item.data, updatedAt: new Date() })
          .where(eq(users.id, item.id))
        results.push({ id: item.id, status: 'updated' as const })
      } catch (err: any) {
        results.push({ id: item.id, status: 'failed' as const, error: err.message })
      }
    }
  })

  return {
    updated: results.filter(r => r.status === 'updated').length,
    failed: results.filter(r => r.status === 'failed').length,
    results
  }
})
```

## Batch Delete

```typescript
const BatchDeleteBody = Type.Object({
  ids: Type.Array(
    Type.String({ format: 'uuid' }),
    { minItems: 1, maxItems: 100, description: 'IDs to delete' }
  )
})

const BatchDeleteResponse = Type.Object({
  deleted: Type.Integer(),
  notFound: Type.Array(Type.String({ description: 'IDs that were not found' }))
})

app.post('/users/batch-delete', {
  schema: {
    body: BatchDeleteBody,
    response: { 200: BatchDeleteResponse }
  }
}, async (request) => {
  const { ids } = request.body

  // Check which IDs exist
  const existing = await app.db
    .select({ id: users.id })
    .from(users)
    .where(inArray(users.id, ids))

  const existingIds = new Set(existing.map(e => e.id))
  const notFound = ids.filter(id => !existingIds.has(id))

  // Delete existing ones
  if (existingIds.size > 0) {
    await app.db.delete(users).where(inArray(users.id, [...existingIds]))
  }

  return {
    deleted: existingIds.size,
    notFound
  }
})
```

## Transactional Batch with Rollback

For all-or-nothing batch operations:

```typescript
const AtomicBatchBody = Type.Object({
  operations: Type.Array(
    Type.Union([
      Type.Object({
        action: Type.Literal('create'),
        data: CreateUserBody
      }),
      Type.Object({
        action: Type.Literal('update'),
        id: Type.String({ format: 'uuid' }),
        data: UpdateUserBody
      }),
      Type.Object({
        action: Type.Literal('delete'),
        id: Type.String({ format: 'uuid' })
      })
    ]),
    { minItems: 1, maxItems: 50 }
  )
})

app.post('/users/batch-atomic', {
  schema: {
    body: AtomicBatchBody,
    response: {
      200: Type.Object({ success: Type.Boolean(), operationsCount: Type.Integer() }),
      400: ErrorResponse
    }
  }
}, async (request, reply) => {
  try {
    await app.db.transaction(async (tx) => {
      for (const op of request.body.operations) {
        switch (op.action) {
          case 'create':
            await tx.insert(users).values(op.data)
            break
          case 'update':
            await tx.update(users).set(op.data).where(eq(users.id, op.id))
            break
          case 'delete':
            await tx.delete(users).where(eq(users.id, op.id))
            break
        }
      }
    })
    return { success: true, operationsCount: request.body.operations.length }
  } catch (err: any) {
    // Transaction auto-rolls back on error
    reply.status(400)
    return { statusCode: 400, error: 'Bad Request', message: err.message }
  }
})
```

## Rate Limiting for Batch Endpoints

Batch endpoints consume more resources -- apply stricter limits:

```typescript
app.post('/users/batch', {
  config: {
    rateLimit: {
      max: 10,              // 10 batch requests per minute (vs 100 for single)
      timeWindow: '1 minute'
    }
  },
  schema: { body: BatchCreateBody }
}, handler)
```

## Key Points

- Set `maxItems` on batch arrays to prevent abuse (100 is a safe default)
- Use transactions for atomic batch operations (all-or-nothing)
- Use `Promise.allSettled` for non-atomic batches (partial success OK)
- Return per-item status so clients know which items succeeded/failed
- Apply stricter rate limits on batch endpoints
- Use `POST /resource/batch-delete` instead of `DELETE` with body (safer with proxies)
- Consider background processing for very large batches (>100 items)
