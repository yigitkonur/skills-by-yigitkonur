# Tools Deep Dive

## Overview

MCP tools are the primary way servers expose executable functions to LLM clients. This reference covers tool definition, schema formats, discovery, invocation, and response patterns across the official SDK and mcp-use.

## Tool Definition

### Official TS SDK — `registerTool()`

```typescript
import { McpServer } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

server.registerTool('tool-name', {
    title: 'Human-Readable Title',          // Optional display name
    description: 'What this tool does',     // Required for LLM understanding
    inputSchema: z.object({                  // Zod v4 schema
        param1: z.string().describe('Description'),
        param2: z.number().default(10),
        param3: z.boolean().optional(),
    }),
    outputSchema: z.object({                 // Optional: structured output
        result: z.string(),
    }),
    annotations: {                           // Optional: execution hints
        title: 'Display Title',
        readOnlyHint: true,                  // Tool doesn't modify state
        destructiveHint: false,              // Tool is not destructive
        idempotentHint: true,                // Safe to retry
        openWorldHint: false,                // Operates on closed set
    },
}, async (args, ctx) => {
    // args is typed: { param1: string, param2: number, param3?: boolean }
    // ctx provides: ctx.mcpReq.log(), session info, etc.
    return {
        content: [{ type: 'text', text: 'result' }],
        structuredContent: { result: 'value' },  // Matches outputSchema
        isError: false,                           // Optional error flag
    };
});
```

### mcp-use TS — `server.tool()`

```typescript
import { MCPServer, text, object, error } from 'mcp-use/server'
import { z } from 'zod'

server.tool({
    name: 'tool-name',
    description: 'What this tool does',
    schema: z.object({                        // Note: `schema` not `inputSchema`
        param1: z.string().describe('Description'),
        param2: z.number().default(10),
        param3: z.boolean().optional(),
    }),
    annotations: { readOnlyHint: true },
}, async ({ param1, param2, param3 }, ctx) => {
    // ctx can provide: ctx.log(level, message), ctx.elicit(), ctx.sample(), ctx.reportProgress()
    await ctx.log('info', `Processing ${param1}`)
    return text(`Result: ${param1}`)
    // Or: return object({ result: 'value' })
    // Or: return error('Something went wrong')
})
```

### mcp-use Python — `@server.tool()` decorator

```python
from typing import Annotated
from pydantic import Field
from mcp_use import MCPServer
from mcp.types import ToolAnnotations

server = MCPServer(name="my-server")

@server.tool(
    name="tool_name",
    title="Human-Readable Title",
    description="What this tool does",
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def tool_name(
    param1: Annotated[str, Field(description="Description")],
    param2: Annotated[int, Field(default=10, description="With default")],
    param3: Annotated[bool | None, Field(default=None, description="Optional")],
    context: Context,  # Access to MCP context
) -> str:
    return f"Result: {param1}"
```

## Schema Formats

### On the Wire (MCP Protocol)

Tools are described using JSON Schema in the MCP protocol:

```json
{
    "name": "search",
    "description": "Search the database",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": { "type": "string", "description": "Search query" },
            "limit": { "type": "number", "default": 10 }
        },
        "required": ["query"]
    }
}
```

**Key field name**: `inputSchema` (camelCase) — this is the MCP protocol standard.

### At Definition Time

| Framework | Schema System | Key Name |
|---|---|---|
| Official TS SDK | Zod v4 | `inputSchema` (Zod object, converted to JSON Schema) |
| mcp-use TS | Zod | `schema` (Zod object, converted to JSON Schema) |
| mcp-use Python | Pydantic / `Field()` | Function signature + `Annotated[type, Field()]` |
| mcp-use Python client | N/A (consumer) | Receives `inputSchema` as JSON Schema dict |

### Schema Conversion Chain

```
Definition Time          Wire Protocol              Consumer
─────────────           ──────────────             ────────
Zod schema          →   JSON Schema (inputSchema)  →   Pydantic model
z.object({...})         { type: "object", ... }        (via jsonschema_to_pydantic)
                                                        → LangChain BaseTool.args_schema
```

## Response Helpers (mcp-use only)

mcp-use provides response helpers that return properly formatted `CallToolResult` objects:

| Helper | Returns | Use Case |
|---|---|---|
| `text(string)` | Text content (`text/plain`) | Plain text responses |
| `object(data)` | JSON content + structured content | Structured data |
| `markdown(string)` | Markdown content (`text/markdown`) | Rich text documentation |
| `html(string)` / `xml(string)` / `css(string)` / `javascript(string)` | Typed text content with matching MIME | Web/document/code payloads |
| `array(items)` | Wrapped structured array content | List-like structured responses |
| `image(data, mimeType)` | Image content block | Base64 image responses |
| `audio(dataOrPath, mimeType?)` | Audio content block | Audio responses |
| `binary(base64Data, mimeType)` | Binary content block | Arbitrary binary payloads |
| `resource(uri, content)` | Embedded resource content | Embed resource payloads |
| `error(message)` | Error response with `isError: true` | Standardized failures |
| `mix(...)` | Combined content blocks | Multi-part responses |
| `widget({ props, output, metadata?, message? })` | Widget payload + optional model-visible output | Interactive widget responses |

### Usage Examples

```typescript
// Simple text
return text('Hello, world!')

// Structured data
return object({ users: [...], total: 42 })

// Error
return error('Invalid input: query cannot be empty')

// Mixed content
return mix(
    text('Analysis complete:'),
    object({ results: data }),
    image(chartBase64, 'image/png')
)

// Typed response
import type { TypedCallToolResult } from 'mcp-use/server'
return object({ score: 42 }) as TypedCallToolResult<{ score: number }>
```

## Tool Discovery (Client Side)

### mcp-use Python Client

```python
from mcp_use import MCPClient

client = MCPClient(config=config)
await client.create_all_sessions()
session = client.get_session("server-name")

# List all tools
tools = await session.list_tools()
# Returns: list[mcp.types.Tool]

for tool in tools:
    print(f"Name: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Schema: {tool.inputSchema}")  # JSON Schema dict
```

### mcp-use Python Client — Search Tools

```python
# Search across all connected servers
result = await client.search_tools("github", detail_level="full")
# Returns:
# {
#   "meta": {"total_tools": 15, "namespaces": ["server1"], "result_count": 3},
#   "results": [
#     {"name": "tool_name", "server": "server1", "description": "...", "input_schema": {...}}
#   ]
# }
```

### Via MCPAgent (Automatic)

When using `MCPAgent`, tools are automatically:
1. Discovered from all configured servers
2. Converted to LangChain `BaseTool` via `LangChainAdapter`
3. Bound to the agent — no manual discovery needed

## Tool Invocation

### Direct Call (Client Side)

```python
result = await session.call_tool("tool-name", {"param1": "value", "param2": 42})
# Returns: CallToolResult

if result.isError:
    print(f"Error: {result.content[0].text}")
else:
    print(f"Result: {result.content[0].text}")
```

### Via Agent (Automatic)

```python
agent = MCPAgent(llm=llm, client=client, max_steps=30)
result = await agent.run("Do something using the search tool")
# Agent automatically discovers, selects, and invokes tools
```

## Tool Context (Server Side)

### mcp-use TS Context

```typescript
server.tool({ name: 'smart-tool', schema: z.object({...}) },
    async (args, ctx) => {
        // Logging
        await ctx.log('info', 'Processing request')
        await ctx.log('debug', `Args: ${JSON.stringify(args)}`)

        // Progress reporting
        if (ctx.reportProgress) {
            await ctx.reportProgress(50, 100, 'Halfway done')
        }

        // Elicitation (request user input)
        const userInput = await ctx.elicit('Confirm action?', z.object({
            confirm: z.boolean()
        }))

        // Sampling (request LLM completion)
        const sampled = await ctx.sample('Summarize this data...')

        return text(sampled.content[0].text)
    }
)
```

### Official SDK Context

```typescript
server.registerTool('my-tool', { inputSchema: z.object({...}) },
    async (args, ctx) => {
        // Logging
        await ctx.mcpReq.log('info', 'Processing')

        // Progress (manual notification)
        await ctx.mcpReq.sendNotification({
            method: 'notifications/progress',
            params: { progressToken: ctx.mcpReq.progressToken, progress: 50, total: 100 }
        })

        return { content: [{ type: 'text', text: 'result' }] }
    }
)
```

## Tool Naming Conventions

| Context | Convention | Example |
|---|---|---|
| MCP server definition | Any string (alphanumeric + hyphens recommended) | `get-weather`, `search_db` |
| MCP protocol (wire) | Original name from server | `get-weather` |
| mcp-use client (no server manager) | Original name, flat list | `get-weather` |
| mcp-use client (server manager mode) | Meta-tools first, then original names after connect | `list_mcp_servers` → `connect_to_mcp_server` → `get-weather` |
| LangChain BaseTool | Original name | `get-weather` |
| OpenAI API | Must match `^[a-zA-Z0-9_-]+$` | Dots in names will error |

## Common Tool Errors

| Error | Cause | Fix |
|---|---|---|
| `400: Invalid function.name pattern` | Tool name has dots (OpenAI restriction) | Use hyphens/underscores, or use Anthropic/Google |
| `ToolException: X is not a valid tool` | Wrong tool name in call_tool() | Check `list_tools()` for exact names |
| `ValidationError` on tool input | Schema mismatch between client and server | Verify inputSchema matches expected format |
| `isError: true` in result | Tool execution failed (application error) | Check `result.content[0].text` for error message |
