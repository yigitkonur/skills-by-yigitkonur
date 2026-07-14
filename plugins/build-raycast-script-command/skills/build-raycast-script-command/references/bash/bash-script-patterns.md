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

## File Anatomy

1. Start with `#!/usr/bin/env bash`.
2. Add `set -euo pipefail`.
3. Put `# @raycast.*` metadata directly below the setup lines.
4. Put dependency notes above the first dependency check when needed.
5. Keep the final printed line readable.

## Bash Defaults

- use `#!/usr/bin/env bash`
- use `set -euo pipefail`
- quote variable expansions
- use `${1:-}` style guards for optional args
- print one clean final line for success or failure

## Safe Positional Arguments

```bash
query="${1:-}"
scope="${2:-all}"

[[ -n "$query" ]] || { echo "Missing query"; exit 1; }
```

Only read `$2` or `$3` when the matching `@raycast.argument2` or `@raycast.argument3` metadata exists, or when the access is guarded with a default.

## Dependencies

Document extra CLIs and fail before using them:

```bash
# Dependency: This script requires `jq`
# Install via Homebrew: `brew install jq`

command -v jq >/dev/null 2>&1 || { echo "jq is required"; exit 1; }
```

## Mode-Aware Output

| Mode | Bash output shape |
|---|---|
| `fullOutput` | print the full report; multi-line output is expected |
| `compact` | print the important summary last |
| `silent` | print one final confirmation only when useful |
| `inline` | print one short first line and include `@raycast.refreshTime` |

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
