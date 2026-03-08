# Server Session Helpers

> Covers the cached server-only helpers used by layouts and server components to read session, organization, account, passkey, and invitation state. Consult this when a server page needs auth state without talking to Better Auth directly.

## Key files

- `apps/web/modules/saas/auth/lib/server.ts`

## Representative code

```ts
export const getSession = cache(async () => {
  return await auth.api.getSession({
    headers: await headers(),
    query: { disableCookieCache: true },
  });
});

export const getOrganizationList = cache(async () => {
  try {
    return await auth.api.listOrganizations({ headers: await headers() });
  } catch {
    return [];
  }
});
```

## Important helpers

- `getSession()` — fresh session for guards and layouts
- `getActiveOrganization(slug)` — resolve full organization by slug
- `getOrganizationList()` — list user's orgs for layouts and page gates
- `getUserAccounts()` — linked auth providers
- `getUserPasskeys()` — passkey credentials
- `getInvitation(id)` — invitation lookup for login/signup flows

## Implementation notes

- Every helper is wrapped in React `cache()` so repeated calls deduplicate during one render tree.
- `getSession()` disables Better Auth cookie caching because access guards must stay fresh.
- These are the safe server entry points; client code should not import `auth.api.*` directly.

---

**Related references:**
- `references/routing/routing-saas.md` — Server helpers used by SaaS layouts
- `references/auth/session-hook-provider.md` — Client-facing counterpart to these server helpers
- `references/organizations/active-organization-context.md` — Client organization state layered on top of server auth state
