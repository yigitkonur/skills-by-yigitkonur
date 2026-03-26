#!/usr/bin/env bash
set -euo pipefail

# @raycast.schemaVersion 1
# @raycast.title Example Bash Command
# @raycast.mode compact
# @raycast.packageName Examples

value="${1:-world}"
echo "Hello, $value"
