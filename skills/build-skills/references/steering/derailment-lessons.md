# Derailment Lessons — build-skills

Patterns discovered through systematic derailment testing of the build-skills workflow. Each trap below was triggered at least once during real execution and caused measurable friction (wasted steps, wrong output, or recovery effort).

## How to use this file

Read this file at the start of any skill build or revision. Skim the trap titles — if any match your current situation, read the full entry. After completing your build, check the "Post-build audit" section at the end.

---

## Trap 1: Reference overload (Steps 3–4a)

**What happens:** The agent loads all 22+ reference files at once, exhausting context and losing track of which file informed which decision.

**Fix:** Use the reference routing table in SKILL.md. Load only the 3–5 files relevant to your current step. If you need more, load them in the next step.

**Signal you're in this trap:** You've read more than 5 reference files before starting Step 4.

---

## Trap 2: Output location ambiguity

**What happens:** The output contract lists what to produce but not when. The agent batches all output to the end, making intermediate review impossible.

**Fix:** Show each artifact at the step that produces it. The output contract now includes timing hints (e.g., "after Step 2").

**Signal you're in this trap:** You reach Step 7 without having shown any output.

---

## Trap 3: Tool prerequisite assumptions

**What happens:** The skill mentions `skill-dl` but the agent assumes it's installed. First use fails, requiring backtracking.

**Fix:** Run `skill-dl --version` before first use. If missing, check `references/remote-sources.md` for installation. If installation isn't possible, use the MCP fallback tools or manual GitHub search.

**Signal you're in this trap:** A tool command fails with "command not found."

---

## Trap 4: Downloaded skill quality blindness

**What happens:** Downloaded skills are treated as high-quality references when many violate the standards this skill enforces (>500 lines, no references directory, templates inline).

**Fix:** Evaluate every downloaded skill against `references/research/source-verification.md` quality criteria before using it as a positive reference. Quality problems are valid "avoid" column entries.

**Signal you're in this trap:** Your comparison table has no "avoid" entries.

---

## Trap 5: Creation vs. revision path confusion

**What happens:** Test instructions are written assuming one path (usually creation) but the actual task is the other. Trigger tests fail silently for new skills because the skill isn't installed.

**Fix:** Distinguish paths explicitly:
- **New skill:** Install draft to `~/.claude/skills/[name]/` before trigger testing.
- **Revision:** Test against the currently installed version.

**Signal you're in this trap:** All trigger tests "pass" but you didn't install the skill first.

---

## Trap 6: Skip rationale missing

**What happens:** Steps 4–6 are skipped for local-only work but the agent doesn't explain why, making the output look incomplete.

**Fix:** When skipping steps, state the reason: "Steps 4–6 skipped because this is local-only work that doesn't need research artifacts."

**Signal you're in this trap:** Your output jumps from Step 3 to Step 7 without explanation.

---

## Trap 7: Comparison table fabrication

**What happens:** The agent skims downloaded skills (reading titles and match counts) and fabricates comparison entries from memory instead of reading actual content.

**Fix:** For each downloaded skill: read its SKILL.md fully, run `tree` on its `references/`, read the 2–3 most relevant reference files. Only then write the comparison row.

**Signal you're in this trap:** Comparison table entries lack specific file references or line counts.

---

## Trap 8: Orphan files in references

**What happens:** Reference files exist but aren't routed from SKILL.md, so they're never loaded.

**Fix:** Run the routing verification command from the final checks:
```bash
for f in $(find references -name '*.md' -type f); do
  grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"
done
```

**Signal you're in this trap:** The verification command outputs file names.

---

## Trap 9: Frontmatter validation gaps

**What happens:** Description contains `<` or `>` characters, name doesn't match directory, or description exceeds 1024 characters.

**Fix:** Check all three before finalizing:
1. `echo ${#description}` — must be under 1024
2. No angle brackets in frontmatter values
3. Directory name matches frontmatter `name`

**Signal you're in this trap:** Skill upload fails with a cryptic error.

---

## Trap 10: Reference file bloat

**What happens:** Reference files grow beyond 500 lines because content is appended without checking current size.

**Fix:** Before adding content to any reference file, check `wc -l`. If adding your content would exceed 500 lines, split into a new file and add routing.

**Signal you're in this trap:** `find references -name '*.md' -exec wc -l {} + | sort -rn | head -5` shows files over 500 lines.

---

## Trap 11: Checklist used as linear workflow

**What happens:** The master checklist is treated as a sequential todo list instead of a quality gate. Agent works through all 100+ items even for simple revisions.

**Fix:** Use phase markers on checklist headings:
- Phases 0–3 items are "DRAFT ESSENTIAL" — always check these.
- Phases 4+ items are "FINAL AUDIT ONLY" — only for comprehensive quality passes.

**Signal you're in this trap:** You're running checklist items before having a draft.

---

## Trap 12: Research without scoping

**What happens:** Research expands indefinitely — agent downloads 20+ skills and reads all of them without a clear stopping criterion.

**Fix:** Set a research budget before starting:
- Download at most 10 candidates
- Read at most 5 in detail
- Spend at most 30 minutes on research
- Stop when you have 3+ viable comparison entries

**Signal you're in this trap:** You've downloaded more than 10 skills or spent more than 3 steps on research alone.

---

## Post-build audit

After completing your skill build or revision, check these:

1. **Output completeness:** Did you show artifacts at the steps that produced them?
2. **Skip documentation:** Did you explain every skipped step?
3. **Tool verification:** Did you verify prerequisites before using tools?
4. **Quality assessment:** Did your comparison include "avoid" entries?
5. **Test path clarity:** Did you distinguish creation vs. revision in testing?
6. **File sizes:** Are all files under 500 lines?
7. **Routing completeness:** Does every reference file appear in SKILL.md routing?

If any answer is "no," address it before finalizing.
