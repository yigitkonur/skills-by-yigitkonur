#!/usr/bin/env bash
# Compatibility shim forwarding to Node.js ESM implementation (scripts/skill-research.mjs)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec node "${SCRIPT_DIR}/skill-research.mjs" "$@"
