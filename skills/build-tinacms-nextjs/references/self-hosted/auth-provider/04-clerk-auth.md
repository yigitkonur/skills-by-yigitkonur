# Clerk Auth Provider

For apps already using Clerk for user auth. Reuse the same identity provider for the CMS.

## Install

```bash
pnpm add @clerk/clerk-js @clerk/backend tinacms-clerk
```

## Clerk setup

Sign up at https://clerk.com and create an "application." Get credentials from the dashboard:

```env
CLERK_SECRET=sk_test_xxxxxxx
TINA_PUBLIC_CLERK_PUBLIC_KEY=pk_test_xxxxxxx
TINA_PUBLIC_ALLOWED_EMAIL=editor@example.com
```

The `TINA_PUBLIC_ALLOWED_EMAIL` is a comma-separated list of emails allowed to access the CMS.

## Update dev script

Disable auth for local dev:

```json
{
  "scripts": {
    "dev": "TINA_PUBLIC_IS_LOCAL=true tinacms dev -c \"next dev\"",
    "dev:prod": "tinacms dev -c \"next dev\""
  }
}
```

## Frontend (tina/config.ts)

```typescript
import { defineConfig, LocalAuthProvider } from 'tinacms'
import { ClerkAuthProvider } from 'tinacms-clerk/dist/frontend'

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

export default defineConfig({
  // ...
  contentApiUrlOverride: '/api/tina/gql',
  authProvider: isLocal
    ? new LocalAuthProvider()
    : new ClerkAuthProvider(),
  // ...
})
```

## Backend (app/api/tina/[...routes]/route.ts)

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

## How allow-list works

`allowList` is an array of emails permitted to access the CMS. Editors logged into Clerk with one of these emails get authorized; others get rejected.

For larger teams:

- Comma-separated email list in env: `TINA_PUBLIC_ALLOWED_EMAIL=jane@x,john@x,bob@x`
- Or use Clerk Organizations and check membership instead (advanced)

## Maintaining the allow list

Hardcoding in env is simple but inflexible. Alternatives:

1. **Clerk Organization membership** — editors are members of a specific Clerk org
2. **Allow-list feature in Clerk** — paid feature; reference the Clerk Allowlist API
3. **Custom check** — verify against your own DB

For most projects, env-based allow-list is fine for < 20 editors.

## Why Clerk

- App already uses Clerk for user auth — reuse identity
- Clerk's user management UI is excellent
- Free tier covers up to 10k MAU
- OAuth providers, MFA, etc. configurable in Clerk dashboard

## Pros / cons vs Auth.js

| Concern | Clerk | Auth.js |
|---|---|---|
| Setup | Simpler | More complex |
| User management UI | Built-in (Clerk dashboard) | DIY (user collection) |
| OAuth providers | Many, easy to add | Many, manual config |
| Cost | Free up to 10k MAU | Free always |
| Self-hosted? | No (Clerk SaaS) | Yes |

For SaaS-friendly orgs, Clerk is great. For fully self-hosted, Auth.js.

## Edge runtime — DO NOT use

Same as the rest of TinaCMS backend — Node.js only.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `CLERK_SECRET` | Backend fails | Add env var |
| `TINA_PUBLIC_ALLOWED_EMAIL` not split | Whole string treated as one email | `.split(',')` |
| Wrong allow-list email casing | Login denied | Match case exactly |
| Mixed Clerk and Auth.js | Conflicting cookies | Pick one |
| `TINA_PUBLIC_IS_LOCAL=true` in production | Public access | Always false in prod |
