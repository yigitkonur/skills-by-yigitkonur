# Derailment Analysis: Systemic Patterns in build-skills

## Cross-cutting pattern analysis

After executing build-skills literally on a real task (creating `build-mcp-sdk-server`), three systemic patterns emerged across the 18 friction points.

---

## Pattern 1: Output location ambiguity (5 friction points)

**Affected:** F-02, F-07, F-09, F-12, F-18

The skill produces at least 5 intermediate artifacts during execution:
1. Workspace tree (Step 3)
2. Per-skill reading notes (Step 4a)
3. `skills.markdown` research proof (Step 4)
4. Comparison table (Step 5)
5. Success criteria (Step 6)

None of these have specified output locations. The skill says "Build a markdown comparison table" and "Write down what success looks like" without saying WHERE. This is the #1 systemic gap — a skill about producing structured output doesn't specify where its own intermediate outputs go.

**Root pattern:** The skill treats intermediate artifacts as ephemeral (conversation output) but phrases them as if they're persistent ("emit skills.markdown"). This mismatch confuses executors about what should be saved vs. what's disposable.

**Fix strategy:** Add a brief "Artifact output" note early in the workflow: "Intermediate artifacts (workspace scan, comparison table, success criteria) appear in conversation output. Persistent artifacts (`skills.markdown`, the final SKILL.md, reference files) are written to disk."

---

## Pattern 2: Prerequisite and fallback gaps (4 friction points)

**Affected:** F-03, F-04, F-06, F-14

The skill assumes specific tools, environments, and capabilities without verification:
- `skill-dl` must be installed (no check, no install path, no fallback)
- `skill-research.sh` must be executable (no invocation syntax)
- `skill-dl search` has a specific argument format (no inline example)
- Trigger testing requires the skill to be installed (impossible during creation)

**Root pattern:** The skill was written by someone who had all prerequisites satisfied. "Curse of knowledge" — the author's environment was fully set up, so they never encountered these gaps.

**Fix strategy:**
1. Add a prerequisites check at the start of Step 4
2. Add a fallback for environments without `skill-dl`
3. Add inline examples at every tool invocation point
4. Distinguish creation vs. revision paths for Step 8

---

## Pattern 3: Cognitive load spikes (3 friction points)

**Affected:** F-05, F-13, F-16

Three moments in the workflow create sudden cognitive load increases:
- Step 3: "Read every relevant reference file" (22 files, no prioritization)
- Step 7: "Read master-checklist.md" (251 lines at synthesis time)
- Steps 1-9 all look equal but vary wildly in effort (minutes to hours)

**Root pattern:** The skill was designed for correctness (every check is important) but not for human cognitive capacity. Information arrives at the wrong time — too much at once during creative phases.

**Fix strategy:**
1. Add scoping hints: "Use the reference routing table to identify the 3-5 most relevant files"
2. Split the checklist into "draft essentials" (Step 7) and "full audit" (Step 9)
3. Add effort indicators or group steps into phases

---

## Density analysis

The research/evidence phase (Steps 3-4a) contains 8 of 18 friction points — 44% of all friction concentrated in 2 of 9 steps. This is the systemic weak point. The synthesis phase (Steps 5-7) has 3 friction points, mostly about output location. The testing phase (Steps 8-9) has 2 friction points, mostly about temporal assumptions.

```
Steps 1-2:  ■ (1 friction point)
Steps 3-4a: ■■■■■■■■ (8 friction points) ← SYSTEMIC WEAK POINT
Steps 5-6:  ■■ (2 friction points)
Step 7:     ■ (1 friction point)
Steps 8-9:  ■■ (2 friction points)
Overall:    ■■■■ (4 structural points)
```

---

## Root cause distribution

| Category | Code | Count | Percentage |
|---|---|---|---|
| Structural | S1-S4 | 7 | 39% |
| Semantic | M1-M6 | 6 | 33% |
| Operational | O1-O3 | 5 | 28% |

**Structural dominance** means the information exists but is organized wrong (wrong location, wrong time, missing scoping). These are the easiest to fix — mostly reordering, adding inline references, and specifying output locations.

**Semantic issues** include ambiguous terms ("classify" implying singular choice, "target workspace" meaning two things, "emit" implying auto-generation). These need rewording.

**Operational issues** are missing prerequisites, tool interface mismatches, and cognitive overload. These need new content (prerequisite checks, fallbacks, effort indicators).

---

## Fix priority order

1. **F-03** (P0): `skill-dl` prerequisite — add verification + fallback
2. **F-13** (P0): Checklist timing — split routing between Step 7 and Step 9
3. **F-02, F-07, F-12** (P1 cluster): Output locations — add artifact output guidance
4. **F-06, F-04** (P1 cluster): Tool invocation — add inline examples
5. **F-01, F-08** (P1 cluster): Classification and quality — add notes about hybrid types and source quality
6. **F-09, F-11, F-14, F-16, F-18** (P1 remaining): Various — apply targeted fixes

---

## Estimated line impact

Current SKILL.md: ~285 lines (well under 500-line limit, room for additions)

| Fix | Estimated lines added | Lines removed/modified |
|---|---|---|
| Prerequisite check in Step 4 | +6 | 0 |
| Fallback path for Step 4 | +3 | 0 |
| Artifact output note | +4 | 0 |
| Step 2 hybrid type note | +1 | 0 |
| Step 3 workspace clarification | +1 | ~1 modified |
| Step 4 inline examples | +3 | ~2 modified |
| Step 4a quality warning | +1 | 0 |
| Step 4a notes template hint | +1 | 0 |
| Step 5 remove redundant read | 0 | ~1 removed |
| Step 7 checklist split | +1 | ~1 modified |
| Step 8 creation/revision conditional | +2 | ~1 modified |
| Step 9 verification command | +2 | 0 |
| Effort indicators | +4 | ~4 modified |
| Output contract timing | +3 | ~3 modified |
| **Total** | **+32** | **~13 modified** |

Estimated post-fix SKILL.md: ~304 lines (still well under 500-line limit)
