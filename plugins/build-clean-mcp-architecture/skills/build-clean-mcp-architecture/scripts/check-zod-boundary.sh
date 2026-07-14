#!/bin/sh

if [ "$#" -gt 1 ]; then
  echo "usage: $0 [project-root]" >&2
  exit 2
fi

ROOT=${1:-.}
if [ ! -d "$ROOT" ]; then
  echo "error: project root not found: $ROOT" >&2
  exit 2
fi

SRC="$ROOT/src"
if [ ! -d "$SRC" ]; then
  echo "$SRC:1: missing src directory"
  exit 1
fi

if command -v rg >/dev/null 2>&1; then
  SEARCH='rg'
else
  SEARCH='grep'
fi

FINDINGS=0

emit_matches() {
  pattern=$1
  target=$2
  message=$3

  [ -e "$target" ] || return 0

  if [ "$SEARCH" = "rg" ]; then
    matches=$(rg -n --glob '*.ts' --glob '*.tsx' -e "$pattern" "$target" 2>/dev/null || true)
  else
    matches=$(grep -RInE --include='*.ts' --include='*.tsx' "$pattern" "$target" 2>/dev/null || true)
  fi

  [ -n "$matches" ] || return 0

  old_ifs=$IFS
  IFS='
'
  for hit in $matches; do
    file=${hit%%:*}
    rest=${hit#*:}
    line=${rest%%:*}
    text=${rest#*:}
    echo "$file:$line: $message: $text"
    FINDINGS=$((FINDINGS + 1))
  done
  IFS=$old_ifs
}

emit_matches "from ['\"]zod['\"]|from ['\"]zod/" "$SRC/domain" "Zod import in domain layer"
emit_matches "from ['\"]zod['\"]|from ['\"]zod/" "$SRC/application" "Zod import in application layer"
emit_matches "z[.](any|unknown)[[:space:]]*[(]" "$SRC/handlers" "z.any() or z.unknown() in handler schema"

for file in $(find "$SRC/handlers" -type f \( -name '*.ts' -o -name '*.tsx' \) 2>/dev/null); do
  if grep -Eq 'z[.]object[[:space:]]*[(]' "$file" && ! grep -Eq '[.]strict[[:space:]]*[(]' "$file"; then
    echo "$file:1: handler file contains z.object(...) but no .strict() in the same file"
    FINDINGS=$((FINDINGS + 1))
  fi
done

if [ "$FINDINGS" -gt 0 ]; then
  exit 1
fi

exit 0
