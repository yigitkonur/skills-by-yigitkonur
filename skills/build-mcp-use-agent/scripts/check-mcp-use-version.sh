#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: bash scripts/check-mcp-use-version.sh [--target DIR]

Read-only check for mcp-use package facts:
  - Node.js version
  - installed mcp-use version in the target project
  - latest npm version
  - npm engines
  - peer dependencies and optional peer metadata

Options:
  --target DIR  Project directory to inspect. Default: current directory.
  -h, --help    Show this help.

This script never prints environment variable values.
EOF
}

TARGET_DIR="$PWD"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_DIR="${2:-}"
      [[ -n "$TARGET_DIR" ]] || { echo "ERROR: --target requires a directory" >&2; exit 2; }
      shift 2
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      show_help >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "ERROR: target directory does not exist: $TARGET_DIR" >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node is required" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm is required" >&2
  exit 1
fi

cd "$TARGET_DIR"

echo "Target: $(pwd)"
echo "Node:   $(node --version)"
echo ""

INSTALLED_JSON="$(npm list mcp-use --depth=0 --json 2>/dev/null || true)"
LATEST_JSON="$(npm view mcp-use version engines peerDependencies peerDependenciesMeta --json)"

INSTALLED_JSON="$INSTALLED_JSON" LATEST_JSON="$LATEST_JSON" node <<'NODE'
function readJson(name) {
  const raw = process.env[name] || "";
  if (!raw.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch (error) {
    return { parseError: error.message };
  }
}

const installed = readJson("INSTALLED_JSON");
const latest = readJson("LATEST_JSON");
const installedDep = installed.dependencies?.["mcp-use"];

console.log("Installed mcp-use:");
if (installedDep?.version) {
  console.log(`  version: ${installedDep.version}`);
} else if (installed.parseError) {
  console.log(`  unable to parse npm list output: ${installed.parseError}`);
} else {
  console.log("  not installed in this project");
}

console.log("");
console.log("Latest npm mcp-use:");
if (latest.version) {
  console.log(`  version: ${latest.version}`);
  console.log(`  engines.node: ${latest.engines?.node ?? "(not declared)"}`);
} else if (latest.parseError) {
  console.log(`  unable to parse npm view output: ${latest.parseError}`);
} else {
  console.log("  unavailable");
}

const peerDeps = latest.peerDependencies || {};
const peerMeta = latest.peerDependenciesMeta || {};
const names = Object.keys(peerDeps).sort();

console.log("");
console.log("Peer dependencies:");
if (names.length === 0) {
  console.log("  none reported");
} else {
  for (const name of names) {
    const optional = peerMeta[name]?.optional ? " optional" : "";
    console.log(`  ${name}: ${peerDeps[name]}${optional}`);
  }
}
NODE
