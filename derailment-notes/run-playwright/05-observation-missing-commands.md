# Observation: F-05/F-09 Missing Commands

## What happened

Step 4 lists only four command categories (navigation, inputs, clicks, tabs). Missing
entirely: `press`, `resize`, `mousewheel`, `upload` trigger pattern, `dialog-accept`,
`dialog-dismiss`. These commands exist in reference files but are undiscoverable from
SKILL.md alone.

## Root cause

S3 — Incomplete enumeration. The command list was written for the most common cases
but omits keyboard, viewport, file, and dialog primitives that are needed for
non-trivial tasks.

## Impact

P1 — A user encountering a dialog or needing to resize the viewport would have to
search through all reference files or guess command names.

## Fix applied

1. Added four new command categories (keyboard, viewport, uploads, dialogs)
2. Added a summary table mapping categories to all available commands
