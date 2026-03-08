# mcp-use Async Lifecycle

## Overview

mcp-use is **100% async** — there is no synchronous API. All MCP protocol operations require `await`. Entry points must use `asyncio.run()`.

## Lifecycle Diagram

```
MCPClient(config)          ← SYNC: parse config, no connections
    │
    ├─ await create_all_sessions()    ← ASYNC: connects to all servers
    │      └─ connector.connect()     ← starts subprocess / HTTP / WS connection
    │      └─ connector.initialize()  ← MCP protocol handshake
    │
    ├─ get_session("name")            ← SYNC: returns existing session
    │      │
    │      ├─ await list_tools()      ← ASYNC: MCP tools/list request
    │      ├─ await call_tool(…)      ← ASYNC: MCP tools/call request
    │      ├─ await list_resources()  ← ASYNC: MCP resources/list
    │      └─ await read_resource(…)  ← ASYNC: MCP resources/read
    │
    └─ await close_all_sessions()     ← ASYNC: disconnects all
```

```
MCPAgent(llm, client)      ← SYNC: stores references
    │
    └─ await run("query")  ← ASYNC: full lifecycle
           ├─ create sessions (if not created)
           ├─ discover tools
           ├─ convert to LangChain tools
           ├─ create LangGraph agent
           ├─ run agent loop (tool calls + LLM)
           └─ return result string
```

## Correct Code Templates

### Template 1: MCPAgent (Recommended)

```python
import asyncio
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

async def main():
    config = {
        "mcpServers": {
            "server": {"command": "npx", "args": ["-y", "some-server"]}
        }
    }

    client = MCPClient(config=config)
    llm = ChatOpenAI(model="gpt-4o")
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    try:
        result = await agent.run("Your query here")
        print(result)
    finally:
        await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

### Template 2: Direct Tool Calls (No LLM)

```python
import asyncio
from mcp_use import MCPClient

async def main():
    config = {
        "mcpServers": {
            "math": {"command": "npx", "args": ["-y", "@mcp/math-server"]}
        }
    }

    client = MCPClient(config=config)
    try:
        await client.create_all_sessions()
        session = client.get_session("math")

        # Discover tools
        tools = await session.list_tools()
        print(f"Available: {[t.name for t in tools]}")

        # Call a tool
        result = await session.call_tool("add", {"a": 1, "b": 2})
        print(f"Result: {result.content[0].text}")
    finally:
        await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

### Template 3: MCPSession Context Manager

```python
import asyncio
from mcp_use import MCPSession, StdioConnector

async def main():
    connector = StdioConnector(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-everything"]
    )

    async with MCPSession(connector) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("echo", {"message": "hello"})
        print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
```

### Template 4: LangChain Adapter (Manual Integration)

```python
import asyncio
from langchain_openai import ChatOpenAI
from mcp_use import MCPClient
from mcp_use.agents.adapters import LangChainAdapter

async def main():
    client = MCPClient(config=config)
    adapter = LangChainAdapter()
    await adapter.create_all(client)

    langchain_tools = adapter.tools + adapter.resources + adapter.prompts

    # Use with any LangChain agent framework
    from langchain.agents import create_agent
    model = ChatOpenAI(model="gpt-4o")
    agent = create_agent(model=model, tools=langchain_tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": "query"}]})

    await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Lifecycle Mistakes

### Mistake 1: Accessing Sessions Before Creation

```python
# WRONG
client = MCPClient(config=config)
session = client.get_session("server")  # ← Returns None or raises error
```

```python
# CORRECT
client = MCPClient(config=config)
await client.create_all_sessions()       # ← Must create first
session = client.get_session("server")   # ← Now works
```

**Error signature:** `AttributeError: 'NoneType' object has no attribute 'list_tools'`

### Mistake 2: Missing await

```python
# WRONG
tools = session.list_tools()   # ← Returns coroutine, not tools
result = session.call_tool("name", {})  # ← Returns coroutine
```

```python
# CORRECT
tools = await session.list_tools()
result = await session.call_tool("name", {})
```

**Error signature:** `TypeError: object coroutine can't be used in 'await' expression` (if you later try to use it) or silent bugs (coroutine never executed).

### Mistake 3: No asyncio.run()

```python
# WRONG
async def main():
    ...

main()  # ← This does nothing — returns a coroutine object
```

```python
# CORRECT
asyncio.run(main())
```

**Error signature:** `RuntimeWarning: coroutine 'main' was never awaited`

### Mistake 4: No Cleanup

```python
# WRONG — subprocess servers keep running after script exits
client = MCPClient(config=config)
await client.create_all_sessions()
result = await session.call_tool(...)
# Script exits without closing sessions
```

```python
# CORRECT — always clean up
try:
    await client.create_all_sessions()
    ...
finally:
    await client.close_all_sessions()
```

**Symptom:** Orphaned `npx` or `node` processes after script exit.

### Mistake 5: Using MCPClient as Context Manager

```python
# WRONG — MCPClient does NOT support async with
async with MCPClient(config=config) as client:
    ...
```

```python
# CORRECT — MCPSession supports async with, MCPClient does not
client = MCPClient(config=config)
await client.create_all_sessions()
# ... or use MCPSession directly:
async with MCPSession(connector) as session:
    ...
```

**Error signature:** `AttributeError: __aenter__`

## pytest-asyncio Setup

```python
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

# conftest.py
import pytest

# All async test functions are automatically detected and run
# No need for @pytest.mark.asyncio when asyncio_mode = "auto"
```

```python
# test_example.py
from unittest.mock import AsyncMock, MagicMock

async def test_tool_discovery():
    mock_session = AsyncMock()
    mock_session.list_tools.return_value = [...]

    tools = await mock_session.list_tools()
    assert len(tools) > 0
```
