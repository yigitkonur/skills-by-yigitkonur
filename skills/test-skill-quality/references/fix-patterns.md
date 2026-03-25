# Fix Patterns

Proven fix patterns for common derailment types. Match the root cause to a pattern, then apply.

## Pattern 1: Prerequisite Surfacing

**Cures:** S1 (Missing prerequisite)

Add a `## Prerequisite` section at the top of the document, before any workflow steps. Each prerequisite has a verification command and an installation fallback.

**Before:**
```markdown
## Phase 2 — Research
1. Run `skill-dl search` with keywords...
```
Executor hits `command not found`.

**After:**
```markdown
## Prerequisite
Verify `skill-dl` is installed:
    skill-dl --version
If missing:
    curl -fsSL .../install.sh | bash

## Phase 2 — Research
1. Run `skill-dl search` with keywords...
```

**Rule:** Prerequisites go before step 1, never after. If a checklist exists, add it as the first item.

## Pattern 2: Threshold Concretization

**Cures:** M1 (Ambiguous threshold)

Add 2–3 concrete examples for each side of the boundary plus a testable rule of thumb.

**Before:**
```markdown
- **Full research path:** substantial redesign, multi-source merge...
```

**After:**
```markdown
- **Full research path:** ...Examples: adding a new workflow branch, rewriting the decision tree, changing the skill's category.

Rule of thumb: if the change would alter the comparison table, it's the full research path.
```

**Rule:** Every threshold word gets examples on both sides. The rule of thumb must reference something the executor can check.

## Pattern 3: Workflow Path Reconciliation

**Cures:** S2 (Contradictory paths)

Name both paths explicitly, present them in the same section, and add selection criteria.

**Before:**
Document A: "Write a URL file, then run skill-dl"
Document B: "Run skill-research.sh for end-to-end research"
Neither mentions the other.

**After:**
```markdown
Choose one path:
- **Manual path**: write a URL file, then `skill-dl urls.txt`
- **Automated path**: `bash skill-research.sh "kw1,kw2,kw3"`
```

**Rule:** Both paths in one section. Add when-to-use guidance for each.

## Pattern 4: Output Location Specification

**Cures:** M2 (Unstated location)

Specify the exact relative path using a landmark the executor already knows.

**Before:**
```markdown
Emit `skills.markdown`. This is the research artifact.
```

**After:**
```markdown
Write `skills.markdown` to disk in the target skill directory (next to `SKILL.md`).
```

**Rule:** Use relative paths anchored to a known landmark. Prefer "write to disk" over "emit."

## Pattern 5: Execution Method Specification

**Cures:** M4 (Missing execution method)

State the tool/environment, the observation method, and the recording method.

**Before:**
```markdown
- Run 5+ should-trigger queries.
```

**After:**
```markdown
- Write 5+ should-trigger queries. Run each by pasting as a new message in
  Claude.ai (with only this skill enabled) or Claude Code. Record whether
  the skill loaded (visible in the response header or CLI output).
```

**Rule:** Name the tool. State what to observe. State how to record.

## Pattern 6: Format Alignment

**Cures:** M3 (Format inconsistency)

Pick one canonical format, document it in the primary location, add conversion notes at alternate-format boundaries.

**Before:**
Script: `"kw1,kw2,kw3"` (comma-separated)
CLI: `"kw1" "kw2" "kw3"` (space-separated)
No documentation explains the difference.

**After:**
Script header:
```bash
# This script accepts comma-separated keywords ("kw1,kw2,kw3").
# Internally, skill-dl search takes space-separated quoted args.
# Conversion happens automatically — callers should use commas.
```

**Rule:** One canonical format documented once. Conversion note at every alternate boundary.

## Pattern 7: Scaling Guidance

**Cures:** M5 (Assumed knowledge), O4 (Scaling breakdown)

Add a scaling rule that adjusts the instruction based on input size.

**Before:**
```markdown
Read the 2–3 most relevant reference files.
```

**After:**
```markdown
Read reference files: 2–3 for skills with <8 references, 4–5 for skills with 8+.
Pick based on filenames and the skill's stated routing logic.
```

**Rule:** Provide an explicit scaling rule and a selection heuristic.

## Pattern 8: Conditional Gating

**Cures:** Steps that appear unconditional but should be gated.

Add an explicit gate at the top: "Only execute if [condition]. Skip to step N for [other path]."

**Before:**
```markdown
### 4. Run remote research
- Read `references/research-workflow.md`.
```

**After:**
```markdown
### 4. Run remote research (full research path only)

Only execute if step 1 classified the job as **Full research path**. Skip to step 7 for local-only work.
```

**Rule:** Gate at the top, not the bottom. Bold the condition. Name the skip target.

## Pattern 9: Schema Duplication at Point of Use

**Cures:** S3 (Scattered information)

Duplicate small schemas at the point of use. For large schemas, add a precise cross-reference.

**Before:**
SKILL.md: defines 7 comparison table columns
research-workflow.md: says "Build a comparison table" (no columns listed)

**After:**
research-workflow.md:
```markdown
Build a comparison table with at least these columns:
| Column | Purpose |
| Source | Skill name and origin |
| Focus | What the skill covers |
...
```

**Rule:** If schema is ≤10 items, duplicate it. If larger, cross-reference with exact section name.

## Anti-pattern: Errata files

Never create a separate "errata" or "known issues" document. Fixes must go directly into the source. Errata files:
- Require the executor to know they exist
- Create a second source of truth
- Are never read by new executors
- Rot faster than the source document
