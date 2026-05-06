# `scopesSupported` Configuration

Controls which scopes the server advertises in `.well-known/oauth-authorization-server` and what clients request during authorization.

## Where it lives

Every provider factory accepts `scopesSupported`:

```ts
oauth: oauthAuth0Provider({
  scopesSupported: ['openid', 'profile', 'email', 'offline_access'],
})

oauth: oauthWorkOSProvider({
  scopesSupported: ['email', 'offline_access', 'openid', 'profile'],
})

oauth: oauthKeycloakProvider({
  scopesSupported: ['openid', 'profile', 'email'],
})

oauth: oauthCustomProvider({
  scopesSupported: ['openid', 'profile', 'email', 'read:repos'],
  // ... other required fields
})

oauth: oauthProxy({
  scopes: ['openid', 'email', 'profile'], // note: 'scopes', not 'scopesSupported'
  // ...
})
```

Note the inconsistency: built-in providers use `scopesSupported` (advertised in metadata), `oauthProxy` uses `scopes` (which scopes the server requests on the client's behalf).

## Defaults per provider

| Provider | Default `scopesSupported` |
|---|---|
| Auth0 | `['openid', 'profile', 'email', 'offline_access']` |
| WorkOS | `['email', 'offline_access', 'openid', 'profile']` |
| Keycloak | `['openid', 'profile', 'email', 'offline_access', 'roles']` |
| Supabase | `['openid', 'profile', 'email']` |
| Better Auth | `['openid', 'profile', 'email', 'offline_access']` |
| Custom | required — no default |
| OAuth Proxy | `['openid', 'email', 'profile']` |

## When to override

| Goal | Change |
|---|---|
| Disable refresh tokens | Remove `offline_access` |
| Request only minimal identity | `['openid']` only — most providers will still mint a usable `sub` |
| Add provider-specific scopes | Append `'read:repos'`, `'admin:org'`, etc. |
| Match a strict scope policy | Set the exact list — clients cannot request unlisted scopes |

The advertised list is what clients see in `.well-known`. Clients pick scopes from this set. If a client requests a scope outside the list, mcp-use rejects the authorization request.

## Effect on tool gating

`ctx.auth.scopes` is populated from the JWT `scope` claim — what was actually granted, not what was advertised. To gate tools by scope:

```ts
if (!ctx.auth.scopes.includes('write:documents')) {
  return error('Forbidden: write:documents scope required')
}
```

A scope must be:
1. Listed in `scopesSupported` (server advertises it),
2. Configured in the upstream provider (provider issues it),
3. Requested by the client during authorization,
4. Granted by the user during consent.

If any step is missing, `ctx.auth.scopes` will not contain the scope.

## Provider-specific scope quirks

- **Auth0:** `permissions` claim (RFC 9068 token dialect) is separate from `scope`. Use `ctx.auth.permissions`.
- **Keycloak:** realm roles are in `realm_access.roles`, not in `scope`. Use `ctx.auth.user.roles`.
- **WorkOS:** `roles` and `organization_id` come as custom claims on `payload`, not as scopes.
- **Supabase:** scopes are minimal; rely on RLS policies for fine-grained access.
- **Google (proxy):** scope strings are URLs (`https://www.googleapis.com/auth/drive.readonly`). Use full URL strings in `scopes`.

## Anti-patterns

- Don't request `offline_access` if you are not using refresh tokens — it adds consent friction.
- Don't add scopes to `scopesSupported` that the upstream doesn't issue — clients will request them and the consent will fail or strip them.
- Don't rely on `scopesSupported` for security — clients can ignore the advertised list. The actual gate is what the upstream issues.

## Cross-references

- Tool guards: `04-permission-guards.md`
- Refresh tokens: `06-refresh-tokens.md`
- Per-provider scope details: `providers/01-auth0.md` through `providers/07-custom.md`
