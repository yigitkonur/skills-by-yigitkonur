#!/usr/bin/env bash
# Form automation using agent-browser ref-based workflow
# Source: official agent-browser documentation

set -euo pipefail

URL="${1:?Usage: $0 <form-url>}"

echo "Opening form page..."
agent-browser open "$URL"
agent-browser wait --load networkidle

echo "Getting interactive elements..."
agent-browser snapshot -i

echo "---"
echo "Form elements discovered. Use refs to interact:"
echo "  agent-browser fill @e1 \"value\""
echo "  agent-browser select @e2 \"option\""
echo "  agent-browser check @e3"
echo "  agent-browser click @e4  # submit"
echo ""
echo "After submission, re-snapshot to verify:"
echo "  agent-browser diff snapshot"
