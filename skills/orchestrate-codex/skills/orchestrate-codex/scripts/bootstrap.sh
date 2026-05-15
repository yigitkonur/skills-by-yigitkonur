#!/usr/bin/env bash
# DEPRECATED: bootstrap.sh is a 1-line shim forwarding to preflight.sh.
# Removed in v3.0.
#
# Why renamed: bootstrap.sh was named to suggest universality, but only the
# review mode actually invoked it. Other modes deferred the codex auth check
# to the runner's first codex spawn. The rename clarifies intent and is paired
# with dispatcher changes that invoke preflight.sh from every mode handler.
#
# Migration: replace `bash bootstrap.sh` with `bash preflight.sh`.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/_lib.sh" ]]; then
  # shellcheck source=_lib.sh
  source "$SCRIPT_DIR/_lib.sh" 2>/dev/null || true
  oc_log_run_ledger WARN "deprecated_script" script="bootstrap.sh" \
    reason="forwarding to preflight.sh" 2>/dev/null || true
fi

exec bash "$SCRIPT_DIR/preflight.sh" "$@"
