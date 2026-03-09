# Account Settings

> Documents the core user-account settings patterns. Consult this when changing profile forms, session refresh behavior, or account-level settings pages.

## Representative file

- `apps/web/modules/saas/settings/components/ChangeEmailForm.tsx`

## Representative code

```tsx
const { user, reloadSession } = useSession();

const { error } = await authClient.changeEmail({
  newEmail: email,
});

if (!error) {
  toastSuccess(...);
  reloadSession();
}
```

## Common settings patterns

- read initial values from `useSession()`
- validate with Zod where needed
- call `authClient` mutations
- show toast feedback
- reload session after user-profile mutations

This same shape appears across change-name, change-email, password, and related personal account settings flows.

---

**Related references:**
- `references/auth/session-hook-provider.md` — Hook used to access `reloadSession`
- `references/ui/forms.md` — Shared form primitives
- `references/settings/billing-security-and-avatar.md` — Other settings-related components
