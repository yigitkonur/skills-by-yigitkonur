# Consolidated Friction Analysis: run-research

## Combined friction registry (25 items across 2 tests)

### By root cause (sorted by frequency)

| Root Cause | Code | Count | Friction IDs |
|---|---|---|---|
| Missing method specification | O5 | 4 | F-07, F-09, F-17, F-23 |
| Conflicting instructions | M3 | 3 | F-06, F-13, F-24 |
| Missing prerequisite | S2 | 3 | F-02, F-12, F-22 |
| Missing threshold/termination | S3 | 3 | F-08, F-15, F-25 |
| Missing step | S1 | 2 | F-11, F-16 |
| Implicit ordering | M2 | 2 | F-02, F-18 |
| Scope ambiguity/mismatch | M4 | 3 | F-04, F-14, F-19 |
| Missing output location/format | O1 | 2 | F-03, F-10 |
| Vague referent | M1 | 2 | F-05, F-21 |
| Missing conditional | S4 | 1 | F-20 |

### Top fix patterns needed

1. **Execution Method Specification** — 4 friction points need explicit tool mapping (F-07, F-09, F-17, F-23)
2. **Workflow Path Reconciliation** — 3 conflicts between sections need resolution (F-06, F-13, F-24)
3. **Prerequisite Surfacing** — 3 missing prerequisites need explicit callout (F-02, F-12, F-22)
4. **Threshold Concretization** — 3 vague boundaries need specific numbers/criteria (F-08, F-15, F-25)

### P0 fix (must do)

**F-11**: deep_research placement in sequence is undefined. Fix: Add explicit guidance after Step 3 about when/how to call deep_research.

### P1 fixes (high priority, 17 items)

All P1 fixes grouped by SKILL.md section they affect:

**Workflow Selector table** (3 fixes):
- F-02: Add reading order for key references
- F-18: Specify reference reading priority
- F-21: Clarify "Escalate" means "add when insufficient"

**Step 1 — Frame** (2 fixes):
- F-03: Specify WHERE to write the framing
- F-04: Move deep_research format guidance to where it's needed

**Step 2 — Query** (1 fix):
- F-06: Clarify queries are per-tool, not cross-tool

**Step 3 — Read** (2 fixes):
- F-07: Map conceptual steps to tool names
- F-08: Add thread selection count guidance

**Step 4 — Validate** (1 fix):
- F-09: Specify validation methods

**Step 5 — Synthesize** (2 fixes):
- F-10: Add output templates per task type
- F-13: Clarify deep_research output handling

**Cross-cutting** (4 fixes):
- F-12: Prepare deep_research template in Step 1
- F-15: Define verification termination criteria
- F-16: Add source reconciliation step
- F-24: Establish skill authority over tool directives

**Reference routing** (2 fixes):
- F-22: Add file selection guidance
- F-23: Explain how to use domain references

### P2 fixes (nice to have, 5 items)

- F-01: Add "consult selector first" instruction
- F-05: Specify per-tool query volume
- F-14: Generalize "attach code files" to all research types
- F-19: Add query strategy hints per task type
- F-20: Handle "first investigation" case

---

## Impact assessment

The skill is **conceptually excellent** but **procedurally underspecified**. The 5-step framework (Frame → Query → Read → Validate → Synthesize) is the right abstraction, and the workflow selector routing is correct. However:

1. **Step-to-tool mapping is implicit** — agents must infer which tool to use at each step
2. **Cross-step orchestration is missing** — how tools feed into each other isn't specified
3. **deep_research placement is undefined** — the most powerful tool has no clear insertion point
4. **Output expectations are vague** — no templates for what the final synthesis should look like
5. **Tool vs. skill authority is unclear** — tools generate their own "next step" directives

The fixes are primarily **additive** (adding specificity) rather than **structural** (reorganizing). The skill's architecture is sound.
