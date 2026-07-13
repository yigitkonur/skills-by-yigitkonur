---
name: build-raycast-script-command
description: "Use if authoring or fixing a Raycast Script Command (@raycast.* metadata header) — fields, modes."
---

# Build Raycast Script Command

Author or repair a Raycast **Script Command** (a single `.sh` or `.py` file with a `# @raycast.*` metadata header that Raycast discovers from a script directory). This skill is for Script Commands only — *not* the Raycast Extensions API (`@raycast/api`, `ray build`, React `<List>`/`<Detail>` views).

## When to use

*Italicized triggers — match any one:*

- *Creating a new `.sh` or `.py` Raycast Script Command from scratch*
- *Converting an existing Python or shell script into a Raycast Script Command*
- *Adding, removing, or repairing the `# @raycast.title` / `# @raycast.mode` / `# @raycast.argument*` metadata block*
- *Choosing between `fullOutput`, `compact`, `silent`, or `inline` modes (or fixing `refreshTime` / `packageName`)*
- *Wiring `# @raycast.argument*` typed arguments to `sys.argv[1..3]` or `$1..$3`*
- *Diagnosing why a script does not appear in Raycast (discovery, shebang, `chmod +x`, schemaVersion)*
- *Fixing wrong stdout shape, refresh cadence, exit-code-on-failure, or missing-dependency UX*
- *Hardening a command for the Raycast community-repo conventions*

**Do NOT use this skill for:**

- Raycast **Extensions** (anything importing `@raycast/api`, using `ray build`/`ray develop`, JSX views, or an extension `package.json`) — this skill covers Script Commands only.
- Building Chrome or browser extensions — use `build-chrome-extension`.
- Plain Python/Bash scripts with no `# @raycast.*` header and no Raycast integration intent.
- Browser automation flows (`run-agent-browser`).

If you see `import { ... } from "@raycast/api"` or a `package.json` declaring `"raycast": { ... }`, this is an extension — exit this skill.

## Trigger fingerprint

A file is in scope iff **all** are true:

1. Filename ends in `.sh` or `.py` (other interpreters are possible but rare).
2. First line is a shebang (`#!/bin/bash`, `#!/usr/bin/env python3`, etc.).
3. The header contains `# @raycast.schemaVersion 1` and `# @raycast.title …` and `# @raycast.mode …` directly under the shebang.
4. The file is meant to live in a Raycast script directory (added via *Raycast Settings → Extensions → Script Commands → Add Script Directory*), not inside a `src/` extension tree.

If any of (1)–(4) is missing or contradicted, stop and confirm scope before editing.

## Load-bearing rules

Read these before touching the file. Detail lives in `references/` — these are the rules you cannot violate.

### Required metadata (every command)

| Field | Required | Notes |
|---|---|---|
| `# @raycast.schemaVersion 1` | yes | Constant. Wrong/missing → command never appears. |
| `# @raycast.title <Human Title>` | yes | Shown in Raycast root search. |
| `# @raycast.mode <fullOutput\|compact\|silent\|inline>` | yes | Drives stdout contract. |
| `# @raycast.icon` | optional | Emoji or path; improves discoverability. |
| `# @raycast.packageName` | optional | Group label in Raycast UI. |
| `# @raycast.refreshTime <Ns\|Nm\|Nh>` | required for `inline` only | Seconds/minutes/hours. |
| `# @raycast.argument1..3` | optional | JSON object per argument. See below. |

Deep detail: `references/metadata/required-fields.md`.

### Mode → stdout contract

| Mode | Use when | Stdout shown | Failure UX |
|---|---|---|---|
| `fullOutput` | Result is meant to be **read** (lists, reports, multi-line text) | Full text in a result window | Last line + non-zero exit |
| `compact` | One-line confirmation of an action (toast-style) | Last non-empty stdout line | Last line + non-zero exit |
| `silent` | Pure side effect, no UI | Nothing on success | Last line + non-zero exit |
| `inline` | Dashboard widget refreshed on a timer | First non-empty line, refreshed every `refreshTime` | First line + non-zero exit |

`inline` **requires** `# @raycast.refreshTime`. No other mode uses it.

Deep detail: `references/metadata/mode-selection.md`, `references/metadata/inline-refresh-and-errors.md`.

### Typed arguments (Script Commands support 3 only)

```
# @raycast.argument1 { "type": "text",     "placeholder": "query" }
# @raycast.argument2 { "type": "password", "placeholder": "secret", "optional": true }
# @raycast.argument3 { "type": "dropdown", "placeholder": "env", "data": [{"title":"Prod","value":"prod"}] }
```

- **Supported types:** `text`, `password`, `dropdown`. No `select`, no `file`, no `number` — those are extension-only.
- Up to **3** arguments. Args 2 and 3 may be optional; argument 1 is effectively required (Raycast prompts for it).
- In Python, read with `sys.argv[1]`, `sys.argv[2]`, `sys.argv[3]` (always guard length for optionals).
- In Bash, read with `"$1"`, `"$2"`, `"$3"` (always quote; check `-z` for optionals).

Deep detail: `references/metadata/typed-arguments.md`.

### Discovery non-negotiables

A command will **not appear** in Raycast unless **all** are true:

1. The script's parent directory is registered in *Raycast Settings → Script Commands*.
2. File is executable (`chmod +x file.sh` / `chmod +x file.py`).
3. First line is a valid shebang for an interpreter present on the user's `PATH`.
4. Metadata header is **directly under the shebang** with no blank line breaking it (Raycast is strict).
5. `schemaVersion`, `title`, and `mode` are all present and parseable.
6. Filename does not contain `.template.` (those are intentionally hidden as user-edit-required).

Deep detail: `references/troubleshooting/discovery-checklist.md`.

### Failure & dependency UX

- Exit **non-zero** on any error path. Raycast surfaces the last (or first, for `inline`) line of stdout/stderr on failure.
- If the command needs `jq`, `gh`, `requests`, etc., **detect missing deps first** and print a one-line install hint, then exit non-zero. Do not let an opaque `command not found` reach the user.
- Never emit noisy multi-line progress for `compact`, `silent`, or `inline` — they all collapse stdout.

Deep detail: `references/troubleshooting/runtime-and-output-issues.md`, `references/foundations/dependencies-and-portability.md`.

## Workflow

### Step 1 — Detect scope

Inspect the workspace before writing anything:

- Is there an existing `.py` or `.sh` to convert, or is this greenfield?
- Does the existing header use `# @raycast.*`? Is it well-formed?
- Is the surrounding repo a Raycast **Extension** (sniff for `@raycast/api`, `ray build`, `package.json` with `"raycast"` key)? If yes, exit this skill.
- Decide Python vs Bash: see `references/foundations/language-selection.md` and the *Defaults* below.

If the task type is unclear after inspection, read `references/foundations/scope-and-fit.md`.

### Step 2 — Route by task

Read **only** the branch-relevant references before writing:

| Task | Read first |
|---|---|
| New Python command | `references/foundations/workflow.md` → `references/python/file-anatomy.md` → `references/python/implementation-patterns.md` → `references/metadata/mode-selection.md` → `references/python/python-recipes.md` |
| New Bash command | `references/foundations/workflow.md` → `references/bash/bash-script-patterns.md` → `references/metadata/mode-selection.md` → `references/bash/bash-recipes.md` |
| Convert existing script | `references/foundations/workflow.md` → `references/metadata/required-fields.md` → `references/foundations/dependencies-and-portability.md` → `references/troubleshooting/discovery-checklist.md` |
| Choose / fix mode | `references/metadata/mode-selection.md` → `references/metadata/inline-refresh-and-errors.md` → `references/troubleshooting/runtime-and-output-issues.md` |
| Add / fix arguments | `references/metadata/typed-arguments.md` → `references/python/implementation-patterns.md` or `references/bash/bash-script-patterns.md` |
| Command does not appear | `references/troubleshooting/discovery-checklist.md` → `references/metadata/required-fields.md` |
| Wrong runtime / output | `references/troubleshooting/runtime-and-output-issues.md` → `references/metadata/mode-selection.md` → `references/metadata/inline-refresh-and-errors.md` |
| Python vs Bash decision | `references/foundations/language-selection.md` |
| Make it shareable | `references/foundations/community-repo-conventions.md` → `references/foundations/dependencies-and-portability.md` |
| Provenance / source audit | `references/foundations/source-map.md` |

### Step 3 — Build or repair

- Start from `assets/templates/python-script-command.py` or `assets/templates/bash-script-command.sh` — these are seed files, not finished code.
- Place the metadata block directly under the shebang. Use `# @raycast.*` for both Python and Bash (the `#` line-comment syntax is identical).
- Read arguments defensively: guard `sys.argv` length in Python; quote `"$1"` and check `-z "$2"` in Bash.
- Add a missing-dependency precheck and a one-line user-readable failure message for any external tool.
- Match the stdout contract of the chosen mode exactly — see the table above.

### Step 4 — Validate

Run the bundled checkers against the actual command file:

1. `scripts/check-raycast-script-metadata.sh path/to/command.{py,sh}` — verifies shebang, required metadata, mode legality, `refreshTime` presence for `inline`, and typed-argument JSON.
2. `scripts/preview-script.sh path/to/command.{py,sh} [args...]` — runs the command and previews how Raycast will display its stdout for the declared mode.
3. If discovery fails, follow `references/troubleshooting/discovery-checklist.md`.
4. If output/refresh/exit semantics fail, follow `references/troubleshooting/runtime-and-output-issues.md`.
5. Report the exact verification rung reached (read / metadata-checker / preview / installed-and-ran-in-Raycast). Do **not** treat "looks plausible" as a smoke test.

## Defaults (use unless the task contradicts)

- **Python** for: HTTP/API calls, JSON parsing, non-trivial text processing, anything multi-step with structured data.
- **Bash** for: thin wrappers around an existing CLI (`gh`, `pbcopy`, `osascript`, `open`), small filesystem actions.
- **Mode `fullOutput`** when the user is meant to read the result.
- **Mode `compact`** for one-line "did the thing" confirmations.
- **Mode `silent`** for pure side-effects (clipboard, app launch, system action) with no useful output.
- **Mode `inline`** *only* for dashboard-style status widgets (battery, weather, builds) with `refreshTime` set.

## Bundled scripts

Each script has a paired `.md` doc next to it.

| Script | Purpose | Mutates? |
|---|---|---|
| `scripts/check-raycast-script-metadata.sh` | Validate shebang, required metadata, mode, inline `refreshTime`, typed-argument JSON. See `scripts/check-raycast-script-metadata.md`. | No |
| `scripts/preview-script.sh` | Execute the command and preview Raycast's stdout display contract for the declared mode. See `scripts/preview-script.md`. | No |

## Bundled assets

| Asset | Purpose |
|---|---|
| `assets/templates/python-script-command.py` | Seed Python command with metadata header, argument scaffolding, dependency check, and exit-code discipline. |
| `assets/templates/bash-script-command.sh` | Seed Bash command with the same scaffolding. |

## Reference index

| File | When to read |
|---|---|
| `references/foundations/scope-and-fit.md` | Deciding whether the task is really a Script Command and not a full Raycast extension. |
| `references/foundations/workflow.md` | End-to-end build flow for creating or converting a command. |
| `references/foundations/language-selection.md` | Choosing between Python and Bash. |
| `references/foundations/community-repo-conventions.md` | Aligning with `raycast/script-commands` repo conventions for sharing. |
| `references/foundations/dependencies-and-portability.md` | Commands that depend on external tools/packages or must stay portable. |
| `references/foundations/source-map.md` | Provenance for internal references; expanding the skill from original Raycast research. |
| `references/metadata/required-fields.md` | Adding or repairing the metadata header. |
| `references/metadata/mode-selection.md` | Choosing between `fullOutput`, `compact`, `silent`, `inline`. |
| `references/metadata/inline-refresh-and-errors.md` | Inline refresh cadence, first-line/last-line behavior, failure semantics. |
| `references/metadata/typed-arguments.md` | Adding, changing, or debugging `@raycast.argument*`. |
| `references/python/file-anatomy.md` | Layout of a Python command file: shebang, header, code regions. |
| `references/python/implementation-patterns.md` | Wiring `sys.argv`, dependency notes, failure messages, output patterns. |
| `references/python/python-recipes.md` | Concrete copy-shapeable Python command patterns. |
| `references/bash/bash-script-patterns.md` | Building or fixing a Bash-based Script Command. |
| `references/bash/bash-recipes.md` | Concrete copy-shapeable Bash command patterns. |
| `references/troubleshooting/discovery-checklist.md` | Command does not appear in Raycast. |
| `references/troubleshooting/runtime-and-output-issues.md` | Output, refresh, or failure behavior is wrong. |

## Guardrails

- Do not invent metadata fields not in the table above; only those verified against Raycast-owned sources are valid.
- Do not import `@raycast/api`, AI Extension, or extension Form schemas — those belong to extensions, not Script Commands.
- Do not use unsupported argument types (`select`, `file`, `number`); only `text`, `password`, `dropdown`.
- Do not declare `inline` without `refreshTime`.
- Do not emit multi-line progress for `compact`, `silent`, or `inline`.
- Do not read optional arguments unsafely; guard `sys.argv` length and quote `"$1"`/`"$2"`/`"$3"`.
- Do not let `command not found` reach the user — precheck deps and fail readably.
- Do not leave `.template.` in a final filename unless the command intentionally requires user edits before first use.
- Do not pad with shell or Python tutorial content when a routed reference covers it.

## Output contract

When the task is finished, report:

- command file path
- selected mode and **why** it matches the output shape
- metadata fields present (and any optional ones added)
- supported arguments and how they map to `$1..$3` / `sys.argv[1..3]`
- dependencies and any setup notes
- validation run: metadata-checker result and preview result
- Raycast install/use instruction (including adding the script directory if relevant)
- verification rung reached (read / metadata-checker / preview / installed-and-ran-in-Raycast)
