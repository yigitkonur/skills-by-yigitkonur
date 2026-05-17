#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check-langchain-versions.sh [project-dir]

Read package.json and node_modules from a user project, print detected
LangChain package specs/versions, and warn about risky major-version mixes.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

project_dir="${1:-.}"
project_dir="$(cd "$project_dir" && pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
version_ref="$script_dir/../references/start/version-discipline.md"

if [[ ! -f "$project_dir/package.json" ]]; then
  echo "No package.json found in: $project_dir" >&2
  exit 1
fi

node - "$project_dir" "$version_ref" <<'NODE'
const fs = require("fs");
const path = require("path");

const projectDir = process.argv[2];
const versionRef = process.argv[3];
const packageJsonPath = path.join(projectDir, "package.json");
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));

const dependencyBuckets = [
  "dependencies",
  "devDependencies",
  "peerDependencies",
  "optionalDependencies",
];

const packageSpecs = new Map();
for (const bucket of dependencyBuckets) {
  const deps = packageJson[bucket] || {};
  for (const [name, spec] of Object.entries(deps)) {
    if (name === "langchain" || name.startsWith("@langchain/")) {
      if (!packageSpecs.has(name)) packageSpecs.set(name, []);
      packageSpecs.get(name).push(`${bucket}:${spec}`);
    }
  }
}

function installedVersion(name) {
  const parts = name.startsWith("@") ? name.split("/") : [name];
  const packagePath = path.join(projectDir, "node_modules", ...parts, "package.json");
  if (!fs.existsSync(packagePath)) return null;
  return JSON.parse(fs.readFileSync(packagePath, "utf8")).version || null;
}

const packageNames = Array.from(new Set([
  ...packageSpecs.keys(),
  "langchain",
  "@langchain/core",
  "@langchain/langgraph",
  "@langchain/openai",
  "@langchain/langgraph-sdk",
  "@langchain/langgraph-cli",
  "@langchain/textsplitters",
  "@langchain/mcp-adapters",
])).sort((a, b) => a.localeCompare(b));

const rows = packageNames.map((name) => ({
  name,
  spec: packageSpecs.get(name)?.join(", ") || "-",
  installed: installedVersion(name) || "-",
}));

console.log("LangChain package check");
console.log(`Project: ${projectDir}`);
console.log(`Version discipline: ${versionRef}`);
console.log("");
console.log("| Package | package.json spec | installed |");
console.log("|---|---|---|");
for (const row of rows) {
  console.log(`| \`${row.name}\` | \`${row.spec}\` | \`${row.installed}\` |`);
}

const corePackages = ["langchain", "@langchain/core", "@langchain/langgraph", "@langchain/openai"];
const installedCore = rows
  .filter((row) => corePackages.includes(row.name) && row.installed !== "-")
  .map((row) => ({ ...row, major: row.installed.split(".")[0] }));

const majors = new Map();
for (const row of installedCore) {
  if (!majors.has(row.major)) majors.set(row.major, []);
  majors.get(row.major).push(row.name);
}

console.log("");
if (installedCore.length === 0) {
  console.log("No installed core LangChain packages found under node_modules.");
  console.log("Run npm install before checking installed versions, or inspect package.json specs only.");
} else if (majors.size > 1) {
  console.log("WARNING: core LangChain packages use different installed major versions:");
  for (const [major, names] of majors.entries()) {
    console.log(`  major ${major}: ${names.join(", ")}`);
  }
  console.log("Check the version-discipline reference before debugging API behavior.");
} else {
  console.log(`Core LangChain installed major version: ${installedCore[0].major}`);
}

const duplicatedSpecs = Array.from(packageSpecs.entries()).filter(([, specs]) => specs.length > 1);
if (duplicatedSpecs.length > 0) {
  console.log("");
  console.log("WARNING: duplicate package specs across dependency buckets:");
  for (const [name, specs] of duplicatedSpecs) {
    console.log(`  ${name}: ${specs.join(", ")}`);
  }
}
NODE
