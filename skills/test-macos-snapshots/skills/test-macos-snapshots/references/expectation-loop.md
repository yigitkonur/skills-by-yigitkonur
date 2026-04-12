# Expectation Loop

This is the core validation pattern for the skill.

## Step 1: Write the expectation contract

Before capture, write 3-7 bullets covering:

- target window, sheet, or screen
- active section or tab, expressed through the affordance visible at the current window size
- primary visible content block or headline
- critical controls or options that must be visible
- one or two failure signatures that must not appear

Separate:

- **Deterministic structure** — layout, selected section, sheet presence, visible controls, stable labels
- **Layout facts** — collapsed sidebars, compact toolbars, split views, alternate navigation chrome
- **Data-dependent variation** — item names, timestamps, counts, remote content

## Step 2: Run one capture

- Use one command or one test entrypoint.
- Save the absolute image path.
- If the run emits multiple images, select the exact file that matches the target state and say why.

## Step 3: Compare visibly

Review the image in three buckets:

- `Matches`
- `Drift`
- `Better than expected`

The third bucket matters. Sometimes the screenshot proves a stronger state than the original expectation, which means the expectation was underspecified rather than the capture being wrong.

## Step 4: Choose the fix layer

- **Automation fix** — wrong selection, race condition, stale content, clipped modal, wrong window
- **App fix** — real rendering bug, missing control, incorrect state, layout regression
- **Expectation fix** — structurally correct screenshot, but the contract was too specific

## Step 5: Rerun the same target

Reuse the same target state after the fix. Do not switch to a different screenshot to get a pass.
