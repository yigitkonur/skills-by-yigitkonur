# Phase Analysis: Route Path Error (F-03) — P0 Critical

## Friction Point Covered

- **F-03** (P0, S2): Route path in `add-saas-page.md` is wrong

---

## Severity Justification

This is the only **P0** friction point. Following the skill literally creates files in the wrong filesystem location. The page will not render, the route will not match, and the error is silent (no build error — just a 404 at runtime). This is the most critical fix in the entire registry.

---

## The Error

### What `add-saas-page.md` says

```
Path template: apps/web/app/(saas)/app/[organizationSlug]/<page>/page.tsx
```

### What `organization-scoped-page.md` says

Similar path without `(organizations)`:
```
apps/web/app/(saas)/app/[organizationSlug]/<page>/page.tsx
```

### What `routing-saas.md` says

Correctly documents the `(organizations)` route group:
```
apps/web/app/(saas)/app/(organizations)/[organizationSlug]/...
```

### What the actual codebase uses

```
apps/web/app/(saas)/app/(organizations)/[organizationSlug]/<page>/page.tsx
```

---

## Side-by-Side Comparison

```
WRONG (from add-saas-page.md):
apps/web/app/(saas)/app/[organizationSlug]/projects/page.tsx

CORRECT (actual codebase):
apps/web/app/(saas)/app/(organizations)/[organizationSlug]/projects/page.tsx
                        ^^^^^^^^^^^^^^^^
                        Missing route group
```

The `(organizations)` route group is a Next.js route group used to organize organization-scoped pages. It doesn't affect the URL path (parenthesized directories are invisible to the router), but it DOES affect the filesystem structure and layout inheritance.

---

## Why This Is a P0

### Silent failure mode

1. Agent creates `apps/web/app/(saas)/app/[organizationSlug]/projects/page.tsx` — **wrong location**
2. Next.js does not error — both paths are valid filesystem locations
3. Build succeeds — the file is valid React
4. At runtime, navigating to `/app/org-slug/projects` returns 404
5. The correct layout (which wraps `(organizations)` children) does not apply
6. No error message points to the cause

### Debugging cost

Without knowing about the `(organizations)` route group, an agent would:
1. Check the page component for errors (none found)
2. Check the router configuration (no custom router — it's file-based)
3. Check middleware (no issue)
4. Eventually `ls` the directory tree and discover the `(organizations)` group
5. Move the file to the correct location

Estimated debugging time: 10-20 minutes. With the correct path template: 0 minutes.

---

## Root Cause Analysis

**S2 — Stale/incorrect content.** The path template in `add-saas-page.md` was likely written before the `(organizations)` route group was introduced, or was written from memory rather than verified against the codebase.

### The inconsistency

The skill's own reference files contradict each other:

| File | Path used | Correct? |
|---|---|---|
| `routing-saas.md` | `(organizations)/[organizationSlug]/...` | Yes |
| `add-saas-page.md` | `[organizationSlug]/...` (no route group) | No |
| `organization-scoped-page.md` | `[organizationSlug]/...` (no route group) | No |

Two out of three files have the wrong path. The one correct file (`routing-saas.md`) is a reference document, not an action template — so agents following the step-by-step workflow will use the wrong path.

---

## Proposed Fix

### Fix 1: Update `add-saas-page.md`

**Before:**
```
Path: apps/web/app/(saas)/app/[organizationSlug]/<page>/page.tsx
```

**After:**
```
Path: apps/web/app/(saas)/app/(organizations)/[organizationSlug]/<page>/page.tsx

Note: The (organizations) route group is required for org-scoped pages.
It provides the shared layout and context for all organization pages.
See routing-saas.md for the full route tree.
```

### Fix 2: Update `organization-scoped-page.md`

Same path correction. Additionally, expand the file beyond its current ~3 sentences to include:
- Correct path template with `(organizations)`
- Layout inheritance explanation
- Link to `routing-saas.md`

### Fix 3: Add cross-reference validation

Add a note to the skill's maintenance section:
> When updating route structures, verify path templates in ALL reference files:
> `routing-saas.md`, `add-saas-page.md`, `organization-scoped-page.md`

---

## Verification

After applying the fix, test by:
1. Following `add-saas-page.md` literally to create a new page
2. Verify the file lands in `(organizations)/[organizationSlug]/`
3. Verify the page renders at the expected URL
4. Verify the organization layout applies

---

## Impact Assessment

| Metric | Value |
|---|---|
| Severity | P0 — blocks correct page rendering |
| Time to debug without fix | 10-20 minutes |
| Time to debug with fix | 0 minutes |
| Files affected | `add-saas-page.md`, `organization-scoped-page.md` |
| Risk of regression | Low — path is stable once route groups are established |

---

## Cross-References

- F-08 (thin page template) — the page template is both wrong (F-03) and incomplete (F-08)
- F-09 (nav location) — even if the page is in the right place, navigation still needs to be wired
- Clean pass #5 (schema conventions) — shows the skill CAN maintain accurate path/structure docs; the page paths are an outlier
