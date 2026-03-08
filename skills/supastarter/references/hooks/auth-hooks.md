# Auth Hooks

> Overview of client-side auth hooks used by the app. Consult this when you need session-aware client components.

## Primary hook

`apps/web/modules/saas/auth/hooks/use-session.ts` exposes the session context.

Returned values include:

- `user`
- `session`
- `loaded`
- `reloadSession()`

## Practical usage

Settings forms use `useSession()` for default values and to reload the session after account changes. Marketing nav also reads it to swap login vs dashboard CTA.

---

**Related references:**
- `references/auth/session-hook-provider.md` — Detailed session hook behavior
- `references/settings/account-settings.md` — Session-driven settings forms
- `references/marketing/pages.md` — Session-aware marketing nav
