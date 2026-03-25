---
name: enhance-skill-by-derailment
description: Use skill if you are testing a skill's instructional quality by following its workflow literally on a real task, identifying root causes of friction, and fixing the skill's SKILL.md and references/ directly.
---

# Enhance Skill by Derailment Testing

Test any skill's instructions by following them literally on a real task. When you derail — when the instructions fail to guide the next action — identify the root cause (missing instruction, wrong instruction, missing reference) and fix the skill's source files directly. No synthetic report files. The fixes are the deliverable.

## Trigger boundary

Use this skill when:

- testing whether a skill's instructions are complete and unambiguous
- auditing a skill for instructional quality before publishing
- improving a skill after receiving feedback that it's confusing or incomplete
- dogfooding a skill by running its workflow on a real task
- validating that fixes to a skill actually resolved the original friction

Do not use this skill for:

- building a new skill from scratch (use `build-skills`)
- evaluating the quality of a skill's *output* (use evaluation suites)
- reviewing code changes in a pull request (use `review-pr`)
- general documentation improvements not related to skill instructions

## Non-negotiable rules

1. **Follow literally, not intelligently.** Suppress domain knowledge. If the instructions don't specify it, that's a friction point — even if you "know" the answer.
2. **Test on a real task.** Toy examples don't exercise branching logic or error handling. The task must be genuine and non-trivial.
3. **Fix the skill, not the executor.** Every remedy is an edit to the skill's `SKILL.md` or `references/` files. Never "use a smarter agent."
4. **No synthetic note files.** Do not create `derail-notes/`, errata files, or report documents. Track friction points in your working memory during the test. The only files you write are edits to the skill itself.
5. **Only write inside the skill directory.** Edits go to `SKILL.md` and files under `references/`. Never create files outside the skill's folder.
6. **Verify after fixing.** Run grep-based consistency checks and confirm routing integrity after edits.

## Required workflow

### 1. Select the test subject and task

Choose:
- **The skill to test** — any skill with a SKILL.md and optional references
- **The test task** — a real, representative task within the skill's trigger boundary

The test task must be genuinely within scope, complex enough to exercise the full workflow, and executable in the current environment.

### 2. Pre-scan the skill

Before executing, read through the skill once:

- Read SKILL.md fully — note total steps, branching points, cross-references
- Tree the `references/` directory
- List external dependencies (tools, MCP servers, APIs)
- Note the skill's declared trigger boundary

Do NOT execute anything during this step. This is orientation only.

### 3. Execute literally and identify friction

For each step in the skill's workflow:

1. **Read only the current step.** Do not look ahead.
2. **Attempt to execute** using only the information provided in the skill.
3. **When you derail** — when you cannot determine the next action from the instructions alone — immediately diagnose why:

| What went wrong | Root cause type | Fix approach |
|---|---|---|
| Instruction is missing entirely | Missing instruction block | Add the missing section/paragraph to SKILL.md |
| Instruction exists but is wrong or misleading | Wrong instruction | Rewrite the specific text in-place |
| Instruction is vague or ambiguous | Ambiguous threshold (M1) | Add concrete examples, thresholds, or decision criteria |
| Required context is in a reference doc but not linked | Missing cross-reference (S3) | Add a "Read `references/...`" pointer at the point of use |
| Required context doesn't exist in any reference doc | Missing reference doc | Create a new file in `references/` and route it from SKILL.md |
| A prerequisite (tool, config, dependency) isn't declared | Missing prerequisite (S1) | Add to Prerequisites section |
| Two documents contradict each other | Contradictory paths (S2) | Reconcile in one place, remove the contradiction |

See `references/root-cause-taxonomy.md` for the full taxonomy of root causes.
See `references/fix-patterns.md` for proven fix patterns matched to each root cause.

4. **When you succeed but used implicit knowledge** — something not stated in the skill that you happened to know — note it as a lower-severity friction point. Someone else wouldn't have your context.

### 4. Apply fixes as you go

Do not batch fixes for later. When you identify a friction point:

1. **Classify the root cause** using `references/root-cause-taxonomy.md` (S1–S5, M1–M6, O1–O5)
2. **Match it to a fix pattern** from `references/fix-patterns.md`
3. **Apply the fix immediately** to the skill's source files:
   - Edit `SKILL.md` for missing/wrong/ambiguous instructions
   - Edit existing `references/*.md` files for missing context in reference docs
   - Create new `references/*.md` files when a whole topic is undocumented — and add the routing entry to SKILL.md's reference routing table
4. **Keep fixes minimal** — add only what was missing, don't rewrite surrounding text

Priority order if you have many friction points: P0 (blocks progress) first, then P1 (causes confusion), then P2 (minor annoyance).

See `references/friction-classification.md` for severity assignment rules.

### 5. Verify fixes

After all edits:

1. **Routing integrity** — every reference file is reachable from SKILL.md

```bash
find skills/[skill-name]/references -type f -name "*.md" | while read f; do
  basename_no_ext=$(basename "$f" .md)
  grep -q "$basename_no_ext" skills/[skill-name]/SKILL.md || echo "ORPHAN: $f"
done
```

2. **No contradictions** — grep for stale terms that should have been updated
3. **Size constraint** — SKILL.md still under 500 lines: `wc -l skills/[skill-name]/SKILL.md`
4. **No regressions** — fixes didn't introduce new ambiguities

## Output contract

Deliver to the user (in conversation, not in files):

1. **Friction summary** — brief list of what derailed and why (F-01, F-02, etc. with root cause codes)
2. **What worked well** — steps that were unambiguous and executable
3. **Fixes applied** — which file was edited, which friction point it addresses
4. **Verification results** — routing integrity check, line count

This summary is conversational output only — do not write it to a file.

## Decision rules

- If the skill has no references, test only SKILL.md steps
- If a derailment is a bug in an external tool (not the instructions), note it but tag as `external` — don't fix the skill for someone else's bug
- If 3+ P1 items cluster in one step, treat the cluster as compound P0
- If the skill references other skills, test only the current skill's instructions — not the referenced skill's workflow
- If you discover the skill's trigger boundary is wrong, fix it directly in the `description` frontmatter and trigger boundary section

## Do this, not that

| Do this | Not that |
|---|---|
| Follow each step literally as written | Fill in gaps from personal knowledge |
| Fix the source files directly as you find friction | Batch all fixes for a later "apply" phase |
| Edit SKILL.md and references/ only | Create derailment-notes/, errata, or report files |
| Create new reference docs in `references/` when needed | Write standalone docs outside the skill directory |
| Keep fixes minimal — add what's missing | Rewrite entire sections that were working fine |
| Report friction summary in conversation | Write synthetic report documents to disk |
| Describe what was wrong and what you fixed | Label output as "derailment notes" — just explain the friction plainly |
| Verify fixes with grep and routing checks | Assume fixes are correct without verification |

## Reference routing

| File | Read when |
|---|---|
| `references/friction-classification.md` | Assigning severity (P0/P1/P2) to a friction point or choosing between severity levels |
| `references/root-cause-taxonomy.md` | Tagging friction points with root cause codes for pattern analysis |
| `references/fix-patterns.md` | Matching a derailment type to a proven fix pattern |
| `references/metrics-and-iteration.md` | Tracking improvement across multiple test runs or building cross-run reports |
| `references/adaptation-domains.md` | Applying Derailment Testing to non-skill instruction sets (runbooks, SOPs, API docs) |

## Guardrails

- Do not skip the pre-scan. It prevents misidentifying "working as designed" as a derailment.
- Do not fix friction points without reading the root cause taxonomy. Fixes without root cause analysis recur.
- Do not create files outside the skill's directory. No `derail-notes/`, no errata files, no report docs.
- Do not re-test with the same task. Use a different representative task for each run.
- Do not test a skill you are currently building. Build it first (with `build-skills`), then test it.

## Final checks

Before declaring the test complete:

- [ ] All P0 fixes are applied to the skill's source files
- [ ] All P1 fixes are applied (or deferred with justification)
- [ ] No files were created outside the skill's directory
- [ ] Verification grep shows zero stale terms
- [ ] Routing integrity confirmed — no orphaned reference files
- [ ] SKILL.md of tested skill is still under 500 lines after fixes
- [ ] Friction summary delivered in conversation (not written to disk)
- [ ] If a `derailment-notes/` or `derail-notes/` folder exists from prior runs, delete it — those artifacts are obsolete
