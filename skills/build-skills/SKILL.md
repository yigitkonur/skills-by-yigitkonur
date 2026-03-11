---
name: build-skills
description: Use skill if you are creating or substantially revising a Claude skill and need workspace-first evidence, remote comparison, and repo-fit synthesis before writing SKILL.md.
---

# Build Skills

Build or revise Claude skills from evidence, not instinct.

## Trigger boundary

Use this skill when the task is about:

- creating a new Claude skill from scratch
- substantially redesigning an existing skill
- merging patterns from multiple skills or source corpora
- tightening a skill's triggers, workflow, routing, or guardrails without drifting from repo conventions

Do not use this skill for:

- tiny wording or formatting cleanups where outside evidence would not change the result
- general repo documentation work that is not about a Claude skill
- copying a remote skill into the workspace with minor renaming

## Non-negotiable rules

1. **Workspace first.** Inspect the current workspace before searching remotely or drafting anything.
2. **Research before synthesis for non-trivial work.** New skills, major redesigns, multi-source merges, thin local evidence, or explicit comparison requests require remote research.
3. **`skills.markdown` is the proof of research.** If non-trivial research happened, the artifact must exist before synthesis.
4. **Comparison before combination.** Build the comparison table before proposing the design.
5. **Original, repo-fit output only.** Distill patterns; do not rename-clone a source skill.
6. **Keep progressive disclosure clean.** Put trigger logic in frontmatter, workflow and decisions in `SKILL.md`, and bulky detail in `references/`.
7. **Test before shipping.** Run trigger tests and at least one functional test before declaring done.

## Required workflow

### 1. Classify the job

- **Local-only path:** a small cleanup where triggers, structure, and core method stay intact.
- **Full research path:** a new skill, substantial redesign, multi-source merge, thin or stale workspace, or an explicit request for outside comparison.

### 2. Classify the skill type

Before designing, identify the skill's category:

| Category | Description | Key technique |
|---|---|---|
| **Document/Asset creation** | Creates consistent output (docs, code, designs) using Claude's built-in capabilities | Embedded style guides, quality checklists, templates |
| **Workflow automation** | Multi-step processes with consistent methodology | Step-by-step workflow with validation gates, iterative refinement |
| **MCP enhancement** | Workflow guidance on top of an MCP server's tool access | MCP call sequencing, domain expertise, error handling for API calls |

Read `references/patterns/workflow-patterns.md` to choose the right structural pattern.
If the skill enhances an MCP, also read `references/patterns/mcp-enhancement.md`.

### 3. Capture local evidence first

- Produce a tree-style inventory of the target workspace.
- Read the current `SKILL.md` and the local files that define the workflow, references, and constraints.
- Note repo conventions, existing reference coverage, and obvious gaps before widening scope.

### 4. Run remote research when the job is non-trivial

- Read `references/research-workflow.md`.
- Use `references/remote-sources.md` and/or `references/skill-research.sh` to gather a small, high-signal corpus.
- Prefer a few diverse, relevant sources over many near-duplicates.
- Emit `skills.markdown` before moving on.

### 5. Compare before synthesizing

- Read the selected local and remote sources that actually matter.
- Build a markdown comparison table with at least: `Source`, `Focus`, `Strengths`, `Gaps`, `Relevant paths or sections`, and `Inherit / avoid`.
- Every row ends with a decision, not just an observation.

### 6. Define success criteria

Before drafting, write down what success looks like:

- **Trigger accuracy**: 90%+ of relevant queries should fire the skill; 0% of unrelated queries
- **Execution quality**: workflow completes without user correction
- **Token efficiency**: SKILL.md under 500 lines, references loaded only when needed

### 7. Synthesize the repo-fit result

- Rewrite for the current repo and task.
- Keep `SKILL.md` lean: trigger boundary, workflow, decision rules, output contract, guardrails, and reference routing.
- Reuse existing references instead of duplicating them.
- Add new files only when clearly necessary and explicitly routed.
- Read `references/authoring/description-engineering.md` to craft the description field.
- Read `references/checklists/master-checklist.md` for the full quality checklist.

### 8. Test the skill

- Run 5+ should-trigger queries and 5+ should-NOT-trigger queries.
- Run at least one complete functional test of the primary workflow.
- Ask Claude "When would you use [skill-name]?" and verify the answer matches intent.
- Read `references/authoring/testing-methodology.md` for the full testing guide.

### 9. Finish with repo-fit and cleanup checks

- Confirm directory name, frontmatter `name`, and canonical labels stay aligned.
- Confirm every file in `references/` is explicitly routed from `SKILL.md`.
- Confirm the result feels synthesized from evidence, not copied from the most detailed source.
- Confirm no `<` or `>` in frontmatter, no reserved names ("claude", "anthropic").
- If a shared repo issue blocks a clean result, report it instead of editing shared files by default.

## Decision rules

- If outside research would materially change the answer, do not stay local.
- If the local workspace already contains the needed detail, route to that file instead of rewriting it.
- If two sources conflict, prefer the pattern that is clearer, leaner, and more compatible with the target repo.
- Prefer patterns that improve agent decisions. Reject bulk that adds machinery without improving the outcome.
- If the draft starts resembling one source too closely, stop and convert the source notes into inherit/avoid decisions before rewriting.
- If the skill grows because of examples, templates, or long checklists, move that detail to references or cut it.
- If remote research is skipped, say why it was safe to skip.
- If the skill enhances an MCP, verify tool names against the MCP server documentation before shipping.
- If the description is broad enough to fire on unrelated queries, add negative triggers.

## Do this, not that

| Do this | Not that |
|---|---|
| inventory the workspace and read local source files first | start from remote search results or a remembered template |
| emit `skills.markdown` for non-trivial research | claim research happened because you skimmed URLs |
| build a comparison table before drafting | mentally blend sources and jump to the final `SKILL.md` |
| route detailed guidance to existing references | stuff `SKILL.md` with tutorials, examples, or duplicated checklists |
| inherit patterns selectively with repo-fit reasoning | copy the most detailed source and rename it |
| define success criteria before drafting | ship without any trigger or functional tests |
| add negative triggers when scope is broad | let the skill fire on every tangentially related query |
| use validation scripts for deterministic checks | rely on prose like "validate properly" |

## Output contract

Unless the user wants a different format, show work in this order:

1. workspace scan summary
2. skill type classification (Document/Asset, Workflow, MCP Enhancement)
3. research summary with `skills.markdown` or an explicit reason research was not required
4. markdown comparison table (required for the full research path)
5. selection and synthesis strategy
6. generated or revised skill artifacts
7. trigger test results
8. final repo-fit and cleanup checks

## Reference routing

Load the smallest relevant set for the branch of work you are in.

### Authoring

| File | Read when |
|---|---|
| `references/authoring/skillmd-format.md` | Writing or validating frontmatter, body structure, or progressive-disclosure fit. |
| `references/authoring/description-engineering.md` | Crafting or improving the description field, trigger phrases, or negative triggers. |
| `references/authoring/decision-tree-patterns.md` | Designing branch logic, routing labels, or decision-tree structure. |
| `references/authoring/reference-file-structure.md` | Deciding what belongs in `SKILL.md` versus `references/`, or reorganizing reference layout. |
| `references/authoring/testing-methodology.md` | Planning or running trigger tests, functional tests, or performance comparisons. |

### Patterns

| File | Read when |
|---|---|
| `references/patterns/skill-organization.md` | Deciding whether to split, combine, or trim scope of a skill. |
| `references/patterns/naming-conventions.md` | Checking names, labels, file paths, and repo-native naming fit. |
| `references/patterns/workflow-patterns.md` | Choosing the right structural pattern (Sequential, Multi-MCP, Iterative, Context-aware, Domain). |
| `references/patterns/mcp-enhancement.md` | Designing a skill that enhances an existing MCP server integration. |

### Research

| File | Read when |
|---|---|
| `references/research-workflow.md` | Deciding whether remote research is mandatory or running the non-trivial research path. |
| `references/remote-sources.md` | Searching remote skill sources, selecting candidates, or downloading a research corpus. |
| `references/skill-research.sh` | Running end-to-end parallel discovery and download in one command. |
| `references/comparison-workflow.md` | Building the comparison table or separating evidence, comparison, selection, and generation. |
| `references/source-patterns.md` | Choosing what to inherit, simplify, or avoid from earlier skill patterns. |
| `references/research/source-verification.md` | Filtering low-signal sources, assessing trust, or justifying candidate selection. |
| `references/research/fact-checking.md` | Verifying claims, commands, or ecosystem details before they influence the new skill. |

### Quality and examples

| File | Read when |
|---|---|
| `references/checklists/master-checklist.md` | Running the full 90+ item quality checklist before shipping. |
| `references/examples/annotated-examples.md` | Studying strong structural patterns from real skills without copying them. |
| `references/examples/anti-patterns.md` | Auditing for bloat, overlap, weak triggers, copied structure, or missing tests. |

### Iteration and troubleshooting

| File | Read when |
|---|---|
| `references/iteration/feedback-signals.md` | Interpreting under/over-triggering signals or planning post-ship iteration. |
| `references/iteration/troubleshooting.md` | Diagnosing upload failures, trigger issues, MCP problems, or instruction-following issues. |

### Distribution

| File | Read when |
|---|---|
| `references/distribution/publishing.md` | Publishing, packaging, API distribution, or community-distribution concerns. |

## Guardrails and recovery

- Do not draft the final skill before reading the current workspace.
- Do not say research is complete unless `skills.markdown` exists for the non-trivial path.
- Do not hide the comparison table inside prose or skip it because sources "look similar."
- Do not copy a source skill wholesale, even as a temporary scaffold.
- Do not add files to `references/` unless they are needed and routed.
- Do not ship without running at least basic trigger tests.
- Do not use `<` or `>` in any frontmatter field.
- Do not use "claude" or "anthropic" in the skill name.

Recovery moves:

- **Local evidence is thin or contradictory:** say so, then widen the evidence set before drafting.
- **Research corpus is noisy:** cut it down to the few sources you can actually compare well.
- **Draft is bloating:** move detail to existing references or delete it.
- **Triggers are misfiring:** read `references/authoring/description-engineering.md` and fix.
- **MCP calls failing:** read `references/iteration/troubleshooting.md` for diagnosis.
- **Repo-fit conflict touches shared files:** report the shared issue instead of editing outside the target skill by default.

## Final checks

Before you finish, confirm all of the following:

- [ ] frontmatter `name` matches the directory name exactly
- [ ] `name` does not contain "claude" or "anthropic"
- [ ] description follows the formula: what + when + trigger phrases
- [ ] description is under 1024 characters with no `<` or `>`
- [ ] `SKILL.md` body is under 500 lines
- [ ] `SKILL.md` contains decisions and routing, not bulky reference content
- [ ] every reference file is explicitly routed
- [ ] no orphaned files in `references/`
- [ ] the final result is clearly synthesized from evidence and comparison
- [ ] no dead weight was added just because another skill had it
- [ ] at least 3 trigger tests passed (should-trigger and should-NOT-trigger)
- [ ] primary workflow completes without error in at least one test
- [ ] for full quality: ran `references/checklists/master-checklist.md`
