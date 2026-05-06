# Self-hosted Overview

When and how to run TinaCMS' backend yourself instead of using TinaCloud.

## When to self-host

Default is TinaCloud (see `references/concepts/03-tinacloud-vs-self-hosted.md`). Self-host when:

- You need full backend control (custom auth, custom DB)
- Compliance/data-residency rules require it
- You've outgrown TinaCloud paid tiers
- You want to avoid SaaS dependency

For most projects, **TinaCloud is simpler and cheaper at small scale.**

## Architecture

Self-hosted TinaCMS replaces TinaCloud with **three pluggable modules** in a Next.js API route:

```
        ┌─ Auth Provider (Auth.js, Clerk, custom) ─┐
        │                                           │
Editor →┼─ Database Adapter (Vercel KV, MongoDB) ──┼→ Git Provider (GitHub) → repo
        │                                           │
        └─ The Tina Backend (createDatabase + handler) ┘
```

You implement (or pick) all three. They wire into `app/api/tina/[...routes]/route.ts`.

## Limitations vs TinaCloud

| Feature | TinaCloud | Self-hosted |
|---|---|---|
| Editorial Workflow | ✓ | ✗ (DIY via PR-based git workflow) |
| Built-in fuzzy search | ✓ | ✗ (use Algolia/Meilisearch externally) |
| Edge runtime | n/a (you talk to TinaCloud) | ✗ (Node.js only) |
| Setup time | 30 min | 4–8 hours |
| Backend code | None | ~150 LOC + auth wiring |

If Editorial Workflow or built-in search are critical, stay on TinaCloud.

## Setup steps

1. Read `references/self-hosted/01-architecture.md` to understand the pieces
2. Choose components: auth + DB + git provider
3. Either:
   - Use the Vercel starter (`references/self-hosted/02-nextjs-vercel-starter.md`)
   - Add to existing site (`references/self-hosted/03-existing-site-add.md`)
   - Manual setup (`references/self-hosted/04-manual-setup.md`)

## Migration

Both directions work:

- TinaCloud → self-hosted: `references/self-hosted/05-migrating-from-tinacloud.md`
- Self-hosted → TinaCloud: reverse the above; mostly just env var swaps + remove backend route

Content stays the same — both use git as the source of truth.

## Default-stance recommendations

Even when self-hosting, default to:

| Module | Recommended |
|---|---|
| Auth | Auth.js (`tinacms-authjs`) — most flexible |
| DB | Vercel KV — easiest on Vercel |
| Git | GitHub via `tinacms-gitprovider-github` |

Switch to alternatives (Clerk, MongoDB, custom git) only when you have specific reasons.

## Edge runtime — DO NOT use

The TinaCMS backend (`@tinacms/datalayer`, `@tinacms/graphql`) requires Node.js APIs. **It does not run in:**

- Cloudflare Workers
- Vercel Edge Functions
- Any V8-isolate runtime

Use a Node.js-compatible host: Vercel Functions, Netlify Functions, AWS Lambda, your own VPS.

## Reading order

| File | Topic |
|---|---|
| `references/self-hosted/01-architecture.md` | Three-module design |
| `references/self-hosted/02-nextjs-vercel-starter.md` | Official starter walkthrough |
| `references/self-hosted/03-existing-site-add.md` | Brownfield add |
| `references/self-hosted/04-manual-setup.md` | From scratch |
| `references/self-hosted/05-migrating-from-tinacloud.md` | Move off TinaCloud |
| `references/self-hosted/06-querying-data.md` | databaseClient differences |
| `references/self-hosted/07-user-management.md` | Auth.js user collection |
| `references/self-hosted/08-limitations.md` | What you give up |
| `references/self-hosted/tina-backend/01-nextjs-app-route.md` | Backend route impl |
| `references/self-hosted/tina-backend/02-vercel-functions.md` | Vercel Functions deploy |
| `references/self-hosted/git-provider/01-overview.md` | Git provider interface |
| `references/self-hosted/git-provider/02-github.md` | GitHub provider |
| `references/self-hosted/git-provider/03-make-your-own.md` | Custom git impl |
| `references/self-hosted/database-adapter/01-overview.md` | DB adapter interface |
| `references/self-hosted/database-adapter/02-vercel-kv.md` | Vercel KV |
| `references/self-hosted/database-adapter/03-mongodb.md` | MongoDB |
| `references/self-hosted/database-adapter/04-make-your-own.md` | Custom adapter |
| `references/self-hosted/auth-provider/01-overview.md` | Auth provider interface |
| `references/self-hosted/auth-provider/02-authjs.md` | Auth.js (recommended) |
| `references/self-hosted/auth-provider/03-tinacloud-auth.md` | TinaCloud-as-auth-only |
| `references/self-hosted/auth-provider/04-clerk-auth.md` | Clerk |
| `references/self-hosted/auth-provider/05-bring-your-own.md` | Custom auth |
