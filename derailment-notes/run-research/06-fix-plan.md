# Fix Plan: run-research SKILL.md

## Planned edits organized by SKILL.md section

### 1. Add pre-step instruction (before Step 1)
**Fixes:** F-01, F-02, F-18
**Edit:** Add a paragraph before Step 1 saying:
- Consult the Workflow Selector table FIRST to identify starting tool and sequence
- Read the first domain reference (e.g., library-research.md) for task-specific patterns
- Read method reference only if domain reference doesn't cover your scenario

### 2. Enhance Workflow Selector table
**Fixes:** F-19, F-21
**Edits:**
- Rename "Escalate with" to "Add when basic sequence insufficient"
- Add "Query hint" column with task-type-specific query strategies
- Add footnote: "Complete minimum sequence first. Add escalation tools one at a time."

### 3. Rewrite Step 1 — Frame
**Fixes:** F-03, F-04, F-12, F-20
**Edits:**
- Specify where to write framing: "in a reasoning step or scratch pad"
- Move deep_research format guidance to Step 3 or a dedicated sub-section
- Add "If initial investigation, note what you suspect and plan to try"
- Add "If your sequence includes deep_research, draft GOAL and WHY fields now"

### 4. Rewrite Step 2 — Generate queries
**Fixes:** F-05, F-06
**Edits:**
- Clarify queries are per-tool: "Generate queries for one tool at a time"
- Add specific volume guidance: "search_google: 5–7, search_reddit: 8–20"

### 5. Rewrite Step 3 — Read sources
**Fixes:** F-07, F-08, F-11
**Edits:**
- Map steps to tools: "Use scrape_pages with use_llm=true and specific extraction targets"
- Add thread selection: "Select 5–10 Reddit threads with highest engagement"
- Add deep_research placement: "Call deep_research after completing minimum sequence"

### 6. Rewrite Step 4 — Validate
**Fixes:** F-09, F-15, F-25
**Edits:**
- Specify methods: "Use scrape_pages on official docs, deep_research for counter-evidence, or targeted search_google"
- Add termination criteria: "Sufficient when 2+ independent sources confirm each key claim"

### 7. Rewrite Step 5 — Synthesize
**Fixes:** F-10, F-13, F-16
**Edits:**
- Add output templates per task type
- Clarify deep_research handling: "If deep_research was used, augment its output — don't re-do"
- Add source reconciliation step: "Identify agreements and disagreements before synthesizing"

### 8. Add new core rule
**Fixes:** F-24
**Edit:** Add rule: "Follow the skill's steps, not tool-generated next-step suggestions"

### 9. Update Recovery paths
**Fixes:** F-14, F-22
**Edits:**
- Generalize "attach code files" to "attach relevant files (code, config, architecture docs)"
- Add file identification guidance: "Grep for error message, trace stack to source, or find entry point"

### 10. Update Reference router
**Fixes:** F-17, F-23
**Edits:**
- Add domain reference usage instruction
- Specify version verification process

## Constraint: SKILL.md must stay under 500 lines
Current: 143 lines. Budget: ~357 lines for additions. Most fixes are sentence-level additions, so this is comfortably within budget.
