---
name: build-skill
description: "Use if creating, redesigning, or merging agent skills adhering to agentskills.io specifications, integrating run-research for quality context, MJS/Python scripts, and multi-mode workflows."
disable-model-invocation: true
license: MIT
metadata:
  author: yigitkonur
  version: "3.1.0"
---

# Build Agent Skills

Synthesize robust, spec-compliant agent skills adhering to the open [Agent Skills Specification](https://agentskills.io/specification). Built on empirical research, progressive disclosure, deterministic scripting, and verified domain context.

## Mandatory Companion Prerequisite: `run-research`

High-quality skills cannot be built in a vacuum or from stale model memory. Skill authoring requires verified ground truth:
- **Prerequisite skill**: [`skills/run-research`](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/run-research)
- **Install command**: `npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-research -y`

> **Standing Invariant**: Never draft a skill based on assumptions, unverified library contracts, or generic training weights. When non-trivial APIs, frameworks, or domain workflows are involved, invoke `run-research` first to gather authoritative documentation, verifiable quotes, and real code patterns. **If `run-research` is not installed or available, refuse to run and prompt the user to install it before proceeding.** Quality skills cannot exist without quality context.

## When to Use

Use this skill when you are:
- *creating a new agent skill from scratch* ("make me a skill for X", "scaffold a skill", "I need a skill that does Y")
- *substantially redesigning or refactoring an existing skill* ("rewrite this skill", "clean up this bloated skill")
- *merging multiple skills or disparate source corpora into one* ("combine these skills into one coherent skill")
- *extracting an in-flight conversation into a skill* ("convert what we just did into a skill", session reaching 200k–400k tokens)
- *authoring a framework- or repo-specific skill* with extensive reference blocks grounded in live documentation
- *auditing a skill for agentskills.io specification compliance* (frontmatter fields, script conventions, progressive disclosure)

Do NOT use this skill for:
- *testing live derailment resistance* — use `audit-skill-by-derailment`
- *one-off quick script fixes* where outside skill patterns or documentation aren't relevant
- *blind cloning* of a remote skill without synthesis, adaptation, or repo-fit

## Core Non-Negotiable Rules

1. **Specification compliance first**: Frontmatter strictly adheres to `agentskills.io/specification` (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). No arbitrary top-level fields.
2. **Context grounding before drafting**: Invoke `run-research` for all non-trivial domains. Refuse to run without verified research and refuse to hallucinate APIs or edge cases.
3. **Progressive disclosure architecture**: Keep `SKILL.md` under 500 lines (<5,000 tokens). Offload bulky documentation to `references/` (1-level deep) and deterministic operations to `scripts/`.
4. **Deterministic scripting**: Write bundled scripts in portable JavaScript (`.mjs` ES Modules) or Python (`.py`). Avoid fragile shell scripts (`.sh`).
5. **Reproduce, test, and verify**: Always test scripts and verify execution infrastructure before declaring done.
6. **Comparison before combination**: When researching remote skills, build a structured comparison table with explicit inherit/avoid decisions.

## Available Scripts

Scripts live in `scripts/` and run directly via Node.js or Python without external global installations:

- **`scripts/skill-dl.mjs`** — Discovery, download, and specification auditor.
  - Search registry: `node scripts/skill-dl.mjs search "typescript" "mcp" --top 10`
  - Download candidate: `node scripts/skill-dl.mjs download anthropics/skills/mcp-builder -o ./research-corpus`
  - Audit spec compliance: `node scripts/skill-dl.mjs inspect ./skills/build-skill`
- **`scripts/skill-research.mjs`** — End-to-end multi-query discovery → download → corpus inspection pipeline:
  - `node scripts/skill-research.mjs "typescript,mcp,server" ./research-corpus 3`

*(Backward-compatible bash shims `scripts/skill-dl` and `scripts/skill-research.sh` forward directly to these `.mjs` scripts).*

## Four Operational Modes

### Mode 1: Discovery Mode (Registry & Consortium Sweep)
Use when researching existing patterns on `skills.sh`, GitHub, and external repositories before writing code.
1. **Registry Discovery**: Run `node scripts/skill-dl.mjs search` across 3–10 orthogonal keywords to find top candidate skills with consensus scoring.
2. **Subagent Consortium**: Deploy up to 3–5 parallel sub-agents to summarize each candidate skill across distinct lenses:
   - *Architecture & Progressive Disclosure*: How `references/` and line counts are structured.
   - *Script & Tool Automation*: What logic is scripted in `scripts/` vs left in prose.
   - *Triggers & Description Calibrations*: Negative triggers, precision, over-triggering guards.
3. **Individual Skill Visits & Plan Presentation**: After forming the consortium, visit each candidate skill individually. Analyze how its references and scripts affect its execution. Plan the approach, synthesize the comparison table, and present it to the user before code authoring.

### Mode 2: Creation & Distillation Mode (Synthesis & Repo-Fit)
Use after discovery to draft a new skill or perform a major refactor from discovered knowledge.
1. **Distillation via Sub-Agents**: Hand refined discovery data to sub-agents to produce distilled outputs, combining everything into the repository's native conventions and vocabulary.
2. **Draft Plan First**: Draft a structural plan (`SKILL.md`, `references/`, `scripts/`) before writing code so the skill reflects original design rather than being passively biased by external templates.
3. **Iterative Revisitation**: Revisit candidate skills repeatedly as needed to refine edge cases, while preserving strict progressive disclosure boundaries:
   - `SKILL.md`: High-level workflow, decision trees, prerequisites, script summaries, reference routing.
   - `references/`: Deep technical documentation, API tables, and domain-specific checklists (kept 1-level deep).
   - `scripts/`: Deterministic verification, parsing, and scaffolding tools.
4. **Specification Audit**: Verify frontmatter contains only allowed fields and line count stays under 500 lines.

### Mode 3: Conversation-Driven Mode (High-Token Session Distillation)
Use when converting an extensive in-flight conversation (e.g. 200k–400k tokens) into a reusable skill.
1. **Mental Model & Research Alignment**: Ingest the chat context and invoke `run-research` on the fly to ground any ambiguous domain tools or commands used during the session.
2. **Step-by-Step Confession (Up to 5-Level Nested List)**:
   Reconstruct the exact progression of actions, corrections, and discoveries to link back to agent memory:
   - Level 1: Primary Milestone (e.g. Setting up authentication)
     - Level 2: Sub-workflow Phase (e.g. OAuth token exchange debugging)
       - Level 3: Concrete Step Executed (e.g. Inspecting headers and callback payload)
         - Level 4: Error Encountered & Correction (e.g. Fixed state mismatch via Redis PKCE store)
           - Level 5: Deterministic Insight or Invariant (e.g. Token TTL must be ≥300s to avoid refresh race)
3. **Transfer Planning**: Plan which confessed steps transfer into:
   - `SKILL.md` body (core decision trees and non-negotiable gates).
   - `references/` (deep configuration guides and edge case catalogs).
   - Script-ification (convert any repetitive terminal commands into deterministic `.mjs` or `.py` scripts).
4. **Script Scaffolding & Verification**: Implement and test scripts in `scripts/`.

### Mode 4: Pure Research / Documentation-Driven Mode
Use when authoring a skill for a specific repository, library, or framework from scratch.
1. **Exhaustive Extraction via `run-research`**: Query official docs, source code, migration guides, and GitHub issue trackers.
2. **Deep Reference Blocks**: Build detailed, reusable reference files under `references/` containing hundreds of verified references organized into atomic blocks.
3. **Actionable "Do This, Not That" Guidance**: Break instructions down into explicit, imperative steps ("Run...", "Configure...", "Verify...") with clear failure modes and counters.

## Step-by-Step Authoring Workflow

1. **Verify Prerequisites**: Confirm `run-research` is accessible and `node scripts/skill-dl.mjs --where` succeeds.
2. **Select Mode**: Choose Discovery, Creation, Conversation-driven, or Documentation mode.
3. **Execute Research**: Collect evidence via `run-research` and `skill-dl.mjs search`. Build the comparison table.
4. **Draft `SKILL.md`**:
   - Write valid YAML frontmatter conforming to `agentskills.io`.
   - Formulate clear imperative workflow sections with validation gates.
   - Route reference files cleanly.
5. **Develop & Test Scripts**:
   - Author automation scripts in `scripts/` using Node.js (`.mjs`) or Python (`.py`).
   - Run and test scripts with real data; confirm zero-crash execution.
6. **Spec & Quality Validation**:
   - Run `node scripts/skill-dl.mjs inspect .` to verify frontmatter and line counts.
   - Run repository skill validator: `python3 scripts/validate-skills.py`.

## Do This, Not That

| Do This | Not That |
|---|---|
| Ground every skill in verified facts using `run-research` | Hallucinate APIs or procedures from model memory |
| Write portable, robust scripts in Node.js (`.mjs`) or Python (`.py`) | Author fragile shell scripts (`.sh`) with platform-dependent grep/sed |
| Adhere strictly to the 6 canonical `agentskills.io` frontmatter fields | Invent arbitrary frontmatter fields like `user-invocable` or `hooks` |
| Keep `SKILL.md` under 500 lines and route details to `references/` | Stuff monolithic 1,500-line guides into a single `SKILL.md` |
| Test and execute bundled scripts before declaring done | Ship untested scripts that fail on live environments |
| Use 5-level nested lists to capture deep conversational context | Summarize complex troubleshooting sessions into vague bullet points |

## Reference Routing

Read the smallest relevant reference set for your current task:

### Authoring & Formatting
- [`references/authoring/skillmd-format.md`](references/authoring/skillmd-format.md): Official `agentskills.io` frontmatter specification, validation rules, and structural guidelines.
- [`references/authoring/description-engineering.md`](references/authoring/description-engineering.md): Writing high-precision description triggers and negative triggers.
- [`references/authoring/decision-tree-patterns.md`](references/authoring/decision-tree-patterns.md): Branching logic, routing hierarchies, and decision matrices.
- [`references/authoring/reference-file-structure.md`](references/authoring/reference-file-structure.md): Sizing, naming, and nesting discipline for `references/`.
- [`references/authoring/testing-methodology.md`](references/authoring/testing-methodology.md): Trigger evaluation, functional passes, and multi-tier testing.
- [`references/authoring/tdd-for-skills.md`](references/authoring/tdd-for-skills.md): RED-GREEN-REFACTOR pressure testing for discipline skills.
- [`references/authoring/persuasion-principles.md`](references/authoring/persuasion-principles.md): Calibrating authority, commitment, and instruction strictness.
- [`references/authoring/degrees-of-freedom.md`](references/authoring/degrees-of-freedom.md): Balancing prescriptiveness vs model autonomy per step.

### Patterns & Architecture
- [`references/patterns/skill-organization.md`](references/patterns/skill-organization.md): Splitting, merging, and scoping skill boundaries.
- [`references/patterns/naming-conventions.md`](references/patterns/naming-conventions.md): Kebab-case naming, directory alignment, and verb-noun conventions.
- [`references/patterns/workflow-patterns.md`](references/patterns/workflow-patterns.md): Sequential, iterative, multi-MCP, and context-aware patterns.
- [`references/patterns/mcp-enhancement.md`](references/patterns/mcp-enhancement.md): Building skills that wrap and coordinate MCP server tools.

### Research & Sourcing
- [`references/research-workflow.md`](references/research-workflow.md): Grounding with `run-research`, multi-angle discovery, and comparison tables.
- [`references/remote-sources.md`](references/remote-sources.md): Registry workflows with `skills.sh` and `scripts/skill-dl.mjs`.
- [`references/comparison-workflow.md`](references/comparison-workflow.md): Structuring evidence, comparison tables, and inherit/avoid decisions.
- [`references/source-patterns.md`](references/source-patterns.md): Identifying high-signal design patterns from external skills.
- [`references/research/source-verification.md`](references/research/source-verification.md): Filtering low-signal packages and assessing ecosystem authority.
- [`references/research/fact-checking.md`](references/research/fact-checking.md): Verifying claims, commands, and schemas against ground truth.
- [`references/research/search-strategies.md`](references/research/search-strategies.md): Orthogonal search queries and consensus discovery.
- [`references/research/corpus-inspection.md`](references/research/corpus-inspection.md): Auditing downloaded skill corpora for quality and anti-patterns.

### Quality, Checklists & Iteration
- [`references/checklists/master-checklist.md`](references/checklists/master-checklist.md): Comprehensive quality checklist before shipping.
- [`references/examples/annotated-examples.md`](references/examples/annotated-examples.md): Structural patterns from production-grade skills.
- [`references/examples/anti-patterns.md`](references/examples/anti-patterns.md): Catalog of 24 content anti-patterns to avoid.
- [`references/examples/anti-patterns-authoring.md`](references/examples/anti-patterns-authoring.md): Process and authoring pitfalls (AP-25 through AP-34).
- [`references/iteration/feedback-signals.md`](references/iteration/feedback-signals.md): Interpreting trigger signals and user feedback.
- [`references/iteration/troubleshooting.md`](references/iteration/troubleshooting.md): Diagnosing registration, syntax, and execution issues.
- [`references/distribution/publishing.md`](references/distribution/publishing.md): Packaging and publishing skills to registries and repositories.

## Final Shipping Verification Checklist

- [ ] Frontmatter strictly contains valid `agentskills.io` fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`)
- [ ] `name` matches directory name exactly (`build-skill`)
- [ ] Description states WHAT the skill does and WHEN to use it (<1024 characters, no `<` or `>`)
- [ ] `SKILL.md` line count is under 500 lines
- [ ] Companion prerequisite `run-research` is documented and linked
- [ ] All bundled scripts in `scripts/` are written in Node.js (`.mjs`) or Python (`.py`)
- [ ] Bundled scripts execute cleanly (`node scripts/skill-dl.mjs --where`)
- [ ] Every file in `references/` is explicitly routed in the reference routing section
- [ ] Full repository validation passes: `python3 scripts/validate-skills.py`
