---
name: build-skill
description: "Use if creating, redesigning, or merging a Claude skill, with research before writing SKILL.md."
---

# Synthesize Skills

Build or revise Claude skills from evidence — workspace scan, remote comparison, repo-fit synthesis. Comparison table is the proof of research.

## When to use

Use this skill if you are:

- *creating a new Claude skill from scratch* ("make me a skill for X", "scaffold a new skill", "I want a skill that does Y")
- *substantially redesigning an existing skill* ("rewrite this skill", "this skill is bloated, fix the structure")
- *merging multiple skills or source corpora into one* ("combine these into one skill", "synthesize patterns from these three skills")
- *researching skill patterns before authoring* ("find skills like X first", "I need a comparison table before I write")
- *tightening a skill's triggers, decision tree, routing, or workflow without drifting from repo conventions*
- *fixing a skill where the body bloated past 500 lines, references go unrouted, or the description never fires*

Do NOT use this skill for:

- *testing whether an existing skill holds up under a real agent run* — use `audit-skill-by-derailment` instead
- *the upstream skill-creator plugin's eval / benchmark / iterate loop* — that toolchain runs separate `evals/`, graders, and viewers; this repo bans `evals/` and uses a different lean format
- *tiny wording, formatting, or typo cleanups* where outside evidence wouldn't change the result
- *renaming or copying a remote skill into the workspace with minor edits* — that's a clone, not synthesis

## Non-negotiable rules

1. **Workspace first.** Inspect the workspace before searching remotely or drafting anything.
2. **Research before synthesis for non-trivial work.** New skills, major redesigns, multi-source merges, thin local evidence, or explicit comparison requests require remote research.
3. **The comparison table is the proof of research.** If non-trivial research happened, the table appears in output before synthesis.
4. **Comparison before combination.** Build the table before proposing the design.
5. **Original, repo-fit output only.** Distill patterns; do not rename-clone a source skill.
6. **Progressive disclosure.** Trigger logic in frontmatter, workflow and decisions in `SKILL.md`, bulky detail in `references/`.
7. **Test before shipping.** Run trigger tests and at least one functional test before declaring done.

## Available scripts

Scripts live at the skill root. Pure bash — `bash`, `git`, `curl`, `npx` (Node.js). No install, no proxy keys.

- **`scripts/skill-dl`** — discovery & download. Searches via `npx skills find` (primary, no key); layers Serper Google results on `playbooks.com` if `SERPER_API_KEY` is set. Downloads via `git clone --depth 1`. Run `bash scripts/skill-dl --help`.
- **`scripts/skill-research.sh`** — end-to-end discovery → download → corpus inspection wrapper around `skill-dl`. Run `bash scripts/skill-research.sh --help`.

Optional Serper key (broader recall):

```bash
export SERPER_API_KEY=your_serper_key   # optional; without it, npx-only
bash scripts/skill-dl search typescript mcp server --top 20
```

When asking the user, frame the choice as: "search via npx skills only (default), or also enable Serper if you have a key?"

## Workflow

### 1. Classify the job

- **Local-only path:** small cleanup where triggers, structure, and core method stay intact. Examples: typo fixes, reordering sections, tightening one trigger phrase, version bumps.
- **Full research path:** new skill, substantial redesign, multi-source merge, thin or stale workspace, or explicit "compare against X" request. Examples: adding a new workflow branch, rewriting the decision tree, changing skill category, merging two skills, anything that alters *what* the skill does.

Rule of thumb: if the change would alter the comparison table you'd build for this skill, it's the full research path.

### 2. Classify the skill type

| Category | Description | Key technique |
|---|---|---|
| **Document/Asset creation** | Creates consistent output (docs, code, designs) using Claude's built-in capabilities | Embedded style guides, quality checklists, templates |
| **Workflow automation** | Multi-step processes with consistent methodology | Step-by-step workflow with validation gates, iterative refinement |
| **MCP enhancement** | Workflow guidance on top of an MCP server's tool access | MCP call sequencing, domain expertise, error handling for API calls |

Read `references/patterns/workflow-patterns.md` to choose the structural pattern. If the skill enhances an MCP, also read `references/patterns/mcp-enhancement.md`.

### 3. Capture local evidence first

- Tree-style inventory of the target workspace.
- Revision: read the current `SKILL.md` fully — trigger boundary, workflow, decision rules, output contract, guardrails.
- Creation: read the closest 1–2 local skills plus the naming/format references before drafting so you inherit repo conventions.
- Read every relevant file in `references/`: open it, note what it covers and where it has gaps.
- Note reference naming scheme, nesting depth, and whether routing in `SKILL.md` matches what's on disk.

> Loading discipline: load 3–5 relevant reference files per step, not all 22. See `references/authoring/reference-file-structure.md`.

### 4. Run remote research (full research path only)

Skip to step 7 for local-only work.

> Tip: downloaded skills frequently violate this skill's own quality standards (line counts >1000, templates inline, no references). Treat quality problems as signal for the "avoid" column — see `references/research/source-verification.md`.

- Read `references/research-workflow.md` for the full protocol.
- Verify tools: `bash scripts/skill-dl --where`. Depends on `bash`, `git`, `curl`, `npx`. If `npx` missing, install Node.js, or fall back to `skills-as-context-search-skills` / `skills-as-context-get-skill-details` MCP tools, or a manual GitHub `filename:SKILL.md` search.
- Discover: `bash scripts/skill-dl search mcp server typescript sdk --top 20` (3–20 keywords, prioritized markdown table to stdout).
- Download: `bash scripts/skill-dl <url-or-list>`, or run `bash scripts/skill-research.sh "kw1,kw2,kw3"` for parallel end-to-end.
- See `references/remote-sources.md` for `skill-dl` usage patterns.
- Prefer a few diverse, relevant sources over many near-duplicates.
- Show the source shortlist inline — what was downloaded, what made the shortlist, why — before Step 4a.

### 4a. Read the downloaded corpus thoroughly

Reading is a distinct, mandatory step — do not jump from download to comparison.

For each shortlisted skill:

- **Read its `SKILL.md` fully** — not just headings. Capture trigger boundary, workflow structure, decision rules, output contract.
- **Tree its `references/`** — file names, nesting depth. This reveals structural philosophy.
- **Read the 2–3 most relevant reference files** in full.
- **Check `scripts/`** if present — automation patterns prose can't convey.
- **Capture per-skill notes** (heading per skill mapping to comparison columns): structure, workflow style, reference organization, what it does well/poorly, 1–2 inheritable patterns with exact relative paths.

Downloaded sources may not follow this skill's quality standards (e.g., SKILL.md over 500 lines, missing routing). Note these — they inform the "avoid" column.

The notes here are the raw material for Step 5. Skip reading and the comparison table is fabricated from memory.

### 5. Compare before synthesizing

- Build a markdown table with at least: `Source`, `Focus`, `Strengths`, `Gaps`, `Relevant paths or sections`, `Inherit / avoid`.
- Every row ends with a decision, not just an observation.

### 6. Define success criteria

Before drafting:

- **Trigger accuracy**: 90%+ of relevant queries fire the skill; 0% of unrelated queries.
- **Execution quality**: workflow completes without user correction.
- **Token efficiency**: SKILL.md under 500 lines, references loaded only when needed.

### 7. Synthesize the repo-fit result

- Rewrite for the current repo and task.
- Default final path: `skills/<skill-name>/`. If staged elsewhere, move the entire folder before declaring done.
- Keep `SKILL.md` lean: trigger boundary, workflow, decision rules, output contract, guardrails, routing.
- Reuse existing references; do not duplicate them.
- Add new files only when clearly necessary and explicitly routed.
- Read `references/authoring/description-engineering.md` to craft the description field.
- Drafting focuses on three constraints: SKILL.md <500 lines, every reference routed, description follows the formula. Run the full `references/checklists/master-checklist.md` review in Step 9.

### 8. Test the skill

- **Trigger tests:** Write 5+ should-trigger and 5+ should-NOT-trigger queries. Revisions: paste each as a new message in Claude.ai (skill enabled in isolation) or Claude Code, record fire/no-fire. New skills: verify description against test queries manually; live trigger tests after install. See `references/authoring/testing-methodology.md`.
- **Functional test:** Run at least one complete end-to-end functional pass.
- **Self-check:** Ask Claude "When would you use [skill-name]?" and verify the answer matches intent.
- **RED-GREEN-REFACTOR for discipline skills** (TDD, verification, research-before-synthesis): run a pressure scenario *without* the skill first, capture rationalizations verbatim, re-test with the skill loaded. See `references/authoring/tdd-for-skills.md`.

> Tip: For NEW skills, install the draft to the active runtime's skill directory before testing triggers — trigger tests fail silently if the skill isn't loaded. For REVISIONS, test against the currently installed version. If the runtime forbids writing to the installed skill directory, run manual trigger review plus a functional workflow test, report the installation block explicitly, and don't claim live trigger coverage.

### 9. Finish with repo-fit and cleanup

- Confirm directory name, frontmatter `name`, README label all align.
- Confirm every file in `references/` is explicitly routed from `SKILL.md`.
- Confirm the result is synthesized from evidence, not copied from the most detailed source.
- Confirm no `<` or `>` in frontmatter, no reserved names ("claude", "anthropic").
- Shared repo issue blocks a clean result? Report it instead of editing shared files by default.

## Decision rules

- If outside research would materially change the answer, do not stay local.
- If the workspace already contains the needed detail, route to it instead of rewriting it.
- If two sources conflict, prefer the pattern that is clearer, leaner, more compatible with the target repo.
- Prefer patterns that improve agent decisions. Reject bulk that adds machinery without improving outcomes.
- If the draft starts resembling one source too closely, stop and convert source notes into inherit/avoid decisions before rewriting.
- If the skill grows because of examples, templates, or long checklists, move detail to references or cut it.
- If remote research is skipped, say why it was safe to skip.
- If the skill enhances an MCP, verify tool names against MCP server documentation before shipping.
- If the description is broad enough to fire on unrelated queries, add negative triggers.

## Do this, not that

| Do this | Not that |
|---|---|
| inventory the workspace and read local source files first | start from remote search results or a remembered template |
| capture per-source notes with exact relative paths before the comparison table | claim research happened because you skimmed URLs |
| build a comparison table before drafting | mentally blend sources and jump to the final SKILL.md |
| route detailed guidance to existing references | stuff SKILL.md with tutorials, examples, duplicated checklists |
| inherit patterns selectively with repo-fit reasoning | copy the most detailed source and rename it |
| define success criteria before drafting | ship without trigger or functional tests |
| add negative triggers when scope is broad | let the skill fire on every tangentially related query |
| use validation scripts for deterministic checks | rely on prose like "validate properly" |
| read each shortlisted skill's SKILL.md fully, tree its references/, read 2–3 relevant files | skim titles and match counts, then fabricate from memory |
| verify tool prerequisites (`bash scripts/skill-dl --where`, `command -v npx`) | assume tools are installed because the skill mentions them |
| show intermediate artifacts at the step that produces them | batch all output to the end |
| distinguish creation vs revision in testing | write test instructions that only work for one path |
| for discipline skills, run RED baseline and capture rationalizations verbatim | guess which excuses agents might invent |
| pick freedom level per step (high/medium/low) by what breaks when the agent deviates | write the whole skill in one tone — uniformly strict or uniformly loose |

## Output contract

Show work in this order unless the user specifies a different format:

1. skill type classification (Step 2)
2. workspace scan summary (Step 3)
3. source shortlist + selection rationale, or explicit skip reason (Step 4)
4. markdown comparison table (Step 5, required for full research path)
5. success criteria (Step 6)
6. selection and synthesis strategy (Step 7)
7. generated or revised skill artifacts (Step 7)
8. trigger test results (Step 8)
9. final repo-fit and cleanup checks (Step 9)

## Reference routing

Load the smallest relevant set for the branch you are in.

### Authoring

| File | Read when |
|---|---|
| `references/authoring/skillmd-format.md` | Writing or validating frontmatter, body structure, or progressive-disclosure fit. |
| `references/authoring/description-engineering.md` | Crafting or improving the description field, trigger phrases, or negative triggers. |
| `references/authoring/decision-tree-patterns.md` | Designing branch logic, routing labels, or decision-tree structure. |
| `references/authoring/reference-file-structure.md` | Deciding what belongs in SKILL.md vs references/, or reorganizing reference layout. |
| `references/authoring/testing-methodology.md` | Planning or running trigger tests, functional tests, performance comparisons. |
| `references/authoring/tdd-for-skills.md` | Writing a discipline-enforcing skill — run RED baseline before shipping. |
| `references/authoring/persuasion-principles.md` | Choosing persuasion principles (authority, commitment, scarcity, social proof, unity) when a draft reads too soft or too strict. |
| `references/authoring/degrees-of-freedom.md` | Deciding how prescriptive each step should be — high/medium/low freedom by what breaks when the agent deviates. |

### Patterns

| File | Read when |
|---|---|
| `references/patterns/skill-organization.md` | Deciding whether to split, combine, or trim scope of a skill. |
| `references/patterns/naming-conventions.md` | Checking names, labels, file paths, repo-native naming fit. |
| `references/patterns/workflow-patterns.md` | Choosing the structural pattern (Sequential, Multi-MCP, Iterative, Context-aware, Domain). |
| `references/patterns/mcp-enhancement.md` | Designing a skill that enhances an existing MCP server integration. |

### Research

| File | Read when |
|---|---|
| `references/research-workflow.md` | Deciding whether remote research is mandatory, or running the non-trivial research path. |
| `references/remote-sources.md` | Searching remote skill sources, selecting candidates, downloading a research corpus. |
| `references/comparison-workflow.md` | Building the comparison table or separating evidence, comparison, selection, generation. |
| `references/source-patterns.md` | Choosing what to inherit, simplify, or avoid from earlier skill patterns. |
| `references/research/source-verification.md` | Filtering low-signal sources, assessing trust, justifying candidate selection. |
| `references/research/fact-checking.md` | Verifying claims, commands, ecosystem details before they influence the new skill. |
| `references/research/search-strategies.md` | Formulating diverse search keywords, running multi-round skill discovery with skill-dl. |
| `references/research/corpus-inspection.md` | Inspecting downloaded skills for quality, assessing what to inherit or avoid. |

### Quality and examples

| File | Read when |
|---|---|
| `references/checklists/master-checklist.md` | Running the full 90+ item quality checklist before shipping. |
| `references/examples/annotated-examples.md` | Studying strong structural patterns from real skills without copying them. |
| `references/examples/anti-patterns.md` | Auditing the skill's *content* for bloat, overlap, weak triggers, copied structure, missing tests (AP-1 through AP-24). |
| `references/examples/anti-patterns-authoring.md` | Auditing the *authoring process* for reference overload, output batching, tool assumption, path confusion, discipline-skill failures (AP-25 through AP-34). |

### Iteration and troubleshooting

| File | Read when |
|---|---|
| `references/iteration/feedback-signals.md` | Interpreting under/over-triggering signals or planning post-ship iteration. |
| `references/iteration/troubleshooting.md` | Diagnosing upload failures, trigger issues, MCP problems, instruction-following issues. |

### Distribution

| File | Read when |
|---|---|
| `references/distribution/publishing.md` | Publishing, packaging, API distribution, community-distribution concerns. |

## Guardrails and recovery

- Do not draft the final skill before reading the workspace.
- Do not say research is complete unless the comparison table with inherit/avoid decisions exists for the non-trivial path.
- Do not hide the comparison table inside prose or skip it because sources "look similar."
- Do not copy a source skill wholesale, even as a temporary scaffold.
- Do not add files to `references/` unless they are needed and routed.
- Do not ship without trigger tests.
- Do not use `<` or `>` in frontmatter. Do not use "claude" or "anthropic" in the skill name.
- Do not reference bundled scripts with absolute paths. Script paths stay relative to the skill directory root.

Recovery moves:

- **Local evidence is thin or contradictory:** say so, widen the evidence set before drafting.
- **Research corpus is noisy:** cut to a few sources you can compare well.
- **Draft is bloating:** move detail to existing references or delete it.
- **Triggers misfiring:** read `references/authoring/description-engineering.md` and fix.
- **MCP calls failing:** read `references/iteration/troubleshooting.md`.
- **Repo-fit conflict touches shared files:** report it instead of editing outside the target skill by default.

## Final checks

Before declaring done, confirm:

- [ ] frontmatter `name` matches the directory name exactly
- [ ] `name` does not contain "claude" or "anthropic"
- [ ] description follows the formula: what + when + trigger phrases
- [ ] description is under 1024 characters with no `<` or `>`
- [ ] `SKILL.md` body is under 500 lines
- [ ] `SKILL.md` contains decisions and routing, not bulky reference content
- [ ] every reference file is explicitly routed
- [ ] routing verification: `for f in $(find references -name '*.md' -type f); do grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"; done`
- [ ] the final result is clearly synthesized from evidence and comparison
- [ ] no dead weight was added just because another skill had it
- [ ] at least 3 trigger tests passed (should-trigger and should-NOT-trigger)
- [ ] primary workflow completes without error in at least one test
- [ ] full quality pass: ran `references/checklists/master-checklist.md`

Quick orphan check:

```bash
for f in $(find references -name '*.md' -type f); do grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"; done
```
