#!/bin/bash
# audit-server-readiness.sh
# Audit v2 MCP server readiness: check root import, ESM, zod v4, oauth, views, outputSchema, build artifacts.

set -euo pipefail

echo "=== mcp-use v2 Server Readiness Audit ==="
echo ""

if [ ! -f "package.json" ]; then
    echo "✗ No package.json found. Not an mcp-use project?"
    exit 1
fi

PASS=0
WARN=0
FAIL=0

# Helper functions
check_pass() {
    echo "✓ $1"
    ((PASS++))
}

check_warn() {
    echo "⚠ $1"
    ((WARN++))
}

check_fail() {
    echo "✗ $1"
    ((FAIL++))
}

echo "=== 1. Package Configuration ==="

# Check ESM "type": "module"
if grep -q '"type": "module"' package.json; then
    check_pass "ESM-only (\"type\": \"module\")"
else
    check_fail "Not ESM. Add \"type\": \"module\" to package.json"
fi

# Check mcp-use version
if grep -q '"mcp-use":.*@beta\|"mcp-use": "\^2\.' package.json; then
    check_pass "mcp-use v2 (beta or 2.x)"
else
    check_warn "mcp-use may be v1. Verify: npm list mcp-use"
fi

# Check zod v4
if grep -q '"zod": "\^4\.' package.json; then
    check_pass "zod v4 (correct)"
else
    check_warn "zod not v4. Add: npm install zod@^4"
fi

echo ""
echo "=== 2. Server Entry Point ==="

# Find entry file (index.ts or src/index.ts by convention)
ENTRY=""
if [ -f "index.ts" ]; then
    ENTRY="index.ts"
elif [ -f "src/index.ts" ]; then
    ENTRY="src/index.ts"
elif grep -q '"main":' package.json; then
    ENTRY=$(grep '"main":' package.json | head -1 | sed 's/.*"main": *"\([^"]*\)".*/\1/')
fi

if [ -z "$ENTRY" ] || [ ! -f "$ENTRY" ]; then
    check_fail "No entry point found (expected index.ts or src/index.ts)"
else
    check_pass "Entry file: $ENTRY"

    # Check for root MCPServer import (v2)
    if grep -q 'from.*"mcp-use"' "$ENTRY" && grep -q 'MCPServer' "$ENTRY"; then
        check_pass "Root MCPServer import (✓ v2)"
    else
        check_warn "No root MCPServer import in $ENTRY. Expected: import { MCPServer } from \"mcp-use\""
    fi

    # Check for deprecated mcp-use/server import (v1)
    if grep -q 'from.*"mcp-use/server"' "$ENTRY"; then
        check_fail "Found mcp-use/server import (v1 pattern). Change to: import { MCPServer } from \"mcp-use\""
    fi
fi

echo ""
echo "=== 3. Views & MCP Apps Configuration ==="

# Check views/ directory
if [ -d "views" ]; then
    VIEW_COUNT=$(find views -name "view.tsx" -o -name "view.ts" | wc -l)
    if [ "$VIEW_COUNT" -gt 0 ]; then
        check_pass "views/ directory with $VIEW_COUNT view file(s)"
    else
        check_warn "views/ directory exists but no view.tsx/view.ts found"
    fi
else
    check_warn "No views/ directory. Not needed if tool-only server."
fi

echo ""
echo "=== 4. OAuth Configuration ==="

if [ -n "$ENTRY" ] && [ -f "$ENTRY" ]; then
    if grep -q 'oauth:' "$ENTRY"; then
        check_pass "OAuth configuration present in server config"

        # Check for OAuth providers
        if grep -q 'from.*"mcp-use/oauth' "$ENTRY"; then
            check_pass "OAuth provider imported from mcp-use/oauth/*"
        fi
    else
        check_warn "No oauth config (optional; skip if unauthenticated server)"
    fi
fi

echo ""
echo "=== 5. Tool Definitions ==="

if [ -n "$ENTRY" ] && [ -f "$ENTRY" ]; then
    TOOL_COUNT=$(grep -c 'server\.tool(' "$ENTRY" || echo "0")
    if [ "$TOOL_COUNT" -gt 0 ]; then
        check_pass "Found $TOOL_COUNT tool(s) defined"

        # Check for outputSchema
        OUT_SCHEMA=$(grep -c 'outputSchema:' "$ENTRY" || echo "0")
        if [ "$OUT_SCHEMA" -gt 0 ]; then
            check_pass "$OUT_SCHEMA tool(s) with outputSchema (used by views)"
        else
            check_warn "No tools with outputSchema. Views require outputSchema to receive data."
        fi

        # Check for deprecated v1 helpers
        if grep -q 'return text(' "$ENTRY" 2>/dev/null || grep -q 'return object(' "$ENTRY" 2>/dev/null; then
            check_warn "Using deprecated response helpers (text(), object(), etc.). Prefer raw envelopes: { content: [...], structuredContent: ... }"
        fi
    else
        check_warn "No tools found. Is this intentional?"
    fi
fi

echo ""
echo "=== 6. Build Artifacts ==="

if [ -d ".mcp-use/build" ]; then
    check_pass ".mcp-use/build/ directory exists"

    if [ -f ".mcp-use/build/index.js" ] || [ -f ".mcp-use/build/server.js" ]; then
        check_pass "Build output present (server bundle)"
    else
        check_warn ".mcp-use/build/ exists but no .js files. Run: mcp-use build"
    fi
else
    check_warn "No .mcp-use/build/. Run: mcp-use build"
fi

echo ""
echo "=== 7. Generated Type Files ==="

if [ -f ".mcp-use/mcp-env.d.ts" ]; then
    check_pass ".mcp-use/mcp-env.d.ts generated (tool types for views)"
else
    check_warn "No .mcp-use/mcp-env.d.ts. Run: mcp-use typecheck"
fi

echo ""
echo "=== Summary ==="
echo "✓ Pass: $PASS"
[ "$WARN" -gt 0 ] && echo "⚠ Warnings: $WARN"
[ "$FAIL" -gt 0 ] && echo "✗ Failures: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "Fix failures above before deploying."
    exit 1
fi
