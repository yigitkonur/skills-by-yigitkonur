# Metrics and Iteration

How to measure improvement across Derailment Test cycles.

## Per-run metrics

| Metric | Definition | Target |
|---|---|---|
| **Friction count** | Total friction points discovered | ↓ Decreasing |
| **P0 count** | Blocking derailments | 0 after first fix cycle |
| **P0 density** | P0 count / total steps | ↓ Below 0.1 |
| **Derailment density** | Total friction / total steps | ↓ Below 0.5 |
| **Cluster size** | Max friction points in one step | ↓ Below 3 |
| **Clean pass rate** | Steps with no friction / total steps | ↑ Above 0.7 |

## Cross-run tracking table

Maintain this table alongside the derail-notes:

```markdown
| Run | Date | Task | Steps | P0 | P1 | P2 | Total | Density | Clean % |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 2026-03-11 | Swift/watchOS | 7 | 3 | 6 | 10 | 19 | 2.71 | 28% |
| 02 | 2026-03-18 | React MCP | 9 | 0 | 2 | 4 | 6 | 0.67 | 67% |
```

## Interpreting trajectories

**Healthy:**
- P0 drops to 0 after run 1, stays there
- Total friction decreases monotonically
- New friction points are P2 (polish), not P0/P1

**Warning:**
- P0 reappears after fix → fix was incomplete
- Total friction increases → new content added without testing
- Density flat → fixes are superficial

**Red flag:**
- Same P0 in 3+ runs → systemic architectural issue
- New P0 in later runs → fixes introducing contradictions
- Clean pass rate below 30% after 3+ runs → consider full rewrite

## When to stop iterating

- Clean pass rate exceeds 80% across 2 consecutive runs
- P0 count is 0 for 2 consecutive runs
- New friction points are exclusively P2
- Real executors report no confusion

## When to rewrite instead of iterate

- Friction count not decreasing after 3+ runs
- Fixes contradicting each other
- Document grew 50%+ from fixes alone
- More than 30% of content is conditional gates and exception handling

## Recurrence analysis

Track which root causes keep appearing across runs:

```markdown
| Root cause | Run 1 | Run 2 | Run 3 | Status |
|---|---|---|---|---|
| S1 Missing prerequisite | F-01 | — | — | Fixed |
| M4 Missing exec method | F-03, F-17 | F-08 | — | Pattern — author training needed |
| M5 Assumed knowledge | F-10 | F-03 | F-01 | Systemic — needs sections added |
```

**Interpretation:**
- Appears once, never again → fix worked
- Appears twice, gone → took two attempts
- Every run, different location → systemic authoring habit, not a doc fix

## Reporting template

```markdown
# Derailment Test Report — [Skill Name]

## Summary
- **Run:** N
- **Task:** [description]
- **Result:** [N] friction points ([P0], [P1], [P2])
- **Trajectory:** [improving / stable / degrading]

## Key findings
1. [Most important P0]
2. [Recurring pattern]
3. [Structural observation]

## Metrics
| Metric | This run | Previous | Trend |
|---|---|---|---|
| Total friction | X | Y | ↓ |
| P0 count | X | Y | ↓ |
| Clean pass rate | X% | Y% | ↑ |
```
