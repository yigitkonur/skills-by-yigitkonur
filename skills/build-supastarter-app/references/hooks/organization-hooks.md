# Organization Hooks

> Overview of hooks that expose the active organization and member-role state. Consult this when building org-scoped UI.

> ⚠️ **Route group required.** Org hooks only work under the `(organizations)` route group where `ActiveOrganizationProvider` is mounted.

## Primary hook

`apps/web/modules/saas/organizations/hooks/use-active-organization.ts` exposes:

- `activeOrganization`
- `activeOrganizationUserRole`
- `isOrganizationAdmin`
- `loaded`
- `setActiveOrganization()`
- `refetchActiveOrganization()`

## Supporting hook

`member-roles.ts` provides localized labels for member/admin/owner roles.

## Usage example

```tsx
"use client";

import { useActiveOrganization } from "@saas/organizations/hooks/use-active-organization";

export function OrgDashboard() {
  const { activeOrganization, isOrganizationAdmin, loaded } = useActiveOrganization();
  if (!loaded) return null;
  return (
    <div>
      <h1>{activeOrganization?.name}</h1>
      {isOrganizationAdmin && <button>Admin Settings</button>}
    </div>
  );
}
```

---

**Related references:**
- `references/organizations/active-organization-context.md` — Provider that backs the hook
- `references/organizations/organization-select.md` — UI that switches the active organization
- `references/patterns/organization-scoped-page.md` — Using org context in app pages
