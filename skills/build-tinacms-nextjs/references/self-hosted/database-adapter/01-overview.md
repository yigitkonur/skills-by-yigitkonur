# Database Adapter Overview

The database is a **cache for fast queries**, indexed from your git repo. Source of truth is git; the DB is rebuildable from scratch anytime.

## Available adapters

| Adapter | Package | Use when |
|---|---|---|
| **Vercel KV** | `upstash-redis-level` | Vercel-native, easiest |
| **MongoDB** | `mongodb-level` | Heavy load, existing Atlas |
| **Custom** | DIY (level interface) | Postgres, DynamoDB, etc. |

For local dev: `createLocalDatabase()` uses in-memory + filesystem.

## `createDatabase()` factory

```typescript
import { createDatabase } from '@tinacms/datalayer'

createDatabase({
  databaseAdapter: /* required */,
  gitProvider: /* required */,
  tinaDirectory: 'tina',                 // default
  bridge: /* advanced */,
  indexStatusCallback: async (status) => {
    console.log('[indexer]', status)
  },
  namespace: process.env.GITHUB_BRANCH,   // per-branch isolation
  levelBatchSize: 25,                      // ops per write batch
})
```

| Parameter | Required? | Notes |
|---|---|---|
| `databaseAdapter` | ✓ | DB instance |
| `gitProvider` | ✓ | Git provider instance |
| `tinaDirectory` | ✗ | Custom `tina/` location (default `'tina'`) |
| `bridge` | ✗ | Index from non-filesystem (advanced) |
| `indexStatusCallback` | ✗ | Hook for monitoring indexing |
| `namespace` | ✗ | Per-branch isolation; usually the branch name |
| `levelBatchSize` | ✗ | Indexing batch size (default 25) |

## `createLocalDatabase()` factory

```typescript
import { createLocalDatabase } from '@tinacms/datalayer'

const localDb = createLocalDatabase()  // no params
```

For local dev / static-only sites. In-memory adapter + filesystem-only Git provider that doesn't commit.

## Indexing

When the backend boots:

1. Pulls latest content from git (via Git Provider)
2. Indexes each document into the DB Adapter
3. Watches for new commits and re-indexes

For 100 docs: ~5 seconds. For 10k docs: ~5 minutes (one-time cost).

## Reindex on demand

```bash
pnpm tinacms admin reindex
```

Or via API:

```bash
curl -X POST https://your-site.com/api/tina/reindex
```

When git changes outside the admin (push from laptop, automation), trigger reindex.

## DB persistence

The DB persists across function invocations on the same Vercel/server instance. On Vercel cold starts, the DB connection re-establishes (~50-100ms) but the index state is preserved.

## Why a "level"-style interface

TinaCMS uses LevelDB-compatible adapters. Any DB with a sorted key-value abstraction works:

- Vercel KV (Upstash Redis) — has ordered keys
- MongoDB — emulated via `mongodb-level`
- Postgres — would need a custom level adapter
- DynamoDB — custom level adapter

The key requirement: ordered iteration, get/put/delete, prefix scans. Most DBs can satisfy this with the right wrapper.

## Per-branch namespace

```typescript
createDatabase({
  // ...
  namespace: process.env.GITHUB_BRANCH || 'main',
})
```

Without `namespace`, all branches share one index. If editor A is on branch `feature-1` and editor B is on `feature-2`, their changes mix in the DB.

With `namespace`, each branch has its own index. Switching branches = querying a different namespace.

## Performance

| Operation | Cost |
|---|---|
| Read by ID | < 5ms |
| Filter by indexed field | 5-50ms depending on result size |
| Filter by non-indexed field | Slow — falls back to scan |
| Sort by indexed field | < 50ms |

Tune `searchable` flags on schema fields to control what gets indexed.

## Reading order

| File | Topic |
|---|---|
| `references/self-hosted/database-adapter/02-vercel-kv.md` | Vercel KV setup |
| `references/self-hosted/database-adapter/03-mongodb.md` | MongoDB setup |
| `references/self-hosted/database-adapter/04-make-your-own.md` | Custom adapter |
