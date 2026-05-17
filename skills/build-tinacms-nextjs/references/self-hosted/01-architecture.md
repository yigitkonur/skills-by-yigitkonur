# Self-hosted Architecture

The three pluggable modules and how they wire together.

## The pieces

```
                    ┌──────────────────────────────────────────────┐
                    │   Next.js API route (/api/tina/[...routes])  │
                    │     TinaNodeBackend(...)                     │
                    └──────┬───────────┬───────────┬───────────────┘
                           │           │           │
                  ┌────────▼─┐   ┌────▼─────┐   ┌─▼──────────┐
                  │  Auth    │   │ Database │   │    Git     │
                  │ Provider │   │ Adapter  │   │  Provider  │
                  └──────────┘   └──────────┘   └────────────┘
                       │             │                │
                  ┌────▼────┐    ┌──▼─────┐      ┌────▼────┐
                  │ Auth.js │    │ Vercel │      │ GitHub  │
                  │  Clerk  │    │   KV   │      │         │
                  │  Custom │    │MongoDB │      │ Custom  │
                  └─────────┘    └────────┘      └─────────┘
```

## Auth Provider

Decides who can edit. Implements `isAuthorized(req, res)`.

| Provider | Package | Use when |
|---|---|---|
| **Auth.js** | `tinacms-authjs` | OAuth (GitHub, Google, Discord, etc.) — most flexible |
| **Clerk** | `tinacms-clerk` | App already uses Clerk for user auth |
| **TinaCloud** | `@tinacms/auth` | Use TinaCloud as auth-only (DB + Git self-hosted) |
| **Custom** | DIY | Custom JWT validation |

Local dev: `LocalBackendAuthProvider()` always returns authorized.

## Database Adapter

Indexes documents from git into a fast key-value store. Cache, not source of truth.

| Adapter | Package | Use when |
|---|---|---|
| **Vercel KV** | `upstash-redis-level` | Vercel-native, easiest |
| **MongoDB** | `mongodb-level` | Heavy load, existing Atlas |
| **Custom** | DIY (level interface) | Postgres, DynamoDB, etc. |

Local dev: `createLocalDatabase()` uses in-memory + filesystem.

## Git Provider

Where content commits go.

| Provider | Package | Use when |
|---|---|---|
| **GitHub** | `tinacms-gitprovider-github` | Default, most projects |
| **Custom** | DIY | GitLab, Bitbucket, on-prem git |

GitHub is the only first-party option. Others are non-trivial to implement.

## `database.ts` ties them together

```typescript
// tina/database.ts
import { createDatabase, createLocalDatabase } from '@tinacms/datalayer'
import { GitHubProvider } from 'tinacms-gitprovider-github'
import { RedisLevel } from 'upstash-redis-level'
import { Redis } from '@upstash/redis'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'
const branch = process.env.GITHUB_BRANCH || 'main'

export default isLocal
  ? createLocalDatabase()
  : createDatabase({
      gitProvider: new GitHubProvider({
        branch,
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
      namespace: branch,         // per-branch DB isolation
    })
```

## Backend route ties to the database

```typescript
// app/api/tina/[...routes]/route.ts
import { TinaNodeBackend, LocalBackendAuthProvider } from '@tinacms/datalayer'
import { AuthJsBackendAuthProvider, TinaAuthJSOptions } from 'tinacms-authjs'
import databaseClient from '@/tina/__generated__/databaseClient'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

const handler = TinaNodeBackend({
  authProvider: isLocal
    ? LocalBackendAuthProvider()
    : AuthJsBackendAuthProvider({
        authOptions: TinaAuthJSOptions({
          databaseClient,
          secret: process.env.NEXTAUTH_SECRET!,
        }),
      }),
  databaseClient,
})

export { handler as GET, handler as POST }
```

## `tina/config.ts` points at the backend

```typescript
export default defineConfig({
  // ...
  contentApiUrlOverride: '/api/tina/gql',  // YOUR backend
  authProvider: isLocal
    ? new LocalAuthProvider()
    : new AuthJsAuthProvider(),  // matches backend's authProvider
  // ...
})
```

The frontend `authProvider` (in `tina/config.ts`) is the editor-side counterpart of the backend `authProvider` (in the route handler). Both must agree on the auth scheme.

## `createDatabase()` parameters

```typescript
createDatabase({
  databaseAdapter: /* required */,
  gitProvider:     /* required */,
  tinaDirectory:   'tina',           // default
  bridge:          /* advanced */,
  indexStatusCallback: async (s) => {/* optional */},
  namespace:       'main',           // per-branch isolation
  levelBatchSize:  25,               // ops per batch
})
```

| Param | Required? | Notes |
|---|---|---|
| `databaseAdapter` | ✓ | The DB instance |
| `gitProvider` | ✓ | The git provider instance |
| `tinaDirectory` | ✗ | Custom `tina/` location |
| `bridge` | ✗ | Index from non-filesystem (advanced) |
| `indexStatusCallback` | ✗ | Monitor indexing progress |
| `namespace` | ✗ | Per-branch DB isolation |
| `levelBatchSize` | ✗ | Indexing batch size (default 25) |

## How requests flow

A user clicks "Save":

```
1. Admin SPA → POST /api/tina/gql
2. TinaNodeBackend handler:
   a. authProvider.isAuthorized(req, res)
   b. GraphQL resolver runs the mutation:
      - Update DB index (databaseAdapter)
      - Write file to git (gitProvider) → commits and pushes
   c. Return updated document
3. (Optional) Webhook fires → Vercel rebuild
```

For reads (queries), only the DB adapter is touched. No git operation per read.

## When the index drifts from git

Git can change without going through the admin (push from laptop, automated commits). The DB index doesn't auto-refresh in self-hosted setups.

**Fix:** Trigger reindex manually:

```bash
pnpm tinacms admin reindex
```

Or set up a webhook from your git host that calls a `/api/tina/reindex` endpoint after pushes.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `contentApiUrlOverride` in config | Frontend talks to TinaCloud, not your backend | Set to `/api/tina/gql` |
| Mismatched frontend / backend auth providers | Auth fails | Use matching pair |
| Missing `namespace` in createDatabase | Branches share index | Add `namespace: branchName` |
| Used `runtime: 'edge'` on the backend route | Node-only modules fail | Remove edge runtime |
| Forgot `process.env.TINA_PUBLIC_IS_LOCAL` flag | Auth required in local dev | Use the local-dev shortcut |
