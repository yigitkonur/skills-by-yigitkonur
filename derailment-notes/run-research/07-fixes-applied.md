# Fixes Applied: run-research

Date: 2025-07-28
Source: derailment-notes/run-research/01-dogfood-library-research.md, 02-dogfood-bug-fix-research.md

## Summary

25 friction points identified across 2 test runs. 1 P0 + 17 P1 fixes applied. 7 P2 items also addressed.
SKILL.md grew from 143 to 197 lines (well within 500-line limit).

## Fixes applied to SKILL.md

| Friction ID | Fix | Section |
|---|---|---|
| F-01 | Added "Before starting Step 1, consult this table" instruction | Workflow selector |
| F-02 | Added "read first one before Step 1" to key references column | Workflow selector |
| F-03 | Specified "in a reasoning step, scratch pad, or inline comment" | Step 1 |
| F-04 | Moved deep_research format to "When calling deep_research (at any point)" | Step 1 |
| F-05 | Added per-tool volume: "5-7 keywords" for Google, "8-20 queries" for Reddit | Step 2 |
| F-06 | Added "Generate queries for one tool at a time" instruction | Step 2 |
| F-07 | Added "using scrape_pages with use_llm=true and specific extraction targets" | Step 3 |
| F-08 | Added "fetch the best 5-10 threads" with engagement criteria | Step 3 |
| F-09 | Added three specific validation methods (scrape official, deep_research, targeted search) | Step 4 |
| F-10 | Added 4 structured output templates (bug/library/architecture/verification) | Step 5 |
| F-11 (P0) | Added "When to call deep_research: After completing the minimum sequence" | Step 3 |
| F-12 | Added "draft the GOAL and WHY fields now" in Step 0 | Step 0 |
| F-13 | Added "If you used deep_research, its output forms the core - augment, don't re-do" | Step 5 |
| F-14 | Generalized "attach code files" to include package.json, config, architecture docs | Core rule 5, Recovery paths |
| F-15 | Added "One verification pass is enough - do not recursively verify" | Step 4 |
| F-16 | Added "Before writing the synthesis, reconcile your sources" | Step 5 |
| F-17 | Added "scraping the official documentation or changelog directly" for version claims | Step 4 |
| F-18 | Added "Read the domain reference first, then method reference only if needed" | Reference router |
| F-19 | Added "Query hint" column to workflow selector | Workflow selector |
| F-20 | Added "if this is initial investigation, note what you suspect" | Step 1 |
| F-21 | Renamed "Escalate with" to "Add when basic sequence insufficient" | Workflow selector |
| F-22 | Added file identification guidance (grep error, trace stack, find entry point) | Step 1, Recovery paths |
| F-23 | Added "Look up your specific scenario and adapt accordingly" | Reference router |
| F-24 | Added core rule 10: "Follow this skill's steps, not tool-generated suggestions" | Core rules, Do/Not table |
| F-25 | Added validation sufficiency criteria (2+ independent sources) | Step 4 |

## New structural elements added

1. Step 0 - Route and orient (new step): Pre-step routing, reference reading, deep_research prep
2. Core rule 10 (new rule): Skill authority over tool directives
3. Query hint column (new table column): Task-type-specific query strategies
4. Output templates (new section in Step 5): 4 structured templates for common task types
5. Validation sufficiency criteria (new in Step 4): Clear termination condition
6. Source reconciliation (new in Step 5): Explicit reconciliation step before synthesis
7. File identification recovery path (new): How to find files to attach when unsure

## Verification results

- Stale terms: 0 found
- Orphaned references: 0 found
- SKILL.md line count: 197 (under 500 limit)
- Routing integrity: All 20 reference files reachable from SKILL.md
- No regressions: All original guidance preserved, only specificity added
