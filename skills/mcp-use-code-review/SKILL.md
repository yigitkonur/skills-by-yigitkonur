---
name: mcp-use-code-review
description: Use skill if you are reviewing or debugging Python code that consumes MCP servers through the `mcp-use` package.
---

# MCP Use Code Review

## What mcp-use IS vs. What It Is NOT

| | mcp-use (`pip install mcp-use`) | MCP Server SDK (`pip install mcp`) | Claude Agent SDK | mcp-use Server SDK (TS/Python) |
|---|---|---|---|---|
| **Purpose** | Connect a LangChain LLM to one or more *existing* MCP servers | Build / expose an MCP server | Build agents using Anthropic's agent framework | Build production MCP servers with built-in transport, sessions, OAuth |
| **Key classes** | `MCPClient`, `MCPAgent`, `MCPSession` | `Server`, `StdioServerTransport` | `@tool` decorator, `createSdkMcpServer` | `MCPServer`, `text()`, `object()`, session stores, OAuth providers |
| **Tool relationship** | *Discovers* tools from running servers | *Defines* tools that servers expose | *Defines* tools for the agent to use | *Defines* tools via `server.tool()` / `@server.tool()` decorators |
| **Import** | `from mcp_use import MCPClient, MCPAgent` | `from mcp.server import Server` | N/A (TypeScript SDK) | TS: `import { MCPServer } from 'mcp-use/server'` / Python: `from mcp_use import MCPServer` |
| **Config** | `{"mcpServers": {"name": {…}}}` dict | N/A — you write the server code | N/A | Server config object with name, version, sessionStore, OAuth |

**Rule of thumb:** If the file *consumes* MCP tools, it should import from `mcp_use` (client). If it *provides* MCP tools, it can import from `mcp.server` (official SDK) or `mcp-use/server` (mcp-use Server SDK, which wraps the official SDK with production features). Mixing client and server imports in the same file is almost always wrong.

---

## Server Config Schema

The config dict follows the Claude Desktop / Cursor convention. Transport type is auto-detected by key presence.

### Stdio (command-based)

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "env": { "SOME_VAR": "value" }
    }
  }
}
```

Detected when the server entry has a `"command"` key → `StdioConnector`.

### HTTP / SSE / Streamable HTTP

```json
{
  "mcpServers": {
    "remote-server": {
      "url": "http://localhost:3000/mcp",
      "headers": { "Authorization": "Bearer token" },
      "timeout": 5,
      "sse_read_timeout": 300
    }
  }
}
```

Detected when the server entry has a `"url"` key → `HttpConnector` (auto-negotiates Streamable HTTP first, falls back to SSE).

### WebSocket

```json
{
  "mcpServers": {
    "ws-server": {
      "ws_url": "ws://localhost:8080/mcp"
    }
  }
}
```

Detected when the server entry has a `"ws_url"` key → `WebSocketConnector`.

### Loading the config

```python
# From dict
client = MCPClient(config={"mcpServers": {…}})

# From JSON file path
client = MCPClient(config="path/to/config.json")

# Factory methods
client = MCPClient.from_dict(config_dict)
client = MCPClient.from_config_file("config.json")
```

---

## Correct Client Lifecycle

### High-level (MCPAgent — most common)

```python
import asyncio
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

async def main():
    client = MCPClient(config={"mcpServers": {…}})        # 1. parse config (sync)
    llm = ChatOpenAI(model="gpt-4o")                       # 2. create LLM (sync)
    agent = MCPAgent(llm=llm, client=client, max_steps=30) # 3. create agent (sync)
    result = await agent.run("Do something")                # 4. run (async) — connects, discovers tools, runs loop
    print(result)

asyncio.run(main())
```

`agent.run()` handles the entire lifecycle: connect → initialize → discover tools → run agent loop → return result.

### Low-level (MCPClient direct usage)

```python
async def main():
    client = MCPClient(config=config)                            # 1. parse config
    await client.create_all_sessions()                           # 2. connect to all servers (ASYNC)
    session = client.get_session("server-name")                  # 3. get session (sync)
    tools = await session.list_tools()                           # 4. list tools (ASYNC)
    result = await session.call_tool("tool-name", {"arg": "v"})  # 5. call tool (ASYNC)
    await client.close_all_sessions()                            # 6. cleanup (ASYNC)
```

### MCPSession as context manager

```python
async with MCPSession(connector=some_connector) as session:
    await session.initialize()
    tools = await session.list_tools()
    result = await session.call_tool("tool-name", {"arg": "v"})
```

### What requires async/await

| Operation | Async? | Notes |
|---|---|---|
| `MCPClient(config=…)` | No | Just parses config |
| `MCPClient.from_dict(…)` | No | Just parses config |
| `MCPAgent(llm=…, client=…)` | No | Just stores references |
| `agent.run(query)` | **Yes** | Full lifecycle |
| `agent.initialize()` | **Yes** | Connects + discovers tools |
| `client.create_session(name)` | **Yes** | Connects to one server |
| `client.create_all_sessions()` | **Yes** | Connects to all servers |
| `session.list_tools()` | **Yes** | MCP protocol call |
| `session.call_tool(name, args)` | **Yes** | MCP protocol call |
| `client.close_all_sessions()` | **Yes** | Disconnects all |

---

## 6 AI Derailment Patterns

### Pattern 1: Server SDK vs. Client SDK Conflation

**AI writes:**
```python
from mcp.server import Server
from mcp.server.stdio import StdioServerTransport

server = Server("my-app")

@server.tool()
def search(query: str) -> str:
    ...
```

…in a file that should be *consuming* tools from an existing MCP server.

**Why it fails:** `mcp.server.Server` creates a *new* MCP server. The app needs `mcp_use.MCPClient` to *connect* to an already-running server and discover its tools.

**Detect it:**
```
grep for "from mcp.server import" or "StdioServerTransport" in files that also import from mcp_use or reference mcpServers config
```

**Fix:**
```python
from mcp_use import MCPClient, MCPAgent

client = MCPClient(config={"mcpServers": {"server-name": {"command": "…", "args": […]}}})
agent = MCPAgent(llm=llm, client=client)
result = await agent.run("query")
```

---

### Pattern 2: Claude Agent SDK @tool Decorator Misapplication

**AI writes:**
```python
from mcp_use import MCPClient
# Then also tries:
from some_sdk import tool  # or uses @tool decorator

@tool
def search_listings(query: str):
    """Search for listings."""
    ...

# Attempts to register hand-written tools with mcp-use
```

**Why it fails:** mcp-use *discovers* tools from running MCP servers — it does not accept user-defined tool functions. The `@tool` decorator pattern belongs to frameworks that define tools locally (like Claude Agent SDK or LangChain's `@tool`). In mcp-use, tools are defined *in the MCP server*, not in the consumer.

**Detect it:**
```
grep for "@tool" decorator in files that import from mcp_use
grep for "createSdkMcpServer" in any Python file
```

**Fix:**
```python
# Tools come FROM the MCP server, not from your code
client = MCPClient(config={"mcpServers": {"my-server": {"command": "…", "args": […]}}})
agent = MCPAgent(llm=llm, client=client)
# The agent will automatically discover all tools exposed by the server
result = await agent.run("search for listings in Barcelona")
```

---

### Pattern 3: Tool Schema Field Name Mismatch

**AI writes:**
```python
# OpenAI-style schema
tool_def = {
    "name": "search",
    "parameters": {  # ← WRONG key
        "type": "object",
        "properties": {"query": {"type": "string"}}
    }
}

# Or TypeScript SDK style
tool_def = {
    "name": "search",
    "inputSchema": {…}  # Correct MCP key, but wrong context — you shouldn't be defining tools
}
```

**Why it fails:** MCP tools use `inputSchema` (camelCase) in the protocol. But with mcp-use, you don't define tool schemas at all — tools are *discovered* from servers. The `mcp.types.Tool` objects returned by `session.list_tools()` have `name`, `description`, and `inputSchema` attributes. If the agent is writing tool schema dicts, it has fundamentally misunderstood mcp-use's role.

**Detect it:**
```
grep for "parameters" adjacent to tool definitions in mcp_use consumer files
grep for manual Tool() construction or tool schema dicts in consumer code
```

**Fix:**
```python
# Don't define schemas — discover them
session = client.get_session("server-name")
tools = await session.list_tools()  # Returns list[mcp.types.Tool]
for tool in tools:
    print(tool.name)          # str
    print(tool.description)   # str
    print(tool.inputSchema)   # dict (JSON Schema)
```

---

### Pattern 4: Missing Async Lifecycle Steps

**AI writes:**
```python
from mcp_use import MCPClient

client = MCPClient(config=config)
session = client.get_session("server")  # ← CRASH: no sessions created yet
tools = session.list_tools()            # ← Missing await
```

**Why it fails:** `MCPClient(config=…)` only parses the config — it does NOT connect to servers. You must call `await client.create_session("name")` or `await client.create_all_sessions()` before accessing sessions. Also, `list_tools()` is async and requires `await`. When using `MCPAgent`, the `agent.run()` method handles this automatically.

**Detect it:**
```
grep for "client.get_session" not preceded by "await client.create" in the same function
grep for "session.list_tools()" or "session.call_tool(" without "await" prefix
grep for mcp_use usage outside an async function
```

**Fix:**
```python
# Option A: Let MCPAgent handle it (recommended)
agent = MCPAgent(llm=llm, client=client)
result = await agent.run("query")  # Handles connect + discover + run

# Option B: Manual lifecycle
client = MCPClient(config=config)
await client.create_all_sessions()          # ← MUST await this first
session = client.get_session("server")
tools = await session.list_tools()          # ← MUST await
result = await session.call_tool("name", {"arg": "val"})  # ← MUST await
await client.close_all_sessions()           # ← Cleanup
```

---

### Pattern 5: Tool Name Format Incompatibility

**AI writes:**
```python
# Assumes tools are namespaced
result = await session.call_tool("server-name.search", {"query": "test"})

# Or uses dots in tool names with OpenAI
# → Error: string does not match pattern '^[a-zA-Z0-9_-]+$'
```

**Why it fails:** mcp-use exposes tools with their **original names** from the MCP server — no namespace prefix is added. A tool named `search` on the server is just `search`, not `server-name.search`. However, some MCP servers expose tool names containing dots (e.g., `prometheus.execute_query`), which breaks OpenAI's tool name validation regex.

**Detect it:**
```
grep for "call_tool" with dot-separated names like "server.tool"
grep for "Invalid.*function.name.*pattern" in error logs
```

**Fix:**
```python
# Tools use their original server names — no prefix
tools = await session.list_tools()
print([t.name for t in tools])  # e.g., ["search", "get_details", "add"]

# Call by original name
result = await session.call_tool("search", {"query": "test"})

# If a server exposes dotted names and you use OpenAI, sanitize:
# Replace dots with underscores or use a different LLM provider
```

---

### Pattern 6: LangChain Import Path / Version Mismatch

**AI writes:**
```python
# Old-style imports (pre-LangChain 1.0)
from langchain.llms import OpenAI              # ← DEPRECATED path
from langchain.chat_models import ChatOpenAI   # ← DEPRECATED path
from langchain.agents import initialize_agent   # ← REMOVED in 1.0

# Or wrong package
from langchain import ChatOpenAI  # ← Not valid
```

**Why it fails:** mcp-use requires `langchain>=1.0.0`. In LangChain 1.0+, LLM providers moved to separate packages (`langchain-openai`, `langchain-anthropic`, etc.). The old `langchain.llms` and `langchain.chat_models` paths are removed or deprecated. Also, `initialize_agent` was replaced by `create_agent` (from LangGraph).

**Detect it:**
```
grep for "from langchain.llms" or "from langchain.chat_models" in files using mcp_use
grep for "initialize_agent" in files using mcp_use
grep for "from langchain import Chat" (wrong path)
```

**Fix:**
```python
# Correct imports for LangChain 1.0+
from langchain_openai import ChatOpenAI           # pip install langchain-openai
from langchain_anthropic import ChatAnthropic     # pip install langchain-anthropic
from langchain_google_genai import ChatGoogleGenerativeAI  # pip install langchain-google-genai

# mcp-use handles agent creation internally — don't use initialize_agent
from mcp_use import MCPAgent, MCPClient

agent = MCPAgent(llm=ChatOpenAI(model="gpt-4o"), client=client)
result = await agent.run("query")
```

---

## Review Checklist

Run these checks against any mcp-use codebase. Each item is verifiable via grep or file inspection.

### Import Correctness
- [ ] **RC-01**: No `from mcp.server import Server` in consumer/client files
- [ ] **RC-02**: No `StdioServerTransport` import in consumer/client files
- [ ] **RC-03**: No `@tool` decorator used alongside `mcp_use` imports
- [ ] **RC-04**: No `from langchain.llms import` (deprecated path)
- [ ] **RC-05**: No `from langchain.chat_models import` (deprecated path)
- [ ] **RC-06**: No `initialize_agent` usage (removed in LangChain 1.0)
- [ ] **RC-07**: LLM imports use provider packages (`langchain_openai`, `langchain_anthropic`, etc.)

### Config Correctness
- [ ] **RC-08**: Config dict has top-level `"mcpServers"` key (not `"servers"` or `"mcp_servers"`)
- [ ] **RC-09**: Stdio servers have both `"command"` and `"args"` keys
- [ ] **RC-10**: HTTP servers use `"url"` key (not `"endpoint"` or `"base_url"`)
- [ ] **RC-11**: WebSocket servers use `"ws_url"` key (not `"websocket"` or `"ws"`)

### Async Correctness
- [ ] **RC-12**: All mcp-use operations run inside `async def` functions
- [ ] **RC-13**: `agent.run()` is awaited
- [ ] **RC-14**: `client.create_session()` / `client.create_all_sessions()` is awaited before accessing sessions
- [ ] **RC-15**: `session.list_tools()` and `session.call_tool()` are awaited
- [ ] **RC-16**: Entry point uses `asyncio.run(main())` (not bare `main()`)

### Lifecycle Correctness
- [ ] **RC-17**: `client.get_session()` is not called before `create_session()` or `create_all_sessions()`
- [ ] **RC-18**: `client.close_all_sessions()` is called in cleanup (or `try/finally` block)
- [ ] **RC-19**: When using `MCPSession` directly, it uses `async with` or explicit `connect()`/`disconnect()`

### Tool Usage
- [ ] **RC-20**: No manual tool schema definitions (`parameters:` dicts) in consumer code
- [ ] **RC-21**: Tool calls use original server names (no fabricated namespaced names)
- [ ] **RC-22**: No `Tool()` constructor calls in consumer code (tools come from `list_tools()`)

---

## Test Patterns

### Mocking an MCP Server for Unit Tests

```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import Tool, CallToolResult, TextContent

@pytest.fixture
def mock_tools():
    return [
        Tool(
            name="search",
            description="Search for items",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        )
    ]

@pytest.fixture
def mock_session(mock_tools):
    session = AsyncMock()
    session.list_tools.return_value = mock_tools
    session.call_tool.return_value = CallToolResult(
        content=[TextContent(type="text", text="result")],
        isError=False
    )
    session.is_connected = True
    return session

@pytest.fixture
def mock_client(mock_session):
    client = MagicMock()
    client.create_all_sessions = AsyncMock()
    client.get_session = MagicMock(return_value=mock_session)
    client.close_all_sessions = AsyncMock()
    return client
```

### Verifying Tool Discovery

```python
@pytest.mark.asyncio
async def test_tool_discovery(mock_client, mock_session, mock_tools):
    await mock_client.create_all_sessions()
    session = mock_client.get_session("test-server")
    tools = await session.list_tools()

    assert len(tools) == len(mock_tools)
    assert tools[0].name == "search"
    assert "query" in tools[0].inputSchema["properties"]
    mock_session.list_tools.assert_awaited_once()
```

### Asserting a Tool Was Actually Called

```python
@pytest.mark.asyncio
async def test_tool_execution(mock_client, mock_session):
    await mock_client.create_all_sessions()
    session = mock_client.get_session("test-server")
    result = await session.call_tool("search", {"query": "test"})

    mock_session.call_tool.assert_awaited_once_with("search", {"query": "test"})
    assert result.content[0].text == "result"
    assert not result.isError
```

### Testing the Full Agent Loop

```python
@pytest.mark.asyncio
async def test_agent_run():
    with patch("mcp_use.MCPClient") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.create_all_sessions = AsyncMock()
        mock_client.close_all_sessions = AsyncMock()

        # Mock the session and tools
        mock_session = AsyncMock()
        mock_session.list_tools.return_value = [
            Tool(name="add", description="Add numbers",
                 inputSchema={"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}})
        ]
        mock_client.get_session.return_value = mock_session

        # The agent run would be tested via integration test with a real LLM
        # or by mocking the LangChain agent executor
```

### Async Test Setup with pytest-asyncio

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for all tests."""
    return None

# In pyproject.toml or pytest.ini:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"  # All async tests run automatically
```

---

## Common Failure Signatures

| Error Message | Derailment | Check |
|---|---|---|
| `ModuleNotFoundError: No module named 'mcp.server'` in a consumer file | Pattern 1 | Verify imports use `mcp_use`, not `mcp.server` |
| `AttributeError: 'MCPClient' object has no attribute 'tool'` | Pattern 2 | MCPClient discovers tools, doesn't define them |
| `KeyError: 'parameters'` when accessing tool schema | Pattern 3 | MCP uses `inputSchema`, not `parameters` |
| `AttributeError: 'NoneType' object has no attribute 'list_tools'` | Pattern 4 | Call `create_session()` before `get_session()` |
| `RuntimeError: no running event loop` | Pattern 4 | Wrap in `async def` + `asyncio.run()` |
| `TypeError: object NoneType can't be used in 'await' expression` | Pattern 4 | Missing `await` on async call |
| `Error code: 400 - Invalid 'messages[N].tool_calls[0].function.name': string does not match pattern '^[a-zA-Z0-9_-]+$'` | Pattern 5 | Tool name contains dots; sanitize or use different LLM |
| `ToolException: tool-name is not a valid tool` | Pattern 5 | Check tool name matches `list_tools()` output exactly |
| `ModuleNotFoundError: No module named 'langchain.llms'` | Pattern 6 | Use `langchain_openai`, not `langchain.llms` |
| `ImportError: cannot import name 'initialize_agent'` | Pattern 6 | Removed in LangChain 1.0; use `MCPAgent` instead |
| `ModuleNotFoundError: No module named 'langchain_openai'` | Pattern 6 | Run `pip install langchain-openai` |
| `ValueError: Unrecognized message part type: thinking` | N/A (Gemini) | Known Gemini issue (#110); filter thinking blocks or use different model |
| `RuntimeError: Code mode is not enabled` | N/A (Config) | Set `code_mode=True` in `MCPClient` constructor |

---

## Migrating to mcp-use

This section maps official `@modelcontextprotocol/sdk` (TypeScript) patterns to their mcp-use equivalents. If an AI agent sees official SDK patterns in existing code and needs to understand the mcp-use way, use this mapping.

### Server Creation

**Official TS SDK:**
```typescript
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server';

const server = new McpServer(
    { name: 'my-server', version: '1.0.0' },
    { capabilities: { tools: {}, resources: { listChanged: true } } }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

**mcp-use TS equivalent:**
```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
    name: 'my-server',
    version: '1.0.0',
})

await server.listen(3000)  // Built-in HTTP + transport handling
```

**mcp-use Python equivalent:**
```python
from mcp_use import MCPServer

server = MCPServer(name="my-server")
# Tools registered via decorators, then:
# server.run() or use with uvicorn
```

**Key differences:**
- mcp-use wraps the official SDK internally — no need to import both
- Transport is automatic (stdio for CLI, Streamable HTTP for `listen()`)
- No manual `connect(transport)` needed — `listen()` handles everything
- Session management, CORS, and base path are built-in config options

### Tool Definition

**Official TS SDK:**
```typescript
server.registerTool('calculate-bmi', {
    title: 'BMI Calculator',
    description: 'Calculate BMI',
    inputSchema: z.object({
        weightKg: z.number(),
        heightM: z.number()
    }),
    outputSchema: z.object({ bmi: z.number() }),
}, async ({ weightKg, heightM }) => ({
    content: [{ type: 'text', text: String(weightKg / (heightM * heightM)) }],
    structuredContent: { bmi: weightKg / (heightM * heightM) }
}));
```

**mcp-use TS equivalent:**
```typescript
import { text } from 'mcp-use/server'

server.tool({
    name: 'calculate-bmi',
    description: 'Calculate BMI',
    schema: z.object({
        weightKg: z.number(),
        heightM: z.number()
    }),
}, async ({ weightKg, heightM }) => {
    return text(`BMI: ${weightKg / (heightM * heightM)}`)
})
```

**mcp-use Python equivalent:**
```python
@server.tool(name="calculate_bmi", description="Calculate BMI")
async def calculate_bmi(
    weight_kg: Annotated[float, Field(description="Weight in kg")],
    height_m: Annotated[float, Field(description="Height in m")],
) -> str:
    return f"BMI: {weight_kg / (height_m ** 2)}"
```

**Key differences:**
- `registerTool()` → `server.tool()` (config object + callback)
- `inputSchema` → `schema` (same Zod, different key name)
- Manual `content: [{ type: 'text', text: '...' }]` → `text()` helper
- Response helpers: `text()`, `object()`, `markdown()`, `image()`, `audio()`, `binary()`, `error()`, `mix()`

### Resource Definition

**Official TS SDK:**
```typescript
import { ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource('user', new ResourceTemplate('users://{id}', {
    list: async () => ({ resources: [{ uri: 'users://1', name: 'Alice' }] })
}), { title: 'User Profile' }, async (uri, { id }) => ({
    contents: [{ uri: uri.href, text: JSON.stringify({ id, name: `User ${id}` }) }]
}));
```

**mcp-use TS equivalent:**
```typescript
server.resourceTemplate({
    uriTemplate: 'users://{id}',
    name: 'User Profile',
    mimeType: 'application/json',
}, async ({ id }) => object({ id, name: `User ${id}` }))
```

**mcp-use Python equivalent:**
```python
@server.resource(uri="users://{user_id}", name="user_profile", mime_type="application/json")
async def user_profile(user_id: str) -> str:
    return json.dumps({"id": user_id, "name": f"User {user_id}"})
```

### Prompt Definition

**Official TS SDK:**
```typescript
server.registerPrompt('review-code', {
    title: 'Code Review',
    argsSchema: z.object({ code: z.string() })
}, ({ code }) => ({
    messages: [{ role: 'user', content: { type: 'text', text: `Review:\n${code}` } }]
}));
```

**mcp-use TS equivalent:**
```typescript
server.prompt({
    name: 'review-code',
    description: 'Code review prompt',
    schema: z.object({ code: z.string() }),
}, async ({ code }) => text(`Review:\n${code}`))
```

**mcp-use Python equivalent:**
```python
@server.prompt(name="review_code", title="Code Review")
def review_code(code: Annotated[str, Field(description="Code to review")]) -> str:
    return f"Review:\n{code}"
```

### Transport Setup

**Official TS SDK:**
```typescript
// Stdio
const transport = new StdioServerTransport();
await server.connect(transport);

// HTTP (manual setup required)
import express from 'express';
const app = express();
const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: () => randomUUID() });
app.post('/mcp', async (req, res) => { await transport.handleRequest(req, res, req.body); });
app.get('/mcp', async (req, res) => { /* SSE handler */ });
app.listen(3000);
```

**mcp-use equivalent:**
```typescript
// HTTP (one-liner)
await server.listen(3000)  // Handles /mcp endpoint, SSE, sessions automatically

// CLI workflow
// mcp-use dev
// mcp-use build
// mcp-use start
```

### Session Management

**Official TS SDK:** Manual — you track transports in a Map, route by session ID header.

**mcp-use:** Built-in pluggable storage:
```typescript
import { RedisSessionStore, RedisStreamManager } from 'mcp-use/server'

const server = new MCPServer({
    name: 'my-server',
    sessionStore: new RedisSessionStore({ client: redis }),
    streamManager: new RedisStreamManager({ client: redis, pubSubClient: pubSubRedis }),
})
```

Storage backends: `FileSystemSessionStore` (development default), `InMemorySessionStore` (production default without custom store), `RedisSessionStore` (distributed production).

### Authentication

**Official TS SDK:** Manual middleware — implement `OAuthServerProvider`, wire up auth endpoints yourself.

**mcp-use:** Built-in providers:
```typescript
import { MCPServer, oauthAuth0Provider } from 'mcp-use/server'

const server = new MCPServer({
    name: 'protected-server',
    oauth: oauthAuth0Provider({
        domain: 'your-tenant.auth0.com',
        audience: 'https://your-api.example.com',
    }),
})
```

Providers: `oauthAuth0Provider`, `oauthSupabaseProvider`, `oauthWorkOSProvider`, `oauthKeycloakProvider`, `oauthCustomProvider`.

### Quick Migration Checklist

| Official SDK Pattern | mcp-use Equivalent | Notes |
|---|---|---|
| `new McpServer(info, options)` | `new MCPServer(config)` | Config includes transport, sessions, OAuth |
| `server.registerTool(name, config, cb)` | `server.tool(config, cb)` | `inputSchema` → `schema` |
| `server.registerResource(name, uri, meta, cb)` | `server.resource(config, cb)` | Simpler signature |
| `server.registerPrompt(name, config, cb)` | `server.prompt(config, cb)` | Response helpers work |
| `new StdioServerTransport()` + `server.connect(t)` | `server.listen()` or `mcp-use dev/start` workflow | Built-in HTTP transport/session handling |
| `new StreamableHTTPServerTransport(opts)` | `server.listen(port)` | Built-in HTTP server |
| Manual session Map + routing | `sessionStore: new RedisSessionStore(...)` | Pluggable backends |
| Manual OAuth middleware | `oauth: oauthAuth0Provider(...)` | 5 built-in providers |
| Manual `content: [{ type: 'text', text }]` | `text(string)` | 10+ response helpers |
| `ctx.mcpReq.log('info', msg)` | `ctx.log('info', msg)` | Simplified logging |
