#!/usr/bin/env bash
set -u

ROOT="${1:-.}"

row() {
  printf '%-24s %s\n' "$1" "$2"
}

warn() {
  printf 'WARN: %s\n' "$1"
}

if ! command -v node >/dev/null 2>&1; then
  printf 'ERROR: node is required.\n' >&2
  exit 2
fi

if ! command -v npm >/dev/null 2>&1; then
  printf 'ERROR: npm is required.\n' >&2
  exit 2
fi

if [ ! -d "$ROOT" ]; then
  printf 'ERROR: project root not found: %s\n' "$ROOT" >&2
  exit 2
fi

cd "$ROOT" || exit 2

NODE_VERSION="$(node -p 'process.versions.node')"
row "Project root" "$(pwd)"
row "Local Node" "v$NODE_VERSION"

if [ -f package.json ]; then
  PKG_JSON="$(node <<'NODE'
const fs = require("fs");
try {
  const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
  const deps = Object.assign({}, pkg.dependencies, pkg.devDependencies, pkg.peerDependencies, pkg.optionalDependencies);
  let installed = "";
  try {
    installed = JSON.parse(fs.readFileSync("node_modules/mcp-use/package.json", "utf8")).version || "";
  } catch {}
  const managers = [];
  for (const [file, name] of [
    ["package-lock.json", "npm"],
    ["pnpm-lock.yaml", "pnpm"],
    ["yarn.lock", "yarn"],
    ["bun.lockb", "bun"],
    ["bun.lock", "bun"],
  ]) {
    if (fs.existsSync(file)) managers.push(name);
  }
  console.log(JSON.stringify({
    spec: deps["mcp-use"] || "",
    installed,
    managers,
    scripts: pkg.scripts || {},
  }));
} catch (error) {
  console.error(error.message);
  process.exit(3);
}
NODE
)" || {
    printf 'ERROR: package.json exists but could not be parsed.\n' >&2
    exit 3
  }
  MCP_SPEC="$(printf '%s' "$PKG_JSON" | node -e 'const fs=require("fs"); const x=JSON.parse(fs.readFileSync(0,"utf8")); console.log(x.spec || "")')"
  INSTALLED_VERSION="$(printf '%s' "$PKG_JSON" | node -e 'const fs=require("fs"); const x=JSON.parse(fs.readFileSync(0,"utf8")); console.log(x.installed || "")')"
  MANAGERS="$(printf '%s' "$PKG_JSON" | node -e 'const fs=require("fs"); const x=JSON.parse(fs.readFileSync(0,"utf8")); console.log((x.managers || []).join(", ") || "unknown")')"
  row "Package manager" "$MANAGERS"
  if [ -n "$MCP_SPEC" ]; then
    row "package.json mcp-use" "$MCP_SPEC"
  else
    row "package.json mcp-use" "not declared"
  fi
  if [ -n "$INSTALLED_VERSION" ]; then
    row "Installed mcp-use" "$INSTALLED_VERSION"
  else
    row "Installed mcp-use" "not installed under node_modules"
  fi
else
  MCP_SPEC=""
  INSTALLED_VERSION=""
  row "package.json" "not found"
  warn "No package.json found; version checks are limited to npm metadata."
fi

NPM_JSON="$(npm view mcp-use version engines peerDependencies --json 2>/tmp/mcp-use-npm-view.err)" || {
  warn "Could not query npm metadata: $(cat /tmp/mcp-use-npm-view.err 2>/dev/null)"
  exit 0
}

LATEST_VERSION="$(printf '%s' "$NPM_JSON" | node -e 'const fs=require("fs"); const x=JSON.parse(fs.readFileSync(0,"utf8")); console.log(x.version || "")')"
ENGINES_NODE="$(printf '%s' "$NPM_JSON" | node -e 'const fs=require("fs"); const x=JSON.parse(fs.readFileSync(0,"utf8")); console.log((x.engines && x.engines.node) || "")')"
PEER_SUMMARY="$(printf '%s' "$NPM_JSON" | node -e 'const fs=require("fs"); const x=JSON.parse(fs.readFileSync(0,"utf8")); const p=x.peerDependencies||{}; console.log(Object.entries(p).map(([k,v])=>`${k}@${v}`).join(", ") || "none")')"

row "Latest npm mcp-use" "$LATEST_VERSION"
row "Published engines" "${ENGINES_NODE:-none declared}"
row "Peer dependencies" "$PEER_SUMMARY"

if [ -n "$ENGINES_NODE" ]; then
  SATISFIES="$(node - "$NODE_VERSION" "$ENGINES_NODE" <<'NODE'
const version = process.argv[2];
const range = process.argv[3];
function parse(v) {
  const m = String(v).replace(/^v/, "").match(/^(\d+)\.(\d+)\.(\d+)/);
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
}
function cmp(a, b) {
  for (let i = 0; i < 3; i++) {
    if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  }
  return 0;
}
function testClause(v, raw) {
  const c = raw.trim();
  if (!c) return true;
  let m;
  if ((m = c.match(/^>=\s*(\d+\.\d+\.\d+)$/))) return cmp(v, parse(m[1])) >= 0;
  if ((m = c.match(/^>\s*(\d+\.\d+\.\d+)$/))) return cmp(v, parse(m[1])) > 0;
  if ((m = c.match(/^<=\s*(\d+\.\d+\.\d+)$/))) return cmp(v, parse(m[1])) <= 0;
  if ((m = c.match(/^<\s*(\d+\.\d+\.\d+)$/))) return cmp(v, parse(m[1])) < 0;
  if ((m = c.match(/^\^(\d+)\.(\d+)\.(\d+)$/))) {
    const min = [Number(m[1]), Number(m[2]), Number(m[3])];
    const max = [min[0] + 1, 0, 0];
    return cmp(v, min) >= 0 && cmp(v, max) < 0;
  }
  if ((m = c.match(/^(\d+\.\d+\.\d+)$/))) return cmp(v, parse(m[1])) === 0;
  return null;
}
const v = parse(version);
let unknown = false;
const ok = range.split("||").some(part => {
  const clauses = part.trim().split(/\s+/);
  return clauses.every(clause => {
    const result = testClause(v, clause);
    if (result === null) unknown = true;
    return result === true;
  });
});
console.log(unknown ? "unknown" : ok ? "yes" : "no");
NODE
)"
  if [ "$SATISFIES" = "no" ]; then
    warn "Local Node v$NODE_VERSION does not satisfy mcp-use engines: $ENGINES_NODE"
  elif [ "$SATISFIES" = "unknown" ]; then
    warn "Could not evaluate engines expression locally: $ENGINES_NODE"
  fi
fi

COMPARE_JSON="$(node - "$LATEST_VERSION" "$MCP_SPEC" "$INSTALLED_VERSION" <<'NODE'
const latest = process.argv[2];
const spec = process.argv[3] || "";
const installed = process.argv[4] || "";
function parse(v) {
  const m = String(v).match(/(\d+)\.(\d+)\.(\d+)/);
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
}
function lt(a, b) {
  if (!a || !b) return false;
  for (let i = 0; i < 3; i++) {
    if (a[i] !== b[i]) return a[i] < b[i];
  }
  return false;
}
const latestV = parse(latest);
const specBase = parse(spec);
const installedV = parse(installed);
console.log(JSON.stringify({
  installedBehind: installedV ? lt(installedV, latestV) : false,
  specBehind: specBase ? lt(specBase, latestV) : false,
  specBase: specBase ? specBase.join(".") : "",
}));
NODE
)"

INSTALLED_BEHIND="$(printf '%s' "$COMPARE_JSON" | node -e 'const fs=require("fs"); console.log(JSON.parse(fs.readFileSync(0,"utf8")).installedBehind ? "yes" : "no")')"
SPEC_BEHIND="$(printf '%s' "$COMPARE_JSON" | node -e 'const fs=require("fs"); console.log(JSON.parse(fs.readFileSync(0,"utf8")).specBehind ? "yes" : "no")')"
SPEC_BASE="$(printf '%s' "$COMPARE_JSON" | node -e 'const fs=require("fs"); console.log(JSON.parse(fs.readFileSync(0,"utf8")).specBase)')"

if [ "$INSTALLED_BEHIND" = "yes" ]; then
  warn "Installed mcp-use $INSTALLED_VERSION is behind latest $LATEST_VERSION."
fi

if [ "$SPEC_BEHIND" = "yes" ]; then
  warn "package.json mcp-use baseline $SPEC_BASE is behind latest $LATEST_VERSION. Reinstall may still resolve newer versions when the range allows it."
fi

exit 0
