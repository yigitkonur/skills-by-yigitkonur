# Marketing Pages

> Documents the public marketing pages, their shared layout, and their navigation chrome. Consult this when adding or changing locale-aware marketing routes, navbar/footer links, or shared public layout composition.

## Key files

- `apps/web/app/(marketing)/[locale]/layout.tsx`
- `apps/web/modules/marketing/shared/components/NavBar.tsx`
- `apps/web/modules/marketing/shared/components/Footer.tsx`

## Grounded behavior

- validates the `locale` route param
- loads locale messages
- wraps children in `Document`, `NextIntlClientProvider`, and `SessionProvider`
- renders shared `NavBar` and `Footer`

This means public pages still know about session state, which is why the navbar can show auth-aware calls to action even on marketing routes.

---

**Related references:**
- `references/routing/routing-marketing.md` — Full marketing route group
- `references/i18n/setup.md` — Locale config source of truth
- `references/marketing/home-page-components.md` — Main landing-page sections
- `references/marketing/content-collections.md` — MDX-backed public content
- `references/hooks/auth-hooks.md` — Auth hooks for session-aware UI
