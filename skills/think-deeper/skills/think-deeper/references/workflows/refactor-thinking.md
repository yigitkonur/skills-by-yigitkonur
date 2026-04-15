# Refactor Thinking

Refactoring means improving structure while protecting behavior.

## First Questions

- What must not change?
- What hurts in the current structure?
- What seam can I use to change one thing at a time?

If the invariants are not explicit, the refactor is not ready.

## Refactor Loop

1. name the invariants
2. identify the structural problem
3. find the narrowest seam
4. plan the change in small stages
5. verify behavior after each stage
6. stop when the structural goal is reached

## Common Invariants

- public API behavior
- data contracts
- error semantics
- persistence behavior
- test expectations
- performance thresholds that matter

## One-Axis Rule

Change one axis at a time:
- move code
- rename boundaries
- extract abstraction
- swap implementation

Do not mix several large axes in one reasoning pass unless they are inseparable.

## Good Refactor Thinking

- behavior is protected explicitly
- structural pain is named clearly
- the path has rollback points
- the end state is simpler, not just different

## Bad Refactor Thinking

- using refactor language to hide a redesign
- changing behavior "while here"
- extracting abstractions before proving they are needed
- moving too much code before a stable seam exists
