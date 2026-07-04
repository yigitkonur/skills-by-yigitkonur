# Scope And Fit

Use this file when deciding whether the task belongs to Raycast Script Commands at all.

## What Script Commands Are

Raycast Script Commands are local scripts discovered from directories that Raycast indexes. They are lighter than full extensions and use top-of-file metadata comments plus normal script execution.

The basic model is:

1. A normal script file exists on disk.
2. Raycast metadata appears at the top as comments.
3. Raycast runs the script and presents its output according to the selected mode.

## Good Fit

Choose a Script Command when the user needs:

- a quick local automation
- a script-first workflow
- stdout-driven UI
- a lightweight wrapper around Python, Bash, or another scripting runtime
- a personal or shareable command without full extension packaging

## Bad Fit

Do not use Script Commands when the task clearly needs:

- React-based Raycast UI
- `@raycast/api`
- List, Grid, Detail, Form, ActionPanel, or other Extensions API components
- `ray build` / `ray develop`
- full extension packaging and store-style structure

That is Raycast Extensions API territory, not Script Commands.

## Important Distinction

Two rule sets exist:

- `Raycast runtime behavior`: what local Script Commands support
- `community repo policy`: extra rules used by `raycast/script-commands` for portability and contribution quality

Example:

- `packageName` is optional at runtime
- the community repo expects it to be present

## Practical Default

If the user says "Raycast script", "Script Command", "make this script callable from Raycast", or "convert this Python/Bash file into a Raycast command", this skill is the right fit.

If the user says "Raycast extension", mentions `@raycast/api`, or wants React-based UI surfaces, stop and switch skills.
