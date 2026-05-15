#!/usr/bin/env bash
# DEPRECATED: manifest-update.sh is a deprecation shim forwarding to
# manifest-update.py --execute. Removed in v3.0.
#
# Translates the bash positional CLI to the Python --flag form:
#   bash manifest-update.sh entry <manifest> <id> k=v ... [--reason X] [--actor Y]
#   → python3 manifest-update.py entry --manifest <manifest> --entry <id>
#                                     --set k=v ... --reason X --actor Y --execute
#
# Why deprecated: maintaining two manifest writers (bash + Python) silently
# diverged on lock-timeout exit code, dry-run semantics, boolean coercion,
# temp-file naming, and parent-dir creation. See:
#   /Users/yigitkonur/dev/unification-strategy/strategy/02-consolidation-decisions.md
#   (Decision 1).
#
# To update bash callers: replace direct invocation with
#   source _lib.sh
#   oc_manifest_set MANIFEST ENTRY_ID k=v k=v ...

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${SCRIPT_DIR}/manifest-update.py"

if [[ ! -f "$PY" ]]; then
  echo "manifest-update.sh shim: manifest-update.py not found at $PY" >&2
  exit 2
fi

# Optional ledger warn (best effort; do not fail the call)
if [[ -n "${OC_RUN_LEDGER:-}" ]]; then
  if [[ -f "${SCRIPT_DIR}/_lib.sh" ]]; then
    # shellcheck source=_lib.sh
    source "${SCRIPT_DIR}/_lib.sh" 2>/dev/null || true
    oc_log_run_ledger WARN "deprecated_script" script="manifest-update.sh" \
      reason="forwarding to manifest-update.py; remove in v3.0" 2>/dev/null || true
  fi
fi

# Parse: support both
#   manifest-update.sh entry <manifest> <id> k=v ... [--reason X] [--actor Y]
#   manifest-update.sh top <manifest> k=v ... [--reason X] [--actor Y]
# --reason / --actor may appear before mode or interleaved with key=value pairs.

REASON=""
ACTOR=""
declare -a POSITIONAL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reason)
      REASON="$2"; shift 2;;
    --actor)
      ACTOR="$2"; shift 2;;
    --reason=*)
      REASON="${1#*=}"; shift;;
    --actor=*)
      ACTOR="${1#*=}"; shift;;
    --help|-h)
      cat >&2 <<EOF
manifest-update.sh — DEPRECATED shim forwarding to manifest-update.py

Usage:
  manifest-update.sh entry <manifest.json> <entry-id> <key=value> [...] [--reason X] [--actor Y]
  manifest-update.sh top   <manifest.json> <key=value> [...] [--reason X] [--actor Y]

Removed in v3.0. Migrate to:
  python3 manifest-update.py entry --manifest <p> --entry <id> --set k=v ... --execute
  python3 manifest-update.py top   --manifest <p> --set k=v ... --execute
EOF
      exit 0
      ;;
    *)
      POSITIONAL+=("$1"); shift;;
  esac
done

if [[ ${#POSITIONAL[@]} -lt 2 ]]; then
  echo "manifest-update.sh: expected at least <mode> <manifest>" >&2
  exit 2
fi
MODE="${POSITIONAL[0]}"
MANIFEST="${POSITIONAL[1]}"

declare -a SET_PAIRS=()
ENTRY=""

case "$MODE" in
  entry)
    if [[ ${#POSITIONAL[@]} -lt 3 ]]; then
      echo "manifest-update.sh: 'entry' mode requires <entry-id>" >&2
      exit 2
    fi
    ENTRY="${POSITIONAL[2]}"
    SET_PAIRS=("${POSITIONAL[@]:3}")
    ;;
  top)
    SET_PAIRS=("${POSITIONAL[@]:2}")
    ;;
  *)
    echo "manifest-update.sh: unknown mode '$MODE' (want 'entry' or 'top')" >&2
    exit 2
    ;;
esac

if [[ ${#SET_PAIRS[@]} -eq 0 ]]; then
  echo "manifest-update.sh: at least one key=value pair required" >&2
  exit 2
fi

# Build Python invocation
declare -a PY_ARGS=("$MODE" "--manifest" "$MANIFEST")
if [[ -n "$ENTRY" ]]; then
  PY_ARGS+=("--entry" "$ENTRY")
fi
for pair in "${SET_PAIRS[@]}"; do
  PY_ARGS+=("--set" "$pair")
done
[[ -n "$REASON" ]] && PY_ARGS+=("--reason" "$REASON")
[[ -n "$ACTOR"  ]] && PY_ARGS+=("--actor" "$ACTOR")
PY_ARGS+=("--execute")

exec python3 "$PY" "${PY_ARGS[@]}"
