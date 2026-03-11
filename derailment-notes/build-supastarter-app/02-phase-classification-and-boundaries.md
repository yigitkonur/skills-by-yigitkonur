# Phase Analysis: Classification & Boundaries (F-01, F-02)

## Friction Points Covered

- **F-01** (P1, M1): Classification assumes single category
- **F-02** (P1, M1): Owning boundary is singular

---

## Context

The test task — "Add an org-scoped Projects CRUD feature with database model, oRPC API endpoints, and a protected SaaS dashboard page" — is inherently composite. It spans three distinct domains:

1. **Data layer** — Prisma/Drizzle schema + query helpers (`packages/database`)
2. **API layer** — oRPC procedures + router wiring (`packages/api`)
3. **Page layer** — Protected SaaS dashboard route (`apps/web`)

Both F-01 and F-02 stem from the same root assumption: that tasks are single-concern.

---

## F-01: Classification Assumes Single Category

### What Step 1 says

> "Classify the change" — singular. The 7 categories are presented as mutually exclusive options. The workflow implies you pick one category, then follow that category's reference bundle.

### How the task was classified

Attempting to classify "Add org-scoped Projects CRUD" into a single category fails:

| Category | Applies? | Why |
|---|---|---|
| Data model change | Yes | New `projects` table in schema |
| API endpoint | Yes | New CRUD procedures + router |
| SaaS page | Yes | New dashboard page under org slug |
| Auth/billing change | Partial | Org-membership check needed |
| Config change | No | — |
| Package update | No | — |
| Styling/theme | No | — |

**Result:** 3 primary categories, 1 partial. The skill provides no guidance for this case.

### What the agent did without guidance

Without composite classification guidance, the agent:
1. Picked "Data model change" as primary (reasonable guess)
2. Read the database bundle first (correct by accident)
3. Had to re-read SKILL.md to find the API and page bundles
4. Lost ~3 minutes navigating between bundles with no clear order

### Proposed fix for Step 1

**Before:**
> Step 1 — Classify the change into one of the 7 categories.

**After:**
> Step 1 — Classify the change. List ALL categories that apply. Most tasks fall into one category. Composite tasks (e.g., new feature with data + API + page) span multiple categories.
>
> **For composite tasks:** Read bundles in dependency order:
> 1. Schema / data model
> 2. Query helpers
> 3. API procedures + router
> 4. Page / UI
> 5. Auth / billing (if applicable)
>
> Complete each layer before moving to the next.

---

## F-02: Owning Boundary Is Singular

### What Step 2 says

> "Locate the owning boundary" — singular. Implies one package directory is the home for all changes.

### How boundaries actually work for this task

| Boundary | Package | Changes needed |
|---|---|---|
| Data layer | `packages/database` | Schema file, query helpers, migrations |
| API layer | `packages/api` | Procedures, module router, root router wiring |
| Page layer | `apps/web` | Page component, layout, navigation entry |

No single boundary "owns" this task. The data layer is the **root dependency** (API and page both depend on it), but the API layer is the **integration point** (page calls API, API calls data).

### What the agent did without guidance

The agent started in `packages/database` (correct instinct) but then faced a decision: move to `packages/api` next, or jump to `apps/web`? Without boundary ordering guidance, the agent:
1. Finished schema changes in `packages/database`
2. Jumped to `apps/web` to create the page (wrong order — page needs API types)
3. Realized API types don't exist yet
4. Backtracked to `packages/api` to create procedures
5. Returned to `apps/web` to wire up the page

This backtracking cost ~5 minutes and introduced a type error that would have been avoided with correct ordering.

### Proposed fix for Step 2

**Before:**
> Step 2 — Locate the owning boundary (the package or app directory that owns this change).

**After:**
> Step 2 — Locate the owning boundary.
>
> **Single-concern tasks:** One package owns the change. Open that directory.
>
> **Composite tasks (multiple categories from Step 1):** Identify all boundaries, then order by dependency:
> 1. `packages/database` — schema + queries (no upstream deps)
> 2. `packages/api` — procedures + routers (depends on database types)
> 3. `apps/web` — pages + components (depends on API types)
>
> Work through boundaries in this order. Complete each boundary's changes before moving to the next.

---

## Root Cause Analysis

Both friction points share the same root cause: **M1 — Missing instruction.** The skill was authored with single-concern tasks in mind. The workflow steps, reference table, and bundle structure all optimize for "I need to change one thing." Real-world feature work almost always spans multiple concerns.

### Why this matters

Composite tasks are the common case for the target audience (developers extending a Supastarter app with new features). A new feature almost always needs: schema then API then page. The skill should treat this as the default path, not an edge case.

---

## Impact Assessment

| Metric | Value |
|---|---|
| Time lost to backtracking | ~5 minutes |
| Files created in wrong order | 2 (page before API) |
| Type errors from wrong order | 1 |
| Severity if unfixed | Moderate — agent recovers but wastes time |

---

## Cross-References

- F-04 (reference table navigation) is a downstream consequence of F-01/F-02
- Clean pass #8 (Step 4 ordering) shows the skill CAN get ordering right — it just doesn't apply the same principle to Steps 1-2
