# Architecture: Model Context Protocol (MCP) Server Sentry Integration

How to instrument MCP servers (stdio & Streamable HTTP / SSE transports) with Sentry while strictly preventing protocol corruption and redacting LLM tokens.

> [!NOTE]
> For connecting AI coding assistants (Claude Code, Antigravity, Cursor) to Sentry's hosted remote MCP server (`mcp.sentry.dev`) or local stdio (`sentry mcp`), see [sentry-mcp-integration.md](file:///Users/mac/dev/skills-by-yigitkonur/skills/use-sentry/references/architectures/sentry-mcp-integration.md).

## The Critical Stdio Constraint

In an MCP server using `stdio` transport:
```
LLM Client <--- JSON-RPC via stdin/stdout ---> MCP Server
```
- **RULE 1: NEVER write anything to `stdout` except valid JSON-RPC frames.**
- If Sentry's `debug: true`, internal loggers, or an unhandled `console.log` writes to `stdout`, the client's JSON parser crashes instantly, disconnecting the MCP server.
- Sentry MUST be configured with `debug: false`, and any internal error logging MUST use `process.stderr.write()`.

## 1. Native Auto-Instrumentation (Modern Sentry SDK)

Modern Sentry SDKs (`@sentry/node`, `@sentry/cloudflare`, `@sentry/bun`) provide native auto-instrumentation for both `@modelcontextprotocol/server` (v2 API) and legacy `@modelcontextprotocol/sdk` (v1 API).

```typescript
import * as Sentry from '@sentry/node';
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio.js';
import { z } from 'zod';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: false, // CRITICAL: Protect stdio JSON-RPC transport
  tracesSampleRate: 1.0,
  integrations: [
    Sentry.mcpServerIntegration({
      recordInputs: true,  // Captures tool input arguments in span data
      recordOutputs: true, // Captures tool return data in span data
    }),
  ],
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
server.registerTool(
  'fetch_user_profile',
  { userId: z.string() },
  async ({ userId }) => {
    return {
      content: [{ type: 'text', text: JSON.stringify({ userId, role: 'admin' }) }],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
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

## 3. Token & Prompt Sanitization

```typescript
function redactMcpArguments(args: any): any {
  if (!args || typeof args !== 'object') return args;
  const sanitized: Record<string, any> = { ...args };
  const sensitiveKeys = ['apikey', 'token', 'authorization', 'password', 'secret', 'jwt'];

  for (const key of Object.keys(sanitized)) {
    if (sensitiveKeys.some((s) => key.toLowerCase().includes(s))) {
      sanitized[key] = '[Filtered]';
    } else if (typeof sanitized[key] === 'string' && sanitized[key].length > 1000) {
      sanitized[key] = sanitized[key].slice(0, 500) + '... [Truncated Payload]';
    }
  }
  return sanitized;
}
```
