#!/usr/bin/env bash
set -u

usage() {
  cat <<'EOF'
Usage: scaffold-mcp-use-server.sh <output-dir> [--force]

Create a minimal HTTP mcp-use/server project:
  package.json
  tsconfig.json
  src/server.ts

The output directory must be empty unless --force is passed.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ $# -lt 1 ]; then
  usage >&2
  exit 2
fi

out="$1"
force=no
if [ "${2:-}" = "--force" ]; then
  force=yes
elif [ -n "${2:-}" ]; then
  echo "ERROR: unknown argument: $2" >&2
  usage >&2
  exit 2
fi

if [ -e "$out" ] && [ ! -d "$out" ]; then
  echo "ERROR: output path exists and is not a directory: $out" >&2
  exit 2
fi

if [ -d "$out" ] && [ "$force" != yes ] && [ -n "$(find "$out" -mindepth 1 -maxdepth 1 2>/dev/null)" ]; then
  echo "ERROR: output directory is not empty: $out" >&2
  echo "Pass --force to overwrite scaffold-managed files." >&2
  exit 2
fi

mkdir -p "$out/src"

for file in "$out/package.json" "$out/tsconfig.json" "$out/src/server.ts"; do
  if [ -e "$file" ] && [ "$force" != yes ]; then
    echo "ERROR: refusing to overwrite existing file: $file" >&2
    exit 2
  fi
done

cat > "$out/package.json" <<'EOF'
{
  "name": "my-mcp-use-server",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev src/server.ts",
    "build": "mcp-use build",
    "start": "mcp-use start",
    "generate-types": "mcp-use generate-types --server src/server.ts",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "mcp-use": "latest",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@mcp-use/cli": "latest",
    "@types/node": "^22.0.0",
    "typescript": "^5.5.0",
    "tsx": "^4.0.0"
  }
}
EOF

cat > "$out/tsconfig.json" <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*", ".mcp-use/**/*"]
}
EOF

cat > "$out/src/server.ts" <<'EOF'
import { MCPServer, object, text } from "mcp-use/server";
import { z } from "zod";

const port = Number.parseInt(process.env.PORT ?? "3000", 10);

const server = new MCPServer({
  name: "my-mcp-use-server",
  version: "1.0.0",
  description: "Minimal HTTP MCP server built with mcp-use",
});

server.get("/health", (c) =>
  c.json({
    status: "ok",
    service: "my-mcp-use-server",
  }),
);

server.tool(
  {
    name: "echo-message",
    description: "Echo a message back to verify tool calls.",
    schema: z.object({
      message: z.string().min(1).describe("Message to echo"),
    }).strict(),
  },
  async ({ message }) => text(message),
);

server.tool(
  {
    name: "server-info",
    description: "Return basic server metadata.",
    schema: z.object({}).strict(),
  },
  async () => object({ name: "my-mcp-use-server", transport: "streamable-http" }),
);

await server.listen(port);
console.log(`MCP server listening on http://localhost:${port}/mcp`);
EOF

cat <<EOF
Created minimal mcp-use HTTP server in: $out

Next commands:
  cd "$out"
  npm install
  npm run typecheck
  npm run dev

Validation:
  Open http://localhost:3000/inspector
  curl -i http://localhost:3000/health
  Run the curl handshake from references/22-validate/02-curl-handshake.md
EOF
