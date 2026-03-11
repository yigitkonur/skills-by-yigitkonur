# Observation: Missing Method Execution Step

Date: 2025-07-12
Related friction points: F-10, F-16

---

The workflow has a structural gap: Step 3 chooses a method, Step 4 gathers evidence, Step 5 decides. But the actual method execution (filling in the decision matrix, running 5 Whys, etc.) never appears as an explicit step.

## Impact

The executor chooses "decision matrix" in step 3, then in step 4 gathers evidence, but never receives the instruction to actually populate the matrix with that evidence. Method execution falls into the gap between steps 3 and 4.

## Fix Applied

Merged method execution into step 4, renaming it to "Build evidence, apply the method." Added explicit instruction: "Execute the chosen method on gathered evidence. If the method has a template (matrix rows, root cause tree), fill it now."
