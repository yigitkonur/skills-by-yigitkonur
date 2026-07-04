#!/usr/bin/env bash
set -u

usage() {
  cat <<'EOF'
Usage: check-mcp-use-version.sh [target-dir]

Find the nearest package.json at or above target-dir, then report declared and
installed versions for mcp-use server prerequisites.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

target="${1:-.}"

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node is required to parse package.json and verify the runtime." >&2
  exit 2
fi

target_abs="$(cd "$target" 2>/dev/null && pwd)"
if [ -z "${target_abs:-}" ]; then
  echo "ERROR: target directory not found: $target" >&2
  exit 2
fi

dir="$target_abs"
pkg=""
while [ "$dir" != "/" ]; do
  if [ -f "$dir/package.json" ]; then
    pkg="$dir/package.json"
    break
  fi
  dir="$(dirname "$dir")"
done

if [ -z "$pkg" ]; then
  echo "ERROR: no package.json found at or above $target_abs" >&2
  exit 2
fi

root="$(dirname "$pkg")"

node - "$pkg" "$root" <<'NODE'
const fs = require("fs");
const path = require("path");

const [pkgPath, root] = process.argv.slice(2);
const names = ["mcp-use", "@mcp-use/cli", "@mcp-use/react", "zod", "typescript"];

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (err) {
    console.error(`ERROR: failed to read ${file}: ${err.message}`);
    process.exit(2);
  }
}

function spec(pkg, name) {
  const buckets = [
    ["dependencies", pkg.dependencies],
    ["devDependencies", pkg.devDependencies],
    ["peerDependencies", pkg.peerDependencies],
    ["optionalDependencies", pkg.optionalDependencies],
  ];
  for (const [bucket, deps] of buckets) {
    if (deps && Object.prototype.hasOwnProperty.call(deps, name)) {
      return `${deps[name]} (${bucket})`;
    }
  }
  return "-";
}

function installedVersion(name) {
  const parts = name.startsWith("@") ? name.split("/") : [name];
  const file = path.join(root, "node_modules", ...parts, "package.json");
  if (!fs.existsSync(file)) return "-";
  try {
    return readJson(file).version || "-";
  } catch {
    return "unreadable";
  }
}

const pkg = readJson(pkgPath);
const nodeMajor = Number(process.versions.node.split(".")[0]);
const hardFailures = [];
const warnings = [];

if (nodeMajor < 18) {
  hardFailures.push(`Node ${process.version} is below the mcp-use minimum of 18.x`);
}

if (!pkg.dependencies || !Object.prototype.hasOwnProperty.call(pkg.dependencies, "zod")) {
  warnings.push("zod is not declared in dependencies; mcp-use treats it as a peer dependency.");
}

if (spec(pkg, "mcp-use") === "-") {
  warnings.push("mcp-use is not declared in this package.");
}

console.log(`Package: ${pkgPath}`);
console.log(`Node: ${process.version}`);
console.log("");
console.log("| Package | Declared | Installed |");
console.log("|---|---|---|");
for (const name of names) {
  console.log(`| ${name} | ${spec(pkg, name)} | ${installedVersion(name)} |`);
}

console.log("");
console.log("Version-sensitive docs warning:");
console.log("- Re-verify CLI/API claims with installed declarations and --help before editing references.");
console.log("- Useful commands: npm view mcp-use version; npm view @mcp-use/cli version; npm view @mcp-use/react version.");
console.log("- If changing one hard-coded version, grep the entire skill for the same value first.");

if (warnings.length) {
  console.log("");
  console.log("Warnings:");
  for (const warning of warnings) console.log(`- ${warning}`);
}

if (hardFailures.length) {
  console.log("");
  console.log("Hard failures:");
  for (const failure of hardFailures) console.log(`- ${failure}`);
  process.exit(2);
}
NODE
