# MongoDB Database Adapter

For projects with heavy content load (10k+ docs), existing MongoDB Atlas usage, or preference for a document database. Uses `mongodb-level` to expose Mongo as a level-compatible adapter.

## Install

```bash
pnpm add mongodb-level
```

`mongodb` (the official driver) is a peer dependency — check the package's docs for the right install command.

## MongoDB Atlas setup

1. Sign up at https://www.mongodb.com/atlas
2. Create a cluster (free M0 tier: 512 MB)
3. Create a database user
4. Whitelist your Vercel function IPs (or `0.0.0.0/0` for "everywhere")
5. Get the connection string

```env
MONGODB_URI=mongodb+srv://user:pass@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

## `tina/database.ts`

```typescript
import { createDatabase, createLocalDatabase } from '@tinacms/datalayer'
import { GitHubProvider } from 'tinacms-gitprovider-github'
import { MongodbLevel } from 'mongodb-level'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'
const branchName = process.env.GITHUB_BRANCH || 'main'

export default isLocal
  ? createLocalDatabase()
  : createDatabase({
      gitProvider: new GitHubProvider({
        branch: branchName,
        owner: process.env.GITHUB_OWNER!,
        repo: process.env.GITHUB_REPO!,
        token: process.env.GITHUB_PERSONAL_ACCESS_TOKEN!,
      }),
      databaseAdapter: new MongodbLevel<string, Record<string, any>>({
        collectionName: `tinacms-${branchName}`,
        dbName: 'tinacms',
        mongoUri: process.env.MONGODB_URI!,
      }),
      namespace: branchName,
    })
```

## Per-branch collections

The pattern `collectionName: tinacms-${branchName}` creates one MongoDB collection per branch:

- `tinacms-main`
- `tinacms-staging`
- `tinacms-feature-xyz`

This isolates branch states. Without per-branch collections, branches mix.

## Atlas M0 free tier limits

| Resource | M0 free |
|---|---|
| Storage | 512 MB |
| Connections | 100 |
| Cluster tier | Shared |

For 5k-10k typical TinaCMS docs, free tier is plenty. Beyond that, M10+ tiers ($60+/month) for production-grade.

## Performance

- Read: ~5-15ms (Atlas connection pooled)
- Write: ~10-30ms

Better than Vercel KV for large datasets due to:

- Lower latency direct connection (vs Upstash REST)
- Better large-payload handling
- Native sorting on indexed fields

## Indexing in Mongo

`mongodb-level` creates indexes automatically based on TinaCMS access patterns. For very large collections, you may want to add custom indexes manually via Atlas UI.

## Connection limits on Vercel

Each Vercel function invocation can open a new Mongo connection. The M0 free tier caps at **100 concurrent connections** (consistent with the table above). With many concurrent function invocations you can exhaust the pool. Paid tiers (M10+) raise the cap to several thousand depending on tier; check Atlas docs for the exact ceiling per cluster size.

Mitigate via connection pooling (`mongodb-level` should handle this automatically). Monitor in Atlas dashboard.

## Backup strategy

Atlas auto-backs up M10+ tiers. M0 free tier has no automated backups.

Since the DB is a cache rebuildable from git, **you don't need to back it up** — the source of truth is git. If the DB is lost, run `pnpm tinacms admin reindex` to rebuild from git.

## Migration from Vercel KV to MongoDB

```typescript
// Just swap the adapter in tina/database.ts:

// Before:
databaseAdapter: new RedisLevel({...})

// After:
databaseAdapter: new MongodbLevel({...})
```

Trigger reindex on first deploy to rebuild the cache.

## Cost comparison

For a 5,000-doc project:

| Option | Monthly cost |
|---|---|
| Vercel KV free | $0 |
| Atlas M0 free | $0 |
| Vercel KV paid (Pro tier KV) | ~$10 |
| Atlas M10 | ~$60 |

For TinaCMS-scale workloads (kilobytes per doc, low concurrency), free tiers cover most projects.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Wrong `mongoUri` format | Connection fails | Test in Mongo Compass first |
| IP not whitelisted in Atlas | Connection refused | Allow `0.0.0.0/0` for serverless |
| Forgot `collectionName` | All branches share one collection | Use per-branch naming |
| Hit M0 connection limit | Random failures under load | Upgrade tier |
| DB out of sync with git | Stale queries | Trigger reindex |
