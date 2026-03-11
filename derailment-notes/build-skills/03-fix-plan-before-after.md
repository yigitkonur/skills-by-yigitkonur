# Derailment Fix Plan: build-skills SKILL.md

## Fix strategy

Apply fixes to `skills/build-skills/SKILL.md` in priority order. Each fix addresses one or more friction points. All fixes are in-place edits — no new reference files needed.

---

## Fix 1: Step 2 — Allow hybrid type classification (F-01)

**Before:**
```markdown
### 2. Classify the skill type

Before designing, identify the skill's category:
```

**After:**
```markdown
### 2. Classify the skill type

Before designing, identify the skill's primary category (skills often combine types — pick the dominant one and note secondary characteristics):
```

**Rationale:** Removes the false implication of mutual exclusivity. Guides users to pick primary and note secondary.

---

## Fix 2: Step 3 — Clarify "target workspace" (F-02)

**Before:**
```markdown
- Produce a tree-style inventory of the target workspace.
```

**After:**
```markdown
- Produce a tree-style inventory of the skill repo workspace. If the skill targets an external framework or SDK, also tree a representative project or the official examples.
```

---

## Fix 3: Step 3 — Add scoping hint for reference reading (F-05)

**Before:**
```markdown
- Read every file in `references/` that is relevant to the task: open each file, read the contents, and note what it covers and where it has gaps.
```

**After:**
```markdown
- Read every file in `references/` that is relevant to the task: use the Reference routing table below to identify the 3–5 most relevant files for your current step, open each one, and note what it covers and where it has gaps.
```

---

## Fix 4: Step 4 — Add prerequisite check, inline example, fallback (F-03, F-06)

**Before:**
```markdown
- Read `references/research-workflow.md` for the complete research protocol.
- Use `skill-dl search` (3–20 keywords) to discover candidates — it outputs a prioritized markdown table to stdout.
- Use `skill-dl` to download selected candidates, or run `references/skill-research.sh` for end-to-end parallel discovery and download in one command.
- See `references/remote-sources.md` for `skill-dl search` usage patterns and download options.
```

**After:**
```markdown
- Read `references/research-workflow.md` for the complete research protocol.
- Verify `skill-dl` is available: `skill-dl --version`. If missing, see `references/remote-sources.md` for installation. If unavailable and installation is not possible, use the `skills-as-context-search-skills` tool as a fallback for discovery and `skills-as-context-get-skill-details` for downloading.
- Use `skill-dl search` with 3–20 space-separated keywords to discover candidates: `skill-dl search mcp server typescript sdk --top 20`. It outputs a prioritized markdown table to stdout.
- Use `skill-dl` to download selected candidates, or run `bash references/skill-research.sh <keyword1> <keyword2> ...` for end-to-end parallel discovery and download in one command.
- See `references/remote-sources.md` for more `skill-dl` usage patterns and download options.
```

---

## Fix 5: Step 4 — Clarify `skills.markdown` creation (F-07, F-10)

**Before:**
```markdown
- Emit `skills.markdown` before moving on.
```

**After:**
```markdown
- Create `skills.markdown` in the workspace root summarizing what was downloaded, what was shortlisted, and why, before moving on.
```

---

## Fix 6: Step 4 — Add invocation syntax for skill-research.sh (F-04)

Already addressed in Fix 4 above — the inline `bash references/skill-research.sh <keyword1> <keyword2> ...` covers this.

---

## Fix 7: Step 4a — Add source quality warning (F-08)

**Before (at end of Step 4a):**
```markdown
The notes you capture here are the raw material for the comparison table in step 5. If you skip reading, the comparison table will be fabricated from memory rather than evidence.
```

**After:**
```markdown
Downloaded sources may not follow the quality standards this skill enforces (e.g., SKILL.md over 500 lines, missing reference routing). Note these issues — they inform the "avoid" column of your comparison table.

The notes you capture here are the raw material for the comparison table in step 5. If you skip reading, the comparison table will be fabricated from memory rather than evidence.
```

---

## Fix 8: Step 4a — Add notes format hint (F-09)

**Before:**
```markdown
- **Capture notes per skill**: overall structure, workflow style, reference organization, what it does well, what it does poorly, and 1–2 patterns worth inheriting (with exact relative paths).
```

**After:**
```markdown
- **Capture notes per skill** (a heading per skill with bullets mapping to comparison table columns): overall structure, workflow style, reference organization, what it does well, what it does poorly, and 1–2 patterns worth inheriting (with exact relative paths).
```

---

## Fix 9: Step 5 — Remove redundant re-read instruction (F-11)

**Before:**
```markdown
- Read the selected local and remote sources that actually matter.
- Build a markdown comparison table with at least: `Source`, `Focus`, `Strengths`, `Gaps`, `Relevant paths or sections`, and `Inherit / avoid`.
```

**After:**
```markdown
- Using your notes from Step 4a, build a markdown comparison table with at least: `Source`, `Focus`, `Strengths`, `Gaps`, `Relevant paths or sections`, and `Inherit / avoid`.
```

---

## Fix 10: Add artifact output guidance after "Non-negotiable rules" (F-12)

Add a new section after "Non-negotiable rules":

```markdown
## Artifact output

Intermediate artifacts (workspace scan, comparison table, success criteria) appear in conversation output as they are produced. Persistent artifacts (`skills.markdown`, final SKILL.md, reference files) are written to disk in the target skill directory.
```

---

## Fix 11: Step 7 — Split checklist routing (F-13)

**Before:**
```markdown
- Read `references/checklists/master-checklist.md` for the full quality checklist.
```

**After:**
```markdown
- During drafting, focus on the key constraints: SKILL.md under 500 lines, every reference file routed, description follows the formula. Run the full `references/checklists/master-checklist.md` audit in Step 9.
```

---

## Fix 12: Step 8 — Add creation vs. revision conditional (F-14)

**Before:**
```markdown
- **Trigger tests:** Write 5+ should-trigger queries and 5+ should-NOT-trigger queries. Run each one by pasting it as a new message in Claude.ai (with only this skill enabled) or Claude Code, and record whether the skill loaded. See `references/authoring/testing-methodology.md` for the full testing guide.
```

**After:**
```markdown
- **Trigger tests:** Write 5+ should-trigger queries and 5+ should-NOT-trigger queries. For revisions, run each one by pasting it as a new message in Claude.ai (with only this skill enabled) or Claude Code, and record whether the skill loaded. For new skills, verify the description against your test queries manually; run live trigger tests after installation. See `references/authoring/testing-methodology.md` for the full testing guide.
```

---

## Fix 13: Step 9 — Add routing verification command (F-15)

Add after the existing Final checks list:

```markdown
Quick routing verification:

```bash
# Check for orphaned reference files (not mentioned in SKILL.md)
for f in references/**/*.md; do grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"; done
```
```

---

## Fix 14: Output contract — Add timing hints (F-18)

**Before:**
```markdown
1. workspace scan summary
2. skill type classification (Document/Asset, Workflow, MCP Enhancement)
3. research summary with `skills.markdown` or an explicit reason research was not required
4. markdown comparison table (required for the full research path)
```

**After:**
```markdown
1. workspace scan summary (after Step 3)
2. skill type classification (after Step 2)
3. research summary with `skills.markdown` or an explicit reason research was not required (after Step 4)
4. markdown comparison table (after Step 5 — present before starting synthesis)
```

---

## Fix 15: "Do this, not that" — reposition key warnings (F-17)

Move the most critical "do this, not that" entries inline as one-line warnings in Steps 3, 4a, and 5 where the mistakes actually happen. Keep the summary table at its current location as a reference.

This is handled by the inline additions in Fixes 7, 8, 9 above.

---

## Estimated final line count

Starting: ~285 lines
Additions: ~35 lines
Removals: ~5 lines
**Final: ~315 lines** (well under 500-line limit)
