# Root Cause Analysis Summary

Date: 2025-07-12
Total: 26 friction points (4 P0, 18 P1, 4 P2)

---

## Distribution

| Code | Name | Count | Friction Points |
|---|---|---|---|
| M4 | Missing execution method | 6 | F-07, F-10, F-16, F-21, F-23, F-24 |
| M5 | Assumed knowledge | 5 | F-04, F-05, F-09, F-12, F-18 |
| M1 | Ambiguous threshold | 5 | F-01, F-08, F-11, F-25, F-26 |
| S2 | Contradictory instructions | 4 | F-10, F-17, F-19, F-24 |
| M6 | Vague verb | 3 | F-03, F-13, F-20 |
| S3 | Scattered information | 3 | F-04, F-06, F-22 |
| O3 | Edge case unhandled | 3 | F-03, F-06, F-14 |

## Compound P0

Three P1 items cluster in Step 3 (F-09, F-10, F-11). Under test-skill-quality rules, 3+ P1 items in one step = compound P0. Step 3 is the critical fix area.

## Top 3 Root Causes

1. **M4 (Missing execution method, 6 instances):** Skill tells WHAT but not HOW. Fix pattern: bridge to reference router + method execution step.
2. **M5 (Assumed knowledge, 5 instances):** Expert blind spot. Fix pattern: inline minimum viable definitions.
3. **M1 (Ambiguous threshold, 5 instances):** Qualitative terms need concrete criteria. Fix pattern: threshold concretization with examples on both sides.
