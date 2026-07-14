# TinaCloud as Auth-only

Use TinaCloud for editor authentication while self-hosting the data layer (DB + git provider). Hybrid approach.

## When this fits

- You like TinaCloud's user dashboard but need a custom DB
- You want to migrate slowly: keep auth, change DB
- You want TinaCloud's per-editor identity in commits without paying for full TinaCloud

## Install

```bash
pnpm add @tinacms/auth
```

## Frontend (tina/config.ts)

```typescript
import { defineConfig, LocalAuthProvider } from 'tinacms'
import { TinaCloudAuthProvider } from '@tinacms/auth'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

export default defineConfig({
  // ...
  contentApiUrlOverride: '/api/tina/gql',
  // Note: still set clientId for TinaCloud auth
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID || '',
  authProvider: isLocal
    ? new LocalAuthProvider()
    : new TinaCloudAuthProvider(),
})
```

## Backend (app/api/tina/[...routes]/route.ts)

```typescript
import { TinaNodeBackend, LocalBackendAuthProvider } from '@tinacms/datalayer'
import { TinaCloudBackendAuthProvider } from '@tinacms/auth'
import databaseClient from '@/tina/__generated__/databaseClient'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

const handler = TinaNodeBackend({
  authProvider: isLocal
    ? LocalBackendAuthProvider()
    : TinaCloudBackendAuthProvider(),
  databaseClient,
})

export { handler as GET, handler as POST }
```

## Required env vars

```env
NEXT_PUBLIC_TINA_CLIENT_ID=<TinaCloud project Client ID>
TINA_PUBLIC_IS_LOCAL=false
# Plus DB and git provider env vars (Vercel KV, GitHub PAT, etc.)
```

You don't need `TINA_TOKEN` (read-only token) — that's for content queries, which go through your self-hosted DB.

## How it works

1. Editor visits `/admin`
2. TinaCloud OAuth flow (login via GitHub through TinaCloud)
3. TinaCloud sets a session cookie
4. Editor returns to `/admin`
5. `/api/tina/gql` (your backend) verifies the TinaCloud session cookie
6. Self-hosted DB serves the content

## Pros / cons

**Pros:**
- TinaCloud user dashboard for managing editors
- Per-editor identity in git commits (TinaCloud handles this)
- Existing TinaCloud account works
- No need to build user management

**Cons:**
- Still depends on TinaCloud (paid tier may apply for users beyond free tier)
- Editorial Workflow not available (still self-hosted backend)
- Mixed model: some things in TinaCloud, others self-hosted

## When to upgrade vs stay hybrid

If you're hitting TinaCloud user limits but love the auth:

- **Stay hybrid + upgrade TinaCloud user tier** — keeps the convenience
- **Migrate to Auth.js** — fully self-hosted, more setup work

Both work. Hybrid is good if you want to keep the path open to going back to full TinaCloud.

## Limitations

- Self-hosted backend means no Editorial Workflow (TinaCloud's feature)
- No built-in fuzzy search (TinaCloud feature requires TinaCloud as the data layer too)
- Auth still depends on TinaCloud uptime

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `clientId` for TinaCloud auth | OAuth fails | Set `NEXT_PUBLIC_TINA_CLIENT_ID` |
| Used `TINA_TOKEN` (read-only) for backend | Wrong scope | Don't need it; backend uses session cookie |
| Mixed Auth.js and TinaCloud auth providers | Cookie conflicts | Pick one |
| Editor not in TinaCloud project Users | Login fails | Add via TinaCloud dashboard |
