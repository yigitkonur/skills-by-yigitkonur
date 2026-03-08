# Task: Add a SaaS Page

> Checklist for adding a new authenticated application page. Consult this when creating dashboard pages under `/app` or org-scoped routes.

## Choose the correct route

- Account-scoped page: `apps/web/app/(saas)/app/<page>/page.tsx`
- Organization-scoped page: `apps/web/app/(saas)/app/[organizationSlug]/<page>/page.tsx`

## What you get automatically

Pages under this tree inherit:

- session enforcement from `/(saas)/layout.tsx`
- onboarding / organization / billing guards from `/(saas)/app/layout.tsx`
- shared dashboard shell through `AppWrapper`

## Practical checklist

1. Place the page in the right route segment
2. Use server components by default
3. Read session/org data from the existing auth and organization helpers
4. Add navigation in the shared SaaS nav if the page should be discoverable

---

**Related references:**
- `references/routing/routing-saas.md` — Full SaaS route tree
- `references/routing/access-guards.md` — Guard behavior before the page renders
- `references/patterns/organization-scoped-page.md` — Org-specific page pattern
