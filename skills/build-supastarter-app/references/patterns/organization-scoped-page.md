# Pattern: Organization-Scoped Page

> Documents the common structure for pages that live under `[organizationSlug]`. Consult this when adding a new org-level dashboard page.

## Route shape

```text
apps/web/app/(saas)/app/[organizationSlug]/<page>/page.tsx
```

## What the route inherits

- auth and onboarding guards
- organization resolution via `ActiveOrganizationProvider`
- organization-aware navbar and menu links

## Practical rule

Prefer reading the active organization from the provider/hook instead of manually resolving the slug inside every nested client component.

---

**Related references:**
- `references/routing/routing-saas.md` — Org route placement in the full tree
- `references/organizations/active-organization-context.md` — Provider and hook for the active org
- `references/tasks/add-saas-page.md` — Step-by-step guide for creating new SaaS pages
