---
name: build-raycast-script-command
description: Use skill if you are building or repairing Raycast Script Commands in Python or Bash and need correct metadata, output modes, arguments, discovery, or runtime behavior.
---

# Build Raycast Script Command

Build Raycast Script Commands with correct metadata, mode selection, argument wiring, and runtime behavior.

## Trigger boundary

Use this skill when the task involves:

- Creating a new Raycast Script Command from scratch
- Converting an existing Python or Bash script into a Raycast Script Command
- Choosing between `fullOutput`, `compact`, `silent`, and `inline`
- Adding or fixing Script Command arguments
- Fixing why a Script Command does not appear in Raycast
- Fixing output, refresh, or failure behavior in a Script Command
- Making a Script Command more shareable or closer to Raycast community conventions

Do NOT use this skill for:

- Full Raycast Extensions API work with `@raycast/api`, React, List, Grid, Form, or Detail views
- General shell scripting that is not intended for Raycast
- General Python scripting that has no Raycast integration

If the project already imports `@raycast/api` or uses `ray build` / `ray develop`, stop and use a Raycast Extensions skill instead.

## Behavioral flow

### Step 1: Detect what exists

Inspect the current workspace before writing anything.

Look for:

- an existing `.py` or `.sh` file to convert
- metadata lines such as `@raycast.title`
- a request for a greenfield command vs a repair task
- whether the command is Python-first, Bash-first, or undecided

### Step 2: Choose the branch

Use this decision tree:

```text
User request
├─ "Create a new command from scratch"
│  ├─ Python is the best fit or unspecified
│  │  → Read references/foundations/workflow.md
│  │  → Read references/python/file-anatomy.md
│  │  → Read references/metadata/mode-selection.md
│  │  → Read references/examples/python-recipes.md
│  └─ Bash is clearly the best fit
│     → Read references/foundations/workflow.md
│     → Read references/bash/bash-script-patterns.md
│     → Read references/metadata/mode-selection.md
│     → Read references/examples/bash-recipes.md
│
├─ "Convert an existing script into a Raycast command"
│  → Read references/foundations/workflow.md
│  → Read references/metadata/required-fields.md
│  → Read references/conventions/dependencies-and-portability.md
│  → Read references/troubleshooting/discovery-checklist.md
│
├─ "Choose or change the output mode"
│  → Read references/metadata/mode-selection.md
│  → Read references/metadata/inline-refresh-and-errors.md
│
├─ "Add or fix arguments"
│  → Read references/arguments/typed-arguments.md
│  → Read references/python/implementation-patterns.md or references/bash/bash-script-patterns.md
│
├─ "Why doesn't this command show up in Raycast?"
│  → Read references/troubleshooting/discovery-checklist.md
│  → Read references/metadata/required-fields.md
│
├─ "Why does runtime behavior/output feel wrong?"
│  → Read references/troubleshooting/runtime-and-output-issues.md
│  → Read references/metadata/mode-selection.md
│  → Read references/metadata/inline-refresh-and-errors.md
│
├─ "Should this be Python or Bash?"
│  → Read references/foundations/language-selection.md
│
└─ "Make this repo-ready or shareable"
   → Read references/conventions/community-repo-conventions.md
   → Read references/conventions/dependencies-and-portability.md
```

### Step 3: Implement directly

Once the branch is clear:

1. Read only the routed references for that branch.
2. Build or edit the Script Command directly.
3. Use the templates in `assets/templates/` only as starting points, not rigid output.
4. Keep the implementation minimal and aligned with Raycast's documented behavior.

### Step 4: Validate before stopping

Always verify these:

- required metadata exists
- chosen `mode` matches the shape of output
- `inline` commands include `refreshTime`
- arguments match how the script reads positional inputs
- failure paths print a human-readable final line and exit non-zero
- dependency instructions exist when the command depends on extra tools or packages

## Core defaults

- Default to Python for API calls, JSON parsing, text processing, and richer logic.
- Default to Bash for tiny shell-native wrappers around existing CLIs or OS actions.
- Default to `fullOutput` if the result is meant to be read.
- Default to `compact` or `silent` for single-line confirmations or actions.
- Use `inline` only for dashboard-style, one-line status commands.

## Key patterns

### Pattern 1: minimal Python command

```python
#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title Example Python Command
# @raycast.mode fullOutput
# @raycast.packageName Examples

print("Hello from Raycast")
```

### Pattern 2: safe optional arguments in Python

```python
import sys

def arg(index: int, default: str = "") -> str:
    return sys.argv[index] if len(sys.argv) > index else default

query = arg(1)
```

### Pattern 3: clean failure path

```python
print("Missing API token")
raise SystemExit(1)
```

### Pattern 4: minimal Bash command

```bash
#!/usr/bin/env bash
set -euo pipefail

# @raycast.schemaVersion 1
# @raycast.title Example Bash Command
# @raycast.mode compact
# @raycast.packageName Examples

echo "Done"
```

## Minimal reading sets

### "Create a new Python Script Command"

- `references/foundations/workflow.md`
- `references/python/file-anatomy.md`
- `references/python/implementation-patterns.md`
- `references/metadata/mode-selection.md`
- `references/examples/python-recipes.md`

### "Create a new Bash Script Command"

- `references/foundations/workflow.md`
- `references/bash/bash-script-patterns.md`
- `references/metadata/mode-selection.md`
- `references/examples/bash-recipes.md`

### "Convert an existing script"

- `references/foundations/workflow.md`
- `references/metadata/required-fields.md`
- `references/conventions/dependencies-and-portability.md`
- `references/troubleshooting/discovery-checklist.md`

### "Add arguments"

- `references/arguments/typed-arguments.md`
- `references/python/implementation-patterns.md`
- `references/bash/bash-script-patterns.md`

### "Fix inline/compact/silent/fullOutput behavior"

- `references/metadata/mode-selection.md`
- `references/metadata/inline-refresh-and-errors.md`
- `references/troubleshooting/runtime-and-output-issues.md`

### "Make it community-repo ready"

- `references/conventions/community-repo-conventions.md`
- `references/conventions/dependencies-and-portability.md`
- `references/troubleshooting/discovery-checklist.md`

## Templates

When a user wants a quick scaffold, start from:

- `assets/templates/python-script-command.py`
- `assets/templates/bash-script-command.sh`

Then adapt the template to the user's exact mode, arguments, and dependencies.

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Using Extensions API concepts in a Script Command | Stop and switch skills; Script Commands are metadata plus normal script execution |
| Choosing `compact` for multi-line output | Move to `fullOutput` |
| Choosing `inline` without `refreshTime` | Add `refreshTime` or switch modes |
| Reading optional args unsafely | Guard Python `sys.argv` and Bash positional params |
| Leaving user-specific placeholders in a runnable file | Use `.template.` or fully configure the command |
| Missing dependency instructions | Add top-of-file dependency notes and readable missing-dependency failures |

## Reference files

| File | When to read |
|---|---|
| `references/foundations/scope-and-fit.md` | Read when deciding whether the task is really a Script Command and not a full Raycast extension. |
| `references/foundations/workflow.md` | Read when creating or converting a command and you need the end-to-end build flow. |
| `references/foundations/language-selection.md` | Read when deciding between Python and Bash. |
| `references/metadata/required-fields.md` | Read when adding or repairing metadata headers. |
| `references/metadata/mode-selection.md` | Read when choosing between `fullOutput`, `compact`, `silent`, and `inline`. |
| `references/metadata/inline-refresh-and-errors.md` | Read when working on inline refresh, first-line/last-line behavior, or failure semantics. |
| `references/arguments/typed-arguments.md` | Read when adding, changing, or debugging Script Command arguments. |
| `references/python/file-anatomy.md` | Read when creating a Python command file or checking placement of metadata and code. |
| `references/python/implementation-patterns.md` | Read when wiring `sys.argv`, dependency notes, failure messages, or Python output patterns. |
| `references/bash/bash-script-patterns.md` | Read when building or fixing a Bash-based Script Command. |
| `references/conventions/community-repo-conventions.md` | Read when the command should follow Raycast community-repo conventions. |
| `references/conventions/dependencies-and-portability.md` | Read when the command depends on tools/packages or must stay portable. |
| `references/troubleshooting/discovery-checklist.md` | Read when a command does not appear in Raycast or seems not to be recognized. |
| `references/troubleshooting/runtime-and-output-issues.md` | Read when output, refresh, or failure behavior is wrong. |
| `references/examples/python-recipes.md` | Read when you need concrete Python command patterns. |
| `references/examples/bash-recipes.md` | Read when you need concrete Bash command patterns. |
| `references/sources/source-map.md` | Read when you need the provenance for the internal references or want to expand the skill from the original Raycast research docs. |

## Guardrails

- Do not invent metadata fields that are not verified in Raycast-owned sources.
- Do not use Extensions API components or `@raycast/api` patterns in a Script Command.
- Do not choose `inline` without `refreshTime`.
- Do not emit noisy multi-line progress output for `compact`, `silent`, or `inline`.
- Do not read optional arguments unsafely; guard Python `sys.argv` access and shell `$2` / `$3` usage.
- Do not hide missing dependencies; document them and fail clearly.
- Do not leave `.template.` in a filename unless the command intentionally requires user edits before use.
- Do not bloat the response with generic shell or Python tutorials when the routed references already cover the needed pattern.

## Final check

Before stopping, make sure the command would pass a practical smoke test:

- visible metadata at the top
- plausible mode
- consistent argument count
- readable success/failure output
- no obvious mismatch between implementation language and task
