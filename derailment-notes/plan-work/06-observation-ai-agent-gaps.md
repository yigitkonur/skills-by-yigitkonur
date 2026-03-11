# Observation: AI-Agent Context Gaps

Date: 2025-07-12
Related friction points: F-06, F-14, F-18

---

The skill assumes human team context in several places:
- Step 2: "critical unknowns have no owner" -- implies organizational roles
- Step 4: Evidence hierarchy assumes access to team members and stakeholders
- Step 6: Audience detection assumes knowing who will read the output

For AI agents executing the skill in a coding assistant context, these assumptions create P1 friction because the instructions cannot be followed literally.

## Fix Applied

Added context-adaptive notes:
- Step 2: "For AI agents: owner = who can answer; resolve-by = can planning proceed without it?"
- Step 4: Codebase evidence examples (config files, test failures, git history)
- Step 6: "If audience unknown, default to output contract section order"
