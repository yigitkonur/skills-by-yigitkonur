# Data Layer Architecture

TinaCMS calls its backend the **Data Layer**. It's a Node.js GraphQL server that:

1. Watches a git repo (the source of truth).
2. Indexes documents into a database (for fast queries).
3. Serves a GraphQL API (typed, generated from the schema).
4. Mutates the git repo (commits content edits via a configured git provider).

## The three pluggable modules

Self-hosted TinaCMS exposes three slots you can swap:

```
            ┌────────────────────────────────────┐
            │            Data Layer              │
            │  (TinaNodeBackend, GraphQL server) │
            └──────────┬───────┬────────┬────────┘
                       │       │        │
              ┌────────┘       │        └─────────┐
              ▼                ▼                  ▼
    ┌────────────────┐  ┌─────────────┐  ┌───────────────┐
    │  Auth Provider │  │ DB Adapter  │  │ Git Provider  │
    │                │  │             │  │               │
    │  Auth.js       │  │  Vercel KV  │  │  GitHub       │
    │  Clerk         │  │  MongoDB    │  │  Custom       │
    │  TinaCloud     │  │  Custom     │  │               │
    │  Custom        │  │             │  │               │
    └────────────────┘  └─────────────┘  └───────────────┘
```

Each module is standalone — you can mix and match (e.g. Clerk auth + MongoDB DB + GitHub git).

## Auth Provider

Decides who can edit. Implements `isAuthorized(req, res)` returning a boolean and (optionally) a user object.

| Provider | Package | When |
|---|---|---|
| **Auth.js** | `tinacms-authjs` | NextAuth-style OAuth (GitHub, Google, Discord) — most common self-hosted choice |
| **Clerk** | `tinacms-clerk` | Already using Clerk for app auth; reuse same identity provider |
| **TinaCloud** | `@tinacms/auth` | Use TinaCloud's hosted auth even though backend is self-hosted |
| **Custom** | DIY | Validate your own JWT/session |

Local development uses `LocalBackendAuthProvider()` which returns `{ isAuthorized: true }` always. Switch with `TINA_PUBLIC_IS_LOCAL=true`.

## Database Adapter

Indexes documents from git into a fast key-value store. The DB is a **cache, not the source of truth** — you can wipe it and re-index from git anytime.

| Adapter | Package | When |
|---|---|---|
| **Vercel KV** | `upstash-redis-level` | Vercel-native, easiest for Vercel Functions deploys |
| **MongoDB** | `mongodb-level` | Heavy content load (10k+ docs), existing Atlas account, want SQL-ish querying flexibility |
| **Custom** | DIY (implement `level`-style interface) | Postgres, Redis, DynamoDB, etc. |

For local dev: `createLocalDatabase()` uses an in-memory adapter — no external dependencies.

## Git Provider

Where content commits go. Implements push/pull semantics.

| Provider | Package | When |
|---|---|---|
| **GitHub** | `tinacms-gitprovider-github` | The default. Works with GitHub PAT or GitHub App. |
| **Custom** | DIY | GitLab, Bitbucket, on-prem git, or non-git stores |

GitHub is the only first-party option. For GitLab/Bitbucket you'd implement the `GitProvider` interface yourself — non-trivial.

## How a request flows

A user clicks "Save" in the admin:

```
1. Admin SPA → POST /api/tina/gql
   { query: "mutation { updateDocument(...) { ... } }", variables: {...} }

2. TinaNodeBackend handler:
   a. Auth Provider checks user identity → allow/deny
   b. GraphQL resolver applies the mutation:
      - Update DB index (DB Adapter)
      - Write file to git (Git Provider) → commits and pushes
   c. Return updated document

3. If TinaCloud webhook configured:
   - TinaCloud notifies Vercel deploy hook → site rebuilds
```

For reads (queries), only the DB Adapter is touched — Git Provider is not in the hot path.

## TinaCloud is the same architecture, fully managed

TinaCloud runs the same three-module backend, but provides Auth + DB + Git Provider as a service. You don't see the modules — you just provide a `clientId` and `token`.

This means migrating between TinaCloud and self-hosted is mostly a question of swapping `tina/config.ts` and adding a backend route. Schemas and content don't change.

## `createDatabase()` factory parameters

```typescript
import { createDatabase } from '@tinacms/datalayer'

createDatabase({
  databaseAdapter: /* required */,
  gitProvider:     /* required */,
  tinaDirectory:   'tina',          // default 'tina'
  bridge:          /* optional - advanced */,
  indexStatusCallback: async (s) => {/* optional */},
  namespace:       process.env.GITHUB_BRANCH,  // for branch isolation
  levelBatchSize:  25,              // ops per write batch
})
```

| Parameter | Required? | Notes |
|---|---|---|
| `databaseAdapter` | yes | The DB Adapter instance |
| `gitProvider` | yes | The Git Provider instance |
| `tinaDirectory` | no | Custom location for `tina/` folder |
| `bridge` | no | Advanced — index from a non-filesystem source |
| `indexStatusCallback` | no | Hook for monitoring indexing progress |
| `namespace` | no | Per-branch DB isolation; usually the branch name |
| `levelBatchSize` | no | Batch size for indexing writes; default 25 |

For local dev/static builds use `createLocalDatabase()` instead — no parameters, in-memory + filesystem-only Git Provider.

## When the DB index drifts

The DB is a cache of the git repo. When git changes outside the admin (e.g. you `git push` a content commit from your laptop), the DB doesn't auto-refresh. Solutions:

- **TinaCloud:** auto-reindexes via GitHub webhook.
- **Self-hosted:** trigger a reindex manually after pushes that bypass the admin (call `POST /api/tina/reindex` or your equivalent endpoint).

If queries return stale data right after a git push, the index is the suspect.
