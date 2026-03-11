# Members and Invitations

> Documents the main organization membership management components. Consult this when changing invite flows, role assignment, or the members/invitations settings UI.

> ⚠️ **No `organizationProcedure`.** There is no org-scoped procedure tier. Use `protectedProcedure` and manually check membership via `auth.api.getFullOrganization()`.

## Key files

- `apps/web/modules/saas/organizations/components/InviteMemberForm.tsx`
- `apps/web/modules/saas/organizations/components/OrganizationMembersBlock.tsx`
- `apps/web/modules/saas/organizations/components/OrganizationRoleSelect.tsx`
- `apps/web/modules/saas/organizations/hooks/member-roles.ts`

## Representative code

```tsx
const formSchema = z.object({
  email: z.email(),
  role: z.enum(["member", "owner", "admin"]),
});

await authClient.organization.inviteMember({
  ...values,
  organizationId,
});
```

## UI structure

- **InviteMemberForm** sends invitations and invalidates the full organization query
- **OrganizationMembersBlock** splits active members and pending invitations into tabs
- **OrganizationRoleSelect** renders translated role values from `useOrganizationMemberRoles()`

This entire cluster is role-sensitive and assumes the active organization context is already available.

## API membership check (for org-scoped procedures)

```typescript
// In a protectedProcedure handler:
const org = await auth.api.getFullOrganization({
  headers: await headers(),
  query: { organizationId: input.organizationId },
});

if (!org) throw new Error("Organization not found");

const membership = org.members.find((m) => m.userId === session.user.id);
if (!membership) throw new Error("Not a member");
```

---

**Related references:**
- `references/organizations/active-organization-context.md` — Source of current org and role data
- `references/auth/better-auth-config.md` — Better Auth organizations plugin background
- `references/mail/email-templates.md` — Invitation email template
