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
FINDINGS=0

report_missing() {
  path=$1
  message=$2
  echo "$path:1: missing $message"
  FINDINGS=$((FINDINGS + 1))
}

for dir in domain application handlers gateways presenters infrastructure; do
  [ -d "$SRC/$dir" ] || report_missing "$SRC/$dir" "canonical directory"
done

[ -d "$SRC/domain/ports" ] || report_missing "$SRC/domain/ports" "domain ports seam"
[ -f "$SRC/infrastructure/config/runtime-config.ts" ] || report_missing "$SRC/infrastructure/config/runtime-config.ts" "runtime config seam"

FOUND_BOOTSTRAP=0
for candidate in \
  "$SRC/infrastructure/server/bootstrap.ts" \
  "$SRC/bootstrap.ts" \
  "$SRC/server.ts" \
  "$SRC/index.ts"
do
  if [ -f "$candidate" ]; then
    FOUND_BOOTSTRAP=1
    break
  fi
done

if [ "$FOUND_BOOTSTRAP" -eq 0 ]; then
  echo "$SRC/infrastructure/server/bootstrap.ts:1: missing composition root candidate"
  FINDINGS=$((FINDINGS + 1))
fi

if [ "$FINDINGS" -gt 0 ]; then
  exit 1
fi

exit 0
