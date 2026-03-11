# Pattern: Organization-Scoped Page

> Documents the common structure for pages that live under `[organizationSlug]`. Consult this when adding a new org-level dashboard page.

## Route shape

> ⚠️ **Steering:** The `(organizations)` route group is REQUIRED in the file path. It does NOT appear in the URL but MUST exist in the directory structure. Omitting it creates a page that silently never renders — no error, no redirect, just blank.

```text
apps/web/app/(saas)/app/(organizations)/[organizationSlug]/<page>/page.tsx
```

**NOT** `apps/web/app/(saas)/app/[organizationSlug]/<page>/page.tsx` — this path will silently fail.

## What the route inherits

- Auth and onboarding guards from `/(saas)/app/layout.tsx`
- Organization resolution and validation from `/(organizations)/[organizationSlug]/layout.tsx`
- `ActiveOrganizationProvider` with prefetched org data
- Dashboard shell via `AppWrapper` with org-aware navbar

## CRUD page skeleton

### Directory structure

```text
apps/web/app/(saas)/app/(organizations)/[organizationSlug]/projects/
  page.tsx                      # Server component: prefetch + render
  _components/
    projects-list.tsx           # Client component: list with query
    create-project-form.tsx     # Client component: create form
    delete-project-button.tsx   # Client component: delete with mutation
```

### Server component (page.tsx)

```tsx
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
      <h1 className="text-2xl font-bold mb-6">Projects</h1>
      <ProjectsList organizationId={organization.id} />
    </HydrationBoundary>
  );
}
```

### Client list component

```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { orpc } from "@shared/lib/orpc-query-utils";
import { DeleteProjectButton } from "./delete-project-button";

export function ProjectsList({ organizationId }: { organizationId: string }) {
  const { data: projects, isLoading } = useQuery(
    orpc.projects.list.queryOptions({ input: { organizationId } }),
  );

  if (isLoading) return <div>Loading...</div>;

  return (
    <ul>
      {projects?.map((p) => (
        <li key={p.id}>
          {p.name}
          <DeleteProjectButton projectId={p.id} organizationId={organizationId} />
        </li>
      ))}
    </ul>
  );
}
```

### Client mutation component

```tsx
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { orpc } from "@shared/lib/orpc-query-utils";
import { toast } from "sonner";

export function DeleteProjectButton({ projectId, organizationId }: { projectId: string; organizationId: string }) {
  const queryClient = useQueryClient();

  const deleteProject = useMutation(
    orpc.projects.delete.mutationOptions({
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["projects", organizationId] });
        toast.success("Project deleted");
      },
      onError: () => toast.error("Failed to delete project"),
    }),
  );

  return (
    <button onClick={() => deleteProject.mutate({ id: projectId })} disabled={deleteProject.isPending}>
      {deleteProject.isPending ? "Deleting…" : "Delete"}
    </button>
  );
}
```

## Navigation item

Add the page to `apps/web/modules/saas/shared/components/AppWrapper.tsx`:

```tsx
import { FolderKanban } from "lucide-react";

// In the nav items array:
{ label: "Projects", href: `/${organizationSlug}/projects`, icon: FolderKanban }
```

## Practical rules

- Prefer reading the active organization from the provider/hook instead of manually resolving the slug inside every nested client component
- Use server components for the page itself; add `"use client"` only for components that need hooks or browser APIs
- Prefetch data in the server component to avoid client waterfalls
- Always add org-membership guards in the API procedures (not in the page)

---

**Related references:**
- `references/routing/routing-saas.md` — Org route placement in the full tree with `(organizations)` route group
- `references/organizations/active-organization-context.md` — Provider and hook for the active org
- `references/tasks/add-saas-page.md` — Step-by-step guide for creating new SaaS pages
- `references/patterns/react-query-orpc.md` — TanStack Query + oRPC consumption
- `references/patterns/server-prefetch.md` — Server prefetch + hydration pattern
- `references/api/procedure-tiers.md` — Org-membership guard pattern for API endpoints
