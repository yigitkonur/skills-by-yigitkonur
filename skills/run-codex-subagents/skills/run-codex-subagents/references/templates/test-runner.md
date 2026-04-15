# test runner template

Copy this into a markdown file when you want a worker focused on verification, reproduction, or test execution rather than general implementation.

~~~~md
---
cwd: .
---

## Objective

Run the required verification commands and explain the result precisely.

## Label

replace-with-test-task-label

## Scope

- Commands to run:
- Files to inspect if a check fails:

## Constraints

- Prefer diagnosis over speculative fixes unless the task explicitly asks for repair.
- Do not edit unrelated files.

## Required checks

```bash
npm run test:unit
```

## Deliverable

- Report pass or fail.
- Include the failing command when relevant.
- Include the smallest useful file references or logs that explain the result.
~~~~
