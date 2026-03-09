# i18n Setup

> Documents the core internationalization configuration shared by next-intl, the web app, and localized email/template flows. Consult this when adding a locale, changing the default locale, or tracing where locale cookies and messages come from.

## Key files

- `packages/i18n/config.ts`
- `packages/i18n/index.ts`
- `apps/web/modules/i18n/request.ts`

## Representative code

```ts
export const config = {
  locales: {
    en: { label: "English", currency: "USD" },
    de: { label: "Deutsch", currency: "EUR" },
  },
  defaultLocale: "en",
  localeCookieName: "NEXT_LOCALE",
} as const;
```

## Implementation notes

- `next.config.ts` points next-intl at `apps/web/modules/i18n/request.ts`.
- The locale cookie name is shared across routing, auth email flows, and message loading.
- `Locale` is derived from the keys of `config.locales`, not manually duplicated.

---

**Related references:**
- `references/i18n/locale-routing.md` — How locale is resolved per request
- `references/i18n/messages-loading.md` — How translations are loaded
- `references/setup/next-config.md` — next-intl plugin wiring in Next.js config
