#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: bash scripts/diagnose-agent-stuck.sh [--target DIR] [--server-command CMD]

Read-only diagnostics for an mcp-use MCPAgent that is not progressing.

Options:
  --target DIR          Project directory to inspect. Default: current directory.
  --server-command CMD  Check whether the first word of a server command is reachable.
  -h, --help            Show this help.

Checks:
  Node version, installed/latest mcp-use, provider env presence by name only,
  maxSteps, autoInitialize, manageConnector, cleanup patterns, server command
  reachability, and common streaming/structured-output mistakes.

This script never prints environment variable values.
EOF
}

TARGET_DIR="$PWD"
SERVER_COMMAND=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_DIR="${2:-}"
      [[ -n "$TARGET_DIR" ]] || { echo "ERROR: --target requires a directory" >&2; exit 2; }
      shift 2
      ;;
    --server-command)
      SERVER_COMMAND="${2:-}"
      [[ -n "$SERVER_COMMAND" ]] || { echo "ERROR: --server-command requires a command" >&2; exit 2; }
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
LATEST_JSON="$(npm view mcp-use version engines --json 2>/dev/null || true)"
SERVER_COMMAND="$SERVER_COMMAND" INSTALLED_JSON="$INSTALLED_JSON" LATEST_JSON="$LATEST_JSON" node <<'NODE'
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

function readJson(name) {
  const raw = process.env[name] || "";
  if (!raw.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function walk(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (["node_modules", ".git", "dist", "build", ".next"].includes(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, files);
    else if (/\.(ts|tsx|js|mjs|cjs)$/.test(entry.name)) files.push(full);
  }
  return files;
}

function hasCommand(commandName) {
  if (!commandName) return false;
  try {
    execFileSync("bash", ["-lc", `command -v ${JSON.stringify(commandName)}`], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

const installed = readJson("INSTALLED_JSON");
const latest = readJson("LATEST_JSON");
const installedVersion = installed.dependencies?.["mcp-use"]?.version;

console.log("mcp-use:");
console.log(`  installed: ${installedVersion || "not installed in this project"}`);
console.log(`  latest:    ${latest.version || "unavailable"}`);
console.log(`  engines:   ${latest.engines?.node || "unavailable"}`);
console.log("");

const envNames = [
  "OPENAI_API_KEY",
  "ANTHROPIC_API_KEY",
  "GOOGLE_API_KEY",
  "GROQ_API_KEY",
  "OPENAI_MODEL",
  "ANTHROPIC_MODEL",
  "GOOGLE_MODEL",
  "GROQ_MODEL",
  "LANGFUSE_PUBLIC_KEY",
  "LANGFUSE_SECRET_KEY",
];

console.log("Provider env presence:");
for (const name of envNames) {
  console.log(`  ${name}: ${process.env[name] ? "set" : "unset"}`);
}
console.log("");

const files = walk(process.cwd());
const joined = files.map((file) => {
  try {
    return { file, text: fs.readFileSync(file, "utf8") };
  } catch {
    return { file, text: "" };
  }
});

const maxSteps = [];
const commands = new Set();
let autoInitializeMentions = 0;
let manageConnectorMentions = 0;
let agentCloseMentions = 0;
let closeAllSessionsMentions = 0;
let stringRunMentions = 0;
let streamEventsMentions = 0;
let structuredOutputMentions = 0;
let stepObservationMentions = 0;

for (const { text } of joined) {
  for (const match of text.matchAll(/maxSteps\s*:\s*(\d+)/g)) maxSteps.push(Number(match[1]));
  for (const match of text.matchAll(/command\s*:\s*["'`](.*?)["'`]/g)) commands.add(match[1]);
  autoInitializeMentions += (text.match(/autoInitialize\s*:/g) || []).length;
  manageConnectorMentions += (text.match(/manageConnector\s*:/g) || []).length;
  agentCloseMentions += (text.match(/agent\.close\s*\(/g) || []).length;
  closeAllSessionsMentions += (text.match(/closeAllSessions\s*\(/g) || []).length;
  stringRunMentions += (text.match(/\.run\s*\(\s*["'`]/g) || []).length;
  streamEventsMentions += (text.match(/streamEvents\s*\(/g) || []).length;
  structuredOutputMentions += (text.match(/on_structured_output|event\.data\.output/g) || []).length;
  stepObservationMentions += (text.match(/step\.observation/g) || []).length;
}

console.log("Agent config scan:");
console.log(`  files scanned: ${files.length}`);
console.log(`  maxSteps values: ${maxSteps.length ? maxSteps.join(", ") : "none found"}`);
console.log(`  autoInitialize mentions: ${autoInitializeMentions}`);
console.log(`  manageConnector mentions: ${manageConnectorMentions}`);
console.log(`  agent.close mentions: ${agentCloseMentions}`);
console.log(`  closeAllSessions mentions: ${closeAllSessionsMentions}`);
if (agentCloseMentions && closeAllSessionsMentions) {
  console.log("  note: both cleanup APIs appear; verify ownership scope and avoid double cleanup for the same client.");
}
console.log("");

console.log("Server command reachability:");
const explicit = process.env.SERVER_COMMAND || "";
if (explicit) {
  const first = explicit.trim().split(/\s+/)[0];
  console.log(`  ${explicit}: ${hasCommand(first) ? "first command reachable" : "first command missing"}`);
}
if (commands.size === 0) {
  console.log("  no command: entries found in scanned source");
} else {
  for (const command of [...commands].sort()) {
    console.log(`  ${command}: ${hasCommand(command) ? "reachable" : "missing"}`);
  }
}
console.log("");

console.log("Streaming and structured-output scan:");
console.log(`  plain-string run() calls: ${stringRunMentions}`);
console.log(`  streamEvents() mentions: ${streamEventsMentions}`);
console.log(`  structured-output event handling mentions: ${structuredOutputMentions}`);
console.log(`  step.observation mentions: ${stepObservationMentions}`);
if (stringRunMentions) {
  console.log("  note: prefer object-form run({ prompt }) in production code.");
}
if (streamEventsMentions && !structuredOutputMentions) {
  console.log("  note: structured output with streamEvents() should consume on_structured_output and event.data.output.");
}
if (stepObservationMentions) {
  console.log("  note: step.observation can be empty at yield time; use streamEvents() for live tool results.");
}
NODE
