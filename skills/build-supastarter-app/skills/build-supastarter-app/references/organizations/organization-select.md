# Organization Select

> Documents the navbar organization switcher that lets users jump between organizations or their personal account. Consult this when changing org-switch UX, collapsed-sidebar behavior, or plan badges in the dashboard shell.

> ⚠️ **Redirect on switch.** Switching organizations navigates to the new org's slug URL. Ensure your page handles the new `organizationSlug` param.

## Key files

- `apps/web/modules/saas/organizations/components/OrganizationSelect.tsx`

## Behavior

- Shows the active org name, logo, and plan badge
- Lists all available organizations as radio/select items
- Supports collapsed-sidebar mode with tooltip-friendly rendering
- Includes a personal-account option and a create-organization shortcut when enabled

## Implementation notes

- The component works with `useActiveOrganization()` rather than re-implementing org lookup logic.
- Switching orgs ultimately goes through `setActiveOrganization()` from the active-org context.
- This is a shell-level component, so most changes belong here or in the context provider rather than in individual pages.

---

**Related references:**
- `references/organizations/active-organization-context.md` — State and switching logic behind the selector
- `references/routing/middleware-proxy.md` — How the navbar and shell embed the selector
- `references/payments/plans-config.md` — Plan badges displayed for organizations
