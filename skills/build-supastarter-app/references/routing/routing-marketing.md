# Marketing Route Group

> Marketing pages live under the locale-aware `/(marketing)/[locale]` route group and share a single public shell. Use this reference when adding a public page, debugging locale handling, or tracing how the marketing layout composes document, i18n, auth session state, and chrome.

## Locale-scoped route shape

The marketing surface is anchored at `apps/web/app/(marketing)/[locale]/layout.tsx`, so public pages inherit a locale segment in the URL rather than using plain root-level routes. The layout resolves the dynamic `locale` param, validates it, and loads the locale message bundle before rendering children.

```tsx
// apps/web/app/(marketing)/[locale]/layout.tsx
export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

setRequestLocale(locale);

if (!locales.includes(locale as any)) {
  notFound();
}
```

Because `generateStaticParams()` returns every supported locale from `@repo/i18n/config`, Next.js can pre-render the marketing layout for each locale path.

## Marketing shell composition

After locale setup, the layout renders a document wrapper, translation provider, session provider, and the visible marketing chrome:

```tsx
// apps/web/app/(marketing)/[locale]/layout.tsx
<Document locale={locale}>
  <NextIntlClientProvider locale={locale} messages={messages}>
    <SessionProvider>
      <NavBar />
      <main className="min-h-screen">{children}</main>
      <Footer />
    </SessionProvider>
  </NextIntlClientProvider>
</Document>
```

The important shell pieces are the shared `NavBar`, the `main` container with `min-h-screen`, and the shared `Footer`. This keeps public pages visually consistent while still giving them access to session-aware UI.

## Why marketing still has a session provider

Even though marketing routes are public, `SessionProvider` is still mounted in the layout. That lets the public shell react to signed-in state without moving those pages into the SaaS route tree.

## Relationship to middleware and locale routing

Marketing routes are the requests that eventually fall through to `next-intl` middleware in `apps/web/proxy.ts`. Paths such as `/onboarding` and `/choose-plan` explicitly bypass locale handling, but marketing pages remain locale-driven and therefore rely on the `[locale]` route group plus `next-intl` request routing.

---

**Related references:**
- `references/routing/layout-chain.md` — Side-by-side provider order for marketing and SaaS layouts
- `references/routing/providers-document.md` — Shared `Document` and `ClientProviders` behavior used by marketing too
- `references/i18n/locale-routing.md` — How locale detection and routing interact with the marketing tree
