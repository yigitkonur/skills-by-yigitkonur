# `client` and `contentApiUrlOverride`

How the TinaCMS client connects to its backend. The default points at TinaCloud; setting `contentApiUrlOverride` redirects to your self-hosted backend.

## TinaCloud (default)

```typescript
export default defineConfig({
  branch: '...',
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID || '',
  token: process.env.TINA_TOKEN || '',
  // contentApiUrlOverride: undefined  ← omit this for TinaCloud
  // ...
})
```

The client points at `https://content.tinajs.io/<version>/content/<clientId>/github/<branch>` automatically.

## Self-hosted

```typescript
export default defineConfig({
  branch: '...',
  clientId: '',
  token: '',
  contentApiUrlOverride: '/api/tina/gql',  // YOUR backend route
  // ...
})
```

With `contentApiUrlOverride` set, the client posts queries to your Next.js API route at `/api/tina/gql` instead of TinaCloud.

## The two clients

After `tinacms build`, you get up to two clients:

| Client | When | Path |
|---|---|---|
| `client` | Always — TinaCloud or self-hosted | `tina/__generated__/client.{ts,js}` |
| `databaseClient` | Self-hosted only | `tina/__generated__/databaseClient.{ts,js}` |

### `client` — talks to the configured GraphQL endpoint

```typescript
import { client } from '@/tina/__generated__/client'

const result = await client.queries.page({ relativePath: 'home.md' })
```

Use this in:
- Server Components (App Router) — preferred
- Route handlers (`app/api/.../route.ts`)
- `getStaticProps` / `getServerSideProps` (Pages Router)
- Client Components (works but adds bundle weight)

### `databaseClient` — direct DB access (self-hosted only)

```typescript
import databaseClient from '@/tina/__generated__/databaseClient'

const result = await databaseClient.request({
  query: '...',
  variables: { ... },
})
```

Use this when:
- You're inside the self-hosted backend route handler — bypasses HTTP, hits DB directly
- You're writing a custom data-fetching server function
- You don't want to round-trip through `/api/tina/gql`

For most app code, stick with `client`.

## `client` config section (rarely needed)

```typescript
client: {
  // Optional config — most projects omit this
  skip: false,            // skip client generation
  // ... advanced options
},
```

The `client` section is for advanced cases like overriding the auto-generated query module. Most projects don't set it.

## How `contentApiUrlOverride` resolves

1. Without override → `https://content.tinajs.io/...` (TinaCloud)
2. With override starting with `/` → your domain + path (e.g. `https://example.com/api/tina/gql`)
3. With override absolute → that exact URL

For most self-hosted setups, `'/api/tina/gql'` is right — it matches the catch-all backend route at `app/api/tina/[...routes]/route.ts`.

## Switching between TinaCloud and self-hosted

Toggling between modes is mostly:

```typescript
const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

export default defineConfig({
  branch: '...',
  clientId: isLocal ? '' : process.env.NEXT_PUBLIC_TINA_CLIENT_ID,
  token: isLocal ? '' : process.env.TINA_TOKEN,
  contentApiUrlOverride: isLocal ? '/api/tina/gql' : undefined,
  // ...
})
```

You also need to add the backend route (`app/api/tina/[...routes]/route.ts`), database adapter, and auth provider for self-hosted. See `references/self-hosted/`.

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Set `contentApiUrlOverride` but no backend route | "Failed to fetch /api/tina/gql" | Add `app/api/tina/[...routes]/route.ts` |
| Forgot to omit `clientId`/`token` for self-hosted | TinaCloud thinks you're a client (auth errors) | Use empty strings |
| `client` import vs `databaseClient` import confusion | Network round-trip when DB direct works | Use `databaseClient` inside backend route handlers |
| Using `client` from a Server Component but env vars not set | Build fails | Set `NEXT_PUBLIC_TINA_CLIENT_ID` and `TINA_TOKEN` (TinaCloud) or `TINA_PUBLIC_IS_LOCAL=true` |

## Verification

```typescript
// In any server component:
import { client } from '@/tina/__generated__/client'

export default async function Page() {
  try {
    const result = await client.queries.page({ relativePath: 'home.md' })
    return <pre>{JSON.stringify(result.data, null, 2)}</pre>
  } catch (e) {
    return <pre>{(e as Error).message}</pre>
  }
}
```

Hit the page and verify content loads. If you see the JSON, the client is wired correctly.
