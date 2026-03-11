# Phase Analysis: Reference Navigation (F-04)

## Friction Point Covered

- **F-04** (P1, S3): Reference table has no multi-bundle guidance

---

## Context

The SKILL.md reference table maps categories to reference bundles. Each category points to a set of `.md` files containing patterns, templates, and conventions. For a single-category task, the table works well — you look up your category, read the listed files, and proceed.

The test task required reading 3 bundles simultaneously. The reference table provided no guidance on reading order, overlap, or cross-bundle dependencies.

---

## The Reference Table Problem

### Current structure (simplified)

| Category | Bundle files |
|---|---|
| Data model | `schema-overview.md`, `query-patterns.md`, `migration-guide.md` |
| API endpoint | `procedure-tiers.md`, `root-router.md`, `module-router.md` |
| SaaS page | `add-saas-page.md`, `organization-scoped-page.md`, `routing-saas.md` |

### What happens with a composite task

The agent must read files from all three bundles. Questions that arise:

1. **Which bundle first?** Data then API then Page (dependency order), but this isn't stated.
2. **Which files can be skipped?** `migration-guide.md` may not be needed if using auto-migration. No skip criteria.
3. **Do files overlap?** `query-patterns.md` and procedure examples both show `db` usage — which is authoritative? (This becomes F-11.)
4. **What's the total reading load?** 9+ files across 3 bundles. Agent read all 9 before writing any code — excessive.

### Actual reading order used by the agent

1. `schema-overview.md` — needed, read first (correct)
2. `query-patterns.md` — needed, read second (correct)
3. `procedure-tiers.md` — needed (correct)
4. `add-saas-page.md` — read too early, before API was built
5. `root-router.md` — needed (correct)
6. `module-router.md` — needed (correct)
7. `organization-scoped-page.md` — read too early
8. `routing-saas.md` — needed, but read last (should have been read before page files)
9. `migration-guide.md` — read but not needed for this task

**Result:** 9 files read, 1 unnecessary, 2 read out of order.

---

## The Missing "Composite Task" Reading Order

### Proposed addition to reference table

> **Composite tasks** (spanning data + API + page):
>
> Read and execute in this order:
>
> **Phase A — Data layer** (complete before moving on)
> 1. `schema-overview.md` — define your table
> 2. `query-patterns.md` — write query helpers
> 3. Run `pnpm generate` to update types
>
> **Phase B — API layer** (complete before moving on)
> 4. `procedure-tiers.md` — choose procedure tier
> 5. `module-router.md` — create module router
> 6. `root-router.md` — wire into root router
>
> **Phase C — Page layer**
> 7. `routing-saas.md` — understand route structure
> 8. `add-saas-page.md` — create page file
> 9. `organization-scoped-page.md` — org-scoped patterns
>
> **Skip list for composite tasks:**
> - `migration-guide.md` — only if manual migration is needed
> - Files for categories not in your task

---

## Impact on Agent Behavior

### Without reading order guidance

```
Read all 9 files -> build mental model -> start coding -> realize order matters ->
backtrack to re-read files in correct order -> resume coding
```

Total time: ~12 minutes reading + 5 minutes backtracking = ~17 minutes

### With reading order guidance

```
Read Phase A files -> code data layer -> read Phase B files -> code API layer ->
read Phase C files -> code page layer
```

Estimated time: ~10 minutes reading (interleaved with coding) = ~10 minutes

### Time saved

~7 minutes per composite task. For a typical feature buildout involving 3-5 composite tasks, this compounds to 20-35 minutes saved.

---

## Bundle Dependency Map

```
packages/database
  schema-overview.md
  query-patterns.md
        |
        | depends on
        v
packages/api
  procedure-tiers.md
  module-router.md
  root-router.md
        |
        | depends on
        v
apps/web
  routing-saas.md
  add-saas-page.md
  organization-scoped-page.md
```

---

## Root Cause

**S3 — Structural gap.** The reference table structure assumes one-to-one mapping between task and bundle. The structure itself doesn't support composite tasks. Adding a "composite task" callout is a minimal fix; restructuring the table to show dependencies would be ideal.

---

## Cross-References

- F-01 (single classification) — upstream cause; if Step 1 doesn't support composite tasks, the reference table doesn't need to either
- F-02 (single boundary) — same root assumption
- Clean pass #8 (Step 4 ordering) — proves the skill understands dependency ordering; it just doesn't apply it to reading
