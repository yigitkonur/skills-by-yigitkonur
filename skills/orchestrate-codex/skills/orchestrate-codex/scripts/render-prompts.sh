#!/usr/bin/env bash
# DEPRECATED: forwards to render.sh --mode template. Removed in v3.0.
#
# Old CLI:
#   render-prompts.sh INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]
# New CLI:
#   render.sh --mode template INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/_lib.sh" ]]; then
  # shellcheck source=_lib.sh
  source "$SCRIPT_DIR/_lib.sh" 2>/dev/null || true
  oc_log_run_ledger WARN "deprecated_script" script="render-prompts.sh" \
    reason="forwarding to render.sh --mode template" 2>/dev/null || true
fi

if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
  cat >&2 <<'EOF'
render-prompts.sh — DEPRECATED shim forwarding to render.sh --mode template
Removed in v3.0. Use:
  bash render.sh --mode template INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]
EOF
  exit 0
fi

exec bash "$SCRIPT_DIR/render.sh" --mode template "$@"
