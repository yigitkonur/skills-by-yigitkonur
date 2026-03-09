# Messages Loading

> Documents how translation messages are loaded for pages and emails. Consult this when a locale exists in config but strings are missing at runtime.

## Key files

- `packages/i18n/index.ts`
- `packages/i18n/lib/messages.ts`
- `apps/web/modules/i18n/request.ts`

## Flow outline

1. Resolve the active locale
2. Import the locale's message bundle through the i18n package
3. Pass those messages into `NextIntlClientProvider` or template rendering helpers

## Implementation notes

- The i18n package is the shared source of truth for messages across the app and mail templates.
- Request-time loading keeps the web app and email rendering aligned on the same locale keys.
- Missing locale/message problems usually come from config, import paths, or an unsupported locale value.

---

**Related references:**
- `references/i18n/setup.md` — Locale definitions and config
- `references/i18n/locale-routing.md` — How the active locale is chosen
- `references/mail/template-rendering.md` — Localized subject/body rendering for emails
