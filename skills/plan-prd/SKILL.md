---
name: plan-prd
description: Use skill if you are writing a PRD, product requirements document, feature spec, or requirements document with structured discovery, codebase-grounded analysis, and AI-agent-actionable output.
---

# Plan PRD

Create AI-agent-actionable Product Requirements Documents through structured discovery, codebase-grounded analysis, and iterative drafting.

## Trigger boundary

Use this skill when:
- Starting a new product or feature development cycle
- Translating a vague idea into a structured requirements document
- A stakeholder needs a "source of truth" for what to build and why
- User asks to "write a PRD", "spec this out", "document requirements", or "plan a feature"

Do NOT use when:
- Decomposing an existing PRD into issues (use `plan-issue-tree`)
- Writing a technical design doc without product requirements context
- Creating a bug report or incident postmortem
- The task is a small bug fix that does not need formal requirements

## Format decision

Before starting the full workflow, assess what format fits:

| Situation | Format | Action |
|---|---|---|
| New feature or product with multiple stakeholders | Full PRD | Follow the complete workflow below |
| Small enhancement with clear scope | Lightweight PRD | Skip Phase 2 edge case analysis, use abbreviated template |
| AI/ML feature where behavior is hard to specify in prose | Eval-first PRD | Add evaluation criteria section, consider "demos before memos" |
| Problem is already well-understood by the team | User stories only | Skip to Phase 3 and draft stories + acceptance criteria directly |

Ask the user which format fits if unclear. Default to Full PRD. Read `references/discovery/format-decision.md` for detailed guidance.

## Workflow

### Phase 1: Discovery (mandatory — never skip)

Gather context before writing a single line of the PRD.

**Step 1 — Gather the problem space.** Ask the user:
- What problem are we solving, and for whom?
- Why does this matter now? (If they cannot explain why now vs. later, the priority is questionable.)
- What does success look like? How will we measure it?
- Are there constraints? (Tech stack, timeline, budget, compliance)
- What have we already tried or considered?

Do not assume answers. Label unknowns as `TBD` rather than inventing constraints.

**Step 2 — Explore the codebase (mandatory for feature work).**
Read the relevant parts of the existing codebase:
- Identify existing architecture, patterns, and conventions
- Find related modules, APIs, or components the feature will touch
- Note test patterns and prior art for testing
- Understand data models, schemas, and integration points

**Step 3 — Interview relentlessly.**
Walk down each branch of the design tree, resolving dependencies between decisions one by one. Do not move on until you reach a shared understanding with the user.

Key areas: user flows, data requirements, integration points, permissions, performance expectations (with numeric thresholds), rollout strategy.

For structured elicitation questions, read `references/discovery/elicitation-questions.md`.

### Phase 2: Analysis

**Step 4 — Codebase-aware edge case analysis.**
Scan the codebase for existing patterns before asking the user about edge cases. Classify each edge case:

| Status | Meaning |
|---|---|
| Auto-handled | Existing pattern covers this; document the pattern |
| User-confirmed | Asked the user; captured their decision |
| Open | Needs stakeholder input; mark as `TBD` in the PRD |

**Step 5 — Architecture options (when applicable).**
For significant architectural decisions, sketch 2-3 options with Pros / Cons / Effort. Present to the user. Do not prescribe architecture — describe trade-offs and let them decide.

### Phase 3: Drafting

**Step 6 — Write the PRD.**
Use the template in `references/templates/prd-template.md`. The PRD has 10 sections:

1. **Problem Statement** — Who / What / Why / Evidence
2. **Why Now?** — Strategic timing and urgency
3. **Success Metrics** — Primary (ONE metric), Secondary, Guardrail (what must NOT get worse)
4. **User Personas** — 2-3 personas with goals, pain points, behaviors
5. **User Stories + Acceptance Criteria** — Numbered, extensive, atomic/measurable/binary
6. **Solution Overview + Implementation Decisions** — High-level approach, decisions, module sketch
7. **Technical Constraints + NFRs** — Performance, security, accessibility with numeric thresholds
8. **Testing Strategy** — What to test, how, prior art from codebase
9. **Out of Scope + Non-Goals** — What we are NOT building and why
10. **Risks, Dependencies, Open Questions** — Known unknowns with mitigation plans

### Phase 4: Validation

**Step 7 — Quality review.**
Validate against these checks before presenting:

- [ ] Every requirement is concrete and measurable (no "fast", "easy", "intuitive" without thresholds)
- [ ] Acceptance criteria are atomic, binary (pass/fail), and verb-first
- [ ] Success metrics have baseline AND target values
- [ ] Out of Scope section exists with clear rationale
- [ ] No file paths or code snippets (they become outdated quickly)
- [ ] All unknowns labeled `TBD` with owner or next step
- [ ] Non-functional requirements have numeric thresholds
- [ ] PRD can be decomposed into 5-15 minute execution blocks for an AI agent

For the full checklist, read `references/quality/prd-checklist.md`.

**Step 8 — Present and iterate.**
Ask the user: Does the problem statement capture the pain? Are the success metrics right? Is anything missing from user stories? Are technical constraints accurate? Should anything move in/out of scope?

### Phase 5: Finalization

**Step 9 — Output.**
Write the finalized PRD to:
- **GitHub Issue**: `gh issue create` with the PRD as body
- **File**: `docs/prd/{feature-name}.md` or the project's convention
- **Both**: Create the file AND the GitHub issue linking to it

**Step 10 — Optional decomposition.**
Break the PRD into vertical slices (tracer bullets) — thin end-to-end slices through ALL integration layers, NOT horizontal layer-by-layer slices. Classify each slice as HITL (needs human decision) or AFK (autonomous implementation). Read `references/templates/decomposition-guide.md`.

## Requirements quality standards

Write concrete, measurable requirements:

```diff
# Vague (BAD)
- The search should be fast and return relevant results.
- The UI must look modern and be easy to use.
- The system should handle errors gracefully.

# Concrete (GOOD)
+ Search returns results within 200ms for datasets up to 10K records.
+ Search achieves >= 85% Precision@10 on the benchmark eval set.
+ UI follows the project's design system; scores 100% on Lighthouse Accessibility.
+ All API errors return structured JSON with error code, message, and retry guidance.
```

## Common pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Skipping discovery | PRD contains invented constraints | Go back to Phase 1; ask at least 3 clarifying questions |
| Vague requirements | "Should be fast", "user-friendly" | Add numeric thresholds to every performance/quality claim |
| Solution-first thinking | PRD describes implementation, not outcomes | Rewrite to focus on what the user needs, not how to build it |
| Missing "Why Now?" | No urgency rationale | Add strategic context; if no urgency, flag to user |
| No guardrail metrics | Feature succeeds but breaks adjacent behavior | Add "what must NOT get worse" metrics |
| PRD as waterfall spec | 40-page document nobody reads | Keep under 150-200 discrete requirements; phase into blocks |
| File paths in PRD | PRD outdated within days | Use module/component names, not file paths |

## Reference routing

### Discovery
| File | Read when |
|---|---|
| `references/discovery/elicitation-questions.md` | Conducting the Phase 1 interview; need structured questions by category |
| `references/discovery/format-decision.md` | Deciding between Full PRD, Lightweight, Eval-first, or Stories-only |

### Templates
| File | Read when |
|---|---|
| `references/templates/prd-template.md` | Drafting Phase 3; need the full 10-section template with per-section guidance |
| `references/templates/decomposition-guide.md` | Phase 5 decomposition into vertical slices and GitHub issues |

### Quality
| File | Read when |
|---|---|
| `references/quality/prd-checklist.md` | Phase 4 validation; running the full quality audit |
| `references/quality/acceptance-criteria-guide.md` | Writing acceptance criteria; need format guidance and examples |
| `references/quality/anti-patterns.md` | Reviewing the PRD for common mistakes with symptom/fix patterns |

### Examples
| File | Read when |
|---|---|
| `references/examples/good-prd-example.md` | Need a worked example of a complete PRD |
| `references/examples/requirements-quality.md` | Need vague-vs-concrete examples for calibrating requirement quality |

## Minimal reading sets

### "I need to write a PRD from scratch"
- `references/discovery/elicitation-questions.md`
- `references/templates/prd-template.md`
- `references/quality/prd-checklist.md`

### "I need to improve an existing PRD"
- `references/quality/prd-checklist.md`
- `references/quality/anti-patterns.md`
- `references/examples/requirements-quality.md`

### "I need to break a PRD into implementation tasks"
- `references/templates/decomposition-guide.md`
- `references/quality/acceptance-criteria-guide.md`

## Guardrails

- Do not write the PRD before completing discovery. Ask at least 3 clarifying questions first.
- Do not include file paths or code snippets in the PRD. Use module/component names.
- Do not use vague language without thresholds. Every "fast", "secure", "scalable" needs a number.
- Do not prescribe architecture. Describe trade-offs; let the team decide.
- Do not skip codebase exploration for feature work.
- Do not hallucinate constraints. If the user did not specify, ask or label `TBD`.
- Do not create a monolithic PRD exceeding 200 discrete requirements.

## Final reminder

This skill produces a PRD, not an implementation plan. The PRD defines WHAT to build and WHY. For HOW, use `plan-work` or `plan-issue-tree` after the PRD is approved. Load only the reading set that matches your current phase.
