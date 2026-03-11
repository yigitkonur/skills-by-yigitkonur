# Cross-run Comparison: init-copilot-review Derailment Tests

Date: 2025-07-18

---

## Summary

Two derailment tests were run against the `init-copilot-review` skill:

| Attribute | Run 1 | Run 2 |
|---|---|---|
| Target repo | dubinc/dub | pocketbase/pocketbase |
| Stack | Next.js + TypeScript monorepo | Go single-binary backend |
| SKILL.md version | Original (170 lines) | Post-fix (198 lines) |
| Report file | 01-dogfood-nextjs-monorepo.md | 02-dogfood-go-backend.md |

## Friction comparison

| Metric | Run 1 (pre-fix) | Run 2 (post-fix) | Delta |
|---|---|---|---|
| Total friction points | 16 | 4 | -12 (75% reduction) |
| P0 (blocks progress) | 0 | 0 | 0 |
| P1 (causes confusion) | 8 | 1 | -7 (87.5% reduction) |
| P2 (minor annoyance) | 8 | 3 | -5 (62.5% reduction) |
| Friction density (per step) | 2.67 | 0.67 | -2.00 |
| Steps with zero friction | 0 | 3 | +3 |
| References needed | 2 | 0 | -2 |

## Fix validation (14/14 applicable fixes confirmed)

All 14 applicable fixes from Run 1 were validated in Run 2:
- F-01 through F-05: resolved
- F-06: resolved (not applicable to Go, but threshold criteria made decision clear)
- F-07: N/A (Next.js-specific)
- F-08 through F-16: resolved

## New friction points in Run 2

4 NEW friction points found, all previously unexercised edge cases:

| ID | Title | Severity | Root cause | Fix applied? |
|---|---|---|---|---|
| F-01 (new) | No guidance for existing copilot files | P1 | O3 | Yes |
| F-02 (new) | Svelte/frontend scope not addressed | P2 | O3 | No fix needed |
| F-03 (new) | Brace expansion not validated against Copilot | P2 | M5 | Yes |
| F-04 (new) | Rule deduplication depth unclear | P2 | M4 | Yes |

## Total fixes applied to SKILL.md

| Source | P0 | P1 | P2 | Total |
|---|---|---|---|---|
| Run 1 friction points | 0 | 8 | 8 | 16 |
| Run 2 friction points | 0 | 1 | 2 | 3 |
| **Total fixes** | **0** | **9** | **10** | **19** |

## SKILL.md changes

- **Before**: 170 lines
- **After**: 198 lines (+28 lines, 16.5% growth)
- **Diff**: 42 insertions, 14 deletions
- **Under 500-line limit**: Yes (198/500 = 39.6%)

## Root cause distribution (both runs combined)

| Root cause | Run 1 | Run 2 | Combined |
|---|---|---|---|
| M1 (Ambiguous threshold) | 5 | 0 | 5 |
| M4 (Missing execution method) | 4 | 1 | 5 |
| M5 (Assumed knowledge) | 3 | 1 | 4 |
| O3 (Edge case unhandled) | 2 | 2 | 4 |
| M6 (Vague verb) | 1 | 0 | 1 |
| M3 (Format inconsistency) | 1 | 0 | 1 |
| M2 (Unstated location) | 1 | 0 | 1 |

## Conclusion

The derailment testing methodology successfully identified and resolved 19 friction points across 2 runs on deliberately different project types (TypeScript monorepo vs Go backend). The 75% friction reduction between runs validates that the fixes are effective and generalizable. The remaining 4 friction points from Run 2 are edge cases impossible to discover in Run 1 -- confirming the recommendation to not re-test with the same task.
