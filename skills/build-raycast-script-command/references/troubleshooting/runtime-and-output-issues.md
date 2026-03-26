# Runtime And Output Issues

Use this file when the command runs but feels wrong in Raycast.

## Symptom Table

| Symptom | Likely cause |
|---|---|
| only one line shows up | command is `compact`, `silent`, or `inline` |
| inline shows wrong text | Raycast uses the first line |
| compact shows wrong text | Raycast uses the last line |
| inline does not refresh | missing or bad `refreshTime` |
| error toast is unhelpful | failure path does not print a readable final line |
| command floods output | wrong mode for a long-running task |

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

- remote comparison: `writing-user-outputs`
