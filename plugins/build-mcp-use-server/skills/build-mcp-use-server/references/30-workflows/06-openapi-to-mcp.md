# Workflow: OpenAPI to MCP

*Read this for an end-to-end workflow: import an OpenAPI specification into an MCPServer.*

## Steps

### 1. Scaffold

```bash
npx create-mcp-use-app@2.0.0-beta.14 my-openapi-mcp --template blank --npm --install
cd my-openapi-mcp
```

**Verify:** `index.ts` exports a blank server.

### 2. Load a Parsed OpenAPI Document

Provide a locally parsed OpenAPI document. Resolve remote `$ref` values before this step because `fromOpenAPI` does not bundle them.

```typescript
import { MCPServer } from "mcp-use";
import openapi from "./openapi.json" with { type: "json" };

const server = MCPServer.fromOpenAPI({
  spec: openapi,
  baseUrl: "https://api.example.com",
  name: "example-api",
  version: "1.0.0",
  auth: { type: "bearer", token: process.env.API_TOKEN },
  tags: ["public"],
  exclude: [{ operationId: "deleteAccount" }],
});

export default server;
server.listen();
```

**Verify:** `npm run typecheck` passes and the environment contains `API_TOKEN` when bearer auth is required.

### 3. Inspect Generated Tools

```bash
npm run dev
```

Open `http://127.0.0.1:3000/mcp/inspector`, connect to `http://127.0.0.1:3000/mcp`, and open **Tools**.

**Verify:** Operations included by `tags` appear as tools; excluded operations do not appear.

### 4. Call One Generated Tool

Choose one operation and supply its mapped arguments:

- path parameters: required top-level fields
- query/header parameters: top-level fields
- JSON request body: `body`
- cookie parameters: ignored

**Verify:** A 2xx JSON response returns structured data; a non-2xx upstream response returns an MCP error.

### 5. Build and Deploy

```bash
npm run build
npm run deploy
```

**Verify:** Build output appears under `.mcp-use/build/`, then call the same tool against the deployed MCP URL.

## Limits

- JSON request and response bodies only.
- No automatic remote `$ref` bundling.
- No automatic model-friendly workflow design; replace low-level generated operations with curated `server.tool()` declarations when necessary.

Read `references/17-advanced/03-openapi-fromopenapi.md` for every option and limitation.
