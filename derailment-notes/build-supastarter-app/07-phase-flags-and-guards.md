# Phase Analysis: Flags & Guards (F-07)

## Friction Point Covered

- **F-07** (P2, M4): Step 5 "check flags" vague for new features

---

## Context

Step 5 of the SKILL.md workflow says to "check flags" before finalizing a change. This is a sensible guard rail — feature flags, billing gates, and role checks prevent incomplete features from reaching users. However, the instruction is too vague to be actionable for new features.

---

## The Vagueness Problem

### What Step 5 says

> "Check flags and guards."

### What the agent needs to know

1. **Which flags?** Feature flags, billing flags, beta flags, environment flags?
2. **Where are flags defined?** Config file, database, environment variable, feature flag service?
3. **Does this task need a flag?** New CRUD feature — is it behind a flag by default?
4. **What about role checks?** Should only admins create projects? Should members have read-only access?
5. **What about billing gates?** Is "Projects" a free-tier feature or premium?

### What the agent did

The agent:
1. Read Step 5 — "check flags"
2. Searched for "feature flag" in the codebase — found a feature flags system
3. Could not determine if the new Projects feature needed a flag
4. Made a judgment call: skipped the flag (reasonable for a CRUD tutorial task)
5. No role-based access control was added (may be a security gap for production use)

### Time cost: ~2 minutes (minimal because agent chose to skip)

### Risk: Medium — skipping flags is fine for development, problematic for production

---

## What's Missing: A Decision Matrix

Step 5 needs a sub-checklist that maps change types to relevant guards:

### Proposed decision matrix

| Change type | Feature flag? | Billing gate? | Role check? | Notes |
|---|---|---|---|---|
| **New module/feature** | Recommended | Check pricing tier | Check who can access | Flag allows gradual rollout |
| **New API endpoint** | Optional | If behind paid tier | Based on data sensitivity | Public endpoints need rate limiting |
| **New page** | If feature is flagged | Match API tier | Inherit from feature | Page should check flag too |
| **Schema change** | Not applicable | Not applicable | Not applicable | Schema is always deployed |
| **Bug fix** | No | No | No | Ship immediately |
| **Config change** | No | No | No | — |
| **UI-only change** | Only if behind flag | No | No | — |

### Feature flag checklist for new features

When adding a new module (like "Projects"):

- [ ] **Define the flag:** Add `FEATURE_PROJECTS` to the feature flags config
- [ ] **Gate the API:** Check the flag in the module router before exposing procedures
- [ ] **Gate the page:** Check the flag in the page server component before rendering
- [ ] **Gate the nav:** Only show the nav entry if the flag is enabled
- [ ] **Default value:** Set to `false` in production, `true` in development

### Role check checklist for org-scoped features

- [ ] **List/Read:** All org members (or restrict to specific roles?)
- [ ] **Create:** All org members or admin-only?
- [ ] **Update:** Creator-only, admin-only, or all members?
- [ ] **Delete:** Admin-only (recommended) or creator-only?

---

## Where Flags Live (Reference)

The skill should document where flag configuration lives:

```
Feature flags:     apps/web/config/features.ts (or env-based)
Billing gates:     packages/billing/src/plans.ts
Role definitions:  packages/auth/src/roles.ts
```

*Actual paths vary by project — the skill should provide the default locations with a "check your project" note.*

---

## Proposed Fix for Step 5

### Before

> Step 5 — Check flags and guards.

### After

> Step 5 — Check flags and guards.
>
> **New features:** Consider whether the feature needs:
> - A feature flag for gradual rollout (recommended for new modules)
> - A billing gate if the feature is premium-tier
> - Role-based access control for create/update/delete operations
>
> **Bug fixes / config changes:** Usually no flags needed. Ship directly.
>
> **See the decision matrix in the flags reference** for detailed guidance per change type.
>
> If you add a feature flag:
> 1. Define it in the feature flags config
> 2. Check it in the API router (gate the entire module)
> 3. Check it in the page (prevent rendering)
> 4. Check it in navigation (hide the nav entry)

---

## Impact Assessment

| Metric | Value |
|---|---|
| Severity | P2 — minor friction |
| Time cost | ~2 min (agent skipped the check) |
| Risk if unfixed | Medium — agents may ship ungated features |
| Fix complexity | Low — add decision matrix + examples |

---

## Root Cause

**M4 — Template incomplete.** Step 5 exists as a checkpoint but lacks the specifics to be actionable. The instruction is correct in intent ("check flags") but insufficient in detail ("which flags, where, when").

---

## Cross-References

- F-06 (no org auth) — role checks are a subset of the guards that Step 5 should cover
- Clean pass #6 (decision rules) — "Do this, not that" pairs work well elsewhere; the flags section needs similar decision rules
- Clean pass #7 (recovery paths) — recovery docs cover "I forgot to add a flag" but Step 5 should prevent the mistake
