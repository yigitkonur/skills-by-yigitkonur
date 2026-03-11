# Derailment Test: run-research on "WebSocket library choice for Next.js 15"

Date: 2025-07-28
Skill under test: run-research
Test task: Choose the best WebSocket/real-time solution for a Next.js 15 collaborative app deployed on Vercel (~1000 concurrent users)
Method: Follow SKILL.md steps 1–5 exactly as written, using the Workflow Selector for Pattern C (Library/Dependency Choice)

---

## Pre-scan summary

| Attribute | Value |
|---|---|
| SKILL.md lines | 143 |
| Total steps | 5 (Frame → Query → Read → Validate → Synthesize) |
| Branching points | Workflow Selector table (6 patterns), deep_research conditional in Step 1, recovery paths |
| Reference files | 20 (5 tool, 5 method, 6 domain, organized in subdirectories) |
| External dependencies | research-powerpack MCP (search_google, scrape_pages, search_reddit, fetch_reddit, deep_research) |
| Trigger boundary | Clear: "coding task that needs external information" |

---

## Friction points

### Workflow Selector (pre-step routing)

**F-01 — Workflow selector placement lacks explicit "read first" instruction** (P2)
The workflow selector table sits before steps 1–5 in the document, but no instruction says "consult the selector before starting step 1." An agent following steps linearly might skip it. The table is essential for choosing the starting tool and sequence.
Root cause: S2 (Missing prerequisite)
Fix: Add a sentence before Step 1: "Before starting, consult the Workflow Selector table above to identify your starting tool and minimum sequence."

**F-02 — "Key references" column doesn't specify WHEN to read them** (P1)
The workflow selector lists key references (e.g., `references/library-research.md`) but never says whether to read them before starting, during execution when stuck, or during synthesis. This leaves the agent guessing about reading order.
Root cause: M2 (Implicit ordering)
Fix: Add to the workflow selector table header or footnote: "Read the first key reference before Step 1. Read additional references only when stuck or during synthesis."

### Step 1 — Frame the research

**F-03 — "Write down the actual decision" has no specified location** (P1)
Step 1 says "Write down the actual decision or question" but doesn't say WHERE to write it — in a crash-think-tool step? In a variable? In a file? A comment? This matters because later steps may need to reference the framing.
Root cause: O1 (Missing output location)
Fix: Change to "Write down the actual decision or question in a scratch pad or reasoning step. Include: the question, stack context, scale constraints, and reversibility assessment."

**F-04 — "If you use deep_research" conditional is ambiguous** (P1)
Step 1 says "If you use deep_research, use the full structured format (GOAL / WHY / KNOWN / APPLY / sub-questions)." But since the workflow selector already told me to start with search_google, it's unclear: does this mean "when you eventually use deep_research later in the sequence" or "if you choose to start with deep_research"? The conditional fires too early in the wrong context.
Root cause: M4 (Scope ambiguity)
Fix: Move this instruction to a new sub-section: "When calling deep_research (at any point in the sequence), always use the full structured format: GOAL / WHY / KNOWN / APPLY / sub-questions."

### Step 2 — Generate diverse queries

**F-05 — "Use the search tool descriptions to calibrate volume" is too vague** (P2)
Step 2 says to use tool descriptions for calibration but doesn't specify WHICH tool (search_google? search_reddit? both?). The tool descriptions have different minimums (search_google: MIN 3/REC 5-7, search_reddit: MIN 3/REC 20+). An agent might not know which tool's description to consult at this stage.
Root cause: M1 (Vague referent)
Fix: Change to "Calibrate query volume per tool: search_google needs 5–7 diverse keywords, search_reddit needs 8–20 diverse angle queries. See each tool reference for specifics."

**F-06 — "Hit every angle on the first call" contradicts sequential workflow** (P1)
Step 2 says "hit every angle on the first call" but the workflow selector defines a SEQUENCE of tools (search_google → scrape_pages → search_reddit → fetch_reddit). Do I generate queries for ALL tools at once in Step 2, or does Step 2 apply per-tool as I progress through the sequence? The instruction is ambiguous.
Root cause: M3 (Conflicting instructions between sections)
Fix: Clarify: "Generate queries per tool in sequence. When calling search_google, generate 5–7 diverse keywords covering all angles. When you reach search_reddit, generate 8–20 queries from different angles. Don't batch queries across different tools."

### Step 3 — Read actual sources

**F-07 — "Read actual sources" doesn't map to a tool name** (P1)
Step 3 says "Read actual sources, not snippets" but doesn't explicitly say "use scrape_pages for this." The mapping from conceptual step to tool is implicit. An agent unfamiliar with the toolset would be stuck.
Root cause: O5 (Missing method specification)
Fix: Change to "Read actual sources using scrape_pages with use_llm=true and specific extraction targets. Never rely on search result snippets alone."

**F-08 — No guidance on how many Reddit threads to fetch** (P1)
After search_reddit returns 60+ results, there's no guidance on how many to select for fetch_reddit. Should I fetch the top 3? Top 10? All consensus hits? The budget implications (comment tokens distributed across posts) make this an important decision.
Root cause: S3 (Missing threshold)
Fix: Add to Step 3 or to the fetch_reddit reference: "Select 5–10 Reddit threads with highest engagement and relevance. More threads = fewer comments per thread. For library comparisons, prioritize threads with 10+ comments."

### Step 4 — Validate before concluding

**F-09 — "Cross-check claims" lacks method specification** (P1)
Step 4 says "Cross-check any claim that will drive a decision" but doesn't specify HOW. Should I use deep_research? Another search_google round? Check official docs with scrape_pages? The conceptual guidance is sound but the execution path is missing.
Root cause: O5 (Missing method specification)
Fix: Change to "Cross-check decision-driving claims using one of: (a) scrape_pages on official docs/changelogs, (b) a focused deep_research question, or (c) a targeted search_google for counter-evidence. Always check at least one primary source (official docs) and one community source (Reddit/HN)."

### Step 5 — Synthesize

**F-10 — "Produce what the coder actually needs" lacks output template** (P1)
Step 5 says "the answer, the comparison, the snippet, the migration path" but provides no structure or template. For a library comparison, should I produce a table? A ranked list? Prose? A decision matrix? The lack of structure means every agent produces a different format.
Root cause: O1 (Missing output format)
Fix: Add output templates by task type: "For library choices: produce a comparison table (features/cost/DX/caveats), a recommendation with rationale, and a migration path. For bug fixes: produce the root cause, the fix code, and verification steps."

### Workflow integration (cross-cutting)

**F-11 — deep_research placement in the sequence is undefined** (P0)
The workflow selector says "Escalate with deep_research" as part of the library research sequence, but steps 1–5 never explicitly tell you WHEN to call deep_research. Is it during Step 3 (reading)? Step 4 (validation)? Step 5 (synthesis)? This blocks progress because the agent doesn't know where in the workflow to insert the deep_research call.
Root cause: S1 (Missing step)
Fix: Add explicit guidance: "Call deep_research after completing the search → scrape → Reddit sequence (after Step 3). Use it to fill gaps in your findings or synthesize across sources. Frame it with the GOAL/WHY/KNOWN/APPLY format, populating KNOWN with findings from prior steps."

**F-12 — No guidance on preparing deep_research template** (P1)
Core rules say "Never call deep_research with a bare question" and reference the structured format, but Step 1 (framing) doesn't tell you to prepare this template. By the time you need deep_research, you have to construct the template from scratch without guidance on what goes in each field.
Root cause: S2 (Missing prerequisite)
Fix: In Step 1, add: "If your workflow sequence includes deep_research, draft the GOAL and WHY fields now. You'll populate KNOWN with findings from earlier steps before calling it."

**F-13 — deep_research already synthesizes — unclear if agent should re-synthesize** (P1)
deep_research returns a comprehensive synthesis with tables, recommendations, and trade-offs. Step 5 says "Synthesize" but the deep_research output IS a synthesis. Should the agent re-synthesize? Merge it with other data? Present it as-is? The overlap causes confusion.
Root cause: M3 (Conflicting instructions)
Fix: Add to Step 5: "If you used deep_research, its output forms the core of your synthesis. Supplement it with specific quotes or data points from Reddit/scrape that deep_research may have missed. Don't re-do the analysis — augment it."

**F-14 — Recovery path "attach code files" doesn't apply to all research types** (P2)
The recovery path says "Switch to deep_research with attached code files" but library research tasks have no code files to attach. The guidance is too specific to bug-fixing patterns.
Root cause: M4 (Scope mismatch)
Fix: Change to "Switch to deep_research with attached files (code for bug research, package.json/config for library research, architecture docs for design decisions)."

**F-15 — Verification step creates potential infinite loop** (P1)
The do/not-do table says "Run verification search or deep_research before concluding." After running deep_research, should I run ANOTHER search to verify it? And then verify that? The recursion boundary is undefined.
Root cause: S3 (Missing termination condition)
Fix: Add: "Verification is complete when you have at least two independent sources (e.g., official docs + community discussion) confirming each key claim. One verification pass is sufficient — do not recursively verify."

**F-16 — No guidance on merging data from multiple tool outputs** (P1)
After running search_google → scrape_pages → search_reddit → fetch_reddit → deep_research, I have data from 5 different tool calls. The skill provides no guidance on how to merge or reconcile these outputs. The synthesis reference exists but SKILL.md doesn't tell me when to read it.
Root cause: S1 (Missing step)
Fix: Add between Steps 4 and 5: "Before synthesizing, reconcile your sources: identify where search results, Reddit comments, and deep_research agree (high confidence) and where they disagree (needs resolution). The synthesis reference (references/synthesis/synthesize-findings.md) covers reconciliation patterns."

### Reference routing

**F-17 — "Always verify version-sensitive claims" lacks process** (P2)
Core rule 6 says to verify version-sensitive claims but doesn't describe the verification process. Is it a search? A doc scrape? A deep_research call?
Root cause: O5 (Missing method specification)
Fix: Change to "Always verify version-sensitive claims by scraping the official documentation or changelog at the latest URL. Don't trust blog posts or AI-generated claims for version numbers."

**F-18 — Key references listed flat with no reading order** (P1)
The workflow selector lists key references (e.g., `research-patterns.md` and `library-research.md`) as a flat comma-separated list. No reading priority or order is specified. The instructions say "Start with the smallest relevant method reference" but both files are 250+ lines — there's no "smallest" option.
Root cause: M2 (Implicit ordering)
Fix: Change the instruction to: "Read the domain reference first (e.g., library-research.md) for task-specific patterns, then consult the method reference (e.g., research-patterns.md) if the domain reference doesn't cover your specific scenario."

---

## What worked well

1. **Workflow selector routing was correct.** The table correctly identified "Library or dependency choice" and routed me to `search_google` as the starting tool with the right sequence.
2. **The minimum sequence was logical and effective.** search_google → scrape_pages → search_reddit → fetch_reddit exercised different information angles (formal docs vs. community experience).
3. **Core rule 8 (fetch_comments=true, use_llm=false) was valuable.** The raw Reddit comments contained authentic developer opinions that LLM summarization would have diluted.
4. **The deep_research structured format (GOAL/WHY/KNOWN/APPLY) produced excellent results.** When I finally used it, the structured framing led to comprehensive, actionable output.
5. **The 5-step framework is conceptually sound.** Frame → Query → Read → Validate → Synthesize is a solid research pipeline.
6. **Tool reference files are comprehensive.** Each tool reference (search-google.md, scrape-pages.md, etc.) had enough detail to use the tool effectively.
7. **The "do this, not that" table caught a real anti-pattern.** "Run verification search before concluding" prevented me from treating deep_research output as gospel.
8. **Recovery paths existed for common failure modes.** "If results are shallow" and "If two sources disagree" showed the skill anticipated problems.

---

## Derailment density map

| Phase | Steps | Clean passes | Derailments | Severity |
|---|---|---|---|---|
| Pre-step routing | Workflow selector | 1 | 2 (F-01, F-02) | 1×P2, 1×P1 |
| Step 1 — Frame | 1 step | 0 | 2 (F-03, F-04) | 2×P1 |
| Step 2 — Query | 1 step | 0 | 2 (F-05, F-06) | 1×P2, 1×P1 |
| Step 3 — Read | 1 step | 0 | 2 (F-07, F-08) | 2×P1 |
| Step 4 — Validate | 1 step | 0 | 1 (F-09) | 1×P1 |
| Step 5 — Synthesize | 1 step | 0 | 1 (F-10) | 1×P1 |
| Cross-cutting | Workflow integration | 0 | 7 (F-11 to F-17) | 1×P0, 4×P1, 2×P2 |
| Reference routing | 1 check | 0 | 1 (F-18) | 1×P1 |

**Hotspot:** Cross-cutting workflow integration (7 derailments, including the only P0). The individual steps are conceptually sound but the connections between them — when to call which tool, how to merge outputs, where deep_research fits — are underspecified.

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 1 | F-11 |
| P1 | 12 | F-02, F-03, F-04, F-06, F-07, F-08, F-09, F-10, F-12, F-13, F-15, F-16, F-18 |
| P2 | 5 | F-01, F-05, F-14, F-17 |
| **Total** | **18** | |

Note: With 12 P1 items spread across all phases, this constitutes a compound P0 for the overall workflow. The skill works but requires significant domain knowledge gap-filling at nearly every step.

---

## Root cause distribution

| Code | Description | Count |
|---|---|---|
| S1 | Missing step | 2 (F-11, F-16) |
| S2 | Missing prerequisite | 2 (F-02, F-12) |
| S3 | Missing threshold/termination | 2 (F-08, F-15) |
| M1 | Vague referent | 1 (F-05) |
| M2 | Implicit ordering | 2 (F-02, F-18) |
| M3 | Conflicting instructions | 2 (F-06, F-13) |
| M4 | Scope ambiguity/mismatch | 2 (F-04, F-14) |
| O1 | Missing output location/format | 2 (F-03, F-10) |
| O5 | Missing method specification | 3 (F-07, F-09, F-17) |
