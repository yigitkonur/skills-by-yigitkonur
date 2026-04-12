# Troubleshooting

## Blank screenshot

Likely causes:

- capture fired before layout or data load finished
- wrong window or off-screen view was rendered

Fixes:

- wait on an app-ready condition if available
- increase settle time only after confirming there is no better readiness signal
- verify the capture path is targeting the correct window or scene

## Stale content

Likely causes:

- selection changed after the screenshot was queued
- cached state from a previous run is still visible

Fixes:

- reset the target state before capture
- make item selection deterministic
- record the chosen item in a manifest or run log

## Clipped sheet or modal

Likely causes:

- capture happened mid-animation
- base window and attached sheet were not composited correctly

Fixes:

- wait until the modal is fully presented
- if the project renders internally, capture the modal from inside the app rather than with OS-level screenshots

## Focus-dependent failure

Likely causes:

- Accessibility scripting or `screencapture` depended on the app being frontmost

Fixes:

- move the automation into the app or test harness if you can edit the project
- if you must use OS-level tooling, state the focus requirement explicitly and keep the run narrow

## Permission or tooling failure

Likely causes:

- missing Accessibility or screen recording permissions
- build artifacts not present

Fixes:

- verify the app or test runner was built first
- confirm required macOS permissions for the chosen fallback mode
- rerun the narrowest failing step instead of the whole pipeline
