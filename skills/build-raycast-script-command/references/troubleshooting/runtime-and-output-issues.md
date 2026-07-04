# Runtime And Output Issues

Use this file when the command runs but feels wrong in Raycast.

## Symptom Table

| Symptom | Likely cause | Fix |
|---|---|---|
| Only one line shows up | Command is `compact`, `silent`, or `inline` | Switch to `fullOutput` for reports, or compress output to the one line Raycast will show. |
| `compact` shows the wrong line | Raycast shows the last stdout line | Move the useful summary to the final stdout line and send diagnostics to stderr or remove them. |
| `silent` shows unexpected text | Raycast shows the last stdout line if one exists | Print only the intended final confirmation, or print nothing on success. |
| `inline` shows the wrong line | Raycast shows the first stdout line | Print the dashboard value first and keep later output quiet. |
| `inline` does not refresh | Missing, invalid, or too-slow `refreshTime` | Add `@raycast.refreshTime` and keep the command fast and idempotent. |
| Noisy long-running output breaks `compact`, `silent`, or `inline` | The mode cannot handle streaming partial logs | Use `fullOutput`, quiet the underlying command, or print only a final summary. |
| Error toast is unreadable | Failure path does not print a readable final line | Catch the failure, print a user-facing final line, then exit non-zero. |
| Dependency works in Terminal but fails in Raycast | Raycast environment lacks the expected PATH, package, or profile setup | Document the dependency, check for it before use, and avoid relying on shell profile side effects. |

## Fix Rules

- move reports to `fullOutput`
- keep `inline` to one short line
- print the most important summary as the final line in `compact`
- on failure, print a clean message and exit non-zero
- avoid streaming noisy partial logs outside `fullOutput`

## Quick repair examples

| Problem | Repair |
|---|---|
| `compact` shows an unhelpful intermediate log line | move the useful summary to the final printed line |
| `inline` shows only part of a report | compress output to one short status line |
| failure toast shows a traceback fragment | catch the error, print a readable message, exit non-zero |

## Read Together With

- `references/metadata/mode-selection.md`
- `references/metadata/inline-refresh-and-errors.md`

## Fast triage order

When a command "works but feels wrong", inspect in this order:

1. current `mode`
2. actual printed output shape
3. whether the useful line is first or last
4. failure printing plus exit code
5. whether the task is simply too noisy for the chosen mode
