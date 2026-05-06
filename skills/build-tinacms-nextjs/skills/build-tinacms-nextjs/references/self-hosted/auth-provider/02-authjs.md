# Auth.js Provider

The default for self-hosted. Wraps NextAuth (Auth.js) for both OAuth and email/password.

## Install

```bash
pnpm add tinacms-authjs next-auth
```

## Frontend (tina/config.ts)

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

## Backend (app/api/tina/[...routes]/route.ts)

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

## NextAuth route

`tinacms-authjs` provides the auth callback handler. Wire it up:

```typescript
// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import GitHubProvider from 'next-auth/providers/github'
import { TinaAuthJSOptions } from 'tinacms-authjs'
import databaseClient from '@/tina/__generated__/databaseClient'

const handler = NextAuth(
  TinaAuthJSOptions({
    databaseClient,
    secret: process.env.NEXTAUTH_SECRET!,
    providers: [
      CredentialsProvider({/* email/password */}),
      // OPTIONAL: also allow GitHub OAuth
      GitHubProvider({
        clientId: process.env.GITHUB_CLIENT_ID!,
        clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      }),
    ],
  }),
)

export { handler as GET, handler as POST }
```

`TinaAuthJSOptions` configures the right adapters and callbacks for TinaCMS' user collection.

## Required env vars

```env
NEXTAUTH_SECRET=<32 random chars — generate with `openssl rand -base64 32`>
NEXTAUTH_URL=https://your-site.com   # production only

# For OAuth providers, add their credentials:
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

## User collection

`tinacms-authjs` validates against a user collection in your CMS:

```typescript
// In tina/config.ts schema.collections:
{
  name: 'user',
  path: 'content/users',
  format: 'json',
  fields: [
    { name: 'username', type: 'string', isTitle: true },
    { name: 'email', type: 'string' },
    { name: 'password', type: 'string', ui: { component: 'hidden' } },
  ],
}
```

User files at `content/users/<email>.json`. See `references/self-hosted/07-user-management.md` for management.

## Email/password flow

1. Editor visits `/admin`
2. Redirected to NextAuth signin page
3. Enter email + password
4. NextAuth validates against user collection (bcrypt compare)
5. Sets session cookie
6. Redirects back to `/admin`

## OAuth flow (e.g. GitHub)

1. Editor visits `/admin`
2. Clicks "Sign in with GitHub"
3. OAuth roundtrip
4. NextAuth checks if the GitHub email matches a user in the collection
5. Sets session cookie
6. Redirects back

For OAuth + user-collection match, the email must align between GitHub and the user file.

## Allow-list filtering

```typescript
TinaAuthJSOptions({
  databaseClient,
  secret: process.env.NEXTAUTH_SECRET!,
  providers: [/* ... */],
  callbacks: {
    signIn: async ({ user }) => {
      const allowed = process.env.ALLOWED_EMAILS?.split(',') ?? []
      return Boolean(user.email && allowed.includes(user.email))
    },
  },
})
```

Block users not in the allowlist even if their OAuth login succeeds.

## Session handling

Session cookies are set per-domain. For `your-site.com` and `admin.your-site.com` (subdomains), configure cookies accordingly:

```typescript
TinaAuthJSOptions({
  // ...
  cookies: {
    sessionToken: {
      name: '__Secure-next-auth.session-token',
      options: {
        domain: '.your-site.com',  // shared across subdomains
        // ...
      },
    },
  },
})
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `NEXTAUTH_SECRET` | Auth breaks | Generate and set |
| Forgot `NEXTAUTH_URL` in production | OAuth callbacks fail | Set to your domain |
| Mismatched user-collection schema | Auth.js can't find users | Match the schema in `tinacms-authjs` docs |
| Plaintext password storage | Security disaster | Always bcrypt hash |
| OAuth without user-collection match | Login fails after OAuth roundtrip | Add user file with matching email |
