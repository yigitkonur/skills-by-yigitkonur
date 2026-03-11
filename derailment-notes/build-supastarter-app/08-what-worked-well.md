# What Worked Well

## Context

11 friction points get the spotlight, but 8 clean passes deserve equal documentation. Understanding what works prevents regressions and identifies patterns to replicate.

---

## Clean Pass 1: Root Router Wiring

**Reference:** `references/api/root-router.md`

The 5-step recipe for adding a new module router to the root oRPC router was flawless:
1. Create module file → clear path given
2. Define procedures → tier selection obvious
3. Export router → named export pattern shown
4. Import in root → exact import line provided
5. Wire to root → spread pattern demonstrated

**Why it worked:** Complete, ordered, with exact code for each step. No decision points.

## Clean Pass 2: Procedure Tier Selection

**Reference:** `references/api/procedure-tiers.md`

Three tiers (`public`, `protected`, `organization`) with clear selection criteria:
- No auth needed → `publicProcedure`
- User must be logged in → `protectedProcedure`
- Org context required → `organizationProcedure`

**Why it worked:** Exhaustive options with unambiguous selection rules. The context shape for each tier was shown, so I knew what `ctx` contained.

## Clean Pass 3: Module Router Pattern

**Reference:** Existing `packages/api/modules/organizations/router.ts`

The skill correctly pointed to existing modules as templates. The file structure was:

```
packages/api/modules/[feature]/
├── router.ts          # oRPC procedures
├── [feature].schema.ts  # Zod schemas
└── index.ts           # re-exports
```

**Why it worked:** Existing code IS the documentation. The skill said "look at existing modules" and they were clean enough to copy.

## Clean Pass 4: Imports Cheatsheet

**Reference:** `references/architecture/imports-cheatsheet.md`

Every `@repo/*` alias was listed with its target package. No guessing which package exports what.

**Why it worked:** Lookup table format. Scanned in 5 seconds. Found `@repo/database` and `@repo/api` immediately.

## Clean Pass 5: Schema Conventions

**Reference:** `references/database/schema-overview.md`

Prisma model conventions were clearly stated:
- Naming: singular PascalCase
- Required fields: `id`, `createdAt`, `updatedAt`
- Relations: explicit with `@relation`
- Indexes: on foreign keys

**Why it worked:** Convention list format. Each item is verifiable. No ambiguity.

## Clean Pass 6: Decision Rules ("Do This, Not That")

**Reference:** SKILL.md "Do this, not that" section

| Do this | Not that |
|---------|----------|
| Put queries in `packages/database` | Don't call `db` from web app directly |
| Use existing `@repo` packages | Don't create new packages unless needed |

**Why it worked:** Anti-patterns are as valuable as patterns. Seeing "not that" prevents the most common missteps.

## Clean Pass 7: Recovery Paths

**Reference:** SKILL.md drift recovery section

The skill includes a "drift recovery" section for when things go wrong. This prevented panic when F-03 caused a wrong file path — the recovery section suggested checking route groups.

**Why it worked:** Acknowledging that things go wrong builds trust. The recovery steps were specific enough to be useful.

## Clean Pass 8: Step 4 Ordering (Data → API → Page)

**Reference:** SKILL.md step 4

The instruction to "change the owner first" with the implicit data → API → page ordering prevented backtracking. I never created a page that referenced non-existent API endpoints, or API endpoints that referenced non-existent database models.

**Why it worked:** The dependency order is correct. Each layer only depends on layers already completed.

---

## Pattern: What Makes a Clean Pass

Analyzing the 8 clean passes, the common traits are:

1. **Exact file paths** — no searching needed
2. **Complete code snippets** — copy-paste-modify, not "figure out the structure"
3. **Lookup table format** — scannable in seconds
4. **Exhaustive options** — every valid choice is listed
5. **Anti-patterns included** — "not that" prevents common mistakes
6. **Correct dependency ordering** — each step builds on the last

These are the properties to replicate when fixing the 11 friction points.
