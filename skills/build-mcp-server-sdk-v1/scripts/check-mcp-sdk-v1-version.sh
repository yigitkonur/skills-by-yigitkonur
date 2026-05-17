#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-.}"
PACKAGE_JSON="$PROJECT_DIR/package.json"

if [ ! -f "$PACKAGE_JSON" ]; then
  echo "FAIL package.json not found in $PROJECT_DIR" >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "FAIL Node.js is required to read package.json" >&2
  exit 1
fi

node - "$PACKAGE_JSON" <<'NODE'
const fs = require("node:fs");

const packageJsonPath = process.argv[2];
const pkg = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
const allDeps = {
  ...(pkg.dependencies || {}),
  ...(pkg.devDependencies || {}),
  ...(pkg.peerDependencies || {}),
  ...(pkg.optionalDependencies || {}),
};

const sdkRange = allDeps["@modelcontextprotocol/sdk"];
const zodRange = allDeps.zod;
const splitPackages = [
  "@modelcontextprotocol/server",
  "@modelcontextprotocol/client",
  "@modelcontextprotocol/core",
].filter((name) => allDeps[name]);

const errors = [];
if (!sdkRange) errors.push("@modelcontextprotocol/sdk is missing");
if (splitPackages.length > 0) {
  errors.push(`v2 split package(s) present: ${splitPackages.join(", ")}`);
}
if (sdkRange && /2\.0\.0-alpha|@next|\bnext\b/i.test(String(sdkRange))) {
  errors.push(`SDK range is not stable v1: ${sdkRange}`);
}
if (!zodRange) errors.push("zod is missing");

if (errors.length > 0) {
  console.error(`FAIL ${errors.join("; ")}`);
  process.exit(1);
}

console.log(`OK @modelcontextprotocol/sdk=${sdkRange} zod=${zodRange}`);
NODE

if command -v grep >/dev/null 2>&1 && command -v find >/dev/null 2>&1; then
  split_imports="$(
    find "$PROJECT_DIR" \
      -path '*/node_modules' -prune -o \
      -path '*/dist' -prune -o \
      -path '*/build' -prune -o \
      -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' \) \
      -exec grep -nE '@modelcontextprotocol/(server|client|core)(["/]|$)' {} + 2>/dev/null || true
  )"

  if [ -n "$split_imports" ]; then
    echo "FAIL v2 split-package import(s) found:" >&2
    echo "$split_imports" >&2
    exit 1
  fi
fi
