# Custom Database Adapter

For Postgres, DynamoDB, or any DB not first-party supported. Implement the level-compatible interface.

## When to consider

- Your org standardizes on Postgres / DynamoDB / Cassandra
- Existing infra you want to reuse
- Specific compliance requires a particular DB

For most projects, Vercel KV or MongoDB suffices.

## The interface

`mongodb-level` and `upstash-redis-level` implement a level-compatible adapter. You can write your own:

```typescript
import { AbstractLevel } from 'abstract-level'

class MyCustomLevel extends AbstractLevel<...> {
  // Implement: get, put, del, batch, iterator
}
```

Reference the [`abstract-level`](https://github.com/Level/abstract-level) docs for the complete interface.

## Required operations

| Operation | TinaCMS uses for |
|---|---|
| `get(key)` | Read a doc by ID |
| `put(key, value)` | Create / update a doc |
| `del(key)` | Delete a doc |
| `batch(ops)` | Bulk indexing during reindex |
| `iterator({ gte, lte })` | Range queries (filter, sort) |

The hardest part is `iterator` — TinaCMS scans key ranges for filter/sort. Your underlying DB needs sorted-key support.

## Postgres example (sketch)

```typescript
import { AbstractLevel } from 'abstract-level'
import { Pool } from 'pg'

class PostgresLevel extends AbstractLevel<...> {
  private pool: Pool

  constructor(opts: { connectionString: string }) {
    super({ encodings: { utf8: true } })
    this.pool = new Pool({ connectionString: opts.connectionString })
  }

  async _open() {
    // Create table if not exists
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS tinacms_kv (
        key TEXT PRIMARY KEY,
        value BYTEA NOT NULL
      )
    `)
  }

  async _get(key: string) {
    const res = await this.pool.query('SELECT value FROM tinacms_kv WHERE key = $1', [key])
    if (res.rowCount === 0) throw Object.assign(new Error('NotFound'), { code: 'LEVEL_NOT_FOUND' })
    return res.rows[0].value
  }

  async _put(key: string, value: Buffer) {
    await this.pool.query(
      'INSERT INTO tinacms_kv (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2',
      [key, value],
    )
  }

  async _del(key: string) {
    await this.pool.query('DELETE FROM tinacms_kv WHERE key = $1', [key])
  }

  // ... batch, iterator, etc.
}
```

This is a sketch — real implementation has many edge cases.

## Test thoroughly

Run the abstract-level test suite against your adapter to verify correctness:

```typescript
import { suite } from 'abstract-level/test'
suite({ test: tap.test, factory: () => new MyCustomLevel({...}) })
```

Or run TinaCMS' own integration tests with your adapter swapped in.

## Performance considerations

- Indexing scans keys in order — sorted key storage is critical
- Heavy writes during initial indexing — bulk-insert support helps
- Concurrent reads while writing — your DB needs MVCC or similar isolation

## Reuse existing community adapters

Before writing from scratch, check:

- TinaCMS Discord for community adapters
- npm for `*-level` packages
- The `abstract-level` ecosystem (https://github.com/Level)

There may be a Postgres or DynamoDB level adapter already.

## When NOT to write custom

- Your DB doesn't support sorted-key access (unsuitable for level-style)
- You don't have time to maintain a one-off adapter
- Vercel KV / MongoDB would work for your use case

Custom adapters are a meaningful engineering investment. Default to Vercel KV or MongoDB unless there's a clear reason.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `iterator` for range scans | Filter / sort queries fail | Implement range iteration |
| No transaction guarantees on `batch` | Partial state on failures | Use DB transactions |
| Slow `get` (no index on `key`) | All reads slow | Index the key column |
| Encoding mismatch (string vs buffer) | Reads return wrong data | Match `encodings` config to your storage |
| Connection pool not closed | Resource leak | Implement `_close()` |
