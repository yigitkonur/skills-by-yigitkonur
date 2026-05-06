# Vercel KV Database Adapter

The default DB adapter for self-hosted projects on Vercel. Backed by Upstash Redis.

## Install

```bash
pnpm add upstash-redis-level @upstash/redis
```

## Enable in Vercel

1. Vercel Project Settings → Storage → Create Database → KV
2. Vercel auto-injects:
   - `KV_REST_API_URL`
   - `KV_REST_API_TOKEN`
   - `KV_URL` (legacy)
   - `KV_REST_API_READ_ONLY_TOKEN`

## `tina/database.ts`

```typescript
import { createDatabase, createLocalDatabase } from '@tinacms/datalayer'
import { GitHubProvider } from 'tinacms-gitprovider-github'
import { RedisLevel } from 'upstash-redis-level'
import { Redis } from '@upstash/redis'

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
      databaseAdapter: new RedisLevel({
        redis: new Redis({
          url: process.env.KV_REST_API_URL!,
          token: process.env.KV_REST_API_TOKEN!,
        }),
        debug: process.env.DEBUG === 'true',
      }),
      namespace: branchName,
    })
```

## Quotas

Vercel KV free tier:

| Resource | Free | Paid |
|---|---|---|
| Storage | 100 MB | scales |
| Commands | 30k/day | scales |
| Bandwidth | 256 MB/day | scales |

For most TinaCMS projects: free tier covers it. The DB stores serialized doc content + indexes — typically 10-50 KB per document.

For a 1000-doc project: ~50 MB total — well within free tier.

## Performance

- Read: ~10-30ms (Upstash REST API roundtrip)
- Write: ~30-100ms (network + persistence)
- Connection pooling: handled by the SDK

## Region

Pick a Vercel KV region close to your Vercel function region:

| Vercel function region | Nearest KV region |
|---|---|
| `iad1` (Washington DC) | `us-east-1` |
| `sfo1` (San Francisco) | `us-west-1` |
| `cdg1` (Paris) | `eu-west-1` |
| `hnd1` (Tokyo) | `ap-northeast-1` |

Cross-region: 100-200ms added latency.

## Multiple environments

For staging + production with separate KV stores:

```env
# Production:
KV_REST_API_URL=https://prod.kv.vercel-storage.com
KV_REST_API_TOKEN=xxx-prod

# Staging:
KV_REST_API_URL=https://staging.kv.vercel-storage.com
KV_REST_API_TOKEN=xxx-staging
```

Set per-environment in Vercel env config.

## Limitations vs MongoDB

| Concern | Vercel KV | MongoDB |
|---|---|---|
| Storage | 100 MB free, scales | Free up to 512 MB on Atlas M0 |
| Query patterns | Sorted KV | Document store |
| Cost at scale | Cheaper for small/medium | Cheaper for large |
| Latency | Slightly higher (REST API) | Lower (direct connection) |

For < 5k docs, Vercel KV is simpler. For 10k+ docs, MongoDB may be faster.

## Migration to MongoDB

Switching adapters in self-hosted is straightforward:

1. Set up MongoDB
2. Update `tina/database.ts` to use `MongodbLevel` instead of `RedisLevel`
3. Trigger reindex (the DB rebuilds from git)

Content stays in git; only the DB cache changes.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot to enable Vercel KV | Connection fails at runtime | Enable in Project Settings → Storage |
| Used `KV_URL` instead of `KV_REST_API_URL` | Old vs new API | Use the REST API vars |
| Hit 30k commands/day on free tier | Backend returns errors | Upgrade or reduce indexing |
| Wrong namespace (multiple branches collide) | Cross-contamination | Set `namespace: branchName` |
| Vercel KV region far from function region | Slow queries | Match regions |
