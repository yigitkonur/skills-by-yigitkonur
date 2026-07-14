#!/usr/bin/env bash
# install-coolify-cli.sh — install the `coolify` CLI to ~/.local/bin.
#
# The CLI is optional for this skill (deploys go through the API), but it's the
# easiest way to read status/logs and verify a context: `coolify resource list`,
# `coolify context verify`.
#
# Usage: install-coolify-cli.sh [version]     # default 1.0.3
set -euo pipefail

VERSION="${1:-1.0.3}"
INSTALL_DIR="$HOME/.local/bin"
PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) ARCH="amd64";;
  aarch64|arm64) ARCH="arm64";;
esac

echo "🚀 Installing Coolify CLI v${VERSION} (${PLATFORM}/${ARCH}) → ${INSTALL_DIR}"
mkdir -p "$INSTALL_DIR"

URL="https://github.com/coollabsio/coolify-cli/releases/download/${VERSION}/coolify-cli_${VERSION}_${PLATFORM}_${ARCH}.tar.gz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "📥 $URL"
curl -fsSL "$URL" -o "$TMP/coolify-cli.tar.gz"
tar -xzf "$TMP/coolify-cli.tar.gz" -C "$TMP"
mv "$TMP/coolify" "$INSTALL_DIR/coolify"
chmod +x "$INSTALL_DIR/coolify"

echo ""
echo "✅ Installed. Next:"
echo "  1. Ensure ${INSTALL_DIR} is on PATH:  export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "  2. Get an API token at app.coolify.io → Keys & Tokens"
echo "  3. Add a context:  coolify context add cloud https://app.coolify.io <token>"
echo "  4. Verify:         coolify context verify"
