# Self-host with Clerk + MongoDB Playbook

Full self-hosted stack: Clerk auth + MongoDB DB + GitHub git provider. Uncommon but well-supported combination.

## When this fits

- App already uses Clerk
- Existing MongoDB Atlas account (or want to use Mongo)
- Need full self-hosted control
- Comfortable maintaining the backend

## Architecture

```
Editor → /admin (admin SPA)
   ↕ ClerkAuthProvider (frontend)
   ↓
/api/tina/[...routes] (backend route)
   ↕ ClerkBackendAuthProvider (backend) → Clerk
   ↓
@tinacms/datalayer (TinaNodeBackend handler)
   ├─→ MongodbLevel adapter → MongoDB Atlas
   └─→ GitHubProvider → GitHub repo
```

## Install

```bash
pnpm add \
  @tinacms/datalayer \
  tinacms-gitprovider-github \
  tinacms-clerk \
  @clerk/clerk-js @clerk/backend \
  mongodb-level
```

## Clerk setup

1. Sign up at https://clerk.com
2. Create application
3. Get keys from API Keys tab:

```env
CLERK_SECRET=sk_test_xxx
TINA_PUBLIC_CLERK_PUBLIC_KEY=pk_test_xxx
TINA_PUBLIC_ALLOWED_EMAIL=editor1@example.com,editor2@example.com
```

## MongoDB Atlas setup

1. Sign up at https://www.mongodb.com/atlas
2. Create cluster (M0 free works for moderate use)
3. Create database user
4. Whitelist `0.0.0.0/0` for serverless deploys
5. Get connection string:

```env
MONGODB_URI=mongodb+srv://user:pass@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

## GitHub PAT

```env
GITHUB_OWNER=<owner>
GITHUB_REPO=<repo>
GITHUB_BRANCH=main
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx
```

Required scope: `repo` (full).

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
      databaseAdapter: new MongodbLevel({
        collectionName: `tinacms-${branchName}`,
        dbName: 'tinacms',
        mongoUri: process.env.MONGODB_URI!,
      }),
      namespace: branchName,
    })
```

## `tina/config.ts`

```typescript
import { defineConfig, LocalAuthProvider } from 'tinacms'
import { ClerkAuthProvider } from 'tinacms-clerk/dist/frontend'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

export default defineConfig({
  branch: process.env.GITHUB_BRANCH || 'main',
  contentApiUrlOverride: '/api/tina/gql',
  authProvider: isLocal
    ? new LocalAuthProvider()
    : new ClerkAuthProvider(),
  build: { outputFolder: 'admin', publicFolder: 'public' },
  media: { tina: { mediaRoot: 'uploads', publicFolder: 'public' } },
  schema: {
    collections: [/* your collections */],
  },
})
```

## `app/api/tina/[...routes]/route.ts`

```typescript
import { TinaNodeBackend, LocalBackendAuthProvider } from '@tinacms/datalayer'
import { ClerkBackendAuthProvider } from 'tinacms-clerk'
import databaseClient from '@/tina/__generated__/databaseClient'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

const handler = TinaNodeBackend({
  authProvider: isLocal
    ? LocalBackendAuthProvider()
    : ClerkBackendAuthProvider({
        allowList: process.env.TINA_PUBLIC_ALLOWED_EMAIL?.split(',') ?? [],
        secretKey: process.env.CLERK_SECRET!,
      }),
  databaseClient,
})

export { handler as GET, handler as POST }
```

## Package scripts

```json
{
  "scripts": {
    "dev": "TINA_PUBLIC_IS_LOCAL=true tinacms dev -c \"next dev\"",
    "dev:prod": "tinacms dev -c \"next dev\"",
    "build": "tinacms build && next build"
  }
}
```

## Test locally

```bash
pnpm dev
# Open http://localhost:3000/admin/index.html
# Should load without auth (LocalAuthProvider)
```

Make an edit → saves to `content/` directly (no git commit, no DB).

## Deploy to Vercel

```bash
git push origin main
# Vercel auto-deploys
```

In Vercel:

1. Add all env vars from above
2. Set `TINA_PUBLIC_IS_LOCAL=false`
3. Redeploy

## Verify production

1. Visit `/admin/index.html`
2. Should redirect to Clerk login
3. Log in with an allowed email
4. Should land in admin
5. Make an edit, save
6. Edit appears in MongoDB and gets committed to GitHub

## Cost estimate

| Component | Cost |
|---|---|
| Vercel Hobby/Pro | $0–$20/mo |
| Atlas M0 (free tier) | $0 |
| GitHub | Free |
| Clerk (up to 10k MAU) | $0 |

Total: $0–$20/month. Very cheap for the architecture.

## Limitations

- No Editorial Workflow (self-hosted limitation)
- No built-in fuzzy search (use Algolia/Meilisearch externally)
- Cold starts on Vercel Functions (~500ms)

## Common mistakes

| Mistake | Fix |
|---|---|
| Forgot to enable Atlas IP allowlist | Connection refused | Allow 0.0.0.0/0 for serverless |
| Mismatched Clerk frontend/backend providers | Auth fails | Use ClerkAuthProvider + ClerkBackendAuthProvider |
| `TINA_PUBLIC_ALLOWED_EMAIL` not split | Whole string treated as one | `.split(',')` |
| Used `runtime: 'edge'` on backend | Build fails | Node.js only |
| Forgot `namespace` in createDatabase | Branches share index | Add namespace |
