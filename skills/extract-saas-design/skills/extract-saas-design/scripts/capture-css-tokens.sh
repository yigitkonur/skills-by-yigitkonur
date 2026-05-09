#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 TARGET_ROOT" >&2
  exit 2
fi

root=$1
if [ ! -d "$root" ]; then
  echo "Target root is not a directory: $root" >&2
  exit 2
fi

search() {
  local pattern=$1

  if command -v rg >/dev/null 2>&1; then
    rg -n --no-heading \
      --glob '!node_modules/**' \
      --glob '!.git/**' \
      --glob '!dist/**' \
      --glob '!build/**' \
      --glob '!coverage/**' \
      --glob '*.css' \
      --glob '*.scss' \
      --glob '*.less' \
      --glob '*.html' \
      --glob '*.tsx' \
      --glob '*.jsx' \
      --glob '*.ts' \
      --glob '*.js' \
      -e "$pattern" "$root" || true
    return
  fi

  find "$root" \
    \( -path '*/node_modules/*' -o -path '*/.git/*' -o -path '*/dist/*' -o -path '*/build/*' -o -path '*/coverage/*' \) -prune -o \
    -type f \( -name '*.css' -o -name '*.scss' -o -name '*.less' -o -name '*.html' -o -name '*.tsx' -o -name '*.jsx' -o -name '*.ts' -o -name '*.js' \) -print0 |
    while IFS= read -r -d '' file; do
      grep -nE "$pattern" "$file" 2>/dev/null | sed "s#^#$file:#" || true
    done
}

count_matches() {
  local label=$1
  local pattern=$2
  local count
  count=$(search "$pattern" | wc -l | tr -d ' ')
  printf '%-10s %s\n' "$label" "$count"
}

echo "# CSS Token Capture"
echo
echo "Target root: $root"
echo

echo "## Color Space Counts"
count_matches "oklch" 'oklch\('
count_matches "hsl" 'hsla?\('
count_matches "rgb" 'rgba?\('
count_matches "hex" '#[[:xdigit:]]{3,8}'
echo

echo "## CSS Custom Property Definitions"
search '--[A-Za-z0-9_-]+[[:space:]]*:[[:space:]]*[^;}]+' |
  sed -E 's/.*(--[A-Za-z0-9_-]+)[[:space:]]*:[[:space:]]*([^;}]+).*/\1: \2/' |
  sort | uniq -c | sort -rn || true
echo

echo "## CSS Custom Property Usage Counts"
search 'var\(--[A-Za-z0-9_-]+' |
  grep -oE 'var\(--[A-Za-z0-9_-]+' |
  sed 's/^var(//' |
  sort | uniq -c | sort -rn || true
echo

echo "## Chart And Sidebar Token Lines"
search '--(chart|sidebar)-[A-Za-z0-9_-]+' | sort -u || true
