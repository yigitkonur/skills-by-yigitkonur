# Login Flow

> Explains the adaptive sign-in UI that supports password, magic link, OAuth, and passkey flows in one component. Consult this when changing login UX, redirect behavior, or two-factor handling.

> ⚠️ **Redirect after login.** The post-login redirect chain is: invitation URL → `redirectTo` param → `config.saas.redirectAfterSignIn`. Onboarding guard may intercept.

## Key files

- `apps/web/modules/saas/auth/components/LoginForm.tsx`
- `packages/auth/config.ts`
- `packages/auth/client.ts`

## Representative code

```ts
const formSchema = z.union([
  z.object({ mode: z.literal("magic-link"), email: z.email() }),
  z.object({ mode: z.literal("password"), email: z.email(), password: z.string().min(1) }),
]);

const onSubmit = form.handleSubmit(async (values) => {
  if (values.mode === "password") {
    const { data } = await authClient.signIn.email({ ...values });
    if ((data as any).twoFactorRedirect) {
      router.replace(withQuery("/auth/verify", Object.fromEntries(searchParams.entries())));
      return;
    }
    router.replace(redirectPath);
  } else {
    await authClient.signIn.magicLink({ ...values, callbackURL: redirectPath });
  }
});
```

## Supported paths through the form

- **Password login** — `authClient.signIn.email()`
- **Magic link** — `authClient.signIn.magicLink()`
- **Passkey** — `authClient.signIn.passkey()` via WebAuthn
- **OAuth** — provider buttons for Google/GitHub
- **2FA handoff** — password login can redirect to `/auth/verify`

## Redirect priority

1. Invitation flow
2. `redirectTo` query parameter
3. `config.saas.redirectAfterSignIn`

## Implementation notes

- The Zod union keeps validation aligned with the chosen auth mode.
- Feature flags in `packages/auth/config.ts` decide which auth methods are actually rendered.
- Invitation-aware redirects preserve the `invitationId` and related search params through the flow.

## Redirect flow

```text
/auth/login → Better Auth → callback → /app
                                        ↓
                                  onboarding incomplete?
                                  → /onboarding
                                  otherwise → /app/[orgSlug]
```

---

**Related references:**
- `references/auth/client-auth-client.md` — Auth client methods used by the form
- `references/auth/feature-flags.md` — Flags that toggle login modes
- `references/auth/signup-invitations.md` — Invitation-aware behavior shared with signup
- `references/routing/access-guards.md` — Guard sequence that drives redirects
