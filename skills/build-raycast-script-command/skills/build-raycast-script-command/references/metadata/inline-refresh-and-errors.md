# Inline Refresh And Errors

Use this file when the command is `inline` or when error behavior is confusing.

## Inline Rules

Official Raycast rules:

- `refreshTime` is required for `inline`
- if `refreshTime` is missing, Raycast falls back to `compact`
- minimum refresh interval is `10s`
- only the first 10 inline commands auto-refresh

## Output Semantics

- `inline` uses the first line of output
- `compact` uses the last line of output
- `silent` shows the last line if one exists
- `fullOutput` shows everything

## Failure Contract

If the script exits non-zero:

- Raycast treats it as a failure
- for `inline` and `compact`, the last line becomes the error message

That means the failure path should print a clean final line before exiting.

## Long-Running Tasks

Raycast explicitly warns that long-running commands with lots of partial output are not a good fit for:

- `compact`
- `silent`
- `inline`

Move those to `fullOutput` or make them quieter.

## ANSI Reminder

Raycast's repo documentation explicitly supports ANSI color for:

- `fullOutput`
- `inline`

Do not assume ANSI survives in `compact` or `silent`.
