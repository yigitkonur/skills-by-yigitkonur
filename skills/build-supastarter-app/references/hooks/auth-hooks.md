# Auth Hooks

> Overview of client-side auth hooks used by the app. Consult this when you need session-aware client components.

> ⚠️ **Provider required.** Auth hooks require `SessionProvider` from `ClientProviders`. They throw if used outside this context.

## Primary hook

`apps/web/modules/saas/auth/hooks/use-session.ts` exposes the session context.

Returned values include:

- `user`
- `session`
- `loaded`
- `reloadSession()`

## Practical usage

Settings forms use `useSession()` for default values and to reload the session after account changes. Marketing nav also reads it to swap login vs dashboard CTA.

## Usage example

```tsx
"use client";

import { useSession } from "@saas/auth/hooks/use-session";

export function UserGreeting() {
  const { user, loaded } = useSession();
  if (!loaded) return null;
  if (!user) return <a href="/auth/login">Sign in</a>;
  return <span>Hello, {user.name}</span>;
}
```

---

**Related references:**
- `references/auth/session-hook-provider.md` — Detailed session hook behavior
- `references/settings/account-settings.md` — Session-driven settings forms
- `references/marketing/pages.md` — Session-aware marketing nav
