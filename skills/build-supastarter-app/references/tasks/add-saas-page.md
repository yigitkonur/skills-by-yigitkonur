# Task: Add a SaaS Page

> Checklist for adding a new authenticated application page. Consult this when creating dashboard pages under `/app` or org-scoped routes.

## Choose the correct route

> ⚠️ **Steering:** Org-scoped pages MUST include the `(organizations)` route group in the file path. Omitting it creates a page that silently never renders — no error, no redirect, just blank.

- Account-scoped page: `apps/web/app/(saas)/app/(account)/<page>/page.tsx`
- Organization-scoped page: `apps/web/app/(saas)/app/(organizations)/[organizationSlug]/<page>/page.tsx`

## What you get automatically

Pages under the `/app` tree inherit:

- session enforcement from `/(saas)/layout.tsx`
- onboarding / organization / billing guards from `/(saas)/app/layout.tsx`
- shared dashboard shell through `AppWrapper`
- organization resolution (org-scoped only) from `/(organizations)/[organizationSlug]/layout.tsx`

## Complete example: org-scoped page

### Server component (page.tsx)

```tsx
// apps/web/app/(saas)/app/(organizations)/[organizationSlug]/projects/page.tsx
import { dehydrate, HydrationBoundary, QueryClient } from "@tanstack/react-query";
import { getActiveOrganization } from "@saas/organizations/lib/get-active-organization";
import { ProjectsList } from "./_components/projects-list";

export default async function ProjectsPage() {
  const queryClient = new QueryClient();
  const organization = await getActiveOrganization();

  await queryClient.prefetchQuery({
    queryKey: ["projects", organization.id],
    queryFn: () => caller.projects.list({ organizationId: organization.id }),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ProjectsList organizationId={organization.id} />
    </HydrationBoundary>
  );
}
```

### Client component (_components/projects-list.tsx)

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { orpc } from "@shared/lib/orpc-query-utils";

export function ProjectsList({ organizationId }: { organizationId: string }) {
  const { data: projects } = useQuery(
    orpc.projects.list.queryOptions({ input: { organizationId } }),
  );

  return <ul>{projects?.map((p) => <li key={p.id}>{p.name}</li>)}</ul>;
}
```

## Practical checklist

1. Place the page in the correct route segment (see paths above)
2. Use server components by default; add `"use client"` only when hooks or browser APIs require it
3. Read session/org data from the existing auth and organization helpers
4. Add navigation item in `apps/web/modules/saas/shared/components/AppWrapper.tsx` with shape `{ label: string, href: string, icon: LucideIcon }`
5. Add i18n translation keys for the page title and any user-facing strings

> ⚠️ **Steering:** Navigation items go in `AppWrapper.tsx`, not in a layout or sidebar file. The nav shape is `{ label, href, icon }` where `icon` is a Lucide icon import.

---

**Related references:**
- `references/routing/routing-saas.md` — Full SaaS route tree with `(organizations)` and `(account)` branches
- `references/routing/access-guards.md` — Guard behavior before the page renders
- `references/patterns/organization-scoped-page.md` — Org-specific page pattern with CRUD skeleton
- `references/patterns/server-prefetch.md` — Server prefetch + hydration pattern
- `references/cheatsheets/file-locations.md` — Quick file placement lookup
