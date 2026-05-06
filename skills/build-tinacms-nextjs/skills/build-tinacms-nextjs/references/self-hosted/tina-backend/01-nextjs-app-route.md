# Next.js App Router Backend Route

The `/api/tina/[...routes]/route.ts` file — the entry point for the self-hosted TinaCMS backend.

## Standard implementation

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

## Explanation

| Piece | Role |
|---|---|
| `TinaNodeBackend(...)` | Returns a request handler |
| `authProvider` | The Auth Provider — checks `isAuthorized` per request |
| `databaseClient` | The auto-generated DB client (from `tina/__generated__/databaseClient`) |
| `export { handler as GET, handler as POST }` | Exports the handler for both methods |

## File location

`app/api/tina/[...routes]/route.ts` is the canonical path. The catch-all `[...routes]` handles all sub-paths under `/api/tina/`:

```
/api/tina/gql              → GraphQL queries/mutations
/api/tina/auth/...         → auth endpoints (if Auth.js wired)
/api/tina/...              → other routes
```

If you change the location, also update `contentApiUrlOverride` in `tina/config.ts`.

## Edge runtime — DO NOT use

```typescript
// ❌ DO NOT
export const runtime = 'edge'
```

The TinaCMS backend uses Node.js APIs. Edge runtime fails at build or at runtime. Default Node runtime is correct.

## Local-dev shortcut

```typescript
const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

const handler = TinaNodeBackend({
  authProvider: isLocal
    ? LocalBackendAuthProvider()  // skips auth in local dev
    : /* production auth */,
  databaseClient,
})
```

`LocalBackendAuthProvider()` allows all requests — fine for local but never use in production.

## Custom auth — swap the provider

```typescript
import { ClerkBackendAuthProvider } from 'tinacms-clerk'

const handler = TinaNodeBackend({
  authProvider: isLocal
    ? LocalBackendAuthProvider()
    : ClerkBackendAuthProvider({
        allowList: [process.env.TINA_PUBLIC_ALLOWED_EMAIL!],
        secretKey: process.env.CLERK_SECRET!,
      }),
  databaseClient,
})
```

See `references/self-hosted/auth-provider/04-clerk-auth.md`.

## Adding middleware

Wrap the handler:

```typescript
const baseHandler = TinaNodeBackend({/* ... */})

const handler = async (req: Request) => {
  // Custom logic before
  console.log(`[tina] ${req.method} ${new URL(req.url).pathname}`)
  return baseHandler(req)
}

export { handler as GET, handler as POST }
```

For per-environment routing or custom logging.

## CORS

The handler runs on your domain (same-origin as the admin SPA), so no CORS issue. If you need cross-origin (admin on a different domain), add CORS headers manually:

```typescript
const handler = async (req: Request) => {
  const response = await baseHandler(req)
  response.headers.set('Access-Control-Allow-Origin', 'https://admin.example.com')
  response.headers.set('Access-Control-Allow-Methods', 'GET,POST')
  return response
}
```

## Custom error handling

```typescript
const handler = async (req: Request) => {
  try {
    return await baseHandler(req)
  } catch (e) {
    console.error('[tina] handler error', e)
    return new Response(JSON.stringify({ error: 'Internal' }), { status: 500 })
  }
}
```

## Verifying

```bash
# Local dev
curl -X POST http://localhost:3000/api/tina/gql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ __typename }"}'

# Should return:
# {"data":{"__typename":"Query"}}
```

If it returns 401, your auth provider is rejecting the request — check the `isAuthorized` logic.
If it returns 500, check the logs.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `runtime: 'edge'` | Build fails | Remove it |
| Wrong file path | 404 | Use `app/api/tina/[...routes]/route.ts` |
| Forgot to export GET / POST | 405 method not allowed | Both methods |
| Auth provider mismatch with frontend | All requests 401 | Match frontend `tina/config.ts` provider |
| Missed `contentApiUrlOverride` in config | Frontend hits TinaCloud | Set to `/api/tina/gql` |
