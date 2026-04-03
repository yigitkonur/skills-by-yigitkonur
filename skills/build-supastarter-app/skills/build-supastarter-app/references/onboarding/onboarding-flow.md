# Onboarding Flow

> Documents the post-signup onboarding wizard. Consult this when adding steps, changing completion behavior, or debugging the onboarding redirect loop.

> ⚠️ **Onboarding must be enabled in auth config.** If `packages/auth/config.ts` has `users.enableOnboarding: false`, the access guard skips onboarding entirely.

## Key file

- `apps/web/modules/saas/onboarding/components/OnboardingForm.tsx`

## Representative code

```tsx
const onCompleted = async () => {
  await authClient.updateUser({
    onboardingComplete: true,
  });

  await clearCache();
  router.replace(redirectTo ?? "/app");
};
```

## Flow summary

- current step comes from the `?step=` search param
- step components are configured in an in-file `steps` array
- final completion updates `onboardingComplete`
- cache is cleared before redirecting into the app

If more than one step exists, the wizard shows a progress bar.

---

**Related references:**
- `references/onboarding/onboarding-step-one.md` — Default step implementation
- `references/routing/access-guards.md` — Why incomplete users get redirected into onboarding
- `references/auth/feature-flags.md` — Flag that enables onboarding
- `references/patterns/form-with-zod.md` — Form pattern for steps
- `references/auth/feature-flags.md` — Onboarding enable flag
