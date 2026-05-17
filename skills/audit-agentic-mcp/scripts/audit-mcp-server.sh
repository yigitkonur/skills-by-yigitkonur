#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
audit-mcp-server.sh - read-only MCP server static audit

Usage:
  audit-mcp-server.sh [target-path]
  audit-mcp-server.sh --help

Scans a target directory for MCP entrypoints, framework signals, tool
registration candidates, deprecated SSE transport signals, stdout logging, and
detectable schema/annotation/error-handling gaps. Output is deterministic
Markdown. The scan is heuristic and does not parse ASTs.
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

TARGET="${1:-.}"
if [[ ! -d "$TARGET" ]]; then
  echo "error: target path is not a directory: $TARGET" >&2
  exit 2
fi

if command -v rg >/dev/null 2>&1; then
  HAS_RG=1
else
  HAS_RG=0
fi

scan() {
  local pattern="$1"
  if [[ "$HAS_RG" -eq 1 ]]; then
    rg -n --hidden \
      -g '!node_modules' -g '!vendor' -g '!dist' -g '!build' -g '!coverage' \
      -g '!*.lock' -g '!package-lock.json' -g '!pnpm-lock.yaml' \
      "$pattern" "$TARGET" 2>/dev/null || true
  else
    grep -RInE "$pattern" "$TARGET" \
      --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=dist \
      --exclude-dir=build --exclude-dir=coverage 2>/dev/null || true
  fi
}

count_matches() {
  scan "$1" | wc -l | tr -d ' '
}

first_matches() {
  local pattern="$1"
  local limit="${2:-12}"
  scan "$pattern" | sed -n "1,${limit}p"
}

real_target() {
  (cd "$TARGET" && pwd)
}

TOOL_PATTERN='server\.tool|registerTool|@mcp\.tool|@tool|tool\('
SCHEMA_PATTERN='inputSchema|outputSchema|z\.object|z\.string|z\.number|BaseModel|Field\(|jsonschema|JsonSchema'
ANNOTATION_PATTERN='annotations|readOnlyHint|destructiveHint|idempotentHint|openWorldHint'
ERROR_PATTERN='isError|McpError|ProtocolError|try[[:space:]]*\{|catch[[:space:]]*\(|except[[:space:]]'
SSE_PATTERN='SSEServerTransport|/sse|transport=["'\'']sse|transport:[[:space:]]*["'\'']sse|server-sent|EventSource'
STDOUT_PATTERN='console\.log|process\.stdout|print\(|sys\.stdout|logger\.info\(.*stdout'

tool_count="$(count_matches "$TOOL_PATTERN")"
schema_count="$(count_matches "$SCHEMA_PATTERN")"
annotation_count="$(count_matches "$ANNOTATION_PATTERN")"
error_count="$(count_matches "$ERROR_PATTERN")"
sse_count="$(count_matches "$SSE_PATTERN")"
stdout_count="$(count_matches "$STDOUT_PATTERN")"

echo "# MCP Static Audit"
echo
echo "Target: \`$(real_target)\`"
echo

echo "## Likely MCP Entrypoints"
entrypoints="$(first_matches 'McpServer|FastMCP|new Server\(|server\.connect|mcp\.run|StdioServerTransport|StreamableHTTP' 12)"
if [[ -n "$entrypoints" ]]; then
  echo "$entrypoints" | sed 's/^/- /'
else
  echo "- No likely MCP entrypoints found."
fi
echo

echo "## Framework Signals"
for label_pattern in \
  "mcp-use|mcp-use/server" \
  "@modelcontextprotocol/sdk" \
  "@modelcontextprotocol/server" \
  "FastMCP|fastmcp"; do
  label="${label_pattern%%|*}"
  matches="$(first_matches "$label_pattern" 6)"
  if [[ -n "$matches" ]]; then
    echo "### $label"
    echo "$matches" | sed 's/^/- /'
  fi
done
if [[ -z "$(scan 'mcp-use|@modelcontextprotocol/sdk|@modelcontextprotocol/server|FastMCP|fastmcp' | sed -n '1p')" ]]; then
  echo "- No explicit framework dependency or import signals found."
fi
echo

echo "## Tool Surface Signals"
echo "- Tool registration candidates: $tool_count"
echo "- Schema candidates: $schema_count"
echo "- Annotation candidates: $annotation_count"
echo "- Error-handling candidates: $error_count"
echo
tool_matches="$(first_matches "$TOOL_PATTERN" 20)"
if [[ -n "$tool_matches" ]]; then
  echo "### First tool candidates"
  echo "$tool_matches" | sed 's/^/- /'
  echo
fi

echo "## Risk Flags"
if [[ "$sse_count" -gt 0 ]]; then
  echo "### Deprecated or legacy SSE signals ($sse_count)"
  first_matches "$SSE_PATTERN" 12 | sed 's/^/- /'
else
  echo "- No obvious SSE transport signals found."
fi
echo
if [[ "$stdout_count" -gt 0 ]]; then
  echo "### stdout logging signals ($stdout_count)"
  first_matches "$STDOUT_PATTERN" 12 | sed 's/^/- /'
else
  echo "- No obvious stdout logging signals found."
fi
echo

echo "## Heuristic Gaps"
if [[ "$tool_count" -gt 0 && "$schema_count" -eq 0 ]]; then
  echo "- Tool registrations found, but no schema signals detected. Verify every tool validates input."
fi
if [[ "$tool_count" -gt 0 && "$annotation_count" -eq 0 ]]; then
  echo "- Tool registrations found, but no annotation signals detected. Check readOnly/destructive/idempotent/openWorld hints."
fi
if [[ "$tool_count" -gt 0 && "$error_count" -eq 0 ]]; then
  echo '- Tool registrations found, but no error-handling signals detected. Check recoverable `isError` results and protocol errors.'
fi
if [[ "$tool_count" -eq 0 ]]; then
  echo "- No tool registrations detected. Confirm this target is an MCP server and not only client config."
fi
if [[ "$tool_count" -gt 20 ]]; then
  echo "- More than 20 tool candidates detected. Review context budget and progressive discovery."
fi
if [[ "$tool_count" -gt 0 && "$schema_count" -gt 0 && "$annotation_count" -gt 0 && "$error_count" -gt 0 ]]; then
  echo "- No obvious static gaps from the basic heuristic scan."
fi
echo

echo "## Assumptions"
echo "- Read-only scan. No files were modified."
echo "- Counts are regex heuristics, not AST-backed facts."
echo "- Generated files, lockfiles, build output, and dependency directories are excluded."
echo "- Treat findings as triage leads; confirm each one in source before editing."
