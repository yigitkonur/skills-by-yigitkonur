# Signup and Invitations

> Documents the registration flow, invitation-only behavior, email verification, and invitation acceptance. Consult this when changing how new users enter the app or when debugging invited-user edge cases.

## Key files

- `apps/web/app/auth/signup/page.tsx`
- `apps/web/modules/saas/auth/components/SignupForm.tsx`
- `packages/auth/auth.ts`
- `packages/auth/plugins/invitation-only/index.ts`

## Representative code

```ts
if (!(config.enableSignup || invitationId)) {
  redirect(withQuery("/auth/login", params));
}

if (invitationId) {
  const invitation = await getInvitation(invitationId);
  if (!invitation || invitation.status !== "pending" || invitation.expiresAt.getTime() < Date.now()) {
    redirect(withQuery("/auth/login", params));
  }
}

const onSubmit = form.handleSubmit(async ({ email, password, name }) => {
  const { error } = await (authConfig.enablePasswordLogin
    ? authClient.signUp.email({ email, password, name, callbackURL: redirectPath })
    : authClient.signIn.magicLink({ email, name, callbackURL: redirectPath }));

  if (invitationOnlyMode) {
    await authClient.organization.acceptInvitation({ invitationId });
    router.push(config.saas.redirectAfterSignIn);
  }
});
```

## Invitation and verification behavior

- The invitation-only plugin blocks public signup unless the email has a pending invitation.
- Organization invitation emails deep-link to `/auth/login` for existing users and `/auth/signup` for new users.
- Standard public signup requires email verification when `config.enableSignup` is true.
- Invitation-only signup can auto sign in after signup because the invitation already establishes trust.
- The `/auth/signup` page preserves search params, validates invitation status/expiry on the server, and redirects invalid invitations back to `/auth/login`.

## Implementation notes

- When password signup is disabled, the form falls back to magic-link registration instead of rendering a second component.
- Successful public signups usually show a verify-email alert before the user proceeds.
- Invitation flows accept the invitation and redirect immediately after signup/login succeeds.

---

**Related references:**
- `references/auth/better-auth-config.md` — Server plugin setup behind invitation-only mode
- `references/auth/client-auth-client.md` — Client methods used by signup and invitation acceptance
- `references/mail/email-templates.md` — Verification, magic-link, and invitation email templates
