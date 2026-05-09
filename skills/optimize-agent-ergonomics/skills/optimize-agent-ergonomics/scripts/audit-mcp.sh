#!/usr/bin/env bash
set -u

usage() {
  cat <<'USAGE'
Usage:
  audit-mcp.sh <path>

Runs a conservative static MCP source preflight. It counts likely tool
registrations, schema declarations, transports, auth/session signals, and
error-handling patterns. It does not execute the server.
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

target="${1:-}"
if [[ -z "$target" ]]; then
  usage >&2
  exit 2
fi
if [[ ! -e "$target" ]]; then
  echo "target does not exist: $target" >&2
  exit 2
fi

if command -v rg >/dev/null 2>&1; then
  search_count() {
    rg -n -i "$1" "$target" -g '!node_modules' -g '!dist' -g '!build' -g '!coverage' 2>/dev/null | wc -l | tr -d ' '
  }
  search_lines() {
    rg -n -i "$1" "$target" -g '!node_modules' -g '!dist' -g '!build' -g '!coverage' 2>/dev/null | head -20
  }
else
  search_count() {
    grep -RInE "$1" "$target" 2>/dev/null | grep -v '/node_modules/' | wc -l | tr -d ' '
  }
  search_lines() {
    grep -RInE "$1" "$target" 2>/dev/null | grep -v '/node_modules/' | head -20
  }
fi

tool_pattern='registerTool|server\.tool|\.tool\(|@tool|@mcp\.tool|FastMCP|McpServer'
schema_pattern='inputSchema|outputSchema|z\.object|zod|BaseModel|Field\(|jsonschema|JSONSchema|pydantic'
transport_pattern='stdio|StdioServerTransport|StreamableHTTP|SSE|sse|transport|listen\(|http'
error_pattern='isError|McpError|JSON-RPC|jsonrpc|throw |raise |retry_after|next_action'
auth_pattern='oauth|bearer|authorization|auth|session|cors|rate.?limit|tenant'
stdout_pattern='console\.log|print\('

tools=$(search_count "$tool_pattern")
schemas=$(search_count "$schema_pattern")
transports=$(search_count "$transport_pattern")
errors=$(search_count "$error_pattern")
auth=$(search_count "$auth_pattern")
stdout_hazards=$(search_count "$stdout_pattern")

cat <<REPORT
# MCP Static Preflight

Target: $target

| Signal | Count | Meaning |
|---|---:|---|
| tool registrations / server markers | $tools | Map every registered tool before judging granularity. |
| schema declarations | $schemas | Confirm every tool has a flat, validated input shape. |
| transport strings | $transports | Identify stdio, Streamable HTTP, SSE, or custom transport choices. |
| error/retry patterns | $errors | Check for recoverable isError results and retry hints. |
| auth/session/ops signals | $auth | Inspect identity, session, CORS, rate-limit, and tenant handling. |
| stdout pollution hazards | $stdout_hazards | Review any stdout logging in stdio servers. |

## Sample Matches

### Tools
REPORT
search_lines "$tool_pattern"
cat <<REPORT

### Schemas
REPORT
search_lines "$schema_pattern"
cat <<REPORT

### Transports
REPORT
search_lines "$transport_pattern"
cat <<REPORT

### Errors
REPORT
search_lines "$error_pattern"
cat <<REPORT

### Auth / Sessions / Ops
REPORT
search_lines "$auth_pattern"
cat <<REPORT

### Stdout Hazards
REPORT
search_lines "$stdout_pattern"
cat <<REPORT

Limitations: this is static grep-style evidence only. It does not initialize the MCP server, call tools, validate schemas, verify auth, or prove production readiness.
REPORT
