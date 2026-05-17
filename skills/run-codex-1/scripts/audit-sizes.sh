#!/usr/bin/env bash
# DEPRECATED: forwards to audit.py sizes. Removed in v3.0.
#
# Old positional CLI:
#   audit-sizes.sh [--manifest <p>] [<answers> [<log> [<min>]]]
# New flag CLI:
#   audit.py sizes [--manifest <p>] [--answers <d>] [--log <p>] [--min-bytes <N>] [--json]

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Best-effort ledger warn
if [[ -f "$SCRIPT_DIR/_lib.sh" ]]; then
  # shellcheck source=_lib.sh
  source "$SCRIPT_DIR/_lib.sh" 2>/dev/null || true
  oc_log_run_ledger WARN "deprecated_script" script="audit-sizes.sh" \
    reason="forwarding to audit.py sizes" 2>/dev/null || true
fi

# Translate old positional CLI to new flag CLI.
declare -a PY_ARGS=("sizes")
declare -a POS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest)
      PY_ARGS+=("--manifest" "$2"); shift 2;;
    --manifest=*)
      PY_ARGS+=("--manifest" "${1#*=}"); shift;;
    --json)
      PY_ARGS+=("--json"); shift;;
    --help|-h)
      cat >&2 <<'EOF'
audit-sizes.sh — DEPRECATED shim forwarding to audit.py sizes
Removed in v3.0. Use:
  python3 audit.py sizes [--manifest <p>] [--answers <d>] [--log <p>] [--min-bytes <N>] [--json]
EOF
      exit 0
      ;;
    *)
      POS+=("$1"); shift;;
  esac
done
# Old positionals: ANSWERS LOG MIN_BYTES
[[ ${#POS[@]} -ge 1 ]] && PY_ARGS+=("--answers" "${POS[0]}")
[[ ${#POS[@]} -ge 2 ]] && PY_ARGS+=("--log"     "${POS[1]}")
[[ ${#POS[@]} -ge 3 ]] && PY_ARGS+=("--min-bytes" "${POS[2]}")

exec python3 "$SCRIPT_DIR/audit.py" "${PY_ARGS[@]}"
