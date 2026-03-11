# Execution Protocol

Step-by-step guide for running a Derailment Test on any procedural instruction set.

---

## Prerequisites

Before starting, you need:

1. **The instruction set** — a complete, self-contained document (skill file, runbook, SOP, tutorial)
2. **A real task** — a genuine, non-trivial task that exercises the instruction set's intended workflow
3. **A derail-notes directory** — create `derail-notes/` in the project root for structured output
4. **The naive executor mindset** — commit to following only what is written, not what you know

## Phase 0: Preparation

### 0.1 Select the test task

The task must be:

- **Real** — not hypothetical. You will actually execute it.
- **Representative** — it should exercise the main workflow, not an edge case.
- **Non-trivial** — it must involve enough complexity to hit branching logic, cross-references, and multi-step sequences.
- **Within scope** — the task should clearly fall within the instruction set's declared trigger boundary.

**Good test tasks:**
- "Research and design a Swift/watchOS skill" (tests a skill-building workflow)
- "Deploy the staging environment" (tests a deployment runbook)
- "Onboard a new API integration" (tests an integration guide)

**Bad test tasks:**
- "Fix a typo" (too trivial, won't exercise the workflow)
- "Do something vaguely related" (won't test the trigger boundary)

### 0.2 Record the test metadata

Before execution, write the header of your derail-notes file:

```markdown
# Derailment Test: [instruction-set-name] on "[task-description]"

Date: YYYY-MM-DD
Instruction set: [name and version/path]
Test task: [one-line description]
Tester: [who is executing]
Method: Follow [document-name] steps N–M exactly as written

---
```

### 0.3 Pre-scan the instruction set

Read the instruction set once, end-to-end, without executing anything. Note:

- Total number of steps
- Branching points (if/then logic)
- External dependencies (tools, files, services)
- Cross-references to other documents

This pre-scan is for orientation only. The actual test must be done fresh, following each step sequentially.

## Phase 1: Literal Execution

### The core loop

For each step in the instruction set:

1. **Read the step** — read only the current step, not the next one.
2. **Attempt to execute** — do exactly what the step says, using only the information provided.
3. **Record the outcome**:
   - **Clean pass** — the step was unambiguous and executable. No note needed.
   - **Derailment** — you could not determine the next action from the instructions alone. Record a friction point.
   - **Implicit knowledge used** — you could execute the step, but only because you already knew something not stated. Record a friction point of lower severity.

### The naive executor contract

During execution, you must NOT:

- Fill in unstated defaults from personal knowledge
- Skip steps that seem unnecessary
- Reorder steps that seem out of sequence
- Interpret vague language charitably ("properly", "as needed", "appropriate")
- Consult external sources not referenced in the instructions

You MUST:

- Stop and record a friction point whenever the instructions leave you uncertain
- Follow branching logic exactly as stated, even if you think a different branch applies
- Execute commands exactly as written (including wrong ones — record the failure)
- Note when two documents contradict each other

### Recording friction points

Each friction point gets a structured entry:

```markdown
**F-[NN] — [short title]** (P[0-2])
[One paragraph: what happened, what the instructions said, what was missing or ambiguous.]
Fix: [Specific change to the instructions that would prevent this derailment.]
```

The ID is sequential within the test run. Severity is assigned using the classification in `03-friction-classification.md`.

## Phase 2: Evidence Collection

After literal execution, collect quantitative evidence:

### 2.1 Count the outcomes

| Metric | Value |
|---|---|
| Total steps attempted | |
| Clean passes | |
| Derailments (P0) | |
| Derailments (P1) | |
| Derailments (P2) | |
| Steps requiring external knowledge | |

### 2.2 Map derailment locations

Create a step-by-step map showing where derailments cluster:

```
Step 1: Classify → F-02 (P1)
Step 2: Classify type → clean
Step 3: Local evidence → clean
Step 4: Remote research → F-04 (P0), F-05 (P1), F-06 (P1), F-07 (P2)
Step 4a: Read corpus → F-10 (P2), F-11 (P2), F-12 (P2)
Step 5: Compare → F-13 (P0), F-15 (P1)
```

Clustering reveals which workflow phases need the most attention.

### 2.3 Classify root causes

Tag each friction point with a root cause category:

| Root cause | Description | Example |
|---|---|---|
| **Missing prerequisite** | Dependency not stated before first use | "skill-dl not installed" |
| **Ambiguous threshold** | Vague boundary without examples | "substantial redesign" |
| **Contradictory paths** | Two documents prescribe conflicting workflows | URL file vs. script |
| **Unstated location** | Output location not specified | "write skills.markdown" (where?) |
| **Format inconsistency** | Same concept described differently | Comma-separated vs. space-separated |
| **Missing execution method** | Action stated but not how | "Run 5+ queries" (how?) |
| **No error recovery** | Failure case with no guidance | Download fails silently |
| **Assumed knowledge** | Step requires info not in the document | "read the most relevant files" (which?) |

## Phase 3: Derail Notes Assembly

### 3.1 Structure the report

Organize friction points by workflow step, not by discovery order:

```markdown
## Friction points

### [Phase/step name]

**F-01 — [title]** (P0)
...

**F-02 — [title]** (P1)
...
```

### 3.2 Add the "What worked well" section

Every derail report must include positive findings. This prevents the report from being read as pure criticism and highlights structural patterns worth preserving.

```markdown
## What worked well

1. [Feature that worked as designed]
2. [Structural choice that prevented problems]
...
```

### 3.3 Add the priority summary table

```markdown
## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 (blocks progress) | N | F-xx, F-yy |
| P1 (causes confusion) | N | F-xx, F-yy |
| P2 (minor annoyance) | N | F-xx, F-yy |
```

### 3.4 File naming

Use this convention:

```
derail-notes/01-dogfood-[topic].md
derail-notes/02-dogfood-[topic].md
```

Sequential numbering tracks iteration history. The same instruction set tested twice produces two files, enabling comparison.

## Phase 4: Fix Application

### 4.1 Prioritize fixes

Fix all P0 items first. Then P1. P2 items are optional per cycle.

### 4.2 Apply fixes to source files

For each friction point, edit the instruction set at the root cause location. Fixes must be:

- **In-place** — edit the existing instruction, don't add a separate errata document
- **Self-contained** — the fix should make the instruction work without consulting the derail notes
- **Minimal** — add only what was missing, don't restructure the whole document

### 4.3 Cross-reference verification

After all fixes, verify:

- No contradictions introduced between documents
- All cross-references still resolve (no broken links)
- Terminology is consistent across all files
- The instruction set still passes the line-count or size constraints

### 4.4 Mark friction points as resolved

In the derail notes, add the fix status:

```markdown
Fix: Added prerequisite section at top of research-workflow.md. ✓ Applied.
```

## Phase 5: Validation

### 5.1 Grep for consistency

Run automated checks across all modified files:

```bash
# Check for stale terminology
grep -r "install count" skills/build-skills/  # should be zero
grep -r "skills.markdown" skills/build-skills/  # verify consistent usage
```

### 5.2 Routing integrity check

Verify every reference file is reachable from the main instruction document:

```bash
# List all reference files
find references -type f -name "*.md" -o -name "*.sh" | sort

# Check each appears in SKILL.md
for f in $(find references -type f); do
  grep -q "$(basename $f .md)" SKILL.md || echo "ORPHAN: $f"
done
```

### 5.3 Optional: Re-run the test

The gold standard is to re-run the test on the fixed instruction set with the same task. New derailments found in the re-run get the next sequential IDs (F-20, F-21, ...) and go into a new derail-notes file.
