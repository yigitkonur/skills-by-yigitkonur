# Pattern: Organization-Scoped Page

> Documents the common structure for pages that live under `[organizationSlug]`. Consult this when adding a new org-level dashboard page.

## Route shape

```text
apps/web/app/(saas)/app/(organizations)/[organizationSlug]/<page>/page.tsx
```

## Layout inheritance chain

Organization-scoped pages inherit from three nested layouts:

1. `(saas)/layout.tsx` — session enforcement, global providers
2. `(organizations)/layout.tsx` — organization resolution
3. `[organizationSlug]/layout.tsx` — `ActiveOrganizationProvider`, org-aware navigation via `AppWrapper`

This means your page automatically gets authentication, organization context, and the dashboard shell without any additional setup.

## What the route inherits

- auth and onboarding guards
- organization resolution via `ActiveOrganizationProvider`
- organization-aware navbar and menu links

## CRUD page skeleton

For interactive pages (list, create, edit, delete), split into server and client components:

```tsx
// page.tsx — Server Component (data loading)
export default async function ProjectsPage({
  params,
}: {
  params: Promise<{ organizationSlug: string }>;
}) {
  const { organizationSlug } = await params;
  // Use server-side API or query helpers to load data
  return <ProjectsList organizationSlug={organizationSlug} />;
}
```

```tsx
// Place client components in apps/web/modules/saas/<feature>/components/
"use client";

export function ProjectsList({ organizationSlug }: { organizationSlug: string }) {
  // Use @repo/api hooks for data fetching and mutations
  // Render interactive UI here
}
```

## Practical rules

1. Keep `page.tsx` as a server component for initial data loading.
2. Move all interactivity (forms, buttons, optimistic updates) to client components in `apps/web/modules/saas/<feature>/components/`.
3. Use `@repo/api` query hooks in client components, not direct database calls.
4. Read the active organization from the provider/hook instead of manually resolving the slug inside every nested client component.
5. Add navigation item to `apps/web/modules/saas/shared/components/AppWrapper.tsx`.

---

**Related references:**
- `references/routing/routing-saas.md` — Org route placement in the full tree
- `references/organizations/active-organization-context.md` — Provider and hook for the active org
- `references/tasks/add-saas-page.md` — Step-by-step guide for creating new SaaS pages
