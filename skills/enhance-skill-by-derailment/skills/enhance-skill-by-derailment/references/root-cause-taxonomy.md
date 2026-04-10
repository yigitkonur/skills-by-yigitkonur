# Root Cause Taxonomy

Tag each friction point with a code to understand WHY it broke.
Use the smallest set of codes that explains the whole miss.
Five symptoms can still come from one bad paragraph or one bad example.

## Structural causes (S)

| Code | Root cause | Typical severity |
|---|---|---|
| S1 | Missing prerequisite — tool/file/config not declared before use | P0 |
| S2 | Contradictory paths — two docs prescribe different workflows | P0 |
| S3 | Scattered information — required info split across files without cross-ref | P1 |
| S4 | Orphaned reference — file exists but never routed from SKILL.md | P2 |
| S5 | Circular dependency — doc A says "see B"; doc B says "see A" | P1 |

## Semantic causes (M)

| Code | Root cause | Typical severity |
|---|---|---|
| M1 | Ambiguous threshold — vague word ("substantial") without examples | P1 |
| M2 | Unstated location — output destination not specified | P0 |
| M3 | Format inconsistency — same concept with different syntax | P1 |
| M4 | Missing execution method — what to do stated, how to do it not | P1 |
| M5 | Assumed knowledge — step requires info not in the document | P1-P2 |
| M6 | Vague verb — action word with multiple interpretations | P2 |

## Operational causes (O)

| Code | Root cause | Typical severity |
|---|---|---|
| O1 | Silent failure — command fails without error or recovery guidance | P1 |
| O2 | Tool output mismatch — different format than documented | P2 |
| O3 | Edge case unhandled — valid input produces unexpected behavior | P2 |
| O4 | Scaling breakdown — works small, breaks at realistic scale | P2 |
| O5 | Stale reference — docs reference tool version/flag that no longer exists | P1 |
| O6 | Harness-induced drift — the test prompt or wrapper changed the task enough to create fake friction | P1 |

## Root cause → fix pattern mapping

| Root cause | Fix pattern |
|---|---|
| S1 | Prerequisite Surfacing |
| S2 | Workflow Path Reconciliation |
| S3 | Schema Duplication at Point of Use |
| M1 | Threshold Concretization |
| M2 | Output Location Specification |
| M4 | Execution Method Specification |
| M5 | Scaling Guidance or Prerequisite Surfacing |
| O1 | Error Recovery Addition |
| O6 | Harness Alignment |
