# Derailment Test: build-skills → create build-mcp-sdk-server

## Test metadata

| Field | Value |
|---|---|
| Skill under test | `build-skills` |
| SKILL.md location | `skills/build-skills/SKILL.md` |
| Test task | Create a new `build-mcp-sdk-server` skill from scratch |
| Workspace | MCP TypeScript SDK cloned to `/tmp/mcp-typescript-sdk` |
| Path classification | Full Research Path (new skill creation) |
| Skill type classification | MCP Enhancement + Workflow hybrid |
| Tester approach | Literal execution — followed every step exactly as written |
| Reference files read | 22 build-skills refs + 5 test-skill-quality refs |
| Remote sources downloaded | 4 skills via `skill-dl` (fastmcp, mcp-expert, mcp-server-builder, converting-mcps-to-skills) |

---

## Friction log

### F-01 · P1 · Step 2 · Skill type is presented as mutually exclusive

**Root cause:** M2 (Ambiguous term — "classify" implies single category)

**What happened:** Step 2 says "Classify the skill type" and presents a 3-row table (Document/Asset, Workflow, MCP Enhancement). The word "classify" implies a single-label choice. But the target skill (`build-mcp-sdk-server`) is clearly both a Workflow *and* an MCP Enhancement — it guides users through a multi-step process AND enhances MCP server development.

**What I expected:** Guidance on how to handle hybrid types. The `workflow-patterns.md` reference file actually covers combining patterns beautifully (lines 273-285), but Step 2 doesn't mention this possibility. It sends you to read `workflow-patterns.md` to "choose the right structural pattern" — singular.

**Fix direction:** Add a note to Step 2: "Skills often combine types. Pick the primary type and note secondary characteristics. See the 'Combining patterns' section of `references/patterns/workflow-patterns.md`."

---

### F-02 · P1 · Step 3 · "Target workspace" is ambiguous

**Root cause:** S3 (Missing context specification)

**What happened:** Step 3 says "Produce a tree-style inventory of the target workspace." When building a skill *about* an external technology (MCP TypeScript SDK), there are two workspaces: (a) the skills repo where the skill will live, and (b) the project/SDK being targeted. I didn't know which one to tree. I ended up doing both, which was the right call, but the instruction left me guessing.

**What I expected:** Explicit guidance: "If the skill targets an external technology, tree both the skill repo and a representative project using that technology."

**Fix direction:** Reword to: "Produce a tree of the target skill's workspace. If the skill targets an external framework or SDK, also inspect a representative project or the official documentation."

---

### F-03 · P0 · Step 4 · `skill-dl` dependency with no install path or fallback

**Root cause:** O1 (Missing prerequisite — external tool not guaranteed)

**What happened:** Step 4 says "Use `skill-dl search` (3–20 keywords) to discover candidates" and "Use `skill-dl` to download selected candidates." `skill-dl` happened to be installed in my environment, but there is zero guidance on:
1. How to install `skill-dl` if missing
2. How to verify it's installed (`which skill-dl` or `skill-dl --version`)
3. What to do if it's not available (fallback to manual URL fetching? `skills-as-context-search-skills` tool?)

This is a **hard blocker** for any user who doesn't have `skill-dl` pre-installed. The `references/remote-sources.md` file has install instructions, but Step 4 doesn't tell you to read that file *before* trying to use the tool.

**What I expected:** Step 4 should start with "Verify `skill-dl` is available: `skill-dl --version`. If not installed, see `references/remote-sources.md` for installation. If `skill-dl` is unavailable and cannot be installed, use the `skills-as-context-search-skills` MCP tool as a fallback."

**Fix direction:** Add prerequisite check at start of Step 4. Add fallback path for environments without `skill-dl`.

---

### F-04 · P1 · Step 4 · `skill-research.sh` execution details missing

**Root cause:** M5 (Execution method unspecified)

**What happened:** Step 4 says "run `references/skill-research.sh` for end-to-end parallel discovery and download in one command." But:
1. How do I run it? `bash references/skill-research.sh`? `sh`? `chmod +x && ./`?
2. What arguments does it take?
3. What working directory should I be in?
4. What does it actually do vs. manual `skill-dl` calls?

The reference file `skill-research.sh` exists and has comments inside, but Step 4 doesn't tell me to read its header first.

**What I expected:** Either inline the invocation syntax or say "Read the header of `references/skill-research.sh` for usage before running it."

**Fix direction:** Add invocation example: `bash references/skill-research.sh <keyword1> <keyword2> ...` or route to the script's own documentation.

---

### F-05 · P2 · Step 3 · "Read every relevant reference file" with 22 files

**Root cause:** S2 (Missing scoping — no prioritization guidance)

**What happened:** Step 3 says "Read every file in `references/` that is relevant to the task." But there are 22 reference files organized across 7 subdirectories. Without knowing which are relevant at *this* stage (vs. later stages), I read all 22. This consumed significant time and context.

**What I expected:** Step 3 should narrow: "Read the reference routing table at the bottom of SKILL.md to identify which files are relevant to the current task. Focus on the 3-5 most relevant at this stage."

**Fix direction:** Add scoping hint: "Use the Reference routing section at the bottom to identify which files apply to your current task type."

---

### F-06 · P1 · Step 4 · `skill-dl search` argument format undocumented

**Root cause:** O2 (Tool interface mismatch)

**What happened:** SKILL.md says `skill-dl search` with "3–20 keywords." I initially tried `skill-dl search "mcp server typescript sdk build"` (quoted string), which failed with: `search requires at least 3 keywords (got 1)`. The tool requires space-separated unquoted arguments: `skill-dl search mcp server typescript sdk build`.

**What I expected:** An inline example in Step 4: `skill-dl search keyword1 keyword2 keyword3 ... --top 20`

**Fix direction:** Add example invocation with explicit argument format.

---

### F-07 · P2 · Step 4 · `skills.markdown` output location unspecified

**Root cause:** S4 (Missing output location)

**What happened:** Step 4 says "Emit `skills.markdown` before moving on." But WHERE? The skill's workspace root? The current directory? The skill being built? A temp directory? I had to guess.

The `references/research-workflow.md` file does specify a location (line ~30), but Step 4 doesn't tell you to check that file for output path, only for "the complete research protocol."

**What I expected:** "Emit `skills.markdown` in the workspace root (or the skill's directory)."

**Fix direction:** Specify output location inline in Step 4.

---

### F-08 · P1 · Step 4a · Downloaded sources violate the skill's own quality standards

**Root cause:** M3 (Contradictory guidance — external sources exceed 500-line limit)

**What happened:** Step 4a says "Read its SKILL.md fully" for each downloaded skill. The `fastmcp` SKILL.md is 2,614 lines. The `mcp-server-builder` SKILL.md is 968 lines. Both FAR exceed the 500-line limit this very skill enforces. Reading 3,500+ lines of bloated sources creates confusion: are these good examples? Should I follow their patterns?

**What I expected:** A warning in Step 4a: "Downloaded sources may not follow the quality standards this skill enforces. Note bloat and anti-patterns — these inform the 'avoid' column of your comparison table."

**Fix direction:** Add a note to Step 4a about evaluating source quality critically, not treating downloads as examples to follow.

---

### F-09 · P1 · Step 4a · No format specified for per-skill notes

**Root cause:** S3 (Missing output specification)

**What happened:** Step 4a says "Capture notes per skill: overall structure, workflow style, reference organization, what it does well, what it does poorly, and 1–2 patterns worth inheriting (with exact relative paths)." But there's no format template. Are these inline? In a temp file? In a specific structure? The notes are "raw material for the comparison table" but the comparison table has 6 columns — the notes list has 6+ bullet points with no column mapping.

**What I expected:** A brief template or format example showing how notes map to comparison table columns.

**Fix direction:** Add a one-line example: "Use a heading per skill with bullet points that map to the comparison table columns."

---

### F-10 · P2 · Step 4 · `skills.markdown` not auto-generated by `skill-dl`

**Root cause:** M1 (Implied automation — "emit" suggests auto-generation)

**What happened:** "Emit `skills.markdown` before moving on" implies the tool creates this file. But `skill-dl` downloads skill directories — it doesn't produce a `skills.markdown` summary file. You must manually create it yourself. The verb "emit" is ambiguous — does the tool emit it, or should I?

**What I expected:** "Create `skills.markdown` summarizing what was downloaded, what was shortlisted, and why."

**Fix direction:** Change "Emit" to "Create" and add what should be in the file.

---

### F-11 · P1 · Step 5 · Redundant re-read instruction

**Root cause:** S2 (Redundant guidance — already done in 4a)

**What happened:** Step 5 opens with "Read the selected local and remote sources that actually matter." But I already read them in Step 4a — that was the entire point of the separate reading step. This instruction wastes context tokens or makes me wonder if I should re-read differently.

**What I expected:** "Using your notes from Step 4a, build a markdown comparison table..."

**Fix direction:** Remove the redundant read instruction from Step 5. Reference Step 4a's output instead.

---

### F-12 · P1 · Steps 5-6 · Artifact output location never specified

**Root cause:** S4 (Missing output location — systemic)

**What happened:** Step 5: "Build a markdown comparison table." Step 6: "Write down what success looks like." Neither says WHERE to put these artifacts. In chat output? In a temp file? In the skill's directory? In a planning document? For a skill that produces multiple intermediate artifacts (notes, comparison table, success criteria, skills.markdown), the lack of output location guidance is a systemic gap.

**What I expected:** A section at the top specifying: "Intermediate artifacts (comparison table, success criteria, research summaries) should appear in the conversation output. Final artifacts (SKILL.md, references/) are written to disk."

**Fix direction:** Add an "Artifact output" subsection to the workflow preamble specifying what goes where.

---

### F-13 · P0 · Step 7 · 251-line checklist loaded at synthesis time

**Root cause:** O3 (Cognitive overload — massive reference at creative stage)

**What happened:** Step 7 says "Read `references/checklists/master-checklist.md` for the full quality checklist." This checklist is 251 lines with 90+ items across 7 phases. Loading all 90+ checks at draft time is impractical — it's a pre-ship audit, not a draft-time guide. During synthesis, I need a short "top 10 things to get right" list, not a comprehensive audit.

**What I expected:** Step 7 should reference a "draft-time essentials" subset (10-15 items). The full 90+ item checklist should be routed to Step 9 (final checks) instead.

**Fix direction:** Split the checklist routing: Step 7 references a "draft essentials" subset, Step 9 references the full audit checklist.

---

### F-14 · P1 · Step 8 · Trigger tests require the skill to already exist

**Root cause:** M2 (Temporal impossibility — test before creation)

**What happened:** Step 8 says "Write 5+ should-trigger queries... Run each one by pasting it as a new message in Claude.ai (with only this skill enabled) or Claude Code, and record whether the skill loaded." But during creation, the skill doesn't exist yet! You can't test trigger loading for a skill you haven't finished writing. This step makes sense for revision, not creation.

**What I expected:** For creation workflows: "Draft your trigger tests now. After writing the skill, install it and run the tests. For now, verify the description against the trigger test queries manually."

**Fix direction:** Add a conditional: "For new skills, draft trigger tests alongside the skill. Run them after installation. For revisions, run them immediately."

---

### F-15 · P2 · Step 9 · No tooling for routing verification

**Root cause:** S1 (Missing verification method)

**What happened:** Step 9 says "Confirm every file in `references/` is explicitly routed from SKILL.md." This is a mechanical check — perfect for a grep command — but no command is provided. I had to manually cross-reference.

**What I expected:** A verification command: `for f in references/**/*.md; do grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"; done`

**Fix direction:** Add a verification script or command in the Final checks section.

---

### F-16 · P1 · Overall · No effort signaling per step

**Root cause:** O1 (Missing effort calibration)

**What happened:** All 9 steps look equal in the workflow (numbered 1-9, similar formatting). But Steps 1-3 take minutes, Steps 4-4a take 30+ minutes of intensive reading, Step 7 is the main creative work (could be hours), and Step 8 requires a separate environment. This creates false expectations of linear effort.

**What I expected:** Brief effort indicators: "[quick]", "[intensive reading]", "[main creative work]", "[requires separate environment]"

**Fix direction:** Add effort tags or group steps into phases with effort hints.

---

### F-17 · P2 · Overall · "Do this, not that" table is positioned too late

**Root cause:** S1 (Structural ordering — warnings after workflow)

**What happened:** The "Do this, not that" table appears AFTER the 9-step workflow and output contract. By the time I read it, I'd already completed steps 1-7 and made some of the mistakes it warns against (e.g., "mentally blend sources and jump to the final SKILL.md").

**What I expected:** The table (or its key items) should appear as guardrails within the relevant steps, not as a retrospective summary.

**Fix direction:** Move critical "do/don't" items inline to their relevant workflow steps. Keep the table as a summary but position it before the workflow or as a quick-reference section.

---

### F-18 · P1 · Output contract · No progressive output guidance

**Root cause:** S3 (Missing output timing specification)

**What happened:** The Output contract says "show work in this order: 1. workspace scan summary, 2. skill type classification, 3. research summary..." (8 items). But it doesn't say WHEN to show each item. After completing all 9 steps? After each relevant step? The 8-item list implies a massive end-of-workflow dump, but some items (workspace scan, skill type) are available early and useful for checkpointing.

**What I expected:** "Show each item as it becomes available. The workspace scan and skill type should appear early. The comparison table should appear before synthesis begins."

**Fix direction:** Add timing hints to the output contract items, or say "produce each item at the step that generates it."

---

## Density map

| Step | Friction count | P0 | P1 | P2 |
|---|---|---|---|---|
| Step 1 | 0 | 0 | 0 | 0 |
| Step 2 | 1 | 0 | 1 | 0 |
| Step 3 | 2 | 0 | 1 | 1 |
| Step 4 | 4 | 1 | 2 | 1 |
| Step 4a | 2 | 0 | 2 | 0 |
| Step 5 | 2 | 0 | 2 | 0 |
| Step 6 | 0 | 0 | 0 | 0 |
| Step 7 | 1 | 1 | 0 | 0 |
| Step 8 | 1 | 0 | 1 | 0 |
| Step 9 | 1 | 0 | 0 | 1 |
| Overall/structural | 4 | 0 | 2 | 2 |
| **TOTAL** | **18** | **2** | **11** | **5** |

**Compound P0:** Steps 3-4a have 5 P1 friction points in 2 consecutive steps, which per test-skill-quality rules (3+ P1 in same step = compound P0) constitutes a compound P0. The research/evidence capture phase is the systemic weak point.

---

## What worked well

1. **Workspace-first discipline.** The insistence on inspecting local evidence before remote research genuinely prevented premature jumping to conclusions. I had a much better foundation for the comparison table because I started with what existed.

2. **Comparison table requirement.** Forcing a structured comparison before synthesis caught quality differences between sources (e.g., fastmcp's 2600-line bloat vs. mcp-expert's clean progressive disclosure) that I would have missed with mental blending.

3. **Progressive disclosure philosophy.** The principle of keeping SKILL.md lean and routing detail to references is excellent and consistently enforced throughout the workflow.

4. **Trigger boundary clarity.** The "Trigger boundary" section is crystal clear about what fires and what doesn't. The negative examples are helpful.

5. **Reference routing table.** The detailed routing table at the bottom of SKILL.md is the best feature — it tells you exactly which file to read for which task, preventing unnecessary context loading.

6. **"Do this, not that" table.** The content is excellent even though the positioning is suboptimal. Each row captures a real mistake that saves significant time.

7. **Guardrails and recovery section.** The explicit recovery moves for thin evidence, noisy corpus, and bloating draft are practical and actionable.

8. **Decision rules.** The rules about when to stay local vs. go remote, and when to prefer one source over another, are clear and well-calibrated.

---

## Priority summary

| Priority | ID | Step | Fix type | One-line fix |
|---|---|---|---|---|
| P0 | F-03 | 4 | Prerequisite Surfacing | Add `skill-dl` install check + fallback path |
| P0 | F-13 | 7 | Scaling Guidance | Split checklist routing: draft essentials in Step 7, full audit in Step 9 |
| P1 | F-01 | 2 | Threshold Concretization | Note that types can combine; route to "Combining patterns" |
| P1 | F-02 | 3 | Output Location Specification | Clarify "target workspace" when skill targets external tech |
| P1 | F-04 | 4 | Execution Method Specification | Add invocation syntax for skill-research.sh |
| P1 | F-06 | 4 | Schema Duplication at Point of Use | Add inline `skill-dl search` example with argument format |
| P1 | F-08 | 4a | Conditional Gating | Add warning that downloaded sources may not meet quality standards |
| P1 | F-09 | 4a | Format Alignment | Add brief template mapping notes to comparison columns |
| P1 | F-11 | 5 | Workflow Path Reconciliation | Remove redundant read instruction, reference Step 4a output |
| P1 | F-12 | 5-6 | Output Location Specification | Add artifact output subsection specifying what goes where |
| P1 | F-14 | 8 | Conditional Gating | Add creation vs. revision conditional for trigger testing |
| P1 | F-16 | Overall | Scaling Guidance | Add effort indicators or phase groupings |
| P1 | F-18 | Output | Format Alignment | Add timing hints to output contract items |
| P2 | F-05 | 3 | Scaling Guidance | Add scoping hint for reference reading |
| P2 | F-07 | 4 | Output Location Specification | Specify where `skills.markdown` goes |
| P2 | F-10 | 4 | Threshold Concretization | Change "Emit" to "Create" with content guidance |
| P2 | F-15 | 9 | Execution Method Specification | Add grep-based routing verification command |
| P2 | F-17 | Overall | Workflow Path Reconciliation | Reposition key warnings inline at decision points |

---

## Metrics

| Metric | Value |
|---|---|
| Total friction points | 18 |
| P0 (blockers) | 2 |
| P1 (confusion) | 11 |
| P1 compound (3+ P1 in adjacent steps) | 1 (Steps 3-4a) |
| P2 (minor) | 5 |
| Steps with zero friction | 2 of 9+2 (Steps 1, 6) |
| Highest density step | Step 4 (4 friction points) |
| Dominant root cause category | S (Structural) — 7 of 18 |
| Second root cause category | M (Semantic) — 6 of 18 |
| Third root cause category | O (Operational) — 5 of 18 |
