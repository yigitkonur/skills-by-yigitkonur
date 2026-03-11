# Density Map and Metrics

## Derailment Density Map

```
Step 1 ██████████░░░░░░░░░░ (2 friction: F-01, F-02)
Step 2 ░░░░░░░░░░░░░░░░░░░░ (0 — clean pass)
Step 3 █████░░░░░░░░░░░░░░░ (1 friction: F-04)
Step 4 ████████████████████ (4 friction: F-03, F-05, F-10, F-11) ← HOTSPOT
Step 5 █████░░░░░░░░░░░░░░░ (1 friction: F-07)
Step 6 ██████████░░░░░░░░░░ (3 friction: F-06, F-08, F-09)
```

### Analysis

**Step 4 is the hotspot** with 4 friction points including the only P0 (F-03). This makes sense: step 4 is "Change the owner first" — the step where actual code is written. It's where reference files are consumed and their quality directly impacts execution.

**Steps 2 and 3** are relatively clean because they're navigational — finding boundaries and reading references. The information exists; it's just organized for single-category tasks.

**Step 6** has 3 friction points but all are P1/P2 — things that slow down rather than block. The "validate" step catches real issues but its patterns are incomplete.

---

## Scoring (per metrics-and-iteration.md)

### Severity-weighted score

```
Score = (P0 × 3) + (P1 × 2) + (P2 × 1)
     = (1 × 3)  + (6 × 2)  + (4 × 1)
     = 3 + 12 + 4
     = 19
```

### Quality grade

| Grade | Score range | Description |
|-------|-----------|-------------|
| A | 0–5 | Production-ready |
| B | 6–12 | Minor polish needed |
| C | 13–20 | **Significant gaps** ← THIS |
| D | 21+ | Major rewrite needed |

**Grade: C** — Significant gaps. The skill's structure is sound but reference files have incomplete templates, missing patterns, and one critical path error.

### After fixes

```
Expected post-fix score:
  P0: 0 (F-03 fixed) → 0 × 3 = 0
  P1: 0 (all 6 fixed) → 0 × 2 = 0
  P2: 0 (all 4 fixed) → 0 × 1 = 0
  Score: 0 → Grade A
```

This assumes all fixes are effective. A re-test with a different task would confirm.

---

## Root Cause Distribution

```
M4 Missing execution method  ███████████████ (3: F-05, F-07, F-08)
M1 Ambiguous threshold        ██████████ (2: F-01, F-02)
S3 Scattered information       ██████████ (2: F-04, F-11)
M5 Assumed knowledge           █████ (1: F-06)
M2 Unstated location           █████ (1: F-09)
S1 Missing prerequisite        █████ (1: F-10)
S2 Contradictory paths         █████ (1: F-03)
```

### Pattern

**M-class (missing content) dominates** with 7 of 11 friction points. This means the skill's structure and navigation are sound — the gaps are in the reference files' content, not in the workflow design.

**S-class (structural) issues** account for 4 friction points. The S2 (contradictory path, F-03) was the most damaging. S3 (scattered, F-04 and F-11) is a design choice that trades modularity for navigability — acceptable with better cross-references.

---

## Cross-Run Comparison Template

For future re-tests on different tasks:

| Metric | Run 1 (Projects CRUD) | Run 2 (___) |
|--------|----------------------|-------------|
| Task | Org-scoped CRUD feature | |
| Total steps | ~21 | |
| Clean passes | 8 (38%) | |
| P0 | 1 | |
| P1 | 6 | |
| P2 | 4 | |
| Total friction | 11 | |
| Derailment density | 0.52 | |
| Severity-weighted score | 19 | |
| Grade | C | |
| Top root cause | M4 (3) | |
| Hotspot step | Step 4 (4 friction) | |

### Recommended Run 2 task

To maximize coverage, test a task that exercises:
- The billing/payments pathway (untested in run 1)
- The marketing site pages (different from SaaS dashboard)
- A config-heavy change (env vars, feature flags)

Suggested: "Add a new subscription plan with usage-based billing and a marketing pricing page"
