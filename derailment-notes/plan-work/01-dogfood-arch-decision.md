# Derailment Test: plan-work on "Monolith vs Event-Driven Microservices"

Date: 2025-07-12
Skill under test: plan-work
Test task: Decide whether to keep a monolithic Express.js API or split into event-driven microservices, given reliability complaints during peak usage, a 6-week timeline, and 2 engineers with distributed-systems experience.
Method: Follow SKILL.md steps 1-6 exactly as written.

---

## Pre-scan summary

| Property | Value |
|---|---|
| SKILL.md lines | 199 |
| Workflow steps | 6 (Classify, Frame, Choose method, Evidence, Decide, Package) |
| Reference files | 9 domain files + 1 README |
| External dependencies | None (pure planning skill) |
| Quality gates | 1 final gate (7 checkboxes), 1 done-conditions list (6 items) |
| Output contract sections | 9 |

---

## Friction points

### Step 1: Classify the planning job

**F-01** (P1, M1) No tiebreaker when two planning jobs seem equally dominant. The instruction says "Pick one dominant job first" from 6 modes. For the test task, "compare options" and "diagnose a cause" both apply. No tiebreaking rule given.
Fix: Add tiebreaker and precedence ordering.

**F-02** (P1, M2) "State it explicitly" gives no format or placement guidance. Where should the classification be stated?
Fix: State it in the output. This becomes section 2 of the output contract.

**F-03** (P2, M6) "Do not run every planning mode at once" has no exception path for genuine multi-mode tasks.
Fix: Complete the first mode fully, then start a second pass.

### Step 2: Frame the mission

**F-04** (P0, S3) 5W2H referenced as gate condition but never defined in SKILL.md. Defined only in ref 01, but reference router would not send you there for a non-vague request.
Fix: Inline 5W2H (Who, What, Where, When, Why, How, How-much).

**F-05** (P1, M5) "facts vs. assumptions" has no separation methodology.
Fix: A fact has observable evidence; an assumption is unverified belief.

**F-06** (P1, O3) "critical unknowns have no owner" assumes organizational context.
Fix: For AI agents: owner = who can answer; resolve-by = can planning proceed without it.

**F-07** (P1, M4) "decision-ready gap list" format is undefined.
Fix: Numbered list: (a) missing info, (b) who provides, (c) what it blocks, (d) suggested default.

**F-08** (P1, M1) "success cannot be observed" is subjective without examples.
Fix: Add "(no metric, test, or outcome you could check)."

### Step 3: Choose method

**F-09** (P0, M5) Method table assumes executor knows what each method IS. "Decision matrix" named but never defined. Reference router exists but workflow never invokes it.
Fix: Add: Consult the reference router to load the reference file for your method.

**F-10** (P0, S2) No explicit "execute the method" step. Steps go choose->evidence->decide, but method execution falls in a gap.
Fix: Merge method execution into step 4.

**F-11** (P1, M1) "closes a clear gap" is undefined.
Fix: Add "a companion only if primary method cannot answer a question the user explicitly asked."

### Step 4: Build evidence

**F-12** (P1, M5) Type 1/Type 2 used but never defined.
Fix: Inline "Type 1 = hard to reverse, high blast radius. Type 2 = reversible, low blast radius."

**F-13** (P1, M6) "understand current system behavior" is vague.
Fix: Replace with "document architecture, failure modes, and performance characteristics."

**F-14** (P1, O3) Evidence hierarchy unclear for AI-agent context.
Fix: Add codebase-specific examples for each evidence tier.

### Step 5: Decide

**F-15** (P1, M3) Output shapes miss 2 of 6 planning jobs ("frame the problem", "align people").
Fix: Add missing mappings.

**F-16** (P1, M4) "Always include a fallback option" but options were never generated.
Fix: Add option generation instruction before deciding.

### Step 6: Package

**F-17** (P0, S2) "Two layers" structure contradicts 9-section output contract. Both claim default.
Fix: Step 6 references output contract. First 4 sections = decision brief; rest = execution detail.

**F-18** (P1, M5) No audience detection mechanism.
Fix: If audience unknown, use output contract order.

### Quality/Output

**F-19** (P1, S2) Quality gate (7 items) and done conditions (6 items) overlap but differ.
Fix: Clarify: done conditions = substantive completeness; quality gate = communication quality.

**F-20** (P2, M5) "Decision Frame" in output contract is undefined.
Fix: Define inline.

### Cross-cutting

**F-21** (P1, M4) Reference router never invoked by workflow. Covered by F-09 fix.

**F-22** (P2, S3) Stance says "preferences" but step 2 omits it.
Fix: Sync step 2 to match stance.

**F-23** (P1, M4) Recovery paths unreachable from workflow.
Fix: Add pointers in steps 2 and 3.

**F-24** (P2, S2) Final reminder contradicts workflow.
Fix: Replace with constructive reference check.

**F-25** (P1, M1) No "enough evidence" definition.
Fix: Enough = can fill every method template cell + articulate why leader wins.

**F-26** (P1, M1) Skill boundary with run-research undefined.
Fix: plan-work = immediate context; run-research = original research.

---

## What worked well

1. Step 1 planning job classification prevents scope creep
2. Method table in step 3 is excellently curated with "Avoid" column
3. Anti-derail guardrails table is practical and scannable
4. Recovery paths cover real failure modes with actionable advice
5. 6-step structure is logical and covers the full planning lifecycle
6. Operating stance principle 3 (match depth to reversibility) is the best sentence in the skill
7. Reference router "Start with / Add only if" pattern prevents overload

---

## Density map

| Phase | P0 | P1 | P2 | Total |
|---|---|---|---|---|
| Step 1: Classify | 0 | 2 | 1 | 3 |
| Step 2: Frame | 1 | 4 | 0 | 5 |
| Step 3: Method | 2 | 1 | 0 | 3 |
| Step 4: Evidence | 0 | 3 | 0 | 3 |
| Step 5: Decide | 0 | 2 | 0 | 2 |
| Step 6: Package | 1 | 1 | 0 | 2 |
| Quality/Output | 0 | 1 | 1 | 2 |
| Cross-cutting | 0 | 4 | 2 | 6 |
| **Total** | **4** | **18** | **4** | **26** |

## Root causes

| Code | Name | Count |
|---|---|---|
| M4 | Missing execution method | 6 |
| M5 | Assumed knowledge | 5 |
| M1 | Ambiguous threshold | 5 |
| S2 | Contradictory instructions | 4 |
| M6 | Vague verb | 3 |
| S3 | Scattered information | 3 |
| O3 | Edge case unhandled | 3 |

## Priority summary

| Priority | Count |
|---|---|
| P0 | 4 (F-04, F-09, F-10, F-17) |
| P1 | 18 |
| P2 | 4 |
| Total | 26 |
