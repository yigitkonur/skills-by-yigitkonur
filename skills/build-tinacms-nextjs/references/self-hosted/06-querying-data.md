# Querying Data (Self-hosted)

Self-hosted projects get two clients: `client` (over HTTP) and `databaseClient` (direct DB access). When to use which.

## The two clients

```
tina/__generated__/
├── client.ts             # talks to /api/tina/gql via HTTP
└── databaseClient.ts     # talks directly to the DB (no HTTP)
```

| Client | Where | Latency |
|---|---|---|
| `client` | Anywhere in your app | HTTP roundtrip (~50-200ms locally) |
| `databaseClient` | Inside the backend route handler only | Direct DB call (~5-20ms) |

## When to use `client`

- Server Components (the default path)
- Route handlers that aren't `/api/tina/*`
- `generateStaticParams`, `generateMetadata`
- Client Components (rare)

```tsx
import { client } from '@/tina/__generated__/client'

const result = await client.queries.page({ relativePath: 'home.md' })
```

This is the same code as TinaCloud projects — you're agnostic to whether the backend is TinaCloud or self-hosted.

## When to use `databaseClient`

- Inside the self-hosted backend route handler
- Custom backend logic that needs direct DB access without HTTP overhead

```tsx
// app/api/tina/[...routes]/route.ts
import databaseClient from '@/tina/__generated__/databaseClient'

const handler = TinaNodeBackend({
  authProvider: /* ... */,
  databaseClient,
})
```

The handler internally uses `databaseClient` to read from the DB directly — no HTTP self-call.

## Don't use `databaseClient` in app code

```tsx
// ❌ Don't do this in Server Component:
import databaseClient from '@/tina/__generated__/databaseClient'

const result = await databaseClient.request({ query: '...' })
```

Reasons:

- Bypasses the auth layer (your backend's `isAuthorized` check is skipped)
- Couples your app to the self-hosted backend (loses portability if you migrate to TinaCloud)
- Loses Vercel data cache (`fetchOptions: { next: { revalidate } }` doesn't apply to direct DB calls)

Use `client` (over HTTP) — it's the standard path.

## Hybrid: read at build time

For pure-static pages where you want maximum speed at build:

```tsx
// In a server-only utility:
import databaseClient from '@/tina/__generated__/databaseClient'

export async function getAllPages() {
  // Direct DB read — fast, but bypasses auth + caching
  const result = await databaseClient.request({
    query: `query { pageConnection { edges { node { _sys { filename } } } } }`,
  })
  return result.data.pageConnection.edges
}
```

Use only at build time (`generateStaticParams`). For runtime queries, stick with `client`.

## Auth implications

The HTTP path through `/api/tina/gql` runs `isAuthorized()` for every request. If your auth provider is configured strictly, certain queries may return 401.

For server-side queries (Server Components, generateMetadata), the request comes from your Vercel function — no editor session cookie. The auth provider should treat this as "the trusted server" and allow it. Common patterns:

1. `LocalBackendAuthProvider` in dev — allows all
2. Auth.js — checks for either editor session OR a server token in the request header
3. Custom — check `process.env.TINA_PUBLIC_IS_LOCAL` and bypass auth in dev

Production setups need a server-side token. Consult `tinacms-authjs` docs for the exact mechanism.

## Server token pattern

```typescript
// app/api/tina/[...routes]/route.ts
const handler = TinaNodeBackend({
  authProvider: {
    isAuthorized: async (req: any) => {
      // Allow server-side requests with a shared secret
      const token = req.headers.get('authorization')
      if (token === `Bearer ${process.env.TINA_SERVER_TOKEN}`) return { isAuthorized: true }

      // Otherwise check Auth.js session
      // ... existing logic
    },
  },
  databaseClient,
})
```

Then in server-side queries:

```tsx
const result = await client.queries.page(
  { relativePath: 'home.md' },
  { fetchOptions: { headers: { Authorization: `Bearer ${process.env.TINA_SERVER_TOKEN}` } } },
)
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Used `databaseClient` in app code | Bypasses auth and caching | Use `client` |
| `client` queries fail with 401 in production | Auth provider blocks server-side | Add server token bypass |
| Forgot the difference exists | Suboptimal perf or auth issues | Read this file |
| Used `databaseClient` from a Client Component | Build error (Node-only modules) | Move to Server Component |
