#!/bin/sh
set -eu

if [ ! -f package.json ]; then
  echo "FAIL: package.json not found. Run this from a project root." >&2
  exit 2
fi

node <<'NODE'
const fs = require("node:fs");

const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
const sections = ["dependencies", "devDependencies", "optionalDependencies", "peerDependencies"];
const targets = [
  "@modelcontextprotocol/server",
  "@modelcontextprotocol/node",
  "@modelcontextprotocol/express",
  "@modelcontextprotocol/hono",
  "@modelcontextprotocol/client",
  "@modelcontextprotocol/core",
  "@modelcontextprotocol/sdk",
];

const found = [];
for (const section of sections) {
  const deps = pkg[section] || {};
  for (const name of targets) {
    if (Object.prototype.hasOwnProperty.call(deps, name)) {
      found.push({ name, version: String(deps[name]), section });
    }
  }
}

const splitPackages = new Set(targets.filter((name) => name !== "@modelcontextprotocol/sdk"));
let unsafe = 0;
let warnings = 0;

function isUnsafeAlphaRange(version) {
  const v = version.trim();
  if (/^(latest|alpha|\*)$/i.test(v)) return true;
  if (/^[\^~]/.test(v) && /alpha/i.test(v)) return true;
  if (/[<>=|x*]/i.test(v) && /alpha|2\./i.test(v)) return true;
  return /alpha/i.test(v) && !/^\d+\.\d+\.\d+-alpha\.\d+$/.test(v);
}

console.log("MCP package version check");
if (found.length === 0) {
  console.log("WARN: no Model Context Protocol packages found in package.json");
  process.exit(0);
}

for (const item of found) {
  console.log(`- ${item.name}@${item.version} (${item.section})`);
  if (splitPackages.has(item.name) && isUnsafeAlphaRange(item.version)) {
    console.log(`  FAIL: pin ${item.name} to an exact alpha version, for example 2.0.0-alpha.2`);
    unsafe++;
  }
  if (item.name === "@modelcontextprotocol/sdk") {
    console.log("  WARN: @modelcontextprotocol/sdk is the v1 single-package SDK on npm today.");
    console.log("        Route new v1 work to build-mcp-server-sdk-v1 or ports to convert-mcp-sdk-v1-to-v2.");
    warnings++;
  }
}

if (found.some((item) => item.name === "@modelcontextprotocol/sdk") &&
    found.some((item) => splitPackages.has(item.name))) {
  console.log("WARN: both v1 @modelcontextprotocol/sdk and v2 split packages are present; verify this is an intentional migration state.");
  warnings++;
}

if (unsafe > 0) {
  console.log(`FAIL: ${unsafe} unsafe v2 alpha range(s), ${warnings} warning(s).`);
  process.exit(1);
}

console.log(`PASS: no unsafe v2 alpha ranges found, ${warnings} warning(s).`);
NODE
