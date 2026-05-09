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
      --glob '*.vue' \
      --glob '*.svelte' \
      -e "$pattern" "$root" || true
    return
  fi

  find "$root" \
    \( -path '*/node_modules/*' -o -path '*/.git/*' -o -path '*/dist/*' -o -path '*/build/*' -o -path '*/coverage/*' \) -prune -o \
    -type f \( -name '*.css' -o -name '*.scss' -o -name '*.less' -o -name '*.html' -o -name '*.tsx' -o -name '*.jsx' -o -name '*.ts' -o -name '*.js' -o -name '*.vue' -o -name '*.svelte' \) -print0 |
    while IFS= read -r -d '' file; do
      grep -nE "$pattern" "$file" 2>/dev/null | sed "s#^#$file:#" || true
    done
}

tailwind_spacing='(p|m)(x|y|t|r|b|l)?-(-?\[[^]]+\]|-?px|-?[0-9]+(\.[0-9]+)?)|gap(-x|-y)?-(-?\[[^]]+\]|-?px|-?[0-9]+(\.[0-9]+)?)|space-(x|y)-(-?\[[^]]+\]|-?px|-?[0-9]+(\.[0-9]+)?)'
css_spacing='(padding|margin|gap|row-gap|column-gap)(-[A-Za-z]+)?[[:space:]]*:[[:space:]]*[^;}]+'

echo "# Spacing Scale Audit"
echo
echo "Target root: $root"
echo

echo "## Tailwind Spacing Class Counts"
search "$tailwind_spacing" |
  grep -oE "$tailwind_spacing" |
  sort | uniq -c | sort -rn || true
echo

echo "## CSS Spacing Declaration Counts"
search "$css_spacing" |
  sed -E 's/.*((padding|margin|gap|row-gap|column-gap)(-[A-Za-z]+)?[[:space:]]*:[[:space:]]*[^;}]+).*/\1/' |
  sort | uniq -c | sort -rn || true
echo

echo "## Source Lines With Arbitrary Pixel Spacing"
search '([pm](x|y|t|r|b|l)?|gap(-x|-y)?)-\[[0-9.]+px\]|(padding|margin|gap|row-gap|column-gap)(-[A-Za-z]+)?[[:space:]]*:[[:space:]]*[0-9.]+px' |
  sort -u || true
