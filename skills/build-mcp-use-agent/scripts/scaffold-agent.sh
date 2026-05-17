#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: bash scripts/scaffold-agent.sh --target DIR [--force]

Scaffold a minimal TypeScript mcp-use MCPAgent project.

Options:
  --target DIR  Required destination directory.
  --force       Overwrite generated files if they already exist.
  -h, --help    Show this help.

Generated files:
  package.json
  tsconfig.json
  .env.example
  src/index.ts

This script mutates only the explicit target directory.
EOF
}

TARGET_DIR=""
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_DIR="${2:-}"
      [[ -n "$TARGET_DIR" ]] || { echo "ERROR: --target requires a directory" >&2; exit 2; }
      shift 2
      ;;
    --force)
      FORCE=1
      shift
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

if [[ -z "$TARGET_DIR" ]]; then
  echo "ERROR: --target is required" >&2
  show_help >&2
  exit 2
fi

mkdir -p "$TARGET_DIR/src"

write_file() {
  local path="$1"
  local rel="${path#$TARGET_DIR/}"
  if [[ -e "$path" && "$FORCE" -ne 1 ]]; then
    echo "ERROR: refusing to overwrite existing file: $rel" >&2
    echo "       Re-run with --force to replace generated files." >&2
    exit 1
  fi
  mkdir -p "$(dirname "$path")"
  sed "s/__PROJECT_NAME__/$(basename "$TARGET_DIR" | tr -cd '[:alnum:]_-')/g" > "$path"
  echo "wrote $rel"
}

write_file "$TARGET_DIR/package.json" <<'EOF'
{
  "name": "__PROJECT_NAME__",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "engines": {
    "node": "^20.19.0 || >=22.12.0"
  },
  "scripts": {
    "dev": "tsx src/index.ts",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@langchain/openai": "latest",
    "dotenv": "latest",
    "mcp-use": "latest"
  },
  "devDependencies": {
    "@types/node": "latest",
    "tsx": "latest",
    "typescript": "latest"
  }
}
EOF

write_file "$TARGET_DIR/tsconfig.json" <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*.ts"]
}
EOF

write_file "$TARGET_DIR/.env.example" <<'EOF'
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
EOF

write_file "$TARGET_DIR/src/index.ts" <<'EOF'
import "dotenv/config";
import { MCPAgent } from "mcp-use";

const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) {
  throw new Error("OPENAI_API_KEY is required.");
}

const model = process.env.OPENAI_MODEL || "gpt-4o";

const agent = new MCPAgent({
  llm: `openai/${model}`,
  llmConfig: {
    apiKey,
    temperature: 0,
  },
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
  maxSteps: 10,
  memoryEnabled: false,
  autoInitialize: true,
});

try {
  const result = await agent.run({
    prompt: "List top-level files and summarize their roles.",
  });
  console.log(result);
} finally {
  await agent.close();
}
EOF

cat <<EOF

Next steps:
  cd "$TARGET_DIR"
  cp .env.example .env
  npm install
  npm run typecheck
  npm run dev

Verify OPENAI_MODEL against current provider docs before production use.
EOF
