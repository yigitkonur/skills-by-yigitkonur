# agent-web-interface

`agent-web-interface` is a browser automation MCP server built for LLM agents. Instead of exposing raw DOMs or full accessibility trees, it produces **semantic page snapshots** — compact, structured representations focused on user-visible intent, optimized for LLM recall and reasoning.

## Repository

github.com/lespaceman/agent-web-interface

## Key Features

- Pages reduced to semantic regions and actionable elements
- Actions resolved against stable semantic identifiers (not fragile CSS selectors)
- Snapshots are deterministic and low-entropy across layout shifts and DOM churn
- ~19% fewer tokens and ~33% faster task completion vs. Playwright MCP (benchmarks are task-dependent)

## Configuration in a Plugin

Add to your plugin's `.mcp.json`:

```json
{
  "mcpServers": {
    "agent-web-interface": {
      "command": "npx",
      "args": ["agent-web-interface@latest"],
      "env": {
        "AWI_CDP_URL": "http://localhost:9222"
      }
    }
  }
}
```

## CLI Arguments

The server accepts transport-level arguments only. Browser configuration is per-session via the `navigate` tool.

| Argument | Description | Default |
|----------|-------------|---------|
| `--transport` | Transport mode: `stdio` or `http` | `stdio` |
| `--port` | Port for HTTP transport | `3000` |

## Browser Session Configuration

The browser launches automatically on the first tool call. The `navigate` tool accepts optional parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `headless` | Run browser in headless mode | `false` |
| `isolated` | Use an isolated temp profile | `false` |
| `auto_connect` | Auto-connect to Chrome 144+ via DevToolsActivePort | `false` |

## Using Your Existing Chrome Profile (Chrome 144+)

1. Navigate to `chrome://inspect/#remote-debugging` in Chrome
2. Enable remote debugging and allow the connection
3. Use the `auto_connect` parameter on the `navigate` tool, or set `AWI_CDP_URL`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWI_CDP_URL` | CDP endpoint (http or ws) to connect to existing browser | — |
| `AWI_TRIM_REGIONS` | Set to `false` to disable region trimming | `true` |
| `CHROME_PATH` | Path to Chrome executable | — |
| `LOG_LEVEL` | Logging level | `info` |

## How It's Used in Athena

The `e2e-test-builder` workflow uses `agent-web-interface` through a plugin MCP configuration. Skills like `/explore-website` use the browser to:

1. Navigate to the target URL
2. Take semantic snapshots of each page
3. Extract stable selectors and interaction patterns
4. Feed this information into test generation skills

This allows the agent to understand page structure without relying on fragile CSS selectors or XPath queries.

## Semantic Snapshots vs Raw DOM

Traditional browser automation tools (like Playwright MCP) expose the full DOM or accessibility tree. This is:
- Token-expensive (thousands of DOM nodes)
- Fragile (selectors break on layout changes)
- Noisy (invisible elements, styling artifacts)

Semantic snapshots instead provide:
- Compact region-based page structure
- Actionable elements with stable identifiers
- Intent-focused descriptions
- Deterministic output across page variations
