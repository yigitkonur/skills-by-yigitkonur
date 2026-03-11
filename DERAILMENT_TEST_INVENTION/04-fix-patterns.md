# Fix Patterns

Catalog of recurring fix patterns for common derailment types. Each pattern includes a before/after example from real Derailment Tests.

---

## Pattern 1: Prerequisite Surfacing

**Cures:** Missing prerequisite (S1), silent tool failure
**Severity typically addressed:** P0

### The problem

A dependency (tool, config, permission, file) is required mid-workflow but never declared upfront. The executor discovers the dependency through a runtime failure.

### The fix pattern

Add a `## Prerequisite` or `## Before you start` section at the top of the document, before any workflow steps. List every external dependency with a verification command and an installation fallback.

### Before

```markdown
## Phase 2 — Widen the evidence set

1. Run `skill-dl search` with 3–20 keywords...
```

The executor hits `skill-dl: command not found` during step 1 of Phase 2. The install instructions are in a troubleshooting table 100 lines below.

### After

```markdown
## Prerequisite

Before starting, verify `skill-dl` is installed:

    skill-dl --version

If missing, install it:

    curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash

## Phase 2 — Widen the evidence set

1. Run `skill-dl search` with 3–20 keywords...
```

### Principles

- Prerequisites appear before the first step, never after
- Each prerequisite has a verification command (check if present) and a remediation command (install if missing)
- If the prerequisite check belongs in a checklist, add it as the first item

---

## Pattern 2: Threshold Concretization

**Cures:** Ambiguous threshold (M1), vague boundary words
**Severity typically addressed:** P1

### The problem

A decision point uses subjective language ("substantial", "appropriate", "non-trivial", "as needed") without examples. The executor cannot classify their current situation.

### The fix pattern

Add 2–3 concrete examples for each side of the boundary, plus a rule of thumb that is testable.

### Before

```markdown
### 1. Classify the job

- **Local-only path:** a small cleanup where triggers, structure, and core method stay intact.
- **Full research path:** a new skill, substantial redesign, multi-source merge...
```

"Substantial" is undefined. The executor with a medium-sized change cannot classify it.

### After

```markdown
### 1. Classify the job

- **Local-only path:** a small cleanup where triggers, structure, and core method stay intact. Examples: fixing typos, reordering sections, tightening one trigger phrase, updating a version number.
- **Full research path:** a new skill, substantial redesign, multi-source merge... Examples: adding a new workflow branch, rewriting the decision tree, changing the skill's category, merging two skills, or any change that alters what the skill does (not just how it reads).

Rule of thumb: if the change would alter the comparison table you'd build for this skill, it's the full research path.
```

### Principles

- Every threshold word gets at least 2 examples on each side
- Include a "rule of thumb" that converts the subjective judgment into a testable condition
- The rule of thumb should reference something the executor can check without external knowledge

---

## Pattern 3: Workflow Path Reconciliation

**Cures:** Contradictory paths (S2), parallel workflows
**Severity typically addressed:** P0

### The problem

Two documents (or two sections of the same document) describe different ways to accomplish the same goal. Neither document acknowledges the other's approach, so the executor doesn't know which to follow.

### The fix pattern

Name both paths explicitly and provide selection criteria in a single location.

### Before

Document A says:
```markdown
4. Write a URL file (one URL per line), then run `skill-dl urls.txt -o ./corpus`
```

Document B says:
```markdown
Run `bash skill-research.sh "kw1,kw2,kw3" ./corpus` for end-to-end research
```

Neither mentions the other. The executor encounters both and freezes.

### After

```markdown
4. **Download** — choose one of two paths:
   - **Manual path**: write a URL file (one Playbooks URL per line), then run
     `skill-dl urls.txt -o ./corpus --no-auto-category -f`
   - **Automated path**: run the bundled script
     `bash references/skill-research.sh "kw1,kw2,kw3" ./corpus`
     — it discovers, downloads, and inspects in one command
```

### Principles

- Give each path a name (Manual / Automated, Simple / Advanced, etc.)
- Present both paths in the same section, not in different documents
- Add guidance on when to prefer each path (scale, control, speed)
- Ensure both paths produce equivalent outputs

---

## Pattern 4: Output Location Specification

**Cures:** Unstated location (M2)
**Severity typically addressed:** P0

### The problem

The instruction says "write file X" or "emit artifact Y" without specifying where. The executor must guess the correct directory.

### The fix pattern

Specify the exact relative path in the instruction, using a landmark the executor already knows.

### Before

```markdown
## Phase 3 — Emit `skills.markdown`

Before synthesis, emit `skills.markdown`. This is the durable research artifact.
```

Where? The repo root? The skill directory? A temp directory?

### After

```markdown
## Phase 3 — Write `skills.markdown`

Before synthesis, write `skills.markdown` to disk in the target skill directory (next to `SKILL.md`). This is the durable research artifact.
```

### Principles

- Use relative paths anchored to something the executor already knows (the skill directory, the repo root)
- Prefer "write to disk" over "emit" — the latter is ambiguous about whether it means stdout, a file, or a mental note
- If the location varies by context, state the decision rule

---

## Pattern 5: Execution Method Specification

**Cures:** Missing execution method (M4)
**Severity typically addressed:** P1

### The problem

The instruction states what to do but not how. "Run 5+ queries" — where? In the browser? In the CLI? Mentally?

### The fix pattern

Add the concrete environment, tool, and observation method.

### Before

```markdown
### 8. Test the skill

- Run 5+ should-trigger queries and 5+ should-NOT-trigger queries.
```

### After

```markdown
### 8. Test the skill

- **Trigger tests:** Write 5+ should-trigger queries and 5+ should-NOT-trigger queries. Run each one by pasting it as a new message in Claude.ai (with only this skill enabled) or Claude Code, and record whether the skill loaded.
```

### Principles

- Name the tool or environment explicitly (Claude.ai, terminal, browser, script)
- State what to observe (skill loaded → response header, CLI output, etc.)
- State how to record the result (pass/fail table, notes file, etc.)

---

## Pattern 6: Format Alignment

**Cures:** Format inconsistency (M3)
**Severity typically addressed:** P1

### The problem

The same concept is described with different formats in different locations. Keywords are comma-separated in one place and space-separated in another. Column names differ between the schema and the example.

### The fix pattern

Pick one canonical format, document it in the primary location, and add a conversion note wherever the alternate format appears.

### Before

Script: `bash skill-research.sh "kw1,kw2,kw3"`
CLI: `skill-dl search "kw1" "kw2" "kw3"`

No documentation explains the difference.

### After

Script header comment:
```bash
# NOTE: This script accepts comma-separated keywords in a single string
# because shell quoting makes it awkward to pass pre-quoted arguments.
# Internally, skill-dl search takes space-separated quoted arguments.
# The conversion happens automatically — callers should always use commas.
```

### Principles

- One canonical format, documented once
- Conversion notes at every alternate-format boundary
- Never rely on the executor to discover format differences through errors

---

## Pattern 7: Scaling Guidance

**Cures:** Assumed knowledge (M5), scaling breakdown (O4)
**Severity typically addressed:** P2

### The problem

The instruction says "read the 2–3 most relevant files" but the skill has 19 reference files. Or it says "filter results" but doesn't say how when there are 100+.

### The fix pattern

Add a scaling rule that adjusts the instruction based on the size of the input.

### Before

```markdown
- Read the 2–3 most relevant reference files in full.
```

### After

```markdown
- Read the most relevant reference files: 2–3 files for skills with fewer than 8 references; 4–5 for skills with 8+ references. Pick based on filenames and the skill's stated routing logic.
```

### Principles

- Provide an explicit scaling rule (small set → N items, large set → M items)
- Give a selection heuristic (how to pick which N from the total)
- Acknowledge that the instruction behaves differently at different scales

---

## Pattern 8: Conditional Gating

**Cures:** Steps that appear unconditional but should be gated
**Severity typically addressed:** P1

### The problem

A step reads as mandatory ("Read document X") but only applies to one workflow path. Executors on the other path waste time or get confused.

### The fix pattern

Add an explicit gate at the top of the step: "Only execute this step if [condition]. Skip to step N for [other path]."

### Before

```markdown
### 4. Run remote research

- Read `references/research-workflow.md`.
```

### After

```markdown
### 4. Run remote research when the job is non-trivial

Only execute this step if step 1 classified the job as **Full research path**. Skip to step 7 for local-only work.

- Read `references/research-workflow.md` for the complete research protocol.
```

### Principles

- Gate at the top of the step, not the bottom
- Name the condition and the skip target explicitly
- Use bold formatting for the condition to make it scannable

---

## Pattern 9: Schema Duplication at Point of Use

**Cures:** Scattered information (S3)
**Severity typically addressed:** P1

### The problem

A schema (table columns, required fields, expected format) is defined in document A but needed in document B. Executors reading only document B miss the schema.

### The fix pattern

Duplicate the schema at the point of use, or add a clear cross-reference with the exact section name.

### Before

SKILL.md defines: `Source, Focus, Strengths, Gaps, Relevant paths, Inherit/Avoid`
research-workflow.md says: "Build a markdown comparison table" (no columns listed)

### After

research-workflow.md:
```markdown
## Phase 5 — Build the comparison table

Build a markdown comparison table with at least these columns:

| Column | Purpose |
|---|---|
| Source | Skill name and origin |
| Focus | What the skill covers |
| Size | SKILL.md line count + reference file count |
| Strengths | What it does well |
| Gaps | What it's missing |
| Relevant paths | Specific files or sections worth citing |
| Inherit / Avoid | Decision — what to take vs. what to skip |
```

### Principles

- If the schema is small (≤10 items), duplicate it
- If the schema is large, use a precise cross-reference: "See SKILL.md step 5 for the required columns"
- Never assume the executor will read both documents

---

## Anti-pattern: Errata Files

Do NOT create a separate "errata" or "known issues" document to patch derailments. Fixes must go directly into the source instructions. An errata file:

- Requires the executor to know it exists
- Creates a second source of truth
- Is never read by new executors
- Rots faster than the source document

If you find yourself writing errata, the source document needs editing, not annotating.
