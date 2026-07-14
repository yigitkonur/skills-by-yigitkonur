# Auth Provider Overview

Auth determines who can edit. Self-hosted TinaCMS has four first-party options + custom.

## Available

| Provider | Package | Use when |
|---|---|---|
| **Auth.js** | `tinacms-authjs` | Default — flexible OAuth + email/password |
| **TinaCloud** | `@tinacms/auth` | Use TinaCloud's hosted auth even though backend is self-hosted |
| **Clerk** | `tinacms-clerk` | App already uses Clerk |
| **Custom** | DIY | Custom JWT, LDAP, SSO |

For most projects: Auth.js. For app already on Clerk: Clerk integration.

## Two halves: frontend and backend

```typescript
// tina/config.ts (frontend — what the editor's browser uses)
import { AuthJsAuthProvider } from 'tinacms-authjs'
authProvider: new AuthJsAuthProvider()

// app/api/tina/[...routes]/route.ts (backend — what the API checks)
import { AuthJsBackendAuthProvider } from 'tinacms-authjs'
authProvider: AuthJsBackendAuthProvider({ /* ... */ })
```

Both halves must use **matching providers**. Mismatched = login flow fails.

## Local-dev shortcut

```typescript
const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

// Frontend:
authProvider: isLocal
  ? new LocalAuthProvider()
  : new AuthJsAuthProvider()

// Backend:
authProvider: isLocal
  ? LocalBackendAuthProvider()
  : AuthJsBackendAuthProvider({/* ... */})
```

`Local*AuthProvider` skips auth entirely — fine for `pnpm dev`, never use in production.

## Auth.js (default)

OAuth + email/password via NextAuth. Most flexible. See `references/self-hosted/auth-provider/02-authjs.md`.

## Clerk

For apps using Clerk for app auth. See `references/self-hosted/auth-provider/04-clerk-auth.md`.

## TinaCloud-as-auth

Use TinaCloud just for auth, while self-hosting DB + git. Smaller TinaCloud dependency. See `references/self-hosted/auth-provider/03-tinacloud-auth.md`.

## Custom

Validate your own JWT or session. See `references/self-hosted/auth-provider/05-bring-your-own.md`.

## Common patterns

### Auth.js + GitHub OAuth

Editors log in via GitHub. Their GitHub identity authorizes them.

```typescript
// In your NextAuth config:
providers: [
  GitHubProvider({
    clientId: process.env.GITHUB_CLIENT_ID!,
    clientSecret: process.env.GITHUB_CLIENT_SECRET!,
  }),
],
callbacks: {
  signIn: async ({ user }) => {
    // Allow only specific GitHub emails:
    return user.email?.endsWith('@yourdomain.com') ?? false
  },
}
```

### Clerk + organization

Editors are members of a specific Clerk org.

```typescript
ClerkBackendAuthProvider({
  allowList: process.env.TINA_PUBLIC_ALLOWED_EMAIL?.split(','),
  secretKey: process.env.CLERK_SECRET!,
})
```

### Email-allowlist on top of any auth

```typescript
authProvider: {
  isAuthorized: async (req: any) => {
    const session = await getSession(req)
    if (!session?.user?.email) return { isAuthorized: false }
    const allowed = process.env.ALLOWED_EMAILS?.split(',') ?? []
    return { isAuthorized: allowed.includes(session.user.email) }
  },
}
```

## Reading order

| File | Provider |
|---|---|
| `references/self-hosted/auth-provider/02-authjs.md` | Auth.js (default) |
| `references/self-hosted/auth-provider/03-tinacloud-auth.md` | TinaCloud-as-auth |
| `references/self-hosted/auth-provider/04-clerk-auth.md` | Clerk |
| `references/self-hosted/auth-provider/05-bring-your-own.md` | Custom |

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Mismatched frontend / backend providers | Login appears to work but mutations fail | Use matching pair |
| Local-dev shortcut in production | Public uploads / writes | Always check `TINA_PUBLIC_IS_LOCAL` is false in prod |
| Forgot to allowlist editor emails | Anyone can log in | Add allowList check |
| Mixed OAuth + email/password without UX | Editors confused | Pick one primary, OAuth as supplement |
