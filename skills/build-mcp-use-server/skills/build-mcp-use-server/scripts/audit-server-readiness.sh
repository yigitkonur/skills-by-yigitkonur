#!/usr/bin/env bash
set -u

usage() {
  cat <<'EOF'
Usage: audit-server-readiness.sh [target-dir]

Read-only scan for an mcp-use server package. Prints a categorized checklist for
setup, tools/schemas, transport, auth/session, widgets, production, validation.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

target="${1:-.}"
if [ ! -d "$target" ]; then
  echo "ERROR: target directory not found: $target" >&2
  exit 2
fi

target_abs="$(cd "$target" && pwd)"

if command -v rg >/dev/null 2>&1; then
  search() {
    rg -q "$1" "$target_abs" \
      -g '!node_modules/**' \
      -g '!dist/**' \
      -g '!build/**' \
      -g '!.git/**' \
      -g '!coverage/**'
  }
  list_matches() {
    rg -n "$1" "$target_abs" \
      -g '!node_modules/**' \
      -g '!dist/**' \
      -g '!build/**' \
      -g '!.git/**' \
      -g '!coverage/**' \
      2>/dev/null | head -8
  }
else
  search() {
    grep -R -q "$1" "$target_abs" 2>/dev/null
  }
  list_matches() {
    grep -R -n "$1" "$target_abs" 2>/dev/null | head -8
  }
fi

pkg="$target_abs/package.json"

has_pkg=no
has_type_module=no
has_mcp_use=no
has_zod=no
has_cli=no
has_react=no
has_dev_script=no
has_build_script=no
has_start_script=no
has_generate_types_script=no

if [ -f "$pkg" ]; then
  has_pkg=yes
  if command -v node >/dev/null 2>&1; then
    eval "$(
      node - "$pkg" <<'NODE'
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const deps = Object.assign({}, pkg.dependencies, pkg.devDependencies, pkg.peerDependencies, pkg.optionalDependencies);
const scripts = pkg.scripts || {};
function yn(v) { return v ? "yes" : "no"; }
console.log(`has_type_module=${yn(pkg.type === "module")}`);
console.log(`has_mcp_use=${yn(Boolean(deps["mcp-use"]))}`);
console.log(`has_zod=${yn(Boolean((pkg.dependencies || {}).zod))}`);
console.log(`has_cli=${yn(Boolean(deps["@mcp-use/cli"]))}`);
console.log(`has_react=${yn(Boolean(deps["@mcp-use/react"]))}`);
console.log(`has_dev_script=${yn(Boolean(scripts.dev))}`);
console.log(`has_build_script=${yn(Boolean(scripts.build))}`);
console.log(`has_start_script=${yn(Boolean(scripts.start))}`);
console.log(`has_generate_types_script=${yn(Boolean(scripts["generate-types"]) || Object.values(scripts).some((s) => String(s).includes("generate-types")))}`);
NODE
    )"
  else
    grep -q '"type"[[:space:]]*:[[:space:]]*"module"' "$pkg" && has_type_module=yes
    grep -q '"mcp-use"' "$pkg" && has_mcp_use=yes
    grep -q '"zod"' "$pkg" && has_zod=yes
    grep -q '"@mcp-use/cli"' "$pkg" && has_cli=yes
    grep -q '"@mcp-use/react"' "$pkg" && has_react=yes
    grep -q '"dev"' "$pkg" && has_dev_script=yes
    grep -q '"build"' "$pkg" && has_build_script=yes
    grep -q '"start"' "$pkg" && has_start_script=yes
    grep -q 'generate-types' "$pkg" && has_generate_types_script=yes
  fi
fi

yn_search() {
  if search "$1"; then
    echo yes
  else
    echo no
  fi
}

has_server_import="$(yn_search 'from ["'\"']mcp-use/server["'\"']')"
has_react_import="$(yn_search 'from ["'\"']mcp-use/react["'\"']')"
has_new_server="$(yn_search 'new MCPServer')"
has_tool="$(yn_search 'server\.tool\(')"
has_ui_resource="$(yn_search 'server\.uiResource\(')"
has_allowed_origins="$(yn_search 'allowedOrigins')"
has_cors="$(yn_search 'cors[[:space:]]*:')"
has_health="$(yn_search '["'\"']/health["'\"']')"
has_ready="$(yn_search '["'\"']/ready["'\"']')"
has_auth="$(yn_search 'oauth[A-Za-z]*Provider|oauthProxy|ctx\.auth|Authorization')"
has_session="$(yn_search 'sessionStore|RedisSessionStore|FileSystemSessionStore|InMemorySessionStore|streamManager|RedisStreamManager|stateless')"
has_widget_dir=no
if [ -d "$target_abs/resources" ]; then
  has_widget_dir=yes
fi
has_widget_metadata="$(yn_search 'widgetMetadata|tool\.widget|widget\(')"
has_generate_types_usage="$(yn_search 'generate-types|tool-registry\\.d\\.ts')"

item() {
  local label="$1"
  local status="$2"
  local note="$3"
  printf '  [%s] %s' "$status" "$label"
  if [ -n "$note" ]; then printf ' - %s' "$note"; fi
  printf '\n'
}

echo "mcp-use server readiness audit"
echo "Target: $target_abs"
echo ""

echo "Setup"
item "$([ "$has_pkg" = yes ] && echo "package.json found" || echo "package.json missing")" "$has_pkg" "$pkg"
item '"type": "module"' "$has_type_module" "required for ESM imports"
item "mcp-use declared" "$has_mcp_use" "server framework dependency"
item "zod declared in dependencies" "$has_zod" "peer dependency; should be in dependencies, not only devDependencies"
item "@mcp-use/cli available" "$has_cli" "needed for dev/build/start/deploy/typegen workflows"

echo ""
echo "Tools and schemas"
item "imports from mcp-use/server" "$has_server_import" ""
item "new MCPServer call" "$has_new_server" ""
item "server.tool registrations" "$has_tool" ""
item "generate-types script or usage" "$has_generate_types_script" "package script"
item "generated type usage" "$has_generate_types_usage" ".mcp-use/tool-registry.d.ts or command references"

echo ""
echo "Transport"
item "dev script" "$has_dev_script" ""
item "build script" "$has_build_script" ""
item "start script" "$has_start_script" ""
item "allowedOrigins configured" "$has_allowed_origins" "public HTTP servers need DNS rebinding protection"
item "CORS configured" "$has_cors" "public HTTP servers need deliberate origins and headers"

echo ""
echo "Auth and session"
item "auth config or ctx.auth usage" "$has_auth" ""
item "session/stateless config" "$has_session" ""

echo ""
echo "Widgets"
item "@mcp-use/react available" "$has_react" "needed only for React widgets"
item "imports from mcp-use/react" "$has_react_import" ""
item "resources/ directory" "$has_widget_dir" ""
item "server.uiResource registrations" "$has_ui_resource" ""
item "widget metadata/helper usage" "$has_widget_metadata" ""

echo ""
echo "Production"
item "/health route" "$has_health" ""
item "/ready route" "$has_ready" ""

echo ""
echo "Validation pointers"
echo "  - If tools or schemas changed: run mcp-use generate-types and typecheck."
echo "  - If the server runs locally: verify with Inspector and curl initialize/tools/list/tools/call."
echo "  - If the server is deployed: verify /health, /ready, and one live MCP operation."

echo ""
echo "High-signal matches"
list_matches 'new MCPServer|server\.tool\(|server\.uiResource\(|allowedOrigins|/health|/ready|oauth[A-Za-z]*Provider|RedisSessionStore|McpUseProvider' || true
