# Onboarding Step One

> Documents the default account-setup step used in the onboarding wizard. Consult this when adjusting the initial name/avatar collection experience.

> ⚠️ **`authClient.updateUser()` is the mutation target.** Onboarding updates go through Better Auth’s user update API, not a custom endpoint.

## Key file

- `apps/web/modules/saas/onboarding/components/OnboardingStep1.tsx`

## Representative code

```tsx
const formSchema = z.object({
  name: z.string(),
});

await authClient.updateUser({
  name,
});
```

## What this step collects

- display name
- avatar upload via `UserAvatarUpload`

It reuses the same UI form stack and avatar component used in settings, which keeps onboarding and account settings behavior aligned.

---

**Related references:**
- `references/onboarding/onboarding-flow.md` — Parent wizard behavior
- `references/settings/billing-security-and-avatar.md` — Shared avatar upload component
- `references/ui/forms.md` — Form primitive stack
- `references/auth/client-auth-client.md` — authClient methods
- `references/settings/billing-security-and-avatar.md` — Shared avatar component
