# Root Cause Analysis

## Distribution

| Code | Category | Count | % | Friction points |
|------|----------|-------|---|----------------|
| S1   | Missing prerequisite | 4 | 44% | F-01, F-02, F-08, F-09 |
| M4   | Missing decision criteria | 2 | 22% | F-03, F-04 |
| M5   | Missing scaling guidance | 1 | 11% | F-07 |
| M6   | Missing edge case | 1 | 11% | F-06 |
| O2   | Misleading description | 1 | 11% | F-05 |

## Pattern analysis

**Dominant: S1 (Missing prerequisite) — 44%**
All cluster in Quick start. Classic "curse of knowledge" — author knew
prerequisites but didn't document them.

**Secondary: M4 (Missing decision criteria) — 22%**
Two APIs with different semantics presented without decision guidance.

## Fix pattern mapping

| Root cause | Fix pattern | Count |
|-----------|------------|-------|
| S1 | Prerequisite Surfacing | 4 |
| M4 | Execution Method Specification | 2 |
| M5 | Scaling Guidance | 1 |
| M6 | Execution Method Specification | 1 |
| O2 | Threshold Concretization | 1 |
