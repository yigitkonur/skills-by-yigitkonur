# `ctx.auth` Object

Every tool callback receives a `ctx.auth` object when OAuth is configured. This is the verified identity.

## Shape

```ts
interface AuthContext {
  user: UserInfo                       // verified, normalized identity
  payload: Record<string, unknown>     // raw decoded JWT payload (provider-specific claims)
  accessToken: string                  // the raw bearer token
  scopes: string[]                     // from the JWT 'scope' claim, space-split
  permissions: string[]                // from 'permissions' (Auth0) or 'resource_access' (Keycloak)
}

interface UserInfo {
  userId: string                       // mapped from JWT 'sub' — always present
  email?: string
  name?: string
  username?: string
  nickname?: string
  picture?: string
  roles?: string[]                     // realm roles for Keycloak, custom claims elsewhere
  permissions?: string[]
  [key: string]: unknown               // additional provider-specific claims (e.g. organization_id)
}
```

## When fields are populated

| Field | Populated when |
|---|---|
| `user.userId` | Always — extracted from `sub` claim |
| `user.email`, `user.name` | Provider includes them in the access token (Auth0 with `email` scope, WorkOS standard, Keycloak with profile mapper) |
| `user.roles` | Keycloak `realm_access.roles`; otherwise from custom `getUserInfo` |
| `user.organization_id` | WorkOS multi-tenant tokens |
| `permissions` | Auth0 with RFC 9068 token dialect; Keycloak `resource_access` formatted as `client:role` |
| `scopes` | Always — split from JWT `scope` |
| `accessToken` | Always — the raw token, useful for upstream API calls |
| `payload` | Always — raw decoded JWT for fields that aren't normalized |

## Using in tool handlers

```ts
import { object, text } from 'mcp-use/server'
import { z } from 'zod'

server.tool(
  {
    name: 'create-document',
    schema: z.object({ title: z.string(), content: z.string() }),
  },
  async ({ title, content }, ctx) => {
    const doc = await db.documents.create({
      title,
      content,
      createdBy: ctx.auth.user.userId,
      createdByName: ctx.auth.user.name,
    })
    return text(`Document ${doc.id} created by ${ctx.auth.user.name}`)
  }
)
```

## Calling upstream APIs with `accessToken`

Pass-through tokens are valid against the issuing provider's APIs:

```ts
server.tool(
  { name: 'get-google-profile' },
  async (_args, ctx) => {
    const res = await fetch('https://openidconnect.googleapis.com/v1/userinfo', {
      headers: { Authorization: `Bearer ${ctx.auth.accessToken}` },
    })
    return object(await res.json())
  }
)
```

## Reading provider-specific claims

The factory functions normalize common fields. For anything else, read from `payload`:

```ts
const orgId = ctx.auth.payload.org_id as string | undefined
const tenantId = ctx.auth.payload['https://myapp.com/tenant_id'] as string | undefined
```

Always narrow `payload` reads — TypeScript types them as `unknown`.

## Custom normalization

To reshape claims into the `UserInfo` shape (e.g. namespaced Auth0 roles, nested Supabase metadata), use `getUserInfo` on `oauthCustomProvider()` or `oauthProxy()`. See `providers/07-custom.md`.

## Anti-patterns

- Do **not** trust `ctx.auth.user.email` for authorization — verify the underlying claim is from a verified email scope.
- Do **not** rely on `ctx.auth.user.userId` being a stable cross-provider identifier — it is the provider's `sub`, which is per-tenant.
- Do **not** log `ctx.auth.accessToken`. See `../26-anti-patterns/05-security-and-cors.md`.

## Cross-references

- Tool guards: `04-permission-guards.md`
- Provider-specific claim shapes: `providers/01-auth0.md` through `providers/07-custom.md`
