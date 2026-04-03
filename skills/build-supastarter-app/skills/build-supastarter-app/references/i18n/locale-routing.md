# Locale Routing

> Explains how the app determines the active locale for each request. Consult this when locale URLs, cookies, or next-intl request resolution behave unexpectedly.

## Key files

- `apps/web/modules/i18n/request.ts`
- `apps/web/proxy.ts`
- `apps/web/app/(marketing)/[locale]/layout.tsx`

## Representative code

```ts
export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale) {
    locale = await getUserLocale();
  }
  if (!routing.locales.includes(locale)) {
    locale = routing.defaultLocale;
  }
  return {
    locale,
    messages: await getMessagesForLocale(locale),
  };
});
```

## Implementation notes

- Marketing routes use `[locale]` in the pathname and call `setRequestLocale(locale)`.
- Middleware handles locale-aware routing for public pages while certain SaaS gate pages bypass locale prefixes.
- The locale cookie is a fallback when no locale segment is present.

---

**Related references:**
- `references/i18n/setup.md` — Shared config and locale definitions
- `references/routing/routing-marketing.md` — Marketing locale route group
- `references/api/contact-module.md` — Locale resolution flowing into email side effects
- `references/i18n/messages-loading.md` — How translations are loaded
