# Friction Registry — build-supastarter-app

## Test Metadata

| Field | Value |
|---|---|
| **Skill** | `build-supastarter-app` |
| **Task** | Add an org-scoped Projects CRUD feature with database model, oRPC API endpoints, and a protected SaaS dashboard page |
| **Date** | 2026-03-11 |
| **Method** | Derailment testing — follow SKILL.md literally, record every friction point and clean pass |
| **Total steps attempted** | ~21 (6 workflow steps + ~15 sub-steps) |
| **Clean passes** | 8 (~38%) |
| **Friction points** | 11 |
| **Derailment density** | 11/21 = 0.52 |

---

## Friction Points

### F-01 — Classification assumes single category

| Field | Value |
|---|---|
| **ID** | F-01 |
| **Severity** | P1 |
| **Root cause** | M1 — Missing instruction |
| **Phase** | Step 1 — Classify the change |

**What the instructions said:** "Classify the change" (singular) — the workflow assumes every task maps to exactly one of the 7 categories.

**What actually happened:** The test task spans 3 categories simultaneously: data layer (schema + queries), API layer (oRPC procedures + router), and SaaS page (protected dashboard route). No guidance on composite classification.

**What was missing:** A composite-task recognition pattern: "If your task spans multiple categories, list all that apply and follow bundles in dependency order: data → API → page."

**Proposed fix:** Rewrite Step 1 to accept multiple classifications and provide a dependency-ordered reading list.

---

### F-02 — Owning boundary is singular

| Field | Value |
|---|---|
| **ID** | F-02 |
| **Severity** | P1 |
| **Root cause** | M1 — Missing instruction |
| **Phase** | Step 2 — Locate the owning boundary |

**What the instructions said:** "Locate the owning boundary" (singular) — implies one package owns the change.

**What actually happened:** Task touches `packages/database`, `packages/api`, and `apps/web` simultaneously. No single boundary owns a composite task.

**What was missing:** Guidance for multi-boundary tasks: identify primary boundary (where data model lives) and downstream boundaries (API, UI) that depend on it.

**Proposed fix:** Add a "Composite tasks" callout to Step 2 explaining multi-boundary ownership and execution order.

---

### F-03 — Route path in add-saas-page.md is wrong

| Field | Value |
|---|---|
| **ID** | F-03 |
| **Severity** | P0 |
| **Root cause** | S2 — Stale/incorrect content |
| **Phase** | Step 3 — Page creation |

**What the instructions said:** `apps/web/app/(saas)/app/[organizationSlug]/<page>/page.tsx`

**What actually happened:** Actual codebase uses `(organizations)` route group: `apps/web/app/(saas)/app/(organizations)/[organizationSlug]/<page>/page.tsx`. Following the skill literally creates files in the wrong location.

**What was missing:** The `routing-saas.md` reference file correctly mentions `(organizations)` but `add-saas-page.md` and `organization-scoped-page.md` both omit it from their path templates.

**Proposed fix:** Update all path templates in `add-saas-page.md` and `organization-scoped-page.md` to include `(organizations)` route group. Add a cross-reference to `routing-saas.md`.

---

### F-04 — Reference table has no multi-bundle guidance

| Field | Value |
|---|---|
| **ID** | F-04 |
| **Severity** | P1 |
| **Root cause** | S3 — Structural gap |
| **Phase** | Step 2 — Reference navigation |

**What the instructions said:** Reference table lists bundles by category but assumes you read one bundle per task.

**What actually happened:** Task requires 3 bundles (database + API + SaaS page). No reading order specified, no guidance on which to read first, which sections overlap.

**What was missing:** A "composite task" note in the reference table specifying: "For tasks spanning multiple categories, read bundles in this order: schema → queries → procedures → router → page."

**Proposed fix:** Add a row or callout to the reference table for composite tasks with recommended reading order.

---

### F-05 — Query helper file template incomplete

| Field | Value |
|---|---|
| **ID** | F-05 |
| **Severity** | P2 |
| **Root cause** | M4 — Template incomplete |
| **Phase** | Step 3 — Data layer implementation |

**What the instructions said:** `query-patterns.md` shows function body for query helpers.

**What actually happened:** When creating a new query helper file from scratch, the template lacks the necessary import boilerplate: `import { db } from "../client"` and other standard imports.

**What was missing:** A complete file-level template for new query helper files, not just function bodies.

**Proposed fix:** Add a "New file template" section to `query-patterns.md` showing full file boilerplate including imports.

---

### F-06 — No org-membership authorization pattern

| Field | Value |
|---|---|
| **ID** | F-06 |
| **Severity** | P1 |
| **Root cause** | M5 — Security-relevant gap |
| **Phase** | Step 3 — API layer implementation |

**What the instructions said:** `protectedProcedure` is described as checking session authentication. The skill acknowledges org-scoped access as a concept.

**What actually happened:** For org-scoped CRUD, session auth alone is insufficient. Need to verify the user is a member of the organization. No pattern or middleware example provided.

**What was missing:** An org-membership verification pattern — either as a `organizationProcedure` middleware or an inline check pattern within procedures.

**Proposed fix:** Add an org-scoped procedure example to the API reference showing membership verification before data access.

---

### F-07 — Step 5 "check flags" vague for new features

| Field | Value |
|---|---|
| **ID** | F-07 |
| **Severity** | P2 |
| **Root cause** | M4 — Template incomplete |
| **Phase** | Step 5 — Flags and guards |

**What the instructions said:** Step 5 says to "check flags" but provides no specifics about which flags apply to which types of changes.

**What actually happened:** For a new CRUD feature, unclear whether feature flags, billing gates, or role checks are needed. No decision matrix.

**What was missing:** A sub-checklist mapping change types to relevant flag categories (feature flags for new modules, billing gates for premium features, role checks for admin-only actions).

**Proposed fix:** Add a decision matrix to Step 5: change type → relevant flags/guards.

---

### F-08 — No CRUD page pattern

| Field | Value |
|---|---|
| **ID** | F-08 |
| **Severity** | P1 |
| **Root cause** | M4 — Template incomplete |
| **Phase** | Step 3 — Page implementation |

**What the instructions said:** `organization-scoped-page.md` exists but is only ~3 sentences. No server/client component split guidance.

**What actually happened:** Building a CRUD page requires list view, create form, edit form, delete confirmation — none have templates. No guidance on RSC vs client component boundaries for interactive pages.

**What was missing:** A CRUD page pattern showing: server component for data fetching, client component for forms/interactions, recommended component split.

**Proposed fix:** Expand `organization-scoped-page.md` with a CRUD page template showing server/client component architecture.

---

### F-09 — Nav location unstated

| Field | Value |
|---|---|
| **ID** | F-09 |
| **Severity** | P2 |
| **Root cause** | M2 — Ambiguous instruction |
| **Phase** | Step 3 — Page integration |

**What the instructions said:** `add-saas-page.md` says "Add navigation" to the new page.

**What actually happened:** No indication of where the navigation configuration lives. Is it a sidebar config file? A layout component? A constants file?

**What was missing:** The file path and pattern for adding navigation entries (e.g., "Add entry to `apps/web/config/navigation.ts`").

**Proposed fix:** Add the nav config file path and an example entry to `add-saas-page.md`.

---

### F-10 — Workflow omits `pnpm generate`

| Field | Value |
|---|---|
| **ID** | F-10 |
| **Severity** | P1 |
| **Root cause** | S1 — Missing workflow step |
| **Phase** | Step 3 — Post-schema-change |

**What the instructions said:** Workflow steps cover schema changes, query writing, and procedure creation — but never mention running code generation.

**What actually happened:** After modifying the Prisma/Drizzle schema, the TypeScript types are not updated until `pnpm generate` (or equivalent) is run. Code won't compile without it.

**What was missing:** An explicit step after schema changes: "Run `pnpm generate` to regenerate database types before writing queries or procedures."

**Proposed fix:** Insert a mandatory sub-step after any schema modification: "Run generation command to update types."

---

### F-11 — Query helpers vs direct db calls contradiction

| Field | Value |
|---|---|
| **ID** | F-11 |
| **Severity** | P2 |
| **Root cause** | S3 — Structural gap / contradiction |
| **Phase** | Step 3 — Data access pattern |

**What the instructions said:** `query-patterns.md` advocates using query helper functions for database access.

**What actually happened:** Procedure examples in the API bundle use `db` directly in procedure handlers, contradicting the query helpers pattern.

**What was missing:** A clear decision rule: "Use query helpers for reusable queries; inline `db` calls are acceptable for simple single-use queries in procedures."

**Proposed fix:** Add a decision rule to `query-patterns.md` clarifying when each approach is appropriate.

---

## Clean Passes

| # | Area | Why it worked |
|---|---|---|
| 1 | Root router wiring | `root-router.md` gave a perfect 5-step recipe — no ambiguity |
| 2 | Procedure tier selection | 3 tiers clearly explained with when-to-use context |
| 3 | Module router pattern | Existing `organizations/router.ts` was directly copyable |
| 4 | Imports cheatsheet | Comprehensive, accurate, saved significant lookup time |
| 5 | Schema conventions | Well-documented in `schema-overview.md` |
| 6 | Decision rules | "Do this, not that" pairs were immediately actionable |
| 7 | Recovery paths | Well-scoped drift recovery for common mistakes |
| 8 | Step 4 ordering | Correct dependency order prevented backtracking |

---

## Summary Metrics

| Metric | Value |
|---|---|
| Total friction points | 11 |
| P0 (blocks progress) | 1 |
| P1 (significant friction) | 6 |
| P2 (minor friction) | 4 |
| M1 — Missing instruction | 2 |
| M2 — Ambiguous instruction | 1 |
| M4 — Template incomplete | 3 |
| M5 — Security-relevant gap | 1 |
| S1 — Missing workflow step | 1 |
| S2 — Stale/incorrect content | 1 |
| S3 — Structural gap | 2 |
| Clean passes | 8 |
| Derailment density | 0.52 |
