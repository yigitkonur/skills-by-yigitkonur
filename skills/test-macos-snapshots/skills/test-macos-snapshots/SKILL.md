---
name: test-macos-snapshots
description: Use skill if you are validating a macOS app UI with screenshots, snapshot automation, or visual regression checks and need expectation-first evidence plus drift analysis.
---

# Test macOS Snapshots

Validate one macOS UI state at a time with an explicit expectation-first loop. Declare what the screenshot must prove before capture, then compare the image against that contract and fix the right layer.

## Trigger boundary

Use this skill when you need to:

- validate a macOS window, sheet, or screen with screenshots
- choose or improve a deterministic snapshot automation path
- compare expected UI state against a captured image
- explain visual drift and decide whether the fix belongs in the app, the automation, or the expectation

Do not use this skill when:

- the main job is designing or building the UI rather than validating it
- the main job is driving a live browser; use `run-playwright` or `run-agent-browser` for browser control
- the task is diagnosing runtime internals with a debugger or devtools instead of checking known UI expectations

## Non-negotiable rules

1. **State the expectation before capture.** Do not inspect a screenshot first and retrofit the expected state afterward.
2. **Validate one target state per run.** Do not batch multiple unrelated windows or flows into one screenshot verdict.
3. **Prefer the most deterministic capture path already available.** Use project-native rendering or UI tests before Accessibility or OS-level screenshots.
4. **Record layout facts that affect interpretation.** Note collapsed sidebars, compact toolbars, split-view sizes, or alternate navigation chrome before you classify drift.
5. **Separate deterministic structure from data-dependent variation.** Item names, timestamps, counts, and remote content may vary even when the screenshot is correct.
6. **Explain the result in three buckets.** Always report `Matches`, `Drift`, and `Better than expected`.
7. **Fix the narrowest correct layer and rerun.** Automation bugs, app bugs, and over-specific expectations are different problems.

## Minimal read sets

### One macOS window or sheet

Read these first:

- `references/expectation-loop.md`
- `references/drift-analysis.md`

### Need to choose a capture path

Read these first:

- `references/capture-modes.md`
- `references/expectation-loop.md`

### Blank, stale, clipped, or focus-dependent screenshot

Read these first:

- `references/troubleshooting.md`
- `references/drift-analysis.md`

## Standard workflow

### 1. Choose the capture path

- Inspect the project for existing screenshot or UI-test entrypoints before inventing new automation.
- Prefer capture modes in this order: in-app or in-process rendering, built-in UI-test harness, browser driver for hybrid apps, then Accessibility or window-capture fallback.
- Tell the user which path you chose and why it is safer than the alternatives you rejected.

Use `references/capture-modes.md` when the project exposes multiple possible routes.

### 2. Declare the expected state

Write 3-7 bullets covering:

- target window, sheet, or screen
- active section or navigation state through the affordance that is actually visible in the current layout
- main visible content block or headline
- controls, labels, or options that must be visible
- one or two failure signatures that must not appear

Also separate:

- deterministic structure
- layout facts that affect interpretation
- data-dependent variation

Use `references/expectation-loop.md` for the exact contract shape.

### 3. Capture exactly one target state

- Run one command or one test entrypoint for the chosen state.
- Save the absolute path to the resulting image.
- Prefer condition-based waits or app-ready signals over blind sleeps.
- If the capture emits multiple images, explicitly choose the file that matches the target state and say why.

### 4. Compare expectation against observation

Report the screenshot in three buckets:

- `Matches` — visible evidence that proves the expected state is present
- `Drift` — what differs from the contract and why it likely happened
- `Better than expected` — extra valid evidence the image provides beyond the original contract

Use `references/drift-analysis.md` to classify the mismatch before you change anything.

### 5. Fix the right layer and rerun

- Fix the automation when the wrong state was selected, the capture raced the UI, or the image is stale or clipped.
- Fix the app when the screenshot exposes a real layout, state, or rendering regression.
- Fix the expectation only when the screenshot is structurally correct and your contract was too specific.

Rerun the same target after the fix. Stop after a clean pass or after three iterations with a clear residual-risk note.

## Do this, not that

| Do this | Not that |
|---|---|
| Write the expected state before capture | Infer expectations from the screenshot after the fact |
| Use project-native or test-harness capture when it exists | Start with Accessibility scripting by default |
| Prove navigation state using the visible affordance in the current layout | Require a sidebar highlight when the layout only shows a section title |
| Record actual selected item names when the content is data-dependent | Hardcode unstable names into the expectation |
| Use `Matches`, `Drift`, and `Better than expected` | Return only "looks good" or "looks wrong" |
| Rerun the same target after the fix | Declare success on a different screenshot |

## Reference routing

| Need | Reference |
|---|---|
| Choosing between in-app, UI-test, browser, and fallback capture paths | `references/capture-modes.md` |
| Writing the expectation contract and running the compare loop | `references/expectation-loop.md` |
| Classifying mismatches and picking the fix layer | `references/drift-analysis.md` |
| Recovering from blank, stale, clipped, or focus-dependent captures | `references/troubleshooting.md` |
