---
name: mcp-server-tester
description: Use skill if you need to validate an MCP server, debug broken primitives, or test tools, resources, prompts, and transports before shipping.
license: MIT
metadata:
  author: yigitkonur
  version: "1.0"
---

# MCP Server Testing Suite

This skill provides two testing modes for MCP servers, both powered by `@mcp-use/inspector`.

## How it works

The inspector runs a local web server that proxies JSON-RPC requests to your MCP server. Every MCP operation (initialize, tools/list, tools/call, resources/list, prompts/get, etc.) goes through `curl` calls to the inspector's API. This means you can test any MCP server reachable over HTTP/SSE or WebSocket without needing a config file or daemon.

## Command: `/mcp-test`

**Basic protocol-level testing.** Verifies every MCP primitive works correctly.

When the user invokes `/mcp-test`, follow the guide in `references/basic-test-guide.md`. This command:

1. Asks the user for their MCP server URL (or detects it from context)
2. Starts the inspector in the background
3. Runs through every MCP primitive systematically
4. Reports pass/fail for each check
5. Cleans up the inspector process

Read `references/basic-test-guide.md` for the complete step-by-step procedure.

## Command: `/mcp-test-llm`

**End-to-end LLM-powered testing.** Uses a real LLM to generate business-relevant test scenarios and execute them against the MCP server with tool-use.

When the user invokes `/mcp-test-llm`, follow the guide in `references/llm-test-guide.md`. This command:

1. Asks the user for their MCP server URL
2. Asks for an LLM API key (OpenAI, Anthropic, Google, or OpenRouter)
3. Optionally saves credentials to `.env`
4. Discovers all tools and their schemas
5. Generates business-relevant test cases based on what the tools actually do
6. Executes each test case through the LLM chat endpoint
7. Validates tool calls were made and results are sensible
8. Reports comprehensive results

Read `references/llm-test-guide.md` for the complete step-by-step procedure.
Read `references/providers.md` for LLM provider configuration details (including OpenRouter).

## Reference files

| File | When to read |
|------|-------------|
| `references/basic-test-guide.md` | When running `/mcp-test` |
| `references/llm-test-guide.md` | When running `/mcp-test-llm` |
| `references/inspector-api.md` | Full API reference for the inspector (both commands use this) |
| `references/providers.md` | LLM provider setup including OpenRouter, base URL overrides |
| `references/troubleshooting.md` | When something fails and you need to debug |
| `references/business-cases.md` | How to generate realistic business test cases from tool schemas |

## Important conventions

- Always use `--no-open` when starting the inspector (agents don't need browsers)
- Always disable telemetry: `MCP_USE_ANONYMIZED_TELEMETRY=false`
- Always clean up the inspector process when done (`kill $INSPECTOR_PID`)
- Use the `crash` thinking tool to structure your reasoning at each testing phase
- Report results as a clear pass/fail table, not walls of JSON
- If a test fails, dig into why before moving on — read error messages, check schemas, retry with different inputs
