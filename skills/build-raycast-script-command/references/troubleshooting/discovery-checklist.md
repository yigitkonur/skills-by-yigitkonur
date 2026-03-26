# Discovery Checklist

Use this file when the command does not appear in Raycast or does not seem to be recognized.

## First Checks

1. Does the filename still contain `.template.`?
2. Are all required metadata fields present?
3. Are metadata comments written with `#`?
4. Is the file in a directory actually added to Raycast via `Add Script Directory`?

## Common Causes

| Symptom | Likely cause |
|---|---|
| command never appears | `.template.` still in filename |
| command not recognized | missing `schemaVersion`, `title`, or `mode` |
| metadata ignored | wrong comment syntax or metadata not placed correctly |
| command appears under odd package label | `packageName` omitted and inferred from directory |

## Fast Fix Pattern

Start from a minimal known-good top block:

```python
#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title Example
# @raycast.mode fullOutput
# @raycast.packageName Examples
```

Then add other fields back only as needed.

## What not to chase first

Do not start by rewriting the whole script. Discovery failures are usually simpler:

- bad filename
- missing metadata
- metadata comment syntax problem
- script directory not added in Raycast

## Escalation

If the command appears but behaves strangely, switch to:

- `references/troubleshooting/runtime-and-output-issues.md`
- `references/metadata/mode-selection.md`
