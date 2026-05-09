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

for layer in "$SRC/domain" "$SRC/application"; do
  emit_matches "import[^'\"]*['\"][^'\"]*(mcp-use(/server)?|@modelcontextprotocol/sdk|/handlers/|/presenters/|/resources/|/prompts/|/infrastructure/|handlers/|presenters/|resources/|prompts/|infrastructure/)" "$layer" "inner layer imports a forbidden outer/protocol dependency"
done

if [ "$SEARCH" = "rg" ]; then
  env_matches=$(rg -n --glob '*.ts' --glob '*.tsx' -e 'process[.]env' "$SRC" 2>/dev/null || true)
else
  env_matches=$(grep -RInE --include='*.ts' --include='*.tsx' 'process[.]env' "$SRC" 2>/dev/null || true)
fi

old_ifs=$IFS
IFS='
'
for hit in $env_matches; do
  file=${hit%%:*}
  case "$file" in
    "$SRC/infrastructure/config/runtime-config.ts") continue ;;
  esac
  rest=${hit#*:}
  line=${rest%%:*}
  text=${rest#*:}
  echo "$file:$line: process.env outside runtime-config.ts: $text"
  FINDINGS=$((FINDINGS + 1))
done
IFS=$old_ifs

emit_matches 'console[.](log|info|warn|error|debug)' "$SRC" "console.* under src"

for file in $(find "$SRC" -name index.ts -type f 2>/dev/null); do
  case "$file" in
    "$SRC/index.ts") continue ;;
  esac
  echo "$file:1: index.ts barrel under src; direct imports are preferred"
  FINDINGS=$((FINDINGS + 1))
done

if [ "$FINDINGS" -gt 0 ]; then
  exit 1
fi

exit 0
