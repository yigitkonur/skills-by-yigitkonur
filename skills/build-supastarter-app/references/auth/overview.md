# Auth Overview

> High-level map of the Supastarter authentication system across server config, client helpers, session providers, and the login/signup UI. Consult this first when you need to understand where an auth concern belongs before diving into a narrower reference.
>
> Better Auth lives in `packages/auth`, but the day-to-day consumption points are spread across SaaS server helpers, the session context provider, and the auth form components in `apps/web/modules/saas/auth`.

> ⚠️ **Server vs client.** Server session helpers use React `cache()` and MUST only be called in server components. Use `useSession()` for client components.

## Moving pieces

- `packages/auth/auth.ts` — central Better Auth instance, plugins, hooks, emails, OpenAPI
- `packages/auth/config.ts` — feature flags for signup, magic links, passkeys, onboarding, organizations
- `packages/auth/client.ts` — client-side `authClient`
- `apps/web/modules/saas/auth/lib/server.ts` — cached server helpers used by layouts and pages
- `apps/web/modules/saas/auth/components/SessionProvider.tsx` — session context provider
- `apps/web/modules/saas/auth/components/LoginForm.tsx` — multi-mode sign-in UI
- `apps/web/modules/saas/auth/components/SignupForm.tsx` — signup + invitation flow

## Representative integration

```ts
// packages/auth/client.ts
export const authClient = createAuthClient({
  plugins: [
    magicLinkClient(),
    organizationClient(),
    adminClient(),
    passkeyClient(),
    twoFactorClient(),
  ],
});
```

## Architecture split

- **Server configuration** lives in `packages/auth`
- **Server consumption** happens through cached helpers in `apps/web/modules/saas/auth/lib/server.ts`
- **Client consumption** happens through `authClient`, `SessionProvider`, and `useSession()`
- **Route behavior** is coordinated with SaaS access guards and standalone auth/onboarding pages

## Implementation notes

- Multi-tenancy is part of auth itself through Better Auth's organization plugin.
- Many billing side effects are triggered from auth lifecycle hooks, especially seat updates and pre-delete subscription cleanup.
- Query params such as `invitationId`, `email`, and `redirectTo` are central to the login/signup redirect flows.

---

**Related references:**
- `references/auth/better-auth-config.md` — Full server-side Better Auth configuration
- `references/auth/feature-flags.md` — Toggles that change auth behavior across the app
- `references/auth/client-auth-client.md` — Client-side auth entry point
- `references/auth/server-session-helpers.md` — Cached server helpers used by layouts and pages
