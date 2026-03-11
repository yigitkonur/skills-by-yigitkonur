# Root Cause Taxonomy

Tag each friction point with a root cause code to enable pattern analysis across test runs.

## Structural causes (document architecture)

| Code | Root cause | Description | Typical severity |
|---|---|---|---|
| S1 | **Missing prerequisite** | Tool, file, or config required but not declared before first use | P0 |
| S2 | **Contradictory paths** | Two documents prescribe different workflows for the same situation | P0 |
| S3 | **Scattered information** | Required info split across files without cross-reference | P1 |
| S4 | **Orphaned reference** | File exists in references/ but is never routed from SKILL.md | P2 |
| S5 | **Circular dependency** | Document A says "see B"; document B says "see A" | P1 |

## Semantic causes (language problems)

| Code | Root cause | Description | Typical severity |
|---|---|---|---|
| M1 | **Ambiguous threshold** | Vague boundary word ("substantial", "appropriate") without examples | P1 |
| M2 | **Unstated location** | Output destination not specified (where to write a file) | P0 |
| M3 | **Format inconsistency** | Same concept described with different syntax or naming | P1 |
| M4 | **Missing execution method** | What to do is stated, but how to do it is not | P1 |
| M5 | **Assumed knowledge** | Step requires information not present in the document | P1–P2 |
| M6 | **Vague verb** | Action word with multiple interpretations ("emit", "handle", "process") | P2 |

## Operational causes (discovered during execution)

| Code | Root cause | Description | Typical severity |
|---|---|---|---|
| O1 | **Silent failure** | Command fails without error message or recovery guidance | P1 |
| O2 | **Tool output mismatch** | Tool produces different output format than documented | P2 |
| O3 | **Edge case unhandled** | Valid input produces unexpected behavior | P2 |
| O4 | **Scaling breakdown** | Process works at small scale but breaks at realistic scale | P2 |
| O5 | **Stale reference** | Documentation references a tool version, API, or flag that no longer exists | P1 |

## Using root cause codes

### Tagging

Add the root cause code after the severity in each friction point entry:

```markdown
**F-01 — skill-dl install check buried** (P0, S1)
```

### Pattern analysis

After collecting multiple runs, aggregate root causes:

```markdown
| Root cause | Run 1 | Run 2 | Run 3 | Total | Action |
|---|---|---|---|---|---|
| M4 Missing exec method | 3 | 1 | 0 | 4 | Systemic author habit — training |
| M5 Assumed knowledge | 2 | 2 | 1 | 5 | Add "What you need to know" sections |
| S1 Missing prerequisite | 1 | 0 | 0 | 1 | Fixed after run 1 |
```

### Root cause to fix pattern mapping

Each root cause has a natural fix pattern (see `fix-patterns.md`):

| Root cause | Fix pattern |
|---|---|
| S1 Missing prerequisite | Prerequisite Surfacing |
| S2 Contradictory paths | Workflow Path Reconciliation |
| S3 Scattered information | Schema Duplication at Point of Use |
| M1 Ambiguous threshold | Threshold Concretization |
| M2 Unstated location | Output Location Specification |
| M3 Format inconsistency | Format Alignment |
| M4 Missing execution method | Execution Method Specification |
| M5 Assumed knowledge | Scaling Guidance or Prerequisite Surfacing |
| O1 Silent failure | Error Recovery Addition |
