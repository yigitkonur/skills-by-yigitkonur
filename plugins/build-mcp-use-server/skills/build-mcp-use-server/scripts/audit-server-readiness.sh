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
# NOTE: `((VAR++))` returns the pre-increment value as its exit status; when
# VAR is 0 that status is 0 (bash-false), which kills the script under `set
# -e` on the very first check. `: $((VAR++))` discards the arithmetic exit
# status so the increment can never abort the run.
check_pass() {
    echo "✓ $1"
    : $((PASS++))
}

check_warn() {
    echo "⚠ $1"
    : $((WARN++))
}

check_fail() {
    echo "✗ $1"
    : $((FAIL++))
}

echo "=== 1. Package Configuration ==="

# Check Node version (>= 22.22.2 required for mcp-use v2)
if command -v node &>/dev/null; then
    NODE_VERSION=$(node -v | sed 's/^v//')
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
    NODE_MINOR=$(echo "$NODE_VERSION" | cut -d. -f2)
    NODE_PATCH=$(echo "$NODE_VERSION" | cut -d. -f3)
    if [ "$NODE_MAJOR" -gt 22 ] || { [ "$NODE_MAJOR" -eq 22 ] && { [ "$NODE_MINOR" -gt 22 ] || { [ "$NODE_MINOR" -eq 22 ] && [ "$NODE_PATCH" -ge 2 ]; }; }; }; then
        check_pass "Node.js engine >= 22.22.2 (current: v$NODE_VERSION)"
    else
        check_fail "Node.js $NODE_VERSION is unsupported. mcp-use v2 requires Node >= 22.22.2"
    fi
else
    check_fail "Node.js not found in PATH"
fi

# Check ESM "type": "module"
if grep -q '"type": "module"' package.json; then
    check_pass "ESM-only (\"type\": \"module\")"
else
    check_fail "Not ESM. Add \"type\": \"module\" to package.json"
fi

# Check mcp-use version. `npm install mcp-use@beta` resolves and writes a
# concrete semver range (e.g. "^2.8.2"), never the literal "beta" —
# match any "2." version token after the mcp-use key, with or without a
# leading range operator (^, ~, >=).
if grep -qE '"mcp-use": *"[~^>=]*2\.' package.json; then
    check_pass "mcp-use v2 (2.x)"
else
    check_warn "mcp-use may be v1. Verify: npm list mcp-use"
fi

# Check Standard Schema v1 library (zod, valibot, arktype)
if grep -qE '"(zod|valibot|arktype)":' package.json; then
    SCHEMA_LIB=$(grep -oE '"(zod|valibot|arktype)"' package.json | head -1 | tr -d '"')
    check_pass "Standard Schema v1 library ($SCHEMA_LIB)"
else
    check_warn "No Standard Schema library (zod, valibot, arktype) found in package.json"
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

    # Check for default export (mandated by CLI runners)
    if grep -qE 'export\s+default\s+' "$ENTRY"; then
        check_pass "Default server export present (required for CLI runners)"
    else
        check_warn "No default export found in $ENTRY. CLI runners require: export default server;"
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

        # Check for OpenAI Apps SDK UI compliance
        if grep -q '"@openai/apps-sdk-ui"' package.json; then
            check_pass "@openai/apps-sdk-ui installed (ChatGPT UI compliant)"
        else
            check_warn "No @openai/apps-sdk-ui in package.json. Recommended for ChatGPT Apps UI compliance: npm install @openai/apps-sdk-ui"
        fi
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

# Gather tool candidate files: ENTRY and any files in src/tools or tools
TOOL_FILES=""
if [ -n "$ENTRY" ] && [ -f "$ENTRY" ]; then
    TOOL_FILES="$ENTRY"
fi
if [ -d "src/tools" ]; then
    SRC_TOOL_FILES=$(find src/tools -maxdepth 2 \( -name "*.ts" -o -name "*.js" \) 2>/dev/null || true)
    TOOL_FILES="$TOOL_FILES $SRC_TOOL_FILES"
fi
if [ -d "tools" ]; then
    EXTRA_TOOL_FILES=$(find tools -maxdepth 2 \( -name "*.ts" -o -name "*.js" \) 2>/dev/null || true)
    TOOL_FILES="$TOOL_FILES $EXTRA_TOOL_FILES"
fi

TOOL_COUNT=0
OUT_SCHEMA_COUNT=0
EXPORTED_TOOL_COUNT=0
HAS_DEPRECATED_HELPERS=false

for file in $TOOL_FILES; do
    if [ -f "$file" ]; then
        # Count tool definitions
        COUNT=$(grep -c 'server\.tool(' "$file" 2>/dev/null || true)
        TOOL_COUNT=$((TOOL_COUNT + COUNT))

        # Count outputSchema
        SCHEMA_COUNT=$(grep -c 'outputSchema:' "$file" 2>/dev/null || true)
        OUT_SCHEMA_COUNT=$((OUT_SCHEMA_COUNT + SCHEMA_COUNT))

        # Count exported static tool constants (required for mcp-env.d.ts typing)
        EXP_COUNT=$(grep -cE 'export\s+const\s+[a-zA-Z0-9_]+\s*=\s*server\.tool\(' "$file" 2>/dev/null || true)
        EXPORTED_TOOL_COUNT=$((EXPORTED_TOOL_COUNT + EXP_COUNT))

        # Check for deprecated response helpers: text(), object(), array(), image(), widget(), error(), mix()
        if grep -qE 'return\s+(text|object|array|image|widget|error|mix)\(' "$file" 2>/dev/null; then
            HAS_DEPRECATED_HELPERS=true
        fi
    fi
done

if [ "$TOOL_COUNT" -gt 0 ]; then
    check_pass "Found $TOOL_COUNT tool(s) defined across scanned files"

    if [ "$EXPORTED_TOOL_COUNT" -gt 0 ]; then
        check_pass "$EXPORTED_TOOL_COUNT tool(s) exported as static constants (✓ mcp-env.d.ts live typing)"
    else
        check_warn "No exported static tool constants found. Export tools (export const myTool = server.tool(...)) for View type safety."
    fi

    if [ "$OUT_SCHEMA_COUNT" -gt 0 ]; then
        check_pass "$OUT_SCHEMA_COUNT tool(s) with outputSchema (used by views)"
    else
        check_warn "No tools with outputSchema. Views require outputSchema to receive structured data."
    fi

    if [ "$HAS_DEPRECATED_HELPERS" = true ]; then
        check_warn "Using deprecated response helpers (text(), object(), widget(), array(), etc.). Prefer raw envelopes: { content: [...], structuredContent: ... }"
    fi
else
    check_warn "No tools found in $ENTRY or tools directories. Is this intentional?"
fi

echo ""
echo "=== 6. Build Artifacts ==="

if [ -d ".mcp-use/build" ]; then
    check_pass ".mcp-use/build/ directory exists"

    # mcp-use build always emits .mcp-use/build/index.js (Vite entryFileNames is
    # hardcoded to "index.js"); it never produces server.js.
    if [ -f ".mcp-use/build/index.js" ]; then
        check_pass "Build output present (.mcp-use/build/index.js)"
    else
        check_warn ".mcp-use/build/ exists but no index.js. Run: mcp-use build"
    fi
else
    check_warn "No .mcp-use/build/. Run: mcp-use build"
fi

echo ""
echo "=== 7. Generated Type Files ==="

# mcp-use typecheck writes mcp-env.d.ts to the project root (sibling to
# index.ts/package.json), not under .mcp-use/.
if [ -f "mcp-env.d.ts" ]; then
    check_pass "mcp-env.d.ts generated at project root (tool types for views)"
else
    check_warn "No mcp-env.d.ts at project root. Run: mcp-use typecheck"
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
