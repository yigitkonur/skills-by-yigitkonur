# Mode Selection

Use this file when choosing how Raycast should present the command's output.

## Mode Matrix

| Mode | Raycast shows | Best for |
|---|---|---|
| `fullOutput` | the entire stdout in a separate view | reports, search results, transcripts, readable output |
| `compact` | the last line of stdout in a toast | short result summaries |
| `silent` | the last line of stdout in a HUD-style confirmation | actions that should finish quietly |
| `inline` | the first line inside the command item | dashboard-style status commands |

## Selection Rules

- Use `fullOutput` if a human should read multiple lines.
- Use `compact` if the command finishes with one important summary line.
- Use `silent` if the command mostly performs an action.
- Use `inline` only if the output is short, one-line, and should refresh over time.

## Safe Defaults

If unsure:

- default to `fullOutput`
- downgrade to `compact` or `silent` only when the output is truly short

## Anti-patterns

- multi-line report in `compact`
- streaming noisy progress in `silent`
- verbose logging in `inline`
- dashboard command in `fullOutput` when the point is glanceability

## Quick examples

| Scenario | Good mode |
|---|---|
| transcript, report, or markdown output | `fullOutput` |
| "created ticket", "copied path", "done" | `compact` or `silent` |
| crypto price, service status, unread count | `inline` |

## Common mistakes

| Mistake | Fix |
|---|---|
| choosing mode before inspecting the output shape | inspect output first, then choose |
| using `silent` when the user needs to read details | use `fullOutput` |
| using `inline` for a command that prints multiple lines | compress to one line or switch modes |

- remote comparison: `writing-user-outputs`
