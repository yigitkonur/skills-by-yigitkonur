# Adding Self-hosted to an Existing Site

Migrating an existing Next.js site to self-hosted TinaCMS (without using a starter template).

## Prerequisites

- Existing Next.js App Router project
- TypeScript
- Vercel deployment (or another Node.js host)
- Existing TinaCMS install (or fresh)

## Install dependencies

```bash
pnpm add @tinacms/datalayer tinacms-authjs upstash-redis-level @upstash/redis tinacms-gitprovider-github next-auth
```

## Add `tina/database.ts`

```typescript
import { createDatabase, createLocalDatabase } from '@tinacms/datalayer'
import { GitHubProvider } from 'tinacms-gitprovider-github'
import { RedisLevel } from 'upstash-redis-level'
import { Redis } from '@upstash/redis'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'
const branchName = process.env.GITHUB_BRANCH ||
                   process.env.VERCEL_GIT_COMMIT_REF ||
                   'main'

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
      }),
      namespace: branchName,
    })
```

## Add `app/api/tina/[...routes]/route.ts`

```typescript
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

## Update `tina/config.ts`

```typescript
import { defineConfig, LocalAuthProvider } from 'tinacms'
import { AuthJsAuthProvider } from 'tinacms-authjs'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

export default defineConfig({
  // ...
  contentApiUrlOverride: '/api/tina/gql',
  authProvider: isLocal
    ? new LocalAuthProvider()
    : new AuthJsAuthProvider(),
  // ...
})
```

## Add user collection (for Auth.js)

```typescript
// tina/config.ts schema.collections
{
  name: 'user',
  label: 'Users',
  path: 'content/users',
  format: 'json',
  fields: [
    { name: 'username', type: 'string', isTitle: true, required: true },
    { name: 'email', type: 'string', required: true },
    { name: 'password', type: 'string', ui: { component: 'hidden' } },  // hashed
  ],
}
```

`tinacms-authjs` validates email/password against this collection. Documentation in `references/self-hosted/auth-provider/02-authjs.md`.

## Auth.js setup (NextAuth)

```typescript
// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth'
// ... auth config

const handler = NextAuth(/* config */)
export { handler as GET, handler as POST }
```

`tinacms-authjs` provides helpers — see its README.

## Update env vars

Production:

```env
TINA_PUBLIC_IS_LOCAL=false
NEXTAUTH_SECRET=<32 random chars>
GITHUB_OWNER=<owner>
GITHUB_REPO=<repo>
GITHUB_BRANCH=main
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx
KV_REST_API_URL=https://xxx.kv.vercel-storage.com
KV_REST_API_TOKEN=xxx
```

Local dev:

```env
TINA_PUBLIC_IS_LOCAL=true
```

## Update package scripts

```json
{
  "scripts": {
    "dev": "TINA_PUBLIC_IS_LOCAL=true tinacms dev -c \"next dev\"",
    "dev:prod": "tinacms dev -c \"next dev\"",
    "build": "tinacms build && next build"
  }
}
```

## Migrate from TinaCloud (if applicable)

If your existing site uses TinaCloud:

1. Remove `clientId` and `token` from `tina/config.ts` (or set to empty strings)
2. Add `contentApiUrlOverride` and `authProvider`
3. Remove TinaCloud-specific Vercel env vars
4. Set up self-hosted env vars
5. Redeploy

Content stays in git unchanged. The migration is purely backend wiring.

See `references/self-hosted/05-migrating-from-tinacloud.md`.

## Initial admin user

For local dev, edit `content/users/<your-email>.json` directly with your hashed password. For production, deploy with at least one user already in the repo.

To hash a password:

```typescript
import bcrypt from 'bcryptjs'
console.log(await bcrypt.hash('your-password', 10))
```

## Verify

1. `pnpm dev` (with `TINA_PUBLIC_IS_LOCAL=true`)
2. Open `/admin/index.html` — should load without auth prompt
3. Make a content edit, save → should commit to local filesystem
4. Set `TINA_PUBLIC_IS_LOCAL=false`, restart, reopen admin
5. Should redirect to login → enter credentials → land back in admin
6. Make an edit → should commit to GitHub via the configured PAT

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `contentApiUrlOverride` | Frontend hits TinaCloud (404) | Add it |
| Mismatched frontend `authProvider` and backend auth | Login fails | Use matching pair |
| GitHub PAT without `repo` scope | Saves fail | Regenerate with full scope |
| KV not enabled | DB queries fail | Enable in Vercel settings |
| Initial user not in repo | Can't log in | Add user document before deploy |
