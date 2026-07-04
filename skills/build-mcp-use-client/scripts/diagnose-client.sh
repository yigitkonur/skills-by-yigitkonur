#!/usr/bin/env bash
set -u

ROOT="${1:-.}"

row() {
  printf '%-34s | %-8s | %s\n' "$1" "$2" "$3"
}

if [ ! -d "$ROOT" ]; then
  printf 'ERROR: project root not found: %s\n' "$ROOT" >&2
  exit 2
fi

cd "$ROOT" || exit 2

if [ -f package.json ] && command -v node >/dev/null 2>&1; then
  if ! node -e 'JSON.parse(require("fs").readFileSync("package.json", "utf8"))' >/dev/null 2>&1; then
    printf 'ERROR: package.json exists but could not be parsed.\n' >&2
    exit 3
  fi
fi

FILES="$(find . \
  \( -path './node_modules' -o -path './.git' -o -path './dist' -o -path './build' -o -path './coverage' \) -prune -o \
  \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.json' \) -type f -print)"

count_pattern() {
  pattern="$1"
  if [ -z "$FILES" ]; then
    printf '0'
    return
  fi
  printf '%s\n' "$FILES" | while IFS= read -r file; do
    grep -E "$pattern" "$file" >/dev/null 2>&1 && printf '%s\n' "$file"
  done | sort -u | wc -l | tr -d ' '
}

list_files() {
  pattern="$1"
  limit="${2:-8}"
  if [ -z "$FILES" ]; then
    return
  fi
  printf '%s\n' "$FILES" | while IFS= read -r file; do
    grep -E "$pattern" "$file" >/dev/null 2>&1 && printf '%s\n' "$file"
  done | sort -u | head -n "$limit" | sed 's#^\./##'
}

package_manager="unknown"
[ -f package-lock.json ] && package_manager="npm"
[ -f pnpm-lock.yaml ] && package_manager="pnpm"
[ -f yarn.lock ] && package_manager="yarn"
[ -f bun.lockb ] && package_manager="bun"
[ -f bun.lock ] && package_manager="bun"

printf 'MCP client diagnostic for %s\n\n' "$(pwd)"
printf '%-34s | %-8s | %s\n' "Check" "Result" "Next"
printf '%-34s-+-%-8s-+-%s\n' "----------------------------------" "--------" "----------------------------------------"

if [ -f package.json ]; then
  if command -v node >/dev/null 2>&1; then
    has_mcp="$(node - <<'NODE'
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
const deps = Object.assign({}, pkg.dependencies, pkg.devDependencies, pkg.peerDependencies, pkg.optionalDependencies);
console.log(deps["mcp-use"] || "");
NODE
)"
    if [ -n "$has_mcp" ]; then
      row "package.json mcp-use" "found" "$has_mcp"
    else
      row "package.json mcp-use" "missing" "Install mcp-use before implementing a library client."
    fi
  else
    row "package.json" "found" "Install Node to inspect dependency fields."
  fi
else
  row "package.json" "missing" "This may be a non-Node root; target the package directory."
fi

row "package manager" "$package_manager" "Detected from lockfiles."

main_imports="$(count_pattern 'from ["'"'"']mcp-use["'"'"']|require\(["'"'"']mcp-use["'"'"']\)')"
browser_imports="$(count_pattern 'mcp-use/browser')"
react_imports="$(count_pattern 'mcp-use/react')"
sdk_imports="$(count_pattern '@modelcontextprotocol/sdk')"
row "mcp-use Node imports" "$main_imports" "Use for Node clients."
row "mcp-use/browser imports" "$browser_imports" "Use for browser clients."
row "mcp-use/react imports" "$react_imports" "Use for React hooks/providers."
row "direct SDK imports" "$sdk_imports" "Route raw SDK implementation to SDK skills unless intentional."

config_files="$(find . -maxdepth 3 \
  \( -name 'mcp.json' -o -name 'mcp.config.*' -o -path './.vscode/mcp.json' \) -type f -print | sed 's#^\./##' | paste -sd ', ' -)"
if [ -n "$config_files" ]; then
  row "MCP config files" "found" "$config_files"
else
  row "MCP config files" "none" "Check inline MCPClient config."
fi

if [ -f package.json ] && command -v node >/dev/null 2>&1; then
  scripts="$(node - <<'NODE'
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
const scripts = Object.entries(pkg.scripts || {}).filter(([, v]) => /mcp-use client|tsx|node/.test(String(v)));
console.log(scripts.map(([k, v]) => `${k}: ${v}`).join(" | "));
NODE
)"
  if [ -n "$scripts" ]; then
    row "relevant package scripts" "found" "$scripts"
  else
    row "relevant package scripts" "none" "Add a runnable smoke command when implementing."
  fi
fi

status_mistakes="$(count_pattern 'mcp\.status|server\.status')"
persistence_mistakes="$(count_pattern 'persistenceProvider')"
provider_hooks="$(count_pattern 'useMcpClient|useMcpServer')"
provider_component="$(count_pattern 'McpClientProvider')"
row "React status property" "$status_mistakes" "Use state, not status."
row "React persistence prop" "$persistence_mistakes" "Use storageProvider."
if [ "$provider_hooks" != "0" ] && [ "$provider_component" = "0" ]; then
  row "McpClientProvider" "missing" "useMcpClient/useMcpServer require a provider."
else
  row "McpClientProvider" "$provider_component" "Use one singleton provider for multi-server apps."
fi

client_usage="$(count_pattern 'new MCPClient|MCPClient\.fromDict|MCPClient\.fromConfigFile')"
cleanup_usage="$(count_pattern 'closeAllSessions|client\.close\(|process\.on\(["'"'"']SIG(INT|TERM)["'"'"']')"
if [ "$client_usage" != "0" ] && [ "$cleanup_usage" = "0" ]; then
  row "client cleanup" "missing" "Add closeAllSessions() or client.close() in finally/signal handlers."
else
  row "client cleanup" "$cleanup_usage" "Use client.close() for code mode."
fi

auth_files="$(list_files 'Authorization|authToken|headers[[:space:]]*:|Bearer ' 8 | paste -sd ', ' -)"
if [ -n "$auth_files" ]; then
  row "auth/header patterns" "found" "Review without printing secrets: $auth_files"
else
  row "auth/header patterns" "none" "If auth is required, add OAuth or server-side secret handling."
fi

websocket_refs="$(count_pattern 'WebSocket|websocket|ws://|wss://')"
row "WebSocket references" "$websocket_refs" "MCP clients should use Streamable HTTP or legacy SSE."

reconnect_refs="$(count_pattern 'autoReconnect|reconnectionOptions|resetTimeoutOnProgress|maxTotalTimeout|AbortController')"
row "reconnection/timeouts" "$reconnect_refs" "Add for long-running tools and production clients."

printf '\nSuggested references:\n'
if [ "$main_imports" != "0" ] || [ "$browser_imports" != "0" ]; then
  printf '%s\n' '- references/guides/client-configuration.md'
fi
if [ "$react_imports" != "0" ] || [ "$status_mistakes" != "0" ] || [ "$persistence_mistakes" != "0" ]; then
  printf '%s\n' '- references/guides/usemcp-and-react.md'
fi
if [ -n "$auth_files" ]; then
  printf '%s\n' '- references/guides/authentication.md'
  printf '%s\n' '- references/troubleshooting/common-errors.md'
fi
if [ "$reconnect_refs" = "0" ]; then
  printf '%s\n' '- references/guides/tools.md'
  printf '%s\n' '- references/patterns/production-patterns.md'
fi
if [ "$sdk_imports" != "0" ]; then
  printf '%s\n' '- build-mcp-server-sdk-v1 or build-mcp-server-sdk-v2 if raw SDK code is intentional'
fi
printf '%s\n' '- references/patterns/anti-patterns.md'

exit 0
