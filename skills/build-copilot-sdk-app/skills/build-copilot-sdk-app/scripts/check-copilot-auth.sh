#!/usr/bin/env bash
set -euo pipefail

project_dir="."
run_preflight=1

usage() {
  cat <<'EOF'
Usage: check-copilot-auth.sh [project-dir] [--skip-runtime]

Checks Node, @github/copilot-sdk resolution, token/BYOK env presence, and
optionally runs CopilotClient.getAuthStatus(). Secret values are never printed.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-runtime)
      run_preflight=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      project_dir="$1"
      shift
      ;;
  esac
done

cd "$project_dir"

echo "== Copilot SDK preflight =="
echo "Project: $(pwd)"

if ! command -v node >/dev/null 2>&1; then
  echo "FAIL: node is not on PATH. Install Node that satisfies @github/copilot-sdk engines.node."
  exit 1
fi

node <<'NODE'
const fs = require("fs");
const path = require("path");

function findPackageRoot() {
  let resolved;
  try {
    resolved = require.resolve("@github/copilot-sdk");
  } catch {
    console.error("FAIL: @github/copilot-sdk does not resolve from this project.");
    console.error("Install it with: npm install @github/copilot-sdk");
    process.exit(2);
  }

  let dir = path.dirname(resolved);
  while (dir !== path.dirname(dir)) {
    const pkgPath = path.join(dir, "package.json");
    if (fs.existsSync(pkgPath)) {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
      if (pkg.name === "@github/copilot-sdk") return { dir, pkgPath };
    }
    dir = path.dirname(dir);
  }
  console.error("FAIL: resolved @github/copilot-sdk but could not find package.json.");
  process.exit(2);
}

const { dir, pkgPath } = findPackageRoot();
const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
const current = process.versions.node.split(".").map(Number);
const engine = pkg.engines?.node ?? "unspecified";
const min = String(engine).match(/>=\s*(\d+)\.(\d+)\.(\d+)/);

console.log(`Node: ${process.versions.node}`);
console.log(`@github/copilot-sdk: ${pkg.version}`);
console.log(`Package root: ${dir}`);
console.log(`engines.node: ${engine}`);

if (min) {
  const required = min.slice(1).map(Number);
  const ok =
    current[0] > required[0] ||
    (current[0] === required[0] && current[1] > required[1]) ||
    (current[0] === required[0] && current[1] === required[1] && current[2] >= required[2]);
  if (!ok) {
    console.error(`FAIL: Node ${process.versions.node} does not satisfy ${engine}.`);
    process.exit(3);
  }
}
NODE

present() {
  local name="$1"
  if [[ -n "${!name:-}" ]]; then
    echo "set"
  else
    echo "unset"
  fi
}

echo
echo "GitHub auth env:"
echo "  COPILOT_GITHUB_TOKEN: $(present COPILOT_GITHUB_TOKEN)"
echo "  GH_TOKEN: $(present GH_TOKEN)"
echo "  GITHUB_TOKEN: $(present GITHUB_TOKEN)"

echo
echo "BYOK env:"
echo "  OPENAI_API_KEY: $(present OPENAI_API_KEY)"
echo "  ANTHROPIC_API_KEY: $(present ANTHROPIC_API_KEY)"
echo "  AZURE_OPENAI_KEY: $(present AZURE_OPENAI_KEY)"
echo "  AZURE_OPENAI_ENDPOINT: $(present AZURE_OPENAI_ENDPOINT)"
echo "  FOUNDRY_API_KEY: $(present FOUNDRY_API_KEY)"
echo "  FOUNDRY_BASE_URL: $(present FOUNDRY_BASE_URL)"
echo "  OLLAMA_BASE_URL: $(present OLLAMA_BASE_URL)"

if [[ "$run_preflight" -eq 0 ]]; then
  echo
  echo "Runtime getAuthStatus preflight skipped."
  exit 0
fi

echo
echo "Running CopilotClient.getAuthStatus()..."
set +e
node --input-type=module <<'NODE'
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient({ logLevel: "error" });
try {
  await client.start();
  const auth = await client.getAuthStatus();
  console.log(`isAuthenticated: ${auth.isAuthenticated}`);
  console.log(`authType: ${auth.authType ?? "unknown"}`);
  console.log(`host: ${auth.host ?? "unknown"}`);
  console.log(`login: ${auth.login ?? "unknown"}`);
  if (!auth.isAuthenticated) process.exitCode = 4;
} catch (error) {
  console.error(`getAuthStatus failed: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 4;
} finally {
  await client.stop().catch(() => []);
}
NODE
status=$?
set -e

if [[ "$status" -ne 0 ]]; then
  cat <<'EOF'

Remediation:
- Local interactive GitHub auth: run `npx copilot login` or `copilot login` using the CLI for this project.
- Headless GitHub auth: set one of COPILOT_GITHUB_TOKEN, GH_TOKEN, or GITHUB_TOKEN before starting Node.
- BYOK: set provider env vars, pass `provider`, and pass a `model`; getAuthStatus does not validate provider keys.
- External CLI server: authenticate the external `copilot --headless --port ...` process, then use `cliUrl`.
EOF
  exit "$status"
fi

echo "Auth preflight passed."
