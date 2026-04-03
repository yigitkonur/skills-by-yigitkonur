# Bash Script Patterns

Use this file when the Script Command should stay in shell rather than Python.

## Good Foundation

```bash
#!/usr/bin/env bash
set -euo pipefail

# @raycast.schemaVersion 1
# @raycast.title Example Bash Command
# @raycast.mode silent
# @raycast.packageName Examples

query="${1:-}"
[[ -n "$query" ]] || { echo "Missing query"; exit 1; }

echo "Opened search"
```

## Bash Defaults

- use `#!/usr/bin/env bash`
- use `set -euo pipefail`
- quote variable expansions
- use `${1:-}` style guards for optional args
- print one clean final line for success or failure

## Good Fits

- wrappers around existing CLIs
- URL-openers
- clipboard commands
- small system actions

## Anti-patterns

- large parsing logic that wants Python data structures
- unsafe unquoted variables
- noisy command traces in `compact`, `silent`, or `inline`
- depending on shell profile magic without documenting it

## Small quality checklist

- `set -euo pipefail` present
- required metadata present
- args guarded with `${1:-}` style defaults where needed
- variables quoted
- final success or failure line is readable

## Example failure pattern

```bash
command -v jq >/dev/null 2>&1 || { echo "jq is required"; exit 1; }
```

## Source basis

- remote comparison: `openclaw/skills/shell-scripting`
- remote comparison: `thebushidocollective/han/shell-best-practices`
