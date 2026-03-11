# Metrics and Iteration

How to measure improvement across Derailment Test cycles and build a quality trajectory for procedural instructions.

---

## Core metrics

### Per-run metrics

Collected from each Derailment Test execution.

| Metric | Definition | Target direction |
|---|---|---|
| **Friction count** | Total friction points discovered | ↓ Decreasing across runs |
| **P0 count** | Blocking derailments | 0 after first fix cycle |
| **P0 density** | P0 count / total steps | ↓ Below 0.1 |
| **Derailment density** | Total friction / total steps | ↓ Below 0.5 |
| **Cluster size** | Max friction points in one step | ↓ Below 3 |
| **External knowledge count** | Times the executor needed info not in the document | ↓ 0 is ideal |
| **Fix rate** | Friction points fixed / total friction points | ↑ Above 0.8 for P0+P1 |

### Cross-run metrics

Tracked across multiple Derailment Tests on the same instruction set.

| Metric | Definition | Target direction |
|---|---|---|
| **Recurrence count** | Same derailment type appearing in multiple runs | ↓ 0 after fix |
| **New-to-recurrent ratio** | New friction points / recurring friction points | ↑ Higher = fixes are holding |
| **Run-over-run reduction** | (Run N friction count - Run N+1 friction count) / Run N count | ↑ Positive = improving |
| **Time to first P0** | Steps executed before first blocking derailment | ↑ Higher = cleaner critical path |
| **Clean pass rate** | Steps with no friction / total steps | ↑ Above 0.7 |

## Measurement protocol

### After each run

1. Count friction points by severity
2. Calculate per-run metrics
3. Add a row to the cross-run tracking table

### Cross-run tracking table

Maintain this table in the project or alongside the instruction set:

```markdown
| Run | Date | Task | Steps | P0 | P1 | P2 | Total | Density | Clean % |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 2026-03-11 | Swift/watchOS research | 7 | 3 | 6 | 10 | 19 | 2.71 | 28% |
| 02 | 2026-03-18 | React MCP build | 9 | 0 | 2 | 4 | 6 | 0.67 | 67% |
| 03 | 2026-03-25 | Python CLI scaffold | 8 | 0 | 1 | 2 | 3 | 0.38 | 75% |
```

### Interpreting the trajectory

**Healthy trajectory:**
- P0 count drops to 0 after run 1 and stays there
- Total friction count decreases monotonically (or near-monotonically)
- Clean pass rate increases steadily
- New friction points are P2 (polish), not P0/P1 (structural)

**Warning signals:**
- P0 items reappear after being "fixed" → fix was incomplete or introduced a regression
- Total friction count increases → new content was added without testing
- Derailment density stays flat → fixes are superficial (wording changes) not structural

**Red flags:**
- Same P0 appears in 3+ runs → systemic architectural issue, not a wording problem
- New P0 items appear in later runs → fixes are introducing new contradictions
- Clean pass rate below 30% after 3+ runs → instruction set may need a full rewrite

## Iteration strategies

### Between runs

1. **Fix all P0 items** from the current run before the next run
2. **Fix P1 items** that recurred from a previous run
3. **Defer P2 items** unless they cluster (3+ in one step = compound P0)
4. **Run a targeted re-test** on the fixed steps before running the full protocol again

### When to stop iterating

Stop when:
- Clean pass rate exceeds 80% across 2 consecutive runs
- P0 count is 0 for 2 consecutive runs
- New friction points are exclusively P2
- The instruction set is performing well with real executors (not just test runs)

### When to rewrite instead of iterate

Sometimes iterative fixes create a patchwork document that is technically correct but structurally incoherent. Consider a full rewrite when:

- Friction count is not decreasing after 3+ runs
- Fixes are contradicting each other
- The document has grown 50%+ from fixes alone
- More than 30% of content is conditional gates and exception handling
- A new reader cannot follow the document's logic flow

## Recurrence analysis

The most valuable cross-run analysis is tracking which root causes keep appearing.

### Building a recurrence matrix

```markdown
| Root cause | Run 1 | Run 2 | Run 3 | Status |
|---|---|---|---|---|
| S1 Missing prerequisite | F-01 | — | — | Fixed |
| S2 Contradictory paths | F-04 | — | — | Fixed |
| M1 Ambiguous threshold | F-02 | F-05 | — | Improved |
| M4 Missing exec method | F-03, F-17 | F-08 | — | Pattern, not incident |
| M5 Assumed knowledge | F-10, F-12 | F-03 | F-01 | Systemic — needs architectural fix |
```

### Interpreting recurrence

| Pattern | Meaning | Action |
|---|---|---|
| Appears once, never again | Fix worked | No action |
| Appears twice, then gone | Took two attempts | Review fix quality process |
| Appears in every run, different location | Systemic authoring habit | Author training, not document fix |
| Same root cause, same location | Fix didn't address root cause | Deeper investigation needed |

## Integration with existing quality processes

### With code review

Add a "Derailment Test" checkbox to the PR template for documentation changes:

```markdown
## Documentation changes
- [ ] Derailment Test run on modified instructions
- [ ] P0 friction count: 0
- [ ] Derail notes file attached or linked
```

### With CI/CD

Automated checks can catch some derailment causes:

```yaml
# Example: check for orphaned references
- name: Reference integrity
  run: |
    for ref in $(find references -type f -name "*.md"); do
      basename=$(basename "$ref" .md)
      grep -q "$basename" SKILL.md || echo "ORPHAN: $ref"
    done
```

### With user feedback

Map user-reported issues back to derailment categories:

| User report | Likely root cause | Metric impact |
|---|---|---|
| "I didn't know I needed X installed" | S1 Missing prerequisite | P0 in next test |
| "The docs say two different things" | S2 Contradictory paths | P0 in next test |
| "I wasn't sure which option to pick" | M1 Ambiguous threshold | P1 in next test |
| "It worked but I had to guess where to put the file" | M2 Unstated location | P1 in next test |

## Reporting template

For sharing results with stakeholders:

```markdown
# Derailment Test Report — [Instruction Set Name]

## Summary
- **Run number:** N
- **Task:** [description]
- **Result:** [N] friction points found ([P0], [P1], [P2])
- **Trajectory:** [improving / stable / degrading] vs. previous run

## Key findings
1. [Most important P0, if any]
2. [Recurring pattern, if any]
3. [Structural observation]

## Fixes applied
- [N] P0 fixes
- [N] P1 fixes
- [N] P2 fixes deferred

## Metrics
| Metric | This run | Previous | Trend |
|---|---|---|---|
| Total friction | X | Y | ↓ |
| P0 count | X | Y | ↓ |
| Clean pass rate | X% | Y% | ↑ |

## Next steps
1. [Fix remaining P1 items]
2. [Schedule run N+1 with different task]
```

## Maturity model

Track organizational adoption maturity:

| Level | Description | Indicators |
|---|---|---|
| 0 — Ad hoc | No systematic testing of instructions | User complaints are the primary signal |
| 1 — Reactive | Derailment Tests run after complaints | Tests happen but aren't proactive |
| 2 — Proactive | Tests run before publishing/shipping | Every new instruction set gets at least one test |
| 3 — Integrated | Tests are part of the authoring workflow | Authors run self-tests during writing |
| 4 — Measured | Cross-run metrics tracked and reviewed | Quality trajectory is a managed KPI |
| 5 — Cultural | "Follow literally, not intelligently" is a shared principle | Authors naturally write for naive executors |

Most teams start at Level 0. Running your first Derailment Test puts you at Level 1. The methodology in this document supports progression to Level 4. Level 5 is an organizational culture shift that happens over months.
