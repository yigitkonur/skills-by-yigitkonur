# Fix Patterns

Match the root cause to a pattern, then apply it to the source text that caused the miss.
Default move: rewrite the controlling paragraph and its paired example so the right path becomes the natural one.

## 1. Prerequisite Surfacing (cures S1)
Add prerequisites BEFORE step 1, with verification command and fallback.

## 2. Threshold Concretization (cures M1)
Add 2-3 concrete examples for each side of the boundary + testable rule of thumb.

## 3. Workflow Path Reconciliation (cures S2)
Name both paths, present in same section, add selection criteria.

## 4. Output Location Specification (cures M2)
Specify exact relative path using a landmark the executor knows.

## 5. Execution Method Specification (cures M4)
State the tool, what to observe, and how to record.

## 6. Format Alignment (cures M3)
One canonical format documented once. Conversion note at every alternate boundary.

## 7. Scaling Guidance (cures M5, O4)
Add explicit scaling rule that adjusts instruction based on input size.

## 8. Conditional Gating
Add explicit gate at top of step: "Only execute if [condition]. Skip to step N for [other path]."

## 9. Schema Duplication at Point of Use (cures S3)
If schema <=10 items, duplicate it. If larger, cross-reference with exact section name.

## 10. Harness Alignment (cures O6)
Remove test-harness-only constraints that are not part of the real skill contract.
The executor should be judged against the skill, not against wrapper instructions you added for the test.

## 11. Source Rewrite First
If one sentence, example, or routing table caused the miss, rewrite or delete that source.
Do not preserve bad text and add a warning beside it unless both are truly needed.

## Anti-pattern: Errata files
Never create separate "errata", "known issues", output-summary, or mistake-notebook docs.
Fixes go directly into the source.
