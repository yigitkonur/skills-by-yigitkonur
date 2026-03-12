# Admin Organizations

> Documents the admin-facing organization list and edit surface. Consult this when changing organization search, paging, or maintenance actions from the admin area.

> ⚠️ **Admin org management ≠ org self-service.** This is the admin-only view. End-user org management uses `references/organizations/` components.

## Key files

- `apps/web/modules/saas/admin/component/organizations/OrganizationList.tsx`
- `apps/web/modules/saas/admin/component/organizations/OrganizationForm.tsx`

## What this area supports

- searchable organization table
- pagination and admin editing
- inspection of organization name, logo, and membership-related data

## Practical notes

This area parallels the user-admin table: it is part of the SaaS admin surface, not the organization self-service settings area.

---

**Related references:**
- `references/admin/users-admin.md` — Companion admin surface
- `references/organizations/members-and-invitations.md` — End-user organization management UI
- `references/routing/routing-saas.md` — Admin route placement
- `references/auth/better-auth-config.md` — Auth capabilities for admin
