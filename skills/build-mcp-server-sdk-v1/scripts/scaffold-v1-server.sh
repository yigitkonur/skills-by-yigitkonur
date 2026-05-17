#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: bash scripts/scaffold-v1-server.sh <target-dir> <server-name> [stdio|http-stateful|http-stateless]" >&2
}

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  usage
  exit 1
fi

TARGET_DIR="$1"
SERVER_NAME="$2"
TRANSPORT="${3:-stdio}"

case "$TRANSPORT" in
  stdio|http-stateful|http-stateless) ;;
  *)
    usage
    echo "FAIL transport must be stdio, http-stateful, or http-stateless" >&2
    exit 1
    ;;
esac

if ! printf '%s' "$SERVER_NAME" | grep -Eq '^[A-Za-z0-9._-]+$'; then
  echo "FAIL server-name may only contain letters, numbers, dots, underscores, and hyphens" >&2
  exit 1
fi

PACKAGE_NAME="$(printf '%s' "$SERVER_NAME" \
  | tr '[:upper:]' '[:lower:]' \
  | tr '_' '-' \
  | sed -E 's/[^a-z0-9._-]+/-/g; s/-+/-/g; s/^-//; s/-$//')"

if [ -z "$PACKAGE_NAME" ]; then
  echo "FAIL server-name did not produce a valid package name" >&2
  exit 1
fi

if [ -e "$TARGET_DIR" ] && [ ! -d "$TARGET_DIR" ]; then
  echo "FAIL target path exists and is not a directory: $TARGET_DIR" >&2
  exit 1
fi

if [ -e "$TARGET_DIR" ] && [ -n "$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]; then
  echo "FAIL target directory exists and is not empty: $TARGET_DIR" >&2
  echo "Choose an empty directory or remove existing files before scaffolding." >&2
  exit 1
fi

mkdir -p "$TARGET_DIR/src"

if [ "$TRANSPORT" = "stdio" ]; then
  cat > "$TARGET_DIR/package.json" <<JSON
{
  "name": "$PACKAGE_NAME",
  "version": "0.1.0",
  "type": "module",
  "bin": {
    "$PACKAGE_NAME": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.29.0",
    "zod": "^3.25.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "tsx": "^4.20.0",
    "typescript": "^5.8.0"
  }
}
JSON
else
  cat > "$TARGET_DIR/package.json" <<JSON
{
  "name": "$PACKAGE_NAME",
  "version": "0.1.0",
  "type": "module",
  "bin": {
    "$PACKAGE_NAME": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.29.0",
    "express": "^5.1.0",
    "zod": "^3.25.0"
  },
  "devDependencies": {
    "@types/express": "^5.0.0",
    "@types/node": "^22.0.0",
    "tsx": "^4.20.0",
    "typescript": "^5.8.0"
  }
}
JSON
fi

cat > "$TARGET_DIR/tsconfig.json" <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src/**/*"]
}
JSON

case "$TRANSPORT" in
  stdio)
    cat > "$TARGET_DIR/src/index.ts" <<TS
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer(
  { name: "$SERVER_NAME", version: "0.1.0" },
  { instructions: "Minimal MCP SDK v1 stdio server" },
);

server.registerTool("echo", {
  description: "Echo back the provided message",
  inputSchema: {
    message: z.string().min(1).describe("Message to echo"),
  },
  annotations: {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
}, async ({ message }) => ({
  content: [{ type: "text", text: message }],
}));

const transport = new StdioServerTransport();
await server.connect(transport);
TS
    ;;
  http-stateful)
    cat > "$TARGET_DIR/src/index.ts" <<TS
#!/usr/bin/env node
import { randomUUID } from "node:crypto";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

const app = createMcpExpressApp();
const transports: Record<string, StreamableHTTPServerTransport> = {};

function createServer(): McpServer {
  const server = new McpServer(
    { name: "$SERVER_NAME", version: "0.1.0" },
    { instructions: "Minimal MCP SDK v1 stateful HTTP server" },
  );

  server.registerTool("echo", {
    description: "Echo back the provided message",
    inputSchema: { message: z.string().min(1).describe("Message to echo") },
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  }, async ({ message }) => ({
    content: [{ type: "text", text: message }],
  }));

  return server;
}

app.post("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;

  if (sessionId && transports[sessionId]) {
    await transports[sessionId].handleRequest(req, res, req.body);
    return;
  }

  if (!sessionId && isInitializeRequest(req.body)) {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (newSessionId) => {
        transports[newSessionId] = transport;
      },
    });

    transport.onclose = () => {
      const closedSessionId = transport.sessionId;
      if (closedSessionId) delete transports[closedSessionId];
    };

    const server = createServer();
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    return;
  }

  res.status(400).json({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Bad Request: missing mcp-session-id" },
    id: null,
  });
});

app.get("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;
  if (!sessionId || !transports[sessionId]) {
    res.status(400).send("Invalid or missing mcp-session-id");
    return;
  }
  await transports[sessionId].handleRequest(req, res);
});

app.delete("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;
  if (sessionId && transports[sessionId]) {
    await transports[sessionId].handleRequest(req, res);
    return;
  }
  res.status(200).end();
});

const port = Number(process.env.PORT || 3000);
const httpServer = app.listen(port, () => {
  console.error(\`MCP server listening on http://localhost:\${port}/mcp\`);
});

async function shutdown() {
  for (const transport of Object.values(transports)) {
    await transport.close().catch(() => {});
  }
  httpServer.close(() => process.exit(0));
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
TS
    ;;
  http-stateless)
    cat > "$TARGET_DIR/src/index.ts" <<TS
#!/usr/bin/env node
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

const app = createMcpExpressApp();
const server = new McpServer(
  { name: "$SERVER_NAME", version: "0.1.0" },
  { instructions: "Minimal MCP SDK v1 stateless HTTP server" },
);

server.registerTool("echo", {
  description: "Echo back the provided message",
  inputSchema: { message: z.string().min(1).describe("Message to echo") },
  annotations: {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
}, async ({ message }) => ({
  content: [{ type: "text", text: message }],
}));

const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
});

await server.connect(transport);

app.post("/mcp", async (req, res) => {
  await transport.handleRequest(req, res, req.body);
});

const port = Number(process.env.PORT || 3000);
const httpServer = app.listen(port, () => {
  console.error(\`MCP server listening on http://localhost:\${port}/mcp\`);
});

async function shutdown() {
  await transport.close().catch(() => {});
  httpServer.close(() => process.exit(0));
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
TS
    ;;
esac

echo "Created MCP SDK v1 $TRANSPORT server in $TARGET_DIR"
echo "Next: cd $TARGET_DIR && npm install && npm run build"
