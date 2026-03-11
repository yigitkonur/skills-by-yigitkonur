# sendEmail

> Documents the public `sendEmail()` function that all transactional email flows go through. Consult this when sending a new email, deciding between template mode and raw mode, or debugging provider failures.

## Key files

- `packages/mail/index.ts`
- `packages/mail/util/send.ts`

## Representative code

```ts
export async function sendEmail<T extends TemplateId>(params: { to: string; from?: string; locale?: keyof typeof i18nConfig.locales; } & (...)) {
  const { to, from, locale = i18nConfig.defaultLocale } = params;
  if ("templateId" in params) {
    const template = await getTemplate({ templateId, context, locale });
    subject = template.subject;
    text = template.text;
    html = template.html;
  }
  await send({ to, from, subject, text, html });
}
```

## Modes

- **Template mode** — `templateId` + `context`
- **Raw mode** — `subject` + `html` / `text`

## Implementation notes

- Provider failures are caught and logged; the function returns `true`/`false` instead of throwing.
- Locale defaults to the i18n package's default locale.
- Most auth and marketing flows use template mode rather than raw email bodies.

---

**Related references:**
- `references/mail/template-rendering.md` — How template mode renders HTML/text/subject
- `references/mail/providers.md` — Active provider dispatch
- `references/mail/email-templates.md` — Registered template components
- `references/cheatsheets/imports.md` — Common import patterns
