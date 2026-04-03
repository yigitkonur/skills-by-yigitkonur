# Bash Recipes

Use this file when the command should stay tiny and shell-native.

## Recipe 1: Silent URL opener

```bash
#!/usr/bin/env bash
set -euo pipefail

# @raycast.schemaVersion 1
# @raycast.title Search Docs
# @raycast.mode silent
# @raycast.packageName Examples
# @raycast.argument1 { "type": "text", "placeholder": "Query", "percentEncoded": true }

query="${1:-}"
[[ -n "$query" ]] || { echo "Missing query"; exit 1; }

open "https://example.com/search?q=$query"
echo "Opened search"
```

## Recipe 2: Compact clipboard command

```bash
#!/usr/bin/env bash
set -euo pipefail

# @raycast.schemaVersion 1
# @raycast.title Copy Date
# @raycast.mode compact
# @raycast.packageName Examples

date '+%Y-%m-%d' | pbcopy
echo "Copied date"
```

## Recipe 3: Inline one-line status

```bash
#!/usr/bin/env bash
set -euo pipefail

# @raycast.schemaVersion 1
# @raycast.title Git Branch
# @raycast.mode inline
# @raycast.refreshTime 1m
# @raycast.packageName Examples

printf '%s\n' "$(git branch --show-current 2>/dev/null || echo no-repo)"
```

## Notes

- keep Bash inline output to one line
- use `printf` when formatting matters
- move anything noisy or multi-line to `fullOutput`

## Source basis

- remote comparison: `openclaw/skills/shell-scripting`
