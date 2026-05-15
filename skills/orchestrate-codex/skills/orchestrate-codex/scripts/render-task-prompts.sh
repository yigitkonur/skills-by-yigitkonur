#!/usr/bin/env bash
# DEPRECATED: forwards to render.sh --mode wrap. Removed in v3.0.
#
# Old CLI:
#   render-task-prompts.sh INPUT_DIR OUTPUT_DIR [--mode exec|single] [--prefix on|off] [--force]
# New CLI:
#   render.sh --mode wrap INPUT_DIR OUTPUT_DIR [--mode-target exec|single] [--prefix on|off] [--force]

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/_lib.sh" ]]; then
  # shellcheck source=_lib.sh
  source "$SCRIPT_DIR/_lib.sh" 2>/dev/null || true
  oc_log_run_ledger WARN "deprecated_script" script="render-task-prompts.sh" \
    reason="forwarding to render.sh --mode wrap" 2>/dev/null || true
fi

if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
  cat >&2 <<'EOF'
render-task-prompts.sh — DEPRECATED shim forwarding to render.sh --mode wrap
Removed in v3.0. Use:
  bash render.sh --mode wrap INPUT_DIR OUTPUT_DIR [--mode-target exec|single] [--prefix on|off]
EOF
  exit 0
fi

# Translate --mode exec|single (old) → --mode-target exec|single (new) since
# render.sh's --mode is now the outer (template|wrap) selector.
declare -a NEW_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      NEW_ARGS+=("--mode-target" "$2"); shift 2;;
    --mode=*)
      NEW_ARGS+=("--mode-target" "${1#*=}"); shift;;
    *)
      NEW_ARGS+=("$1"); shift;;
  esac
done

exec bash "$SCRIPT_DIR/render.sh" --mode wrap "${NEW_ARGS[@]}"
