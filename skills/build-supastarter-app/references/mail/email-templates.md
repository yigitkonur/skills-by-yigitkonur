# Email Templates

> Documents the React Email template registry used by auth, invitations, newsletters, and welcome emails. Consult this when adding a new template or tracing which template ID a flow uses.

## Key files

- `packages/mail/emails/index.ts`
- `packages/mail/emails/MagicLink.tsx`
- `packages/mail/emails/OrganizationInvitation.tsx`
- other files in `packages/mail/emails/`

## Registered templates

```ts
export const mailTemplates = {
  magicLink: MagicLink,
  forgotPassword: ForgotPassword,
  newUser: NewUser,
  newsletterSignup: NewsletterSignup,
  organizationInvitation: OrganizationInvitation,
  emailVerification: EmailVerification,
} as const;
```

## Implementation notes

- Template IDs are the keys used by `sendEmail({ templateId: ... })`.
- Auth uses templates for magic links, password reset, verification, welcome emails, and org invitations.
- Templates receive locale-aware translations through the template-resolution layer.

---

**Related references:**
- `references/mail/send-email.md` — Public API that renders and dispatches templates
- `references/mail/template-rendering.md` — How props and translations become HTML/text/subject
- `references/auth/signup-invitations.md` — Signup and invitation flows that trigger these templates
