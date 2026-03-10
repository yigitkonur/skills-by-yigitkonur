# mcp-use LangChain Bridge

## Overview

mcp-use bridges MCP servers to LangChain by converting MCP tools into LangChain `BaseTool` objects. This happens either automatically (via `MCPAgent`) or manually (via `LangChainAdapter`).

## How MCP Tools Become LangChain Tools

```
MCP Server                    mcp-use                         LangChain
─────────                    ────────                        ──────────
Tool {                   →   LangChainAdapter              →  BaseTool(
  name: "search"              .convert_tool()                   name="search",
  description: "…"            1. take inputSchema               description="…",
  inputSchema: {              2. fix_schema()                   args_schema=PydanticModel,
    type: object              3. jsonschema_to_pydantic()       func=async_call_wrapper
    properties: {…}           4. wrap in BaseTool             )
  }
}
```

### Conversion Steps (from `LangChainAdapter`)

1. **Input**: `mcp.types.Tool` with `name`, `description`, `inputSchema` (JSON Schema dict)
2. **Schema fix**: `fix_schema()` preprocesses the JSON Schema (handles edge cases)
3. **Pydantic conversion**: `jsonschema_to_pydantic()` (from `jsonschema-pydantic` package) converts JSON Schema → Pydantic model
4. **Tool wrapping**: Creates a LangChain `BaseTool` with:
   - `name` = original tool name
   - `description` = original description
   - `args_schema` = generated Pydantic model
   - `_run()` / `_arun()` = wrapper that calls `session.call_tool()`
5. **Resources**: MCP resources are also converted to tools (prefixed with `resource_`)
6. **Prompts**: MCP prompts are converted to tools (prefixed with `prompt_`)

## Required LangChain Version

```
langchain >= 1.0.0    (core dependency of mcp-use)
```

mcp-use depends on `langchain>=1.0.0` — it uses the LangGraph-based agent system, not the legacy `AgentExecutor`.

## Required Packages

```bash
pip install mcp-use                    # Core (includes langchain>=1.0.0)
pip install mcp-use[openai]            # + langchain_openai
pip install mcp-use[anthropic]         # + langchain_anthropic

# Or install LLM provider packages directly:
pip install langchain-openai           # ChatOpenAI
pip install langchain-anthropic        # ChatAnthropic
pip install langchain-google-genai     # ChatGoogleGenerativeAI
```

## Correct Import Paths

```python
# mcp-use core
from mcp_use import MCPAgent, MCPClient, MCPSession

# LLM providers (LangChain 1.0+ style — separate packages)
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# Manual adapter usage
from mcp_use.agents.adapters import LangChainAdapter
from mcp_use.agents.adapters import AnthropicMCPAdapter

# LangChain core types (if needed)
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
```

### WRONG Import Paths (Common AI Mistakes)

```python
# ✗ DEPRECATED — removed or broken in LangChain 1.0+
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.tools import Tool

# ✗ NEVER VALID
from langchain import ChatOpenAI
from langchain import MCPClient
```

## Using MCPAgent (Automatic Bridge)

The simplest path — `MCPAgent` handles everything:

```python
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

client = MCPClient(config=config)
llm = ChatOpenAI(model="gpt-4o")
agent = MCPAgent(llm=llm, client=client, max_steps=30)

# Internally:
# 1. Creates sessions for all servers
# 2. Uses LangChainAdapter to convert MCP tools → BaseTool
# 3. Creates a LangGraph CompiledStateGraph agent
# 4. Runs the agent loop

result = await agent.run("Your query")
```

### Supported LLMs

Any LangChain `BaseLanguageModel` works:

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# All of these work with MCPAgent
MCPAgent(llm=ChatOpenAI(model="gpt-4o"), client=client)
MCPAgent(llm=ChatAnthropic(model="claude-sonnet-4-5"), client=client)
MCPAgent(llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash"), client=client)
```

## Using LangChainAdapter (Manual Bridge)

For custom agent setups or when you need more control:

```python
from mcp_use import MCPClient
from mcp_use.agents.adapters import LangChainAdapter

client = MCPClient(config=config)
adapter = LangChainAdapter()
await adapter.create_all(client)     # Creates sessions + converts tools

# Access converted tools
tools = adapter.tools            # list[BaseTool] — from MCP tools
resources = adapter.resources    # list[BaseTool] — from MCP resources
prompts = adapter.prompts        # list[BaseTool] — from MCP prompts

all_tools = tools + resources + prompts
```

### Using Converted Tools with a Custom LangChain Agent

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")
agent = create_agent(
    model=model,
    tools=all_tools,
    system_prompt="You are a helpful assistant."
)

result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Your query"}]
})
```

### Using Converted Tools Directly (No Agent)

```python
# Find a specific tool
search_tool = next(t for t in adapter.tools if t.name == "search")

# Invoke it directly
result = await search_tool.ainvoke({"query": "test"})
print(result)
```

## Anthropic Native Bridge (No LangChain Agent)

For using Anthropic's API directly instead of LangChain's agent:

```python
from anthropic import Anthropic
from mcp_use import MCPClient
from mcp_use.agents.adapters import AnthropicMCPAdapter

client = MCPClient(config=config)
adapter = AnthropicMCPAdapter()
await adapter.create_all(client)

anthropic_tools = adapter.tools + adapter.resources + adapter.prompts

anthropic = Anthropic()
response = anthropic.messages.create(
    model="claude-sonnet-4-5",
    tools=anthropic_tools,
    max_tokens=1024,
    messages=[{"role": "user", "content": "Query"}]
)

# Execute tool calls from the response
for block in response.content:
    if block.type == "tool_use":
        executor = adapter.tool_executors[block.name]
        tool_result = await executor(**block.input)
        content = adapter.parse_result(tool_result)
```

## Key Differences from Direct LangChain Tool Usage

| Aspect | LangChain @tool | mcp-use Bridge |
|---|---|---|
| Tool definition | You write the function + decorator | Tools defined in MCP server, discovered at runtime |
| Schema | Inferred from function signature | Converted from MCP `inputSchema` (JSON Schema → Pydantic) |
| Execution | Runs your Python function | Sends MCP `tools/call` request to server |
| Availability | Static at compile time | Dynamic — depends on which servers are connected |
| Naming | You choose the name | Name comes from server (original, no namespace) |

## Common Bridge Issues

### Tool Names with Special Characters

Some MCP servers expose tool names with dots (e.g., `prometheus.execute_query`). OpenAI's API rejects these:

```
Error code: 400 - Invalid 'messages[N].tool_calls[0].function.name':
string does not match pattern '^[a-zA-Z0-9_-]+$'
```

**Workaround:** Use `disallowed_tools` to filter problematic tools, or use a model that accepts dots (Anthropic, Google).

### Empty Tool Descriptions

Some MCP servers provide tools without descriptions. LangChain may warn or fail:

**Fix:** Use `additional_instructions` on `MCPAgent` to describe tools to the LLM.

### Schema Conversion Failures

Complex JSON Schemas may fail during `jsonschema_to_pydantic()` conversion:

**Fix:** Check for `anyOf`, `oneOf`, or recursive schemas in MCP tools. These may need the `fix_schema()` preprocessing.
