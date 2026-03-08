---
name: skill-builder
description: Use skill if you are creating or redesigning a Claude skill and need workspace-first evidence, remote skill research, and comparison before drafting.
---

# Skill Builder

Build or revise Claude skills from evidence, not instinct.

## Core rule

Inspect the current workspace first.

For new skills, major redesigns, or multi-source merges, research similar remote skills before drafting.
Show `skills.markdown` and a comparison table before you synthesize the final result.

## Default workflow

1. **Classify the job before drafting.**
   - Decide whether this is new-skill creation, substantial redesign, or a small local cleanup.
   - Use the lightest workflow that still preserves evidence quality.

2. **Inspect the local workspace first.**
   - Run `tree` on the current working directory, or produce an equivalent tree-style listing if `tree` is unavailable.
   - Read the files that define the current workflow, constraints, references, and examples.
   - Treat this as the local evidence set.

3. **Escalate to remote research when the task is non-trivial.**
   - Remote research is mandatory for new skills, meaningful redesigns, or any task that combines patterns from multiple sources.
   - Remote research is optional only for small, local-only fixes where outside comparison would not change the outcome.
   - Read `references/research-workflow.md` before running this phase.

4. **Produce a research artifact before synthesis.**
   - Search remote skill ecosystems.
   - Select high-signal candidates instead of collecting near-duplicates.
   - Inspect the downloaded corpus as first-class evidence.
   - Emit `skills.markdown` so the research phase is visible and reusable.

5. **Compare before combining.**
   - Build a markdown table before proposing the design.
   - Include source, focus, strengths, gaps, relevant paths or sections, and inherit-or-avoid decisions.
   - Read `references/comparison-workflow.md` for the comparison sequence and required columns.

6. **Synthesize an original result.**
   - Separate evidence, comparison, selection, and generation.
   - Distill patterns. Do not clone an existing `SKILL.md` and rename it.
   - If the target repo has local conventions, fit the output to those conventions exactly.

7. **Keep the result lean.**
   - Put trigger language, workflow, decision rules, and reference routing in `SKILL.md`.
   - Push bulky detail into `references/`.
   - Add scripts, assets, or extra docs only when they are clearly required by the target repo or workflow.
   - If contributing to a curated pack, remove unnecessary clutter before finishing.

8. **Finish with a repo-fit check.**
   - Confirm canonical naming across directory, frontmatter, README labels, and cross-skill references.
   - Confirm every file in `references/` is explicitly routed from `SKILL.md`.
   - Confirm the final skill matches the target repo’s style and does not ship dead weight.

## Output contract

Unless the user explicitly wants a different format, show work in this order:

1. workspace scan summary
2. research summary with `skills.markdown`
3. markdown comparison table
4. synthesis strategy
5. generated or revised skill artifacts
6. final fit and cleanup checks

## Reference files

Load only the files needed for the task.

| File | When to read |
|---|---|
| `references/research-workflow.md` | Read when creating a new skill, redesigning an existing one, or deciding whether remote research is mandatory. |
| `references/remote-sources.md` | Read when searching Playbooks-style directories, selecting remote skills, or treating downloaded examples as evidence. |
| `references/comparison-workflow.md` | Read when building the markdown comparison table or separating evidence, selection, and synthesis. |
| `references/source-patterns.md` | Read when deciding what to inherit from earlier skill-builder patterns and what to leave out to keep the new result lean. |

## Guardrails

- Do not draft the final skill before reading the current workspace.
- Do not claim research happened unless `skills.markdown` exists.
- Do not compare sources mentally and hide the table.
- Do not copy a source skill wholesale.
- Do not add unreferenced files to `references/`.
- Do not keep packaging helpers, assets, or README clutter unless the target repo genuinely needs them.
