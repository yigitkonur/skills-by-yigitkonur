# Active Organization Context

> Documents the client-side provider and hook that resolve the active organization from the URL and keep session/billing caches in sync. Consult this when changing organization switching, org-aware navbar behavior, or org-scoped page state.

> ⚠️ **Client-side only.** `useActiveOrganization()` only works in client components under the `(organizations)` route group where `ActiveOrganizationProvider` is mounted.

## Key files

- `apps/web/modules/saas/organizations/components/ActiveOrganizationProvider.tsx`
- `apps/web/modules/saas/organizations/hooks/use-active-organization.ts`

## Representative code

```ts
const activeOrganizationSlug = params.organizationSlug as string;
const { data: activeOrganization } = useActiveOrganizationQuery(activeOrganizationSlug, {
  enabled: !!activeOrganizationSlug,
});

const setActiveOrganization = async (organizationSlug: string | null) => {
  const { data: newActiveOrganization } = await authClient.organization.setActive(
    organizationSlug ? { organizationSlug } : { organizationId: null },
  );
  await refetchActiveOrganization();
  router.push(`/app/${newActiveOrganization.slug}`);
};
```

## Implementation notes

- The provider derives the active org from `params.organizationSlug`.
- Switching organizations updates the session query cache and can prefetch org-level purchases.
- `useActiveOrganization()` returns safe defaults when rendered outside the provider.

## Hook return values

```tsx
const {
  activeOrganization,          // full org object or null
  activeOrganizationUserRole,  // "member" | "admin" | "owner"
  isOrganizationAdmin,         // true for admin or owner
  loaded,                      // whether data has been fetched
  setActiveOrganization,       // switch to different org
  refetchActiveOrganization,   // force refresh
} = useActiveOrganization();
```

---

**Related references:**
- `references/organizations/organization-select.md` — Main UI for switching organizations
- `references/auth/server-session-helpers.md` — Server auth helpers that feed org-aware layouts
- `references/payments/plans-config.md` — Org-level billing mode that affects prefetch behavior
