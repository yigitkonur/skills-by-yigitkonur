# Task: Add a Marketing Page

> Checklist for adding a new public-facing page under the locale-aware marketing route group. Consult this when adding blog-like, changelog, or standalone public pages.

## File location

Create pages under:

```text
apps/web/app/(marketing)/[locale]/...
```

## Important constraints

- Marketing pages are locale-scoped
- The shared marketing layout already provides `Document`, `NextIntlClientProvider`, `SessionProvider`, `NavBar`, and `Footer`
- Invalid locales should still resolve through the existing `notFound()` logic in the layout

## Practical checklist

1. Add the page under the `[locale]` route group
2. Use translations or locale-aware content where appropriate
3. Link it from `NavBar.tsx` or `Footer.tsx` if it should be navigable
4. Add/update Playwright coverage if it becomes a primary entry point

---

**Related references:**
- `references/routing/routing-marketing.md` — Marketing route structure
- `references/marketing/pages.md` — Shared chrome and links
- `references/marketing/content-collections.md` — When content should live in MDX/MD instead of JSX
