# Pre-scan: init-copilot-review

Skill under test: init-copilot-review
Date: 2025-07-18
Method: Pre-scan orientation before literal execution

---

## Skill structure

- **SKILL.md**: 170 lines (before fixes), 6 workflow steps, 1 reference routing table
- **references/**: 6 files (4,076 total lines)
  - setup-and-format.md — 293 lines
  - writing-instructions.md — 442 lines
  - scoping-and-targeting.md — 398 lines
  - troubleshooting.md — 404 lines
  - scenarios.md — 1,428 lines
  - micro-library.md — 941 lines

## Workflow steps

1. Ground on the repository before drafting
2. Choose the instruction architecture before writing prose
3. Select rules with evidence and reuse discipline
4. Draft files with scope-safe formatting
5. Validate before presenting anything
6. Present the result as an architecture, not just a dump

## Branching points

- Reference routing table (6 references, conditionally consulted)
- Placement logic table (5 rows, decides root vs scoped)
- Keep/Drop filter (4 rows, rule selection)
- Recovery paths (6 fallback paths)

## External dependencies

- Shell tools: wc, find, ls
- GitHub Copilot review (for instruction files to take effect)
- No MCP servers or APIs required

## Initial observations

1. Reference files are very large — scenarios.md alone is 1,428 lines
2. Skill says "do not read every reference by default" — good guard
3. No shell commands provided for Step 1 (repository inspection)
4. "Representative files" in Step 1 is undefined — how many? what criteria?
5. No stopping criterion for exploration in Step 1
6. "Recurring review themes" has no method — how to find them?
7. "High-signal rules" used in Step 2 but not defined
8. SMSA acronym used in reference routing but only expanded in Step 3
9. No frontmatter YAML example shown inline (only described in prose)
10. No method to verify glob patterns match intended files
