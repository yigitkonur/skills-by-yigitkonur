# Derailment Test: run-research on "Bug fix research — ERR_HTTP_HEADERS_SENT in Fastify"

Date: 2025-07-28
Skill under test: run-research
Test task: Research why Fastify throws ERR_HTTP_HEADERS_SENT under high concurrency with async handlers; find root cause and fix pattern
Method: Follow SKILL.md steps 1–5 exactly as written, using Workflow Selector for Pattern A (Bug Fix)

---

## Pre-scan summary

Same skill as test 01. Reusing pre-scan from first run.
Testing a different workflow path (Bug Fix vs. Library Research) to exercise different routing and reference files.

---

## Friction points

### Workflow Selector

**F-19 — Bug fix workflow has same starting tool as library research** (P2)
The workflow selector routes both "Bug fix / error message" and "Library or dependency choice" to start with `search_google`. While this happens to be correct for both, the identical routing obscures whether the skill is truly differentiating between task types or treating them the same.
Root cause: M4 (Scope flattening)
Fix: Consider adding a "Query strategy hint" column that says "Bug fix: paste exact error message" vs "Library choice: compare named alternatives."

**F-20 — "What you already tried" assumption in framing** (P2)
Step 1 implies the researcher has already attempted solutions ("what you already tried"). For first-investigation research, this field is empty but the skill doesn't acknowledge that case or say to skip it.
Root cause: S4 (Missing conditional)
Fix: Add "If this is initial investigation rather than a stuck debug session, note what you suspect and what you plan to try."

### Workflow escalation

**F-21 — "Escalate" column is ambiguous: additive or replacement?** (P1)
The workflow selector has an "Escalate with" column showing `search_reddit, deep_research with attached code`. It's unclear if "escalate" means "do these IN ADDITION TO the minimum sequence" or "switch to these IF the minimum sequence fails." This matters because it changes whether Reddit is mandatory or optional for bug fixes.
Root cause: M1 (Vague referent)
Fix: Change column header from "Escalate with" to "Add when minimum sequence is insufficient" and add a footnote: "Always complete the minimum sequence first. Add escalation tools one at a time until the answer is clear."

### File attachment

**F-22 — "Attach code files" has no file selection guidance** (P1)
The workflow selector says "deep_research with attached code" but for a project with hundreds of files, HOW do I identify which files are relevant? Grep for the error? Read stack traces? The skill assumes the user already knows which files matter.
Root cause: S2 (Missing prerequisite)
Fix: Add to Step 1 or recovery paths: "To identify files for attachment, grep the codebase for the error message, trace the stack trace to source files, or find the entry point (route handler, middleware) where the error originates."

### Reference usage

**F-23 — Domain reference usage pattern undefined** (P1)
The workflow selector points to `references/bug-fixing.md` but SKILL.md doesn't explain HOW to use it. The reference file has 10 bug types with specific tool recommendations — should I look up my bug type and follow its sequence? Override the workflow selector? Use it as supplementary context?
Root cause: O5 (Missing method specification)
Fix: Add to the reference router: "Domain references provide task-specific patterns. Look up your specific scenario (e.g., 'race condition' in bug-fixing.md) and adapt the tool sequence from the workflow selector accordingly."

### Tool vs. skill authority

**F-24 — Tool-generated directives conflict with skill steps** (P1)
The deep_research and search_google tools return "Next Steps (DO NOT SKIP)" banners with their own workflow recommendations. The skill's steps 1–5 also prescribe a workflow. The agent doesn't know whether to follow the tool's directives or the skill's steps. This is especially confusing when the tool says "VERIFY FINDINGS" but the skill's Step 4 already covers validation.
Root cause: M3 (Conflicting instructions)
Fix: Add to core rules: "Follow the skill's steps, not tool-generated next-step suggestions. Tool outputs may suggest additional actions — treat these as optional unless they reveal a gap the skill's workflow didn't cover."

**F-25 — Unclear when tool validation replaces skill validation** (P1)
deep_research internally cross-references sources and provides confidence levels. Step 4 says "validate before concluding." If deep_research already validated, should the agent do additional validation? The skill doesn't define "sufficiency criteria" for validation.
Root cause: S3 (Missing threshold)
Fix: Add to Step 4: "Validation is sufficient when: (a) at least 2 independent sources confirm the key claim, AND (b) no source contradicts it without resolution. If deep_research provided sourced answers with 2+ references, you can proceed to synthesis."

---

## What worked well

1. **Error message as search query was highly effective.** Pasting `ERR_HTTP_HEADERS_SENT` directly into search_google produced targeted results.
2. **deep_research with file attachment was powerful.** Attaching the actual `reply.js` source gave context-aware answers about Fastify internals.
3. **The GOAL/WHY/KNOWN/APPLY format for deep_research worked excellently.** The structured query produced a comprehensive analysis with specific code patterns.
4. **Reddit search found relevant community discussions.** Even for a technical bug, Reddit had useful experience reports.
5. **The minimum sequence (search_google → scrape_pages) was sufficient for this bug.** The escalation to deep_research added depth but wasn't strictly necessary — good sign that the minimum is correctly calibrated.

---

## Derailment density map

| Phase | Derailments | Severity |
|---|---|---|
| Workflow selector | 2 (F-19, F-20) | 2×P2 |
| Escalation guidance | 1 (F-21) | 1×P1 |
| File attachment | 1 (F-22) | 1×P1 |
| Reference usage | 1 (F-23) | 1×P1 |
| Tool vs skill authority | 2 (F-24, F-25) | 2×P1 |
| **Total** | **7** | 0×P0, 5×P1, 2×P2 |

**Hotspot:** Tool-vs-skill authority — the interaction between tool-generated directives and skill steps needs clarification.

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 0 | — |
| P1 | 5 | F-21, F-22, F-23, F-24, F-25 |
| P2 | 2 | F-19, F-20 |
| **Total** | **7** | |

---

## Cross-run comparison (Test 01 vs Test 02)

| Metric | Test 01 (Library) | Test 02 (Bug Fix) |
|---|---|---|
| Total friction points | 18 | 7 |
| P0 | 1 | 0 |
| P1 | 12 | 5 |
| P2 | 5 | 2 |
| Hotspot | Workflow integration | Tool authority |

Test 02 had fewer friction points because: (a) fewer tools were needed (simpler minimum sequence), and (b) the framing step (Step 1) was more natural for bug fixes (concrete error message vs. abstract comparison). The library research path exercises more of the skill's surface area and exposes more gaps.
