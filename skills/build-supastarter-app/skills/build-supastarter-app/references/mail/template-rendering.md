# Template Rendering

> Explains how the mail package resolves React Email templates into translated email payloads. Consult this when adding a new template or debugging missing subjects/translations.

## Key file

- `packages/mail/util/templates.ts`

## What `getTemplate()` is responsible for

- resolve a registered template by `templateId`
- load locale messages from `@repo/i18n`
- render HTML and plain text output
- produce the translated subject line

## Supporting inputs

- `packages/mail/emails/index.ts` provides the template registry
- `packages/i18n/lib/messages.ts` provides locale-aware message loading
- `packages/mail/config.ts` defines the default sender

## Practical implication

If you add a new email template, you need more than a new `.tsx` file — it also needs:

- registry wiring
- translation keys for subject/content
- compatible context props

---

**Related references:**
- `references/mail/email-templates.md` — Template inventory
- `references/i18n/messages-loading.md` — Locale message loading behavior
- `references/mail/send-email.md` — Public caller-facing API
- `references/mail/providers.md` — Provider dispatch layer
