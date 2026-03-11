# Observation: Assumed Knowledge Throughout Skill

Date: 2025-07-12
Related friction points: F-04, F-05, F-09, F-12, F-18, F-20

---

SKILL.md uses domain terms without inline definitions:
- 5W2H (step 2 gate condition)
- Type 1/Type 2 (step 4 depth calibration)
- Decision matrix (step 3 method table)
- Decision Frame (output contract section 4)

This is an expert blind spot -- the skill was written by someone deeply familiar with the reference library. The terms are defined in reference files, but the workflow never directs the executor to load those files.

## Fix Applied

Inlined minimum viable definitions:
- 5W2H: "Who, What, Where, When, Why, How, How-much" in step 2
- Type 1/Type 2: "Type 1 = hard to reverse, high blast radius; Type 2 = reversible, low blast radius" in step 4
- Decision Frame: "The decision, who decides, constraints, and deadline" in output contract
- facts/assumptions: "A fact has observable evidence you can point to; an assumption is an unverified belief" in step 2
