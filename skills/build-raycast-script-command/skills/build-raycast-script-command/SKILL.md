---
name: build-raycast-script-command
description: Use skill if you are building or repairing Raycast Script Commands in Python or Bash and need correct metadata, output modes, arguments, discovery, or runtime behavior.
---

# Build Raycast Script Command

Build Python or Bash Raycast Script Commands with correct metadata, output mode, argument wiring, discovery behavior, and runtime validation.

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

- Raycast Extensions API work: `@raycast/api`, React views, List/Grid/Form/Detail, `ray build`, `ray develop`, or extension-style `package.json` scaffolding
- Chrome extensions; use `build-chrome-extension`
- Browser automation or test flows; use `run-playwright` or `run-agent-browser` when available
- General Python or shell scripts with no Raycast Script Command integration

If the project is a Raycast Extension, do not use this skill; use project-specific Raycast Extension guidance if available.

## Workflow

### Step 1: Detect what exists

Inspect the current workspace before writing anything.

Look for:

- an existing `.py` or `.sh` file to convert
- metadata lines such as `@raycast.title`
- a request for a greenfield command vs a repair task
- whether the command is Python-first, Bash-first, or undecided

### Step 2: Route by task

Read only the branch-relevant references first.

| Task | Read |
|---|---|
| New Python command | `references/foundations/workflow.md`, `references/python/file-anatomy.md`, `references/python/implementation-patterns.md`, `references/metadata/mode-selection.md`, `references/python/python-recipes.md` |
| New Bash command | `references/foundations/workflow.md`, `references/bash/bash-script-patterns.md`, `references/metadata/mode-selection.md`, `references/bash/bash-recipes.md` |
| Convert existing script | `references/foundations/workflow.md`, `references/metadata/required-fields.md`, `references/foundations/dependencies-and-portability.md`, `references/troubleshooting/discovery-checklist.md` |
| Choose or fix mode | `references/metadata/mode-selection.md`, `references/metadata/inline-refresh-and-errors.md`, `references/troubleshooting/runtime-and-output-issues.md` |
| Add or fix arguments | `references/metadata/typed-arguments.md`, plus `references/python/implementation-patterns.md` or `references/bash/bash-script-patterns.md` |
| Command does not appear | `references/troubleshooting/discovery-checklist.md`, `references/metadata/required-fields.md` |
| Runtime/output is wrong | `references/troubleshooting/runtime-and-output-issues.md`, `references/metadata/mode-selection.md`, `references/metadata/inline-refresh-and-errors.md` |
| Choose Python vs Bash | `references/foundations/language-selection.md` |
| Make it shareable | `references/foundations/community-repo-conventions.md`, `references/foundations/dependencies-and-portability.md` |

### Step 3: Build or repair

- Use `assets/templates/python-script-command.py` or `assets/templates/bash-script-command.sh` only as starting points.
- Keep metadata directly below the shebang and use `# @raycast.*` for Python/Bash.
- Add dependency notes and readable missing-dependency failures when the command needs extra tools or packages.
- Keep failure paths user-readable: print a final useful line and exit non-zero.

## Core defaults

- Default to Python for API calls, JSON parsing, text processing, and richer logic.
- Default to Bash for tiny shell-native wrappers around existing CLIs or OS actions.
- Default to `fullOutput` if the result is meant to be read.
- Default to `compact` or `silent` for single-line confirmations or actions.
- Use `inline` only for dashboard-style, one-line status commands.

## Scripts

Every script lives in `scripts/` and has a paired `<name>.md` doc next to it.

| Script | Purpose | Mutates? |
|---|---|---|
| `scripts/check-raycast-script-metadata.sh` | Validate shebang, required metadata, mode, inline refresh, and typed argument JSON. See `scripts/check-raycast-script-metadata.md`. | No |
| `scripts/preview-script.sh` | Run a command and preview the Raycast stdout display contract for its mode. See `scripts/preview-script.md`. | No |

## Validation flow

When possible, validate the actual command file:

1. Run `scripts/check-raycast-script-metadata.sh path/to/command.py` or `.sh`.
2. Run `scripts/preview-script.sh path/to/command.py [args...]` or `.sh [args...]`.
3. If metadata/discovery fails, read `references/troubleshooting/discovery-checklist.md`.
4. If mode/output/failure behavior fails, read `references/troubleshooting/runtime-and-output-issues.md`.
5. Report the exact verification rung reached. Do not treat "looks plausible" as a smoke test.

## Reference files

| File | When to read |
|---|---|
| `references/foundations/scope-and-fit.md` | Read when deciding whether the task is really a Script Command and not a full Raycast extension. |
| `references/foundations/workflow.md` | Read when creating or converting a command and you need the end-to-end build flow. |
| `references/foundations/language-selection.md` | Read when deciding between Python and Bash. |
| `references/metadata/required-fields.md` | Read when adding or repairing metadata headers. |
| `references/metadata/mode-selection.md` | Read when choosing between `fullOutput`, `compact`, `silent`, and `inline`. |
| `references/metadata/inline-refresh-and-errors.md` | Read when working on inline refresh, first-line/last-line behavior, or failure semantics. |
| `references/metadata/typed-arguments.md` | Read when adding, changing, or debugging Script Command arguments. |
| `references/python/file-anatomy.md` | Read when creating a Python command file or checking placement of metadata and code. |
| `references/python/implementation-patterns.md` | Read when wiring `sys.argv`, dependency notes, failure messages, or Python output patterns. |
| `references/bash/bash-script-patterns.md` | Read when building or fixing a Bash-based Script Command. |
| `references/foundations/community-repo-conventions.md` | Read when the command should follow Raycast community-repo conventions. |
| `references/foundations/dependencies-and-portability.md` | Read when the command depends on tools/packages or must stay portable. |
| `references/troubleshooting/discovery-checklist.md` | Read when a command does not appear in Raycast or seems not to be recognized. |
| `references/troubleshooting/runtime-and-output-issues.md` | Read when output, refresh, or failure behavior is wrong. |
| `references/python/python-recipes.md` | Read when you need concrete Python command patterns. |
| `references/bash/bash-recipes.md` | Read when you need concrete Bash command patterns. |
| `references/foundations/source-map.md` | Read when you need the provenance for the internal references or want to expand the skill from the original Raycast research docs. |

## Guardrails

- Do not invent metadata fields that are not verified in Raycast-owned sources.
- Do not import Raycast Extensions API, AI extension, or Form argument schemas into Script Commands.
- Do not add unsupported argument types such as `select` or `file`; Script Commands support `text`, `password`, and `dropdown`.
- Do not choose `inline` without `refreshTime`.
- Do not emit noisy multi-line progress output for `compact`, `silent`, or `inline`.
- Do not read optional arguments unsafely; guard Python `sys.argv` access and shell `$2` / `$3` usage.
- Do not hide missing dependencies; document them and fail clearly.
- Do not leave `.template.` in a filename unless the command intentionally requires user edits before use.
- Do not bloat the response with generic shell or Python tutorials when the routed references already cover the needed pattern.

## Output contract

When finished, report:

- command file path
- selected mode and why it matches the output shape
- metadata fields present
- supported arguments and how they map to `$1..$3` or `sys.argv[1..3]`
- dependencies and setup notes
- validation run: metadata checker result and preview result
- Raycast install/use instruction, including adding the script directory when relevant
- verification rung reached
