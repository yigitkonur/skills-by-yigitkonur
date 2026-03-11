# Derailment Test: init-greptile-review on dubinc/dub monorepo

Date: 2025-07-14
Skill under test: init-greptile-review
Test task: Generate .greptile/ config for dubinc/dub (Turborepo, Next.js 15, Prisma, Stripe, 12+ packages, 127 API routes)
Method: Follow SKILL.md Phases 1-6 exactly as written

## Friction points (16 total: 0 P0, 7 P1, 9 P2)

### Phase 1 (3 friction points)
- **F-01** (P2, M6): "Inspect" vague verb -> replaced with "Search the repository for these items" + examples
- **F-02** (P1, M1): No guidance on qualifying docs/specs/schemas -> added file type list
- **F-03** (P2, M2): No linter search locations -> added config file patterns

### Phase 2 (5 friction points)
- **F-04** (P1, M6): "Explore the repository" vague -> replaced with concrete exploration method
- **F-05** (P2, S3): Context files duplicated between Phase 1 and 2 -> clarified ownership
- **F-06** (P1, S1): "Recurring failure patterns" impossible without user -> added git log fallback
- **F-16** (P1, M1): No exploration stopping criteria -> added depth guidance paragraph

### Phase 3 (2 friction points)
- **F-07** (P2, M1): rules.md threshold ambiguous -> added "200 character" heuristic
- **F-08** (P2, M1): "genuinely improve" subjective -> replaced with measurable criterion

### Phase 4 (2 friction points)
- **F-09** (P2, M1): "almost every PR" unmeasurable -> replaced with "majority of files"
- **F-10** (P2, M5): No cross-ref to patterns.md -> added explicit reference

### Phase 5 (1 friction point)
- **F-11** (P2, M4): No lint duplication verification method -> added litmus test

### Phase 6 (4 friction points)
- **F-12** (P2, M2): Output file tree location unspecified -> added "in your response"
- **F-13** (P1, M3): Reasoning annotations format unspecified -> added format example
- **F-14** (P1, M5): "Canary test" term undefined -> added inline definition + example
- **F-15** (P1, S3): Phase headers missing reference file routing -> added Read first blockquotes

## What worked well
1. Phase structure is logical and natural (classify -> map -> topology -> rules -> scope -> validate)
2. Reference file catalog is comprehensive (8 files)
3. Config spec is precise with exact JSON schemas
4. Anti-patterns file has clear "do this / not that" tables
5. Scenarios reference covers real-world complexity (monorepo, multi-language, greenfield, migration)
6. Rule severity categories prevent over-alerting

## Priority summary
| Priority | Count | Friction points |
|---|---|---|
| P0 | 0 | - |
| P1 | 7 | F-02, F-04, F-06, F-13, F-14, F-15, F-16 |
| P2 | 9 | F-01, F-03, F-05, F-07, F-08, F-09, F-10, F-11, F-12 |

Clean pass rate: 22/38 steps = 57.9%
Derailment density: Phase 2 (5) > Phase 6 (4) > Phase 1 (3) > Phase 3 (2) = Phase 4 (2) > Phase 5 (1)
