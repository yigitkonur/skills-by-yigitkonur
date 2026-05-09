#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: check-v2-feasibility.sh <project-dir>

Read-only audit for an MCP TypeScript server before an SDK v1 -> v2 migration.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

PROJECT_INPUT="${1:-.}"
if [[ ! -d "$PROJECT_INPUT" ]]; then
  echo "error: project directory not found: $PROJECT_INPUT" >&2
  exit 2
fi

PROJECT="$(cd "$PROJECT_INPUT" && pwd -P)"
PKG="$PROJECT/package.json"
TSCONFIG="$PROJECT/tsconfig.json"

if command -v rg >/dev/null 2>&1; then
  SEARCH_TOOL="rg"
else
  SEARCH_TOOL="grep"
fi

search() {
  local pattern="$1"
  if [[ "$SEARCH_TOOL" == "rg" ]]; then
    rg -n --hidden \
      --glob '!node_modules/**' \
      --glob '!dist/**' \
      --glob '!build/**' \
      --glob '!coverage/**' \
      "$pattern" "$PROJECT" 2>/dev/null || true
  else
    grep -RInE \
      --exclude-dir=node_modules \
      --exclude-dir=dist \
      --exclude-dir=build \
      --exclude-dir=coverage \
      "$pattern" "$PROJECT" 2>/dev/null || true
  fi
}

count_matches() {
  search "$1" | wc -l | tr -d ' '
}

print_sample() {
  local title="$1"
  local pattern="$2"
  local matches
  matches="$(search "$pattern" | sed "s#${PROJECT}/##" | head -12)"
  if [[ -n "$matches" ]]; then
    echo "- $title:"
    printf '%s\n' "$matches" | sed 's/^/  - /'
  fi
}

pkg_value() {
  local key="$1"
  if [[ -f "$PKG" ]]; then
    grep -E "\"$key\"[[:space:]]*:" "$PKG" | head -1 | sed -E "s#.*\"$key\"[[:space:]]*:[[:space:]]*\"([^\"]+)\".*#\1#" || true
  fi
}

sdk_version=""
if [[ -f "$PKG" ]]; then
  sdk_version="$(pkg_value '@modelcontextprotocol/sdk')"
fi

has_sdk="no"
sdk_profile="not detected"
if [[ -n "$sdk_version" && "$sdk_version" != *"@modelcontextprotocol/sdk"* ]]; then
  has_sdk="yes"
  case "$sdk_version" in
    2.0.0-alpha.*) sdk_profile="v2 meta-package ($sdk_version)" ;;
    *1.*|^1.*|~1.*|">=1"*) sdk_profile="v1 dependency ($sdk_version)" ;;
    *) sdk_profile="ambiguous SDK dependency ($sdk_version)" ;;
  esac
fi

type_module="no"
if [[ -f "$PKG" ]] && grep -Eq '"type"[[:space:]]*:[[:space:]]*"module"' "$PKG"; then
  type_module="yes"
fi

node_engine="$(pkg_value node)"
node_below20="unknown"
if [[ -n "$node_engine" && "$node_engine" != *node* ]]; then
  first_major="$(printf '%s\n' "$node_engine" | grep -Eo '[0-9]+' | head -1 || true)"
  if [[ -n "$first_major" ]]; then
    if (( first_major < 20 )); then
      node_below20="yes ($node_engine)"
    else
      node_below20="no ($node_engine)"
    fi
  fi
fi

tsconfig_cjs="no"
if [[ -f "$TSCONFIG" ]] && grep -Eiq '"module"[[:space:]]*:[[:space:]]*"(commonjs|amd|umd)"|"moduleResolution"[[:space:]]*:[[:space:]]*"node"' "$TSCONFIG"; then
  tsconfig_cjs="yes"
fi

module_exports_count="$(count_matches 'module\.exports|exports\.[A-Za-z0-9_]+[[:space:]]*=')"
require_count="$(count_matches '(^|[^A-Za-z0-9_])require\(')"
auth_count="$(count_matches 'mcpAuthRouter|requireBearerAuth|OAuthServerProvider|@modelcontextprotocol/sdk/server/auth/')"
sse_count="$(count_matches 'SSEServerTransport')"
streamable_count="$(count_matches 'StreamableHTTPServerTransport')"
raw_shape_count="$(count_matches '(inputSchema|outputSchema|argsSchema)[[:space:]]*:[[:space:]]*\{')"
ctx_count="$(count_matches 'extra\.(authInfo|sendNotification|sendRequest|requestInfo)')"
error_count="$(count_matches 'McpError|ErrorCode')"
sdk_import_count="$(count_matches '@modelcontextprotocol/sdk/')"

blockers=()
attention=()

if [[ "$has_sdk" != "yes" ]]; then
  blockers+=('`package.json` does not declare `@modelcontextprotocol/sdk`.')
fi
if [[ "$type_module" != "yes" ]]; then
  blockers+=('Missing package.json `"type": "module"`; v2 is ESM-only.')
fi
if [[ "$node_below20" == yes* ]]; then
  blockers+=("Node engine appears below 20: $node_below20.")
fi
if [[ "$tsconfig_cjs" == "yes" || "$module_exports_count" != "0" || "$require_count" != "0" ]]; then
  blockers+=("CommonJS signals found; resolve ESM conversion before a full v2 rewrite.")
fi
if [[ "$sse_count" != "0" ]]; then
  blockers+=('`SSEServerTransport` is present; v2 removes the SSE server transport.')
fi

if [[ "$auth_count" != "0" ]]; then
  attention+=("OAuth router/auth usage")
fi
if [[ "$streamable_count" != "0" ]]; then
  attention+=("Streamable HTTP transport")
fi
if [[ "$raw_shape_count" != "0" ]]; then
  attention+=("raw schema shapes")
fi
if [[ "$ctx_count" != "0" ]]; then
  attention+=('handler `extra` context usage')
fi
if [[ "$error_count" != "0" ]]; then
  attention+=("McpError/ErrorCode call sites")
fi

strategy="stay on v1"
strategy_reason="v2 is alpha; no v1 SDK dependency was detected."
if [[ "$has_sdk" == "yes" ]]; then
  if [[ "$sdk_profile" == v2\ meta-package* ]]; then
    strategy="meta-package shim"
    strategy_reason='the project already appears to use the v2 `@modelcontextprotocol/sdk` meta-package.'
  elif [[ "$auth_count" != "0" ]]; then
    strategy="meta-package + server-auth-legacy"
    strategy_reason="OAuth router/provider usage is present and should not be rewritten in the same step as the SDK port."
  elif [[ "$sse_count" != "0" || "$node_below20" == yes* || "$type_module" != "yes" ]]; then
    strategy="stay on v1"
    strategy_reason="migration blockers must be cleared before direct v2 package adoption."
  elif (( sdk_import_count > 10 || raw_shape_count > 5 || ctx_count > 5 )); then
    strategy="meta-package shim"
    strategy_reason="surface area is large enough that staged migration is safer than a big-bang rewrite."
  else
    strategy="full rewrite"
    strategy_reason="the detected surface area is small and no OAuth/SSE blocker was found."
  fi
fi

echo "# MCP SDK v1 -> v2 feasibility audit"
echo
echo "- Project: \`$PROJECT\`"
echo "- Search tool: \`$SEARCH_TOOL\`"
echo
echo "## Detected server profile"
echo
echo "- SDK dependency: $sdk_profile"
echo "- SDK import sites: $sdk_import_count"
echo "- package.json type module: $type_module"
echo "- Node engine below 20: $node_below20"
echo "- CommonJS signals: require=$require_count, module.exports=$module_exports_count, tsconfig=$tsconfig_cjs"
echo "- OAuth router/provider hits: $auth_count"
echo "- SSE transport hits: $sse_count"
echo "- Streamable HTTP hits: $streamable_count"
echo "- Raw schema candidates: $raw_shape_count"
echo "- Handler context candidates: $ctx_count"
echo "- Error rewrite candidates: $error_count"
echo
echo "## Recommended strategy"
echo
echo "- $strategy - $strategy_reason"
echo
echo "## Blockers"
echo
if ((${#blockers[@]} == 0)); then
  echo "- None detected by static checks."
else
  printf -- '- %s\n' "${blockers[@]}"
fi
echo
echo "## Files/imports requiring attention"
echo
if ((${#attention[@]} == 0)); then
  echo "- No high-risk rewrite candidates detected."
else
  printf -- '- %s\n' "${attention[@]}"
fi
print_sample "@modelcontextprotocol/sdk imports" '@modelcontextprotocol/sdk/'
print_sample "auth-router usage" 'mcpAuthRouter|requireBearerAuth|OAuthServerProvider|@modelcontextprotocol/sdk/server/auth/'
print_sample "transport usage" 'SSEServerTransport|StreamableHTTPServerTransport'
print_sample "raw schema candidates" '(inputSchema|outputSchema|argsSchema)[[:space:]]*:[[:space:]]*\{'
print_sample "handler context usage" 'extra\.(authInfo|sendNotification|sendRequest|requestInfo)'
print_sample "error rewrite candidates" 'McpError|ErrorCode'
echo
echo "## Validation commands to run next"
echo
echo "- \`npx tsc --noEmit\`"
echo "- existing unit/integration test command"
echo "- \`npx @anthropic-ai/mcp-inspector <server command>\`"
echo "- \`mcpc\` smoke checks via \`test-by-mcpc-cli\`, when mcpc is available"
