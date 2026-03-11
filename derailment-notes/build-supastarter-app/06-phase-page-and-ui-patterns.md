# Phase Analysis: Page & UI Patterns (F-08, F-09)

## Friction Points Covered

- **F-08** (P1, M4): No CRUD page pattern
- **F-09** (P2, M2): Nav location unstated

---

## Overview

The page layer is the thinnest part of the skill's reference architecture. While schema conventions and API patterns are well-documented, the page creation guidance consists of:
- `add-saas-page.md` — a brief action checklist
- `organization-scoped-page.md` — approximately 3 sentences
- `routing-saas.md` — route tree reference (accurate but not actionable)

For a CRUD feature page, the agent needs significantly more guidance than these files provide.

---

## F-08: No CRUD Page Pattern

### What `organization-scoped-page.md` provides

Approximately 3 sentences:
1. Org-scoped pages live under `[organizationSlug]`
2. They receive the org slug as a route param
3. Use `protectedPage` wrapper

### What a CRUD page actually requires

A projects CRUD page needs at minimum:

```
projects/
  page.tsx              <- Server component: list view with data fetching
  _components/
    projects-list.tsx   <- Client component: interactive list with delete
    create-project-form.tsx <- Client component: create form
    edit-project-form.tsx   <- Client component: edit form
  [projectId]/
    page.tsx            <- Server component: detail/edit view
```

### Gaps in the current guidance

| Need | Covered? | Notes |
|---|---|---|
| File location | No (wrong path — see F-03) | Missing `(organizations)` route group |
| Server vs client component split | No | No guidance on RSC boundaries |
| Data fetching in server components | No | No pattern for calling API from server component |
| Client-side mutations (create/update/delete) | No | No pattern for oRPC mutations in client components |
| Loading states | No | No skeleton/suspense pattern |
| Error handling in pages | No | No error boundary pattern |
| Form patterns | No | No form library recommendation or pattern |
| List + detail navigation | No | No pattern for list-to-detail flow |

### What the agent did without guidance

The agent:
1. Created a single `page.tsx` with all CRUD logic inlined (violates RSC best practices)
2. Used `"use client"` on the entire page (unnecessary — only interactive parts need it)
3. Guessed at the data fetching pattern (used `fetch` instead of oRPC client)
4. No loading states or error boundaries
5. Working but poorly structured code

### Proposed CRUD page template

Add to `organization-scoped-page.md`:

**Server component** (`page.tsx`) — handles data fetching, renders server-side, passes data to client components.

**Client component** (`_components/projects-list.tsx`) — handles interactivity: click handlers, form state, mutations.

### Key principles the template should convey

1. **Server components for data fetching** — `page.tsx` is always a server component
2. **Client components for interactivity** — forms, buttons, state management
3. **Co-located components** — `_components/` directory next to the page
4. **Type safety** — import types from the API package
5. **Revalidation** — after mutations, revalidate the page data

---

## F-09: Nav Location Unstated

### What `add-saas-page.md` says

> "Add navigation to the new page"

### What it doesn't say

- **Where** the navigation configuration lives
- **What format** the navigation entry takes
- **Which navigation** — sidebar? top nav? both?
- **Whether it's a config file or a component**

### What the agent did

The agent:
1. Searched for "navigation" in the codebase — found 4 possible locations
2. Searched for "sidebar" — found the sidebar component
3. Found a navigation config array in a constants file
4. Added an entry by copying an existing entry's pattern
5. Spent ~4 minutes on what should have been a 30-second task

### Proposed fix

Add to `add-saas-page.md`:

> **Navigation:**
>
> Add a navigation entry to the sidebar config:
>
> File: `apps/web/config/navigation.ts` (or similar — check your project)
>
> The sidebar renders these entries automatically. No component changes needed unless you need custom rendering.

### Why "check your project" caveat

Navigation config location varies between Supastarter versions and customizations. The skill should provide the default location but acknowledge it may have been moved.

---

## Combined Impact

| Friction point | Time cost | Quality impact |
|---|---|---|
| F-08 (no CRUD pattern) | ~8 min building from scratch | Poor RSC boundaries, no loading/error states |
| F-09 (nav unstated) | ~4 min searching | None (eventually found correct location) |
| **Total** | **~12 min** | **Suboptimal page architecture** |

The quality impact of F-08 is more concerning than the time cost. Without a CRUD template, agents produce working but poorly-structured pages that will need refactoring.

---

## Root Cause Analysis

**F-08 — M4 (Template incomplete):** The page reference files were written as quick checklists, not comprehensive templates. This works for simple pages (a settings page, a dashboard widget) but fails for interactive CRUD pages.

**F-09 — M2 (Ambiguous instruction):** "Add navigation" is an instruction, not a guide. It tells the agent what to do but not how or where.

---

## Cross-References

- F-03 (route path error) — page files are both at the wrong path AND too thin
- F-06 (no org auth) — CRUD pages need authorization too, compounding the auth gap
- Clean pass #1 (root router wiring) — shows the skill CAN write detailed step-by-step recipes; page docs need the same treatment
