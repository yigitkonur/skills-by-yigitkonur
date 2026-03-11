# What Worked Well: run-research Skill

## Strengths (preserve these during fixes)

### 1. Workflow Selector Table — Excellent Routing Mechanism
The workflow selector correctly routes different task types to appropriate tool sequences. Both test runs (library research and bug fix) were routed to effective starting tools. The table format is scannable and actionable.

**Preserve:** The table structure, the "Start with" and "Minimum sequence" columns, the task-type categorization.

### 2. 5-Step Framework — Sound Conceptual Pipeline
Frame → Query → Read → Validate → Synthesize mirrors how experienced researchers actually work. The progression from broad discovery to focused validation is correct.

**Preserve:** The 5-step structure, the step names, the conceptual progression.

### 3. Core Rules — Effective Guardrails
Rule 8 (fetch_comments=true, use_llm=false) prevented information dilution. Rule 2 (never deep_research with bare question) prevented poor-quality research. Rule 6 (verify version claims) caught potentially stale information.

**Preserve:** All 9 core rules. They're well-calibrated.

### 4. Reference File Organization — Excellent Knowledge Base
The reference files are comprehensive, well-organized (tools/, strategies/, queries/, synthesis/, fact-checking/, and domain files), and individually useful. Each tool reference has enough detail to use the tool effectively.

**Preserve:** The reference file structure, content quality, and organization.

### 5. Recovery Paths — Good Failure Handling
The recovery paths anticipate real failure modes ("If results are shallow," "If two sources disagree"). These provided actionable alternatives during execution.

**Preserve:** Recovery path section with specific scenarios.

### 6. Do This / Not That Table — Clear Anti-Patterns
The table caught real mistakes: "Run verification search before concluding" prevented premature confidence. "Scrape actual pages" prevented relying on snippets.

**Preserve:** The table format and specific entries.

### 7. deep_research Structured Format — High-Quality Output
The GOAL/WHY/KNOWN/APPLY format consistently produced excellent research results. This is the skill's most powerful technique.

**Preserve:** The format template and the requirement to use it.

### 8. Activation Boundary — Clear Scope
"Coding task that needs external information" is a precise and useful trigger. The exclusion of "internal code search" is helpful differentiation.

**Preserve:** The activation boundary text.

## Metrics Summary

| Metric | Test 01 (Library) | Test 02 (Bug Fix) | Combined |
|---|---|---|---|
| Total friction points | 18 | 7 | 25 |
| P0 | 1 | 0 | 1 |
| P1 | 12 | 5 | 17 |
| P2 | 5 | 2 | 7 |
| Clean passes | Low | Moderate | — |
| Tools exercised | 5/5 | 3/5 | 5/5 |
| Research quality | Excellent | Excellent | — |

Key insight: Despite 25 friction points, the skill produced **excellent research results** in both tests. The friction is primarily about **procedural clarity** (when/how to do things), not **conceptual soundness** (what to do). This means fixes should add specificity without restructuring.
