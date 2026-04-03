# Providers

> Documents the provider layer responsible for actual delivery. Consult this when switching from the development console provider to a production mail service.

## Key files

- `packages/mail/provider/index.ts`
- `packages/mail/provider/console.ts`
- `packages/mail/provider/resend.ts`
- `packages/mail/provider/mailgun.ts`
- `packages/mail/provider/postmark.ts`
- `packages/mail/provider/plunk.ts`
- `packages/mail/provider/nodemailer.ts`

## Provider selection pattern

Like payments and storage, the mail package exports one active provider through the provider barrel. The rest of the package calls `send(...)` from that selection point.

## Practical notes

- The **console** provider is useful in development because it logs payloads instead of delivering them.
- Production providers need verified sender domains and provider-specific API keys.
- `sendEmail()` does template work first; the provider layer only handles the final payload.

---

**Related references:**
- `references/mail/send-email.md` — Public API that delegates to providers
- `references/setup/environment-setup.md` — Mail-related environment variables
- `references/mail/template-rendering.md` — Provider-independent rendering step
- `references/mail/email-templates.md` — Template inventory
