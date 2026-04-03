# Language Selection

Use this file when the user has not chosen Python or Bash yet.

## Choose Python When

- the command calls APIs
- the command parses JSON or HTML
- the command does non-trivial text processing
- the command benefits from clearer data structures or error handling
- the logic would become awkward in shell

## Choose Bash When

- the command is mostly glue around existing CLIs
- the task is a tiny wrapper around `open`, `pbcopy`, `curl`, `git`, `yt-dlp`, or similar tools
- the logic is short and shell-native
- the user already has a working shell script that only needs Raycast metadata

## Tradeoff Table

| Language | Best for | Main risk |
|---|---|---|
| Python | APIs, parsing, richer logic, readable error handling | extra package/runtime dependencies |
| Bash | tiny wrappers, shell-native automation, minimal footprint | brittle quoting and argument handling if overgrown |

## Practical Rule

When both would work, prefer:

- Python for commands the user may extend later
- Bash for very small, stable wrappers

## Examples

Choose Python for:

- "Fetch a URL, parse JSON, and print a formatted summary"
- "Read clipboard text, transform it, and save markdown"
- "Call an API with auth and return a compact result"

Choose Bash for:

- "Open a URL with the selected query"
- "Copy the current date to the clipboard"
- "Wrap a single CLI and report one-line success or failure"

## Common mistakes

| Mistake | Better choice |
|---|---|
| Writing 100+ lines of shell for JSON-heavy logic | Switch to Python |
| Adding Python dependencies for a tiny `open` wrapper | Stay in Bash |
| Choosing based only on personal preference | Choose based on task shape and future maintenance |

- remote comparison: `openclaw/skills/shell-scripting`
