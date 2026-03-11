#!/usr/bin/env bash
# Authenticated session workflow using agent-browser auth vault
# Source: official agent-browser security documentation

set -euo pipefail

SESSION_NAME="${1:?Usage: $0 <session-name> <login-url> <username>}"
LOGIN_URL="${2:?Usage: $0 <session-name> <login-url> <username>}"
USERNAME="${3:?Usage: $0 <session-name> <login-url> <username>}"

echo "Setting up authenticated session: $SESSION_NAME"

# Method 1: Auth vault (recommended)
echo "Enter password:" 
read -rs PASSWORD
echo "$PASSWORD" | agent-browser auth save "$SESSION_NAME" \
  --url "$LOGIN_URL" \
  --username "$USERNAME" \
  --password-stdin

agent-browser auth login "$SESSION_NAME"

# Verify login succeeded
agent-browser snapshot -i
echo "Auth session ready. Use: agent-browser --session-name $SESSION_NAME open <url>"
