# coder mission template

Copy this into a markdown file when you want a worker to implement or modify code.

~~~~md
---
cwd: .
label: replace-with-short-task-label
effort: medium
context_files:
  - path/to/extra-context.md
base_instructions_file: path/to/guardrails.md
---

## Objective

Make the required code change and carry it through verification.

## Scope

- Files or directories the worker owns:
- Existing files it may edit:
- New files it may create:

## Constraints

- Do not touch:
- Preserve:
- Follow any repo conventions already present in the touched files.

## Required checks

Run these commands before finishing:

```bash
npm test
```

## Deliverable

- Implement the change.
- Report the touched files.
- Report the verification results.
~~~~

Tighten the scope before raising effort.
