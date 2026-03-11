# Derailment Test: What Worked Well — build-skills

## Purpose

Per test-skill-quality methodology, derailment notes must include a "What worked well" section. This note expands on the highlights from the friction log with specific evidence.

---

## 1. Workspace-first discipline genuinely improved outcomes

**Evidence:** When I followed Step 3 literally and inventoried the skill repo before searching remotely, I discovered:
- The repo already had 19 skills with established naming conventions (verb-prefix)
- NAMING.md had a 360-line naming standard that would have been violated without local inspection
- CONTRIBUTING.md had quality gates that shaped the entire approach

Without workspace-first, I would have started with the downloaded `mcp-expert` skill and tried to adapt it. That would have produced a rename-clone, not an original skill.

**Transferable principle:** Workspace-first is the single most valuable rule in the skill. It prevented the most common failure mode (copying the best-looking source).

---

## 2. Comparison table caught critical quality differences

**Evidence:** The downloaded sources ranged wildly in quality:
- `fastmcp`: 2,614 lines, bloated with templates embedded in SKILL.md
- `mcp-expert`: 178 lines, clean progressive disclosure, good reference routing
- `mcp-server-builder`: 968 lines, monolithic, no reference files
- `converting-mcps-to-skills`: 125 lines, focused, good script integration

Without a comparison table, I would have gravitated toward `mcp-server-builder` (most detailed) or `fastmcp` (most comprehensive). The table forced me to evaluate each source's strengths AND weaknesses, leading to the correct decision: inherit `mcp-expert`'s structure and `converting-mcps-to-skills`'s focused scope, avoid `fastmcp`'s bloat.

**Transferable principle:** Forcing structured comparison before synthesis is the second most valuable rule.

---

## 3. Reference routing table is excellent UX

**Evidence:** The routing table at the bottom of SKILL.md maps 22 files to specific "read when" conditions. During execution, I used it 4 times:
1. Step 2: Found `workflow-patterns.md` and `mcp-enhancement.md`
2. Step 4: Found `research-workflow.md` and `remote-sources.md`
3. Step 7: Found `description-engineering.md` and `master-checklist.md`
4. Step 9: Found `naming-conventions.md`

Each time, I loaded only the file I needed, saving significant context tokens. Without the table, I would have loaded all 22 files upfront.

**Transferable principle:** Every skill with reference files should have a conditional routing table.

---

## 4. Guardrails and recovery section is practical

**Evidence:** The recovery moves section addressed real problems I encountered:
- "Local evidence is thin or contradictory: say so, then widen the evidence set" — I used this when the MCP SDK repo had different patterns than the downloaded skills
- "Draft is bloating: move detail to existing references or delete it" — I used this when synthesizing tool design patterns

The recovery moves are actionable (specific steps) rather than aspirational (vague guidance).

---

## 5. Decision rules prevent common traps

**Evidence:** Two rules specifically saved me from mistakes:
- "If the draft starts resembling one source too closely, stop and convert the source notes into inherit/avoid decisions" — I noticed my first draft looked too much like `mcp-expert` and restructured
- "If the skill grows because of examples, templates, or long checklists, move that detail to references or cut it" — I moved 3 code examples to what would become reference files

---

## 6. Non-negotiable rules provide clear guardrails

The 7 non-negotiable rules are:
1. Workspace first ✓ (enforced my behavior)
2. Research before synthesis for non-trivial work ✓ (prevented shortcuts)
3. `skills.markdown` is the proof ✓ (created accountability)
4. Comparison before combination ✓ (prevented blending)
5. Original, repo-fit output only ✓ (prevented cloning)
6. Progressive disclosure ✓ (kept SKILL.md lean)
7. Test before shipping ✓ (caught issues in Step 8)

All 7 influenced my behavior positively. None felt arbitrary.

---

## Summary: What to preserve during fixes

When applying friction point fixes, these elements MUST be preserved:
- [ ] Workspace-first sequencing (Steps 1-3 before Step 4)
- [ ] Comparison table as a required gate (Step 5 before Step 7)
- [ ] Reference routing table format and completeness
- [ ] Non-negotiable rules (all 7)
- [ ] Decision rules section
- [ ] Recovery moves section
- [ ] Progressive disclosure philosophy
- [ ] "Do this, not that" table content (even if repositioned)
