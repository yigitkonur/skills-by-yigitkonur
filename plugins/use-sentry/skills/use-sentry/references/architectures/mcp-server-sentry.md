# Architecture: Model Context Protocol (MCP) Server Sentry Integration

How to instrument MCP servers (stdio & SSE / HTTP transports) with Sentry while strictly preventing protocol corruption and redacting LLM tokens.

> [!NOTE]
> For connecting AI coding assistants (Antigravity, Cursor, Claude Code) to Sentry's hosted remote MCP server (`mcp.sentry.dev`), see [sentry-mcp-integration.md](file:///Users/mac/dev/skills-by-yigitkonur/skills/use-sentry/references/architectures/sentry-mcp-integration.md).

## The Critical Stdio Constraint

In an MCP server using `stdio` transport:
```
LLM Client <--- JSON-RPC via stdin/stdout ---> MCP Server
```
- **RULE 1: NEVER write anything to `stdout` except valid JSON-RPC frames.**
- If Sentry's `debug: true`, internal logger, or an unhandled `console.log` writes to `stdout`, the client's JSON parser crashes instantly, disconnecting the MCP server.
- Sentry MUST be configured with `debug: false`, and any internal error logging MUST use `process.stderr.write()`.

## 1. Native Auto-Instrumentation (Modern Sentry SDK)

In `@sentry/node` (v9.46.0+ / v11.1.0+), Sentry automatically instruments `@modelcontextprotocol/sdk` (`McpServer`).

```typescript
import * as Sentry from '@sentry/node';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: false, // CRITICAL: Protect stdio JSON-RPC transport
  tracesSampleRate: 1.0,
  beforeSend(event) {
    if (event.extra?.arguments) {
      event.extra.arguments = redactMcpArguments(event.extra.arguments);
    }
    return event;
  },
});

Sentry.setTag('component', 'mcp-server');
Sentry.setTag('transport', 'stdio');

const server = new McpServer({
  name: 'my-mcp-server',
  version: '1.0.0',
});

// Sentry automatically wraps registered tools with spans and captures unhandled exceptions
```

## 2. Explicit Tool Wrapping (Fallback / Custom Telemetry)

If you need custom metrics, tags, or manual span boundaries:

```typescript
export async function executeMcpTool<T>(
  toolName: string,
  args: Record<string, any>,
  handler: () => Promise<T>
): Promise<T> {
  // 1. Record tool invocation breadcrumb
  Sentry.addBreadcrumb({
    category: 'mcp.tool_call',
    message: `Executing tool: ${toolName}`,
    level: 'info',
    data: {
      tool: toolName,
      argKeys: Object.keys(args || {}),
    },
  });

  // 2. Wrap execution in Sentry span
  return Sentry.startSpan(
    {
      name: `mcp.tool.${toolName}`,
      op: 'mcp.tool',
      attributes: {
        'mcp.tool.name': toolName,
      },
    },
    async (span) => {
      try {
        const result = await handler();
        span.setStatus({ code: 1 }); // OK
        return result;
      } catch (error: any) {
        span.setStatus({ code: 2, message: error.message }); // ERROR

        // Capture exception with tool context
        Sentry.withScope((scope) => {
          scope.setTag('mcp_tool', toolName);
          scope.setExtra('tool_arguments', redactMcpArguments(args));
          Sentry.captureException(error);
        });

        throw error;
      }
    }
  );
}
```

## 3. Redacting Prompt Tokens & Model Payloads

```typescript
function redactMcpArguments(args: any): any {
  if (!args || typeof args !== 'object') return args;

  const sanitized: Record<string, any> = { ...args };
  const sensitiveKeys = ['apikey', 'token', 'authorization', 'password', 'secret', 'jwt'];

  for (const key of Object.keys(sanitized)) {
    if (sensitiveKeys.some((s) => key.toLowerCase().includes(s))) {
      sanitized[key] = '[Filtered]';
    } else if (typeof sanitized[key] === 'string' && sanitized[key].length > 1000) {
      // Truncate massive prompt strings to avoid burning Sentry event quotas
      sanitized[key] = sanitized[key].slice(0, 500) + '... [Truncated Prompt]';
    }
  }

  return sanitized;
}
```
