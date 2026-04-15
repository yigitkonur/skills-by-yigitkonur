# research mission template

Copy this into a markdown file when you want a worker to inspect a codebase, trace a workflow, or summarize findings before any edits happen.

~~~~md
---
cwd: .
---

## Objective

Investigate the target area and report concrete findings with file references.

## Label

replace-with-short-research-label

## Scope

- Focus on:
- Ignore:

## Questions to answer

1. What is the current behavior?
2. Which files or modules control it?
3. What risks or open questions remain?

## Constraints

- Do not make code changes.
- Prefer direct code evidence over guesses.

## Required checks

Run any read-only commands needed to support the findings.

## Deliverable

- Summarize the behavior.
- Include exact file paths.
- Call out risks, gaps, or likely next edits.
~~~~
