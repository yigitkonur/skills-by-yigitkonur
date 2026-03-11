# Admin Users

> Documents the admin-facing user-management table. Consult this when changing search, pagination, or user-level admin actions.

> ⚠️ **Only `adminProcedure` endpoints should back admin pages.** Do not use `protectedProcedure` for admin routes.

## Key file

- `apps/web/modules/saas/admin/component/users/UserList.tsx`

## What this screen supports

- debounced search
- server-backed pagination
- impersonation and admin-role actions
- resend-verification and delete-user actions

## Practical notes

The table is built with TanStack Table and nuqs-style URL state patterns, so admin state is shareable via query params instead of being trapped in ephemeral client state.

---

**Related references:**
- `references/admin/organizations-admin.md` — Parallel admin list for organizations
- `references/routing/routing-saas.md` — Where `/app/admin` lives
- `references/auth/better-auth-config.md` — Admin-related auth capabilities
- `references/auth/server-session-helpers.md` — Server-side session helpers
