# Architecture: Sentry Model Context Protocol (MCP) Integration

Two-way MCP architecture with Sentry:
1. **Consuming Sentry via MCP**: Connecting AI coding agents (Antigravity, Cursor, Claude Code, Windsurf) to Sentry's hosted remote MCP server (`mcp.sentry.dev`).
2. **Monitoring MCP Servers**: Auto-instrumenting your own custom MCP servers using modern Sentry SDKs with stdio isolation.

---

## Part 1: Connecting AI Agents to Sentry via MCP (`mcp.sentry.dev`)

Sentry provides an official hosted Model Context Protocol (MCP) server powered by [`getsentry/sentry-mcp`](https://github.com/getsentry/sentry-mcp). This allows AI agents to directly triage issues, inspect stack traces, fetch correlated logs, and read Seer AI root cause analyses.

### 1. Hosted Endpoints & Scoping

- **Organization-level:** `https://mcp.sentry.dev/mcp/<org_slug>`
- **Project-level:** `https://mcp.sentry.dev/mcp/<org_slug>/<project_slug>`
- **Global:** `https://mcp.sentry.dev/mcp`

### 2. Client Configurations

#### Cursor (`.cursor/mcp.json` or Global Cursor Settings)
```json
{
  "mcpServers": {
    "sentry": {
      "url": "https://mcp.sentry.dev/mcp/my-org/my-project",
      "headers": {
        "Authorization": "Bearer sntryu_YOUR_USER_AUTH_TOKEN"
      }
    }
  }
}
```

#### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "sentry": {
      "command": "npx",
      "args": [
        "-y",
        "@sentry/mcp-server",
        "--auth-token",
        "sntryu_YOUR_USER_AUTH_TOKEN",
        "--org",
        "my-org",
        "--project",
        "my-project"
      ]
    }
  }
}
```

#### Antigravity CLI / IDE (`~/.gemini/antigravity-cli/mcp/sentry.json`)
```json
{
  "command": "npx",
  "args": ["-y", "@sentry/mcp-server"],
  "env": {
    "SENTRY_AUTH_TOKEN": "sntryu_YOUR_USER_AUTH_TOKEN",
    "SENTRY_ORG": "my-org",
    "SENTRY_PROJECT": "my-project"
  }
}
```

### 3. Capabilities Provided by Sentry MCP

AI agents connected to Sentry's MCP server can autonomously invoke tools:
- `find_issues`: Search issues by status, query, or frequency (`is:unresolved`, `lastSeen:-24h`).
- `get_issue`: Inspect stack traces, culprit lines, and tag distributions.
- `get_issue_traces`: Fetch distributed trace trees and span waterfalls.
- `explain_issue`: Trigger Seer AI root-cause analysis.
- `search_logs`: Search correlated structured logs by `traceId` or timestamp.

---

## Part 2: Monitoring Your Custom MCP Server

When developing your own MCP servers (using `@modelcontextprotocol/sdk` in TypeScript or `mcp` in Python), modern Sentry SDKs provide out-of-the-box auto-instrumentation.

### The Stdio Transport Law

```
LLM Client <--- JSON-RPC via stdin/stdout ---> MCP Server
```
- **RULE 1: NEVER write anything to `stdout` except valid JSON-RPC frames.**
- If Sentry's `debug: true`, internal loggers, or `console.log` writes to `stdout`, the client's JSON parser crashes instantly, killing the MCP server connection.
- Sentry MUST be initialized with `debug: false`, and any debug logging must target `process.stderr`.

### TypeScript / Node.js Auto-Instrumentation

Modern Sentry Node SDK (v9.46.0+ / v11.1.0+) automatically detects `@modelcontextprotocol/sdk` and instruments `McpServer` without manual wrapper boilerplate:

```typescript
import * as Sentry from '@sentry/node';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

// 1. Initialize Sentry before importing or initializing transports
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: false, // CRITICAL: Never emit Sentry debug messages to stdout!
  tracesSampleRate: 1.0,
  beforeSend(event) {
    // Redact sensitive API keys or large prompt payloads
    if (event.extra?.arguments) {
      event.extra.arguments = redactMcpArguments(event.extra.arguments);
    }
    return event;
  },
});

Sentry.setTag('component', 'mcp-server');
Sentry.setTag('transport', 'stdio');

// 2. Create standard MCP server — Sentry automatically instruments tool spans
const server = new McpServer({
  name: 'my-agent-tools',
  version: '1.0.0',
});

// Tool calls are automatically wrapped with Sentry spans and exception traps
server.tool(
  'fetch_user_record',
  { userId: z.string() },
  async ({ userId }) => {
    // Context is automatically bound to the active tool span
    return {
      content: [{ type: 'text', text: JSON.stringify({ userId, status: 'active' }) }],
    };
  }
);

// 3. Connect via Stdio
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Python MCP Server Instrumentation

In Python with `mcp` and `sentry-sdk`:

```python
import os
import sentry_sdk
from mcp.server.fastmcp import FastMCP

# Initialize Sentry with MCP integration
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    debug=False, # Protect stdio transport
)

mcp = FastMCP("demo-server")

@mcp.tool()
def calculate_metrics(data: list[float]) -> float:
    # Sentry automatically instruments FastMCP tool executions
    return sum(data) / len(data)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Payload Sanitization Helper

```typescript
function redactMcpArguments(args: any): any {
  if (!args || typeof args !== 'object') return args;
  const sanitized: Record<string, any> = { ...args };
  const sensitiveKeys = ['apikey', 'token', 'authorization', 'password', 'secret', 'jwt'];

  for (const key of Object.keys(sanitized)) {
    if (sensitiveKeys.some((s) => key.toLowerCase().includes(s))) {
      sanitized[key] = '[Filtered]';
    } else if (typeof sanitized[key] === 'string' && sanitized[key].length > 1000) {
      sanitized[key] = sanitized[key].slice(0, 500) + '... [Truncated Prompt]';
    }
  }
  return sanitized;
}
```
