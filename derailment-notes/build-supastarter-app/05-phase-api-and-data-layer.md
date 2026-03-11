# Phase: API and Data Layer (F-05, F-06, F-10, F-11)

## Context

Four friction points surfaced while implementing the database model and oRPC API layer. These cluster around incomplete templates, missing security patterns, and workflow gaps.

---

## F-05 — Query helper template is incomplete (P2, M4)

### What happened

`references/database/query-patterns.md` shows query helper patterns like:

```typescript
export async function getProjectsByOrganization(organizationId: string) {
  return db.project.findMany({ where: { organizationId } });
}
```

But when creating a new file (`packages/database/src/queries/projects.ts`), the template lacks:
- The `import { db } from "../client"` line
- The file-level export structure
- TypeScript return type annotation pattern

An executor new to the codebase would write the function body correctly but have a non-compiling file.

### Impact

P2 because the fix is obvious once you see the compilation error. But it breaks the "follow literally" contract.

### Fix applied

Added "New file template" section to `query-patterns.md`:

```typescript
import { db } from "../client";
// ... function exports
```

---

## F-06 — No org-membership authorization pattern (P1, M5)

### What happened

`references/api/procedure-tiers.md` documents three tiers:
1. `publicProcedure` — no auth
2. `protectedProcedure` — session required
3. `organizationProcedure` — org context required

For Projects CRUD, I used `organizationProcedure`. But this only checks that the user has an active organization in context — it does NOT verify the user is a **member** of that organization. Any authenticated user could potentially access any org's projects by passing a different `organizationSlug`.

This is a security-relevant gap. The skill doesn't document the membership guard pattern.

### Root cause: M5 (Assumed knowledge)

The skill assumes the executor knows to add membership checks. In a real Supastarter app, this is handled by middleware or the `organizationProcedure` itself — but the reference file doesn't explain this.

### Fix applied

Added "Org-membership guard" section to `procedure-tiers.md`:

```typescript
// When you need to verify the user belongs to the target org
const membership = await db.membership.findFirst({
  where: {
    userId: ctx.user.id,
    organizationId: ctx.organization.id,
  },
});
if (!membership) throw new TRPCError({ code: "FORBIDDEN" });
```

### Security note

This was the only security-relevant friction point found. It's P1 because the executor CAN proceed (the code works without the guard), but the resulting feature has an authorization bypass.

---

## F-10 — Workflow omits generation commands (P1, S1)

### What happened

After adding the `Project` model to `schema.prisma`, step 4 says to "Change the owner first" but doesn't mention running:

```bash
pnpm generate    # Regenerate Prisma client types
pnpm db:push     # Push schema to database
```

Without these commands:
- TypeScript compilation fails (Prisma client doesn't know about `Project`)
- API procedures can't import the type
- The executor sees type errors and has to debug why

### Root cause: S1 (Missing prerequisite)

This is a prerequisite step that experienced Supastarter developers do automatically but the skill never mentions.

### Fix applied

Added to step 4's data change sequence:

> After modifying `schema.prisma`, run `pnpm generate && pnpm db:push` to regenerate the Prisma client and sync the database.

---

## F-11 — Query helpers vs direct db calls contradiction (P2, S3)

### What happened

`query-patterns.md` encourages using query helper functions. But procedure examples in `procedure-tiers.md` show direct `db` calls inside procedures:

```typescript
// In query-patterns.md:
export async function getProjects(orgId: string) { ... }

// In procedure-tiers.md:
.handler(async ({ ctx }) => {
  const items = await db.project.findMany({ ... });
})
```

No guidance on when to use each approach.

### Fix applied

Added "When to use query helpers vs direct db calls" to `query-patterns.md`:
- **Use helpers** when the same query is reused across multiple procedures or in server components
- **Use direct calls** for one-off queries scoped to a single procedure

---

## Compound effect

F-05 + F-10 create a compound experience: the executor adds a Prisma model (no generation step), then tries to write query helpers (incomplete template), resulting in two errors that feel like one confusing failure. Fixing both eliminates the compounding.
