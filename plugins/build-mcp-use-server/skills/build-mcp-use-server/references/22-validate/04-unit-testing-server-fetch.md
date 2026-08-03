# Unit Testing via server.fetch

*Read this when you want to test MCP server behavior programmatically without running npm run dev.*

The MCP server's `fetch` handler is a standard Web API handler. You can call it directly with a Request object.

## Basic Test Pattern

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "test-server", version: "1.0.0" });

server.tool(
  {
    name: "add",
    description: "Add two numbers",
    inputSchema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number")
    })
  },
  async ({ a, b }) => ({
    content: [{ type: "text", text: `${a + b}` }]
  })
);

// Test it
async function testAdd() {
  const request = new Request("http://localhost:3000/mcp", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "Mcp-Protocol-Version": "2024-11-05"
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: "add",
        arguments: { a: 2, b: 3 }
      }
    })
  });

  const response = await server.fetch(request);
  const data = await response.json();
  
  console.assert(data.result.content[0].text === "5", "Add failed");
  console.log("✓ Add test passed");
}

testAdd().catch(console.error);
```

## Testing initialize()

```typescript
async function testInitialize() {
  const request = new Request("http://localhost:3000/mcp", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "Mcp-Protocol-Version": "2024-11-05"
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: {},
        clientInfo: { name: "test", version: "1.0" }
      }
    })
  });

  const response = await server.fetch(request);
  const data = await response.json();
  
  console.assert(data.result.serverInfo.name === "test-server");
  console.log("✓ Initialize passed");
}

testInitialize().catch(console.error);
```

## Testing tools/list

```typescript
async function testListTools() {
  const request = new Request("http://localhost:3000/mcp", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream"
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/list",
      params: {}
    })
  });

  const response = await server.fetch(request);
  const data = await response.json();
  
  console.assert(
    data.result.tools.some((t: any) => t.name === "add"),
    "Tool 'add' not found"
  );
  console.log("✓ tools/list passed");
}

testListTools().catch(console.error);
```

## Testing Error Paths

```typescript
async function testToolError() {
  const request = new Request("http://localhost:3000/mcp", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream"
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: "add",
        arguments: { a: "not a number", b: 3 }  // Invalid type
      }
    })
  });

  const response = await server.fetch(request);
  const data = await response.json();
  
  console.assert(data.error !== undefined, "Expected error but got success");
  console.log("✓ Error validation passed");
}

testToolError().catch(console.error);
```

## With a Testing Framework

```typescript
import { describe, it, expect } from "vitest";

describe("MCP Server", () => {
  it("should add numbers", async () => {
    const request = new Request("http://localhost:3000/mcp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: { name: "add", arguments: { a: 5, b: 7 } }
      })
    });

    const response = await server.fetch(request);
    const data = await response.json();

    expect(data.result.content[0].text).toBe("12");
  });
});
```

## Key Points

- **Request object**: Standard Web API `Request` constructor; set `method: "POST"` and headers including both `Content-Type: application/json` and `Accept: application/json, text/event-stream`
- **Accept header required**: Missing `Accept: application/json, text/event-stream` returns `406 Not Acceptable` — this is a hard requirement of the bundled transport, not v2-specific etiquette
- **No session state**: Each call is stateless; no session ID headers needed
- **Protocol version header is optional**: `Mcp-Protocol-Version` is only checked when present; the `initialize` call's `params.protocolVersion` is what actually negotiates the session
- **JSON-RPC format**: Match the exact envelope structure (see references/22-validate/02-curl-handshake.md)
- **Response parsing**: `.json()` returns the JSON-RPC response

Do NOT use mocks for `server.fetch` itself — call it directly. This is the fastest, most reliable unit test path for MCP tools.

