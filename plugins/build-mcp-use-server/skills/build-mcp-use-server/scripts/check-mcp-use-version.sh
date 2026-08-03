#!/bin/bash
# check-mcp-use-version.sh
# Report installed mcp-use/@mcp-use/cli versions; compare against npm dist-tags; detect v1 vs v2.

set -euo pipefail

echo "=== mcp-use Version Check ==="
echo ""

# Prefer the project-local CLI so the report reflects this checkout's installed version.
if [ -x "./node_modules/.bin/mcp-use" ]; then
    MCP_USE_PATH="./node_modules/.bin/mcp-use"
    echo "✓ mcp-use found at: $MCP_USE_PATH"
elif command -v mcp-use &>/dev/null; then
    MCP_USE_PATH="$(command -v mcp-use)"
    echo "✓ mcp-use found at: $MCP_USE_PATH"
else
    echo "✗ mcp-use not found locally or in PATH"
    exit 1
fi

# Detect v1 vs v2 by checking imports in the CLI
if "$MCP_USE_PATH" --version 2>/dev/null | grep -qE '^(4\.|5\.)'; then
    echo "✓ mcp-use CLI: v2 (version 4.x or later)"
    CLI_VERSION="v2"
elif "$MCP_USE_PATH" --version 2>/dev/null | grep -qE '^(3\.|2\.1)'; then
    echo "✓ mcp-use CLI: v1 (version 3.x or earlier)"
    CLI_VERSION="v1"
else
    CLI_VERSION="unknown"
    echo "? mcp-use CLI: version unclear (run: mcp-use --version)"
fi

echo ""

# Check installed mcp-use package version
if [ -f "package.json" ]; then
    if grep -q '"mcp-use":' package.json; then
        LOCAL_MVER=$(grep '"mcp-use":' package.json | head -1 | sed 's/.*"mcp-use": *"\([^"]*\)".*/\1/')
        echo "Local package.json mcp-use: $LOCAL_MVER"

        # Detect v1 vs v2 by checking the package's own exports map.
        # v1 declares a "./server" subpath export (dist/src/server/index.{js,cjs,d.ts});
        # the literal string "mcp-use/server" never appears in package.json, so grepping
        # for it can never match — check the "./server" export key instead.
        if [ -d "node_modules/mcp-use" ]; then
            if grep -q '"\./server"' node_modules/mcp-use/package.json 2>/dev/null; then
                echo "  → Detected v1 package (\"./server\" export key present)"
            elif grep -q '"type": "module"' node_modules/mcp-use/package.json 2>/dev/null && \
                 [ -f "node_modules/mcp-use/dist/index.d.ts" ] && \
                 grep -q 'export.*MCPServer' node_modules/mcp-use/dist/index.d.ts 2>/dev/null; then
                echo "  → Detected v2 package (root MCPServer export, ESM only, no \"./server\")"
            fi
        fi
    else
        echo "No mcp-use in local package.json"
    fi
else
    echo "No package.json found"
fi

echo ""

# Fetch npm dist-tags for comparison
echo "=== npm Dist-Tags Comparison ==="
echo ""

if command -v npm &>/dev/null; then
    if npm view mcp-use dist-tags --json 2>/dev/null | grep -q '"latest"'; then
        LATEST=$(npm view mcp-use dist-tags.latest 2>/dev/null)
        BETA=$(npm view mcp-use dist-tags.beta 2>/dev/null || echo "N/A")
        LEGACY_V1=$(npm view mcp-use dist-tags.legacy-v1 2>/dev/null || echo "N/A")

        echo "mcp-use npm tags:"
        echo "  latest: $LATEST (v1 era)"
        echo "  beta: $BETA (v2)"
        echo "  legacy-v1: $LEGACY_V1"
    else
        echo "✗ Could not fetch npm tags"
    fi
else
    echo "npm not found; skipping npm check"
fi

echo ""

# Check @mcp-use/cli versions
if command -v npm &>/dev/null; then
    CLI_BETA=$(npm view @mcp-use/cli dist-tags.beta 2>/dev/null || echo "N/A")
    echo "@mcp-use/cli beta tag: $CLI_BETA"
fi

echo ""
echo "=== Summary ==="
echo "CLI version detected: $CLI_VERSION"
echo "Run 'mcp-use --version' for exact version"
echo "If v1, migrate to v2@beta using: npm install mcp-use@beta"
