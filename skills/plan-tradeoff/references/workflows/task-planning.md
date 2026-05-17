# Task Planning

Operation: **universal** — any Op can need planning when the work is large or fuzzy enough to need slicing. The slicing primitive (MECE-clean, verifiable, small-enough-to-reason-about) applies regardless of Op.

Planning is the act of turning a large or fuzzy task into a sequence of clear moves without pretending that uncertainty does not exist.

## Plan Around These Fields

- desired outcome
- constraints
- unknowns
- dependencies
- ordered work slices
- verification

## Planning Loop

1. define the outcome
2. list the constraints and unknowns
3. break the work into slices
4. order the slices by dependency
5. keep one active slice at a time
6. revise the plan when evidence changes it

## Slice Quality

A good slice is:
- small enough to reason about
- large enough to matter
- verifiable on its own
- **MECE-clean** with its siblings — mutually exclusive (no overlap), collectively exhaustive (covers the work)

Bad slices are:
- vague
- bundled across unrelated concerns
- impossible to verify independently
- overlapping with other slices (leaks ownership, double-counts effort)

For complex plans where MECE is hard to confirm, route via the SKILL.md master table to `frameworks/decomposition-tools.md` (Issue Trees with the MECE constraint, or Ishikawa for multi-category breakdowns).

## Replanning Rule

Do not treat the first plan as sacred.

Update the plan when:
- a dependency was wrong
- a hidden constraint appeared
- the current slice expanded beyond its budget
- a simpler path emerged

Planning is successful when it reduces confusion without pretending the future is fully known.
