# Bring Your Own Auth Provider

For LDAP, custom JWT, SSO, or any auth not in the first-party providers. Implement the auth provider interface yourself.

## When to consider

- Existing custom auth in your app you want to reuse
- LDAP / SAML / OIDC requirements
- Auth scheme not supported by Auth.js or Clerk
- Compliance requires specific auth flow

For most projects, Auth.js with custom providers covers this without writing your own.

## The interface

```typescript
// Frontend (tina/config.ts):
import { AuthProvider } from 'tinacms'

class MyAuthProvider extends AuthProvider {
  // Methods to implement
}

// Backend (api route):
import type { BackendAuthProvider } from '@tinacms/datalayer'

const myBackendAuthProvider: BackendAuthProvider = {
  isAuthorized: async (req: any, res: any) => {
    // Verify auth, return { isAuthorized: boolean, user?: any }
  },
}
```

## Frontend implementation

```typescript
import { AbstractAuthProvider } from 'tinacms'

export class MyCustomAuthProvider extends AbstractAuthProvider {
  async authenticate() {
    // Open OAuth window, validate token, etc.
    // Return when authentication succeeds
  }

  async getUser() {
    // Return the current user object
    // null if not authenticated
    return { username: 'Jane', email: 'jane@example.com' }
  }

  async logout() {
    // Clear session, redirect, etc.
  }

  async getToken() {
    // Return a token to attach to API requests
    return localStorage.getItem('my-app-token')
  }
}
```

The auth provider is consumed by the TinaCMS admin SPA — it controls how editors log in.

## Backend implementation

```typescript
const myBackendAuthProvider: BackendAuthProvider = {
  isAuthorized: async (req: Request) => {
    const token = req.headers.get('authorization')
    if (!token) return { isAuthorized: false, errorMessage: 'No token', errorCode: 401 }

    try {
      const user = await validateMyJWT(token.replace('Bearer ', ''))
      if (!user) return { isAuthorized: false, errorMessage: 'Invalid token', errorCode: 401 }

      return { isAuthorized: true, user }
    } catch {
      return { isAuthorized: false, errorMessage: 'Auth error', errorCode: 401 }
    }
  },
}
```

The return shape:

```typescript
{
  isAuthorized: boolean,
  user?: any,                  // Available to git provider for author attribution
  errorMessage?: string,
  errorCode?: number,
}
```

## Wire up

```typescript
// tina/config.ts
import { MyCustomAuthProvider } from './my-auth'

authProvider: isLocal ? new LocalAuthProvider() : new MyCustomAuthProvider()

// app/api/tina/[...routes]/route.ts
const handler = TinaNodeBackend({
  authProvider: isLocal ? LocalBackendAuthProvider() : myBackendAuthProvider,
  databaseClient,
})
```

## Example: LDAP via passport-ldapauth

```typescript
import { Strategy as LdapStrategy } from 'passport-ldapauth'
import passport from 'passport'

passport.use(new LdapStrategy({
  server: {
    url: 'ldap://your-ldap-host:389',
    bindDN: 'cn=admin,dc=example,dc=com',
    bindCredentials: process.env.LDAP_BIND_PWD!,
    searchBase: 'ou=people,dc=example,dc=com',
    searchFilter: '(mail={{username}})',
  },
}))

const myBackendAuthProvider: BackendAuthProvider = {
  isAuthorized: async (req: Request) => {
    // Check if request has a valid LDAP-issued session
    const session = await getSessionFromCookie(req)
    if (!session) return { isAuthorized: false }
    return { isAuthorized: true, user: session.user }
  },
}
```

This is a sketch — real LDAP integration is non-trivial.

## Example: Custom JWT

```typescript
import { jwtVerify } from 'jose'

const secret = new TextEncoder().encode(process.env.JWT_SECRET!)

const myBackendAuthProvider: BackendAuthProvider = {
  isAuthorized: async (req: Request) => {
    const token = req.headers.get('authorization')?.replace('Bearer ', '')
    if (!token) return { isAuthorized: false }

    try {
      const { payload } = await jwtVerify(token, secret)
      return {
        isAuthorized: true,
        user: { username: payload.username, email: payload.email },
      }
    } catch {
      return { isAuthorized: false, errorCode: 401 }
    }
  },
}
```

## Testing

Spin up the backend with your custom auth, hit it with curl:

```bash
# Without auth — should fail
curl -X POST http://localhost:3000/api/tina/gql -d '{"query":"{ __typename }"}'

# With auth
curl -X POST http://localhost:3000/api/tina/gql \
  -H 'Authorization: Bearer your-token' \
  -d '{"query":"{ __typename }"}'
```

The backend should return 401 without auth and 200 with valid auth.

## Frontend admin integration

Custom auth providers must hook into the admin SPA's login flow. The exact API shape depends on TinaCMS version — read the source of `LocalAuthProvider`, `AuthJsAuthProvider`, etc. for reference.

## When NOT to write custom

- Auth.js' Credentials provider can wrap most custom auth
- For OAuth, Auth.js has built-in providers for most identity providers
- For SAML, use a community Auth.js SAML provider

Custom auth providers are a real engineering investment — exhaust the Auth.js options first.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Custom frontend auth provider not matching backend | Login appears to succeed but mutations fail | Pair them carefully |
| Forgot to return `user` from backend `isAuthorized` | Git commits attributed to bot account | Always return `user` when authorized |
| Hardcoded auth secrets in code | Security risk | Use env vars |
| Auth check in client bundle (token leak) | Token exposure | Server-side only |
| Used Edge runtime for backend | Build fails | Node.js only |
