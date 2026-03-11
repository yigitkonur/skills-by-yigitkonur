# Observation: F-01 Invocation Model Gap

## What happened

SKILL.md lists bare commands like `snapshot`, `click e0`, `fill e1 "Jane Doe"` without
ever stating these run inside the `playwright-cli` interactive prompt. A reader following
literally would type `snapshot` in their shell and get "command not found."

## Root cause

M4 — Missing prerequisite knowledge. The entire mental model of "launch tool, then
type commands at its prompt" is assumed but never stated.

## Impact

P0 — Blocks progress entirely. Cannot execute any command without knowing the
invocation model.

## Fix applied

Added blockquote after intro paragraph:
> **Invocation model:** Every command listed below is typed at the `playwright-cli`
> prompt after you launch the tool, not as standalone shell commands.

## Verification

`grep -c "Invocation model" skills/run-playwright/SKILL.md` returns 1.
