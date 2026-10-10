# Architecture: Sentry Model Context Protocol (MCP) Integration

Two-way MCP architecture with Sentry:
1. **Consuming Sentry via MCP**: Connecting AI coding agents (Claude Code, Cursor, Antigravity, Windsurf) to Sentry's hosted remote MCP server (`mcp.sentry.dev`) or local stdio server (`sentry mcp`).
2. **Monitoring Custom MCP Servers**: Auto-instrumenting your own MCP servers using modern Sentry SDKs with strict stdio isolation.

---

## Part 1: Connecting AI Agents to Sentry via MCP

Sentry provides official Model Context Protocol (MCP) tooling hosted in [`getsentry/toolkit`](https://github.com/getsentry/toolkit). This gives AI coding assistants direct, tool-based access to unresolved issues, stack traces, breadcrumbs, correlated logs, and Seer AI root-cause analysis.

### 1. Claude Code Official Plugin (Recommended)

Sentry publishes an official Claude Code plugin in the marketplace that registers an autonomous `sentry-mcp` subagent:

```bash
# Add Sentry to marketplace and install
claude plugin marketplace add getsentry/sentry-mcp
claude plugin install sentry-mcp@sentry-mcp
```

*For forward-looking tool variants:*
```bash
claude plugin install sentry-mcp@sentry-mcp-experimental
```

When installed, Claude Code automatically routes debugging, crash inspection, and incident triage prompts directly to the `sentry-mcp` subagent.

### 2. Remote HTTP Endpoint (`https://mcp.sentry.dev/mcp`)

Sentry's remote MCP server runs on Cloudflare Workers and provides HTTP transport:

- **Universal Endpoint:** `https://mcp.sentry.dev/mcp`
- **Authentication:** RFC 9728 OAuth 2.0 or Sentry User Auth Token (`sntryu_...`).
- *(Note: The legacy `/sse` transport endpoint is deprecated in favor of `/mcp`).*

#### Cursor (`.cursor/mcp.json` or Global MCP Settings)
```json
{
  "mcpServers": {
    "sentry": {
      "url": "https://mcp.sentry.dev/mcp",
      "headers": {
        "Authorization": "Bearer sntryu_YOUR_USER_AUTH_TOKEN"
      }
    }
  }
}
```

### 3. Local Stdio Integration via Modern Sentry CLI

If you have the modern `sentry` binary installed (`cli.sentry.dev`), you do not need manual token management in client configs. The CLI launches an authenticated local stdio server directly:

```json
{
  "mcpServers": {
    "sentry": {
      "command": "sentry",
      "args": ["mcp"]
    }
  }
}
```

Authenticate once with `sentry auth login`, and any MCP client will reuse your active session.

#### Fallback via `@sentry/mcp-server`
```json
{
  "mcpServers": {
    "sentry": {
      "command": "npx",
      "args": [
        "-y",
        "@sentry/mcp-server@latest",
        "--access-token=sntryu_YOUR_USER_AUTH_TOKEN"
      ]
    }
  }
}
```

### 4. Verified Sentry MCP Tool Catalog

AI agents connected to Sentry MCP have access to the verified tool surface defined in [`packages/mcp-core/src/tools/catalog/`](https://github.com/getsentry/toolkit/tree/main/packages/mcp-core/src/tools/catalog):

| Tool Name | Purpose |
|---|---|
| `search_issues` | Search unresolved or resolved issues with Sentry search syntax (`is:unresolved`, `age:-24h`) |
| `search_errors` | Search individual error occurrences across projects |
| `get_issue_details` | Inspect issue title, culprit, frequency, first/last seen, and tag breakdown |
| `get_event_stacktrace` | Fetch complete in-app stack traces, source context, and frame variables |
| `get_issue_breadcrumbs` | Fetch chronological user actions, HTTP requests, console logs, and system breadcrumbs |
| `get_trace_details` / `get_span_details` | Inspect distributed trace waterfalls, span latencies, and service boundaries |
| `search_traces` | Query distributed traces by duration, status, or tag |
| `search_logs` | Query correlated structured logs by `traceId` or timestamp |
| `analyze_issue_with_seer` | Trigger Ser AI root cause analysis and code remediation suggestions |
| `search_replays` / `get_replay_details` | Search and inspect frontend Session Replay recordings |
| `search_profiles` / `get_profile_details` | Query and inspect CPU flamegraphs and line-level bottlenecks |
| `search_docs` / `get_doc` | Query official Sentry SDK and platform documentation |
| `find_projects` / `whoami` | Identify active organizations, projects, and caller credentials |
| `search_sentry_tools` / `execute_sentry_tool` | Dynamic catalog discovery and execution for extended administrative tools |

---

## Part 2: Monitoring Your Custom MCP Server

When developing custom MCP servers, Sentry provides automated instrumentation with strict transport protection.

### The Stdio Transport Law

```
LLM Client <--- JSON-RPC via stdin/stdout ---> MCP Server
```
- **RULE 1: NEVER write anything to `stdout` except valid JSON-RPC frames.**
- If Sentry's `debug: true`, internal loggers, or `console.log` writes to `stdout`, the client's JSON parser crashes instantly, breaking the MCP connection.
- Sentry MUST be initialized with `debug: false`, and any debug logging must target `process.stderr`.

### TypeScript / Node.js Instrumentation

Modern Sentry SDKs auto-instrument both modern `@modelcontextprotocol/server` (v2 API) and legacy `@modelcontextprotocol/sdk` (v1 API):

```typescript
import * as Sentry from '@sentry/node';
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio.js';
import { z } from 'zod';

// 1. Initialize Sentry before transports
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: false, // CRITICAL: Protect stdio transport from non-JSON stdout
  tracesSampleRate: 1.0,
  integrations: [
    // Automatically instruments registered tools, resources, and prompts
    Sentry.mcpServerIntegration({
      recordInputs: true,  // Captures tool argument inputs in spans
      recordOutputs: true, // Captures tool response outputs in spans
    }),
  ],
  beforeSend(event) {
    // Redact sensitive credentials in arguments
    if (event.extra?.arguments) {
      event.extra.arguments = redactMcpArguments(event.extra.arguments);
    }
    return event;
  },
});

Sentry.setTag('component', 'mcp-server');
Sentry.setTag('transport', 'stdio');

// 2. Create MCP server
const server = new McpServer({
  name: 'custom-tools',
  version: '1.0.0',
});

// Tool executions are automatically wrapped with Sentry spans and exception traps
server.registerTool(
  'calculate_tax',
  { amount: z.number() },
  async ({ amount }) => {
    return {
      content: [{ type: 'text', text: `Tax: ${amount * 0.2}` }],
    };
  }
);

// 3. Connect Stdio transport
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Python MCP Server Instrumentation

```python
import os
import sentry_sdk
from mcp.server.fastmcp import FastMCP

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    debug=False, # Protect stdio transport
)

mcp = FastMCP("demo-server")

@mcp.tool()
def calculate_metrics(data: list[float]) -> float:
    return sum(data) / len(data)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Argument Sanitization Helper

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
