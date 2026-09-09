# Architecture: Model Context Protocol (MCP) Server Sentry Integration

How to instrument MCP servers (stdio & SSE transports) with Sentry while strictly preventing protocol corruption and redacting LLM tokens.

## The Critical Stdio Constraint

In an MCP server using `stdio` transport:
```
LLM Client <--- JSON-RPC via stdin/stdout ---> MCP Server
```
- **RULE 1: NEVER write anything to `stdout` except valid JSON-RPC frames.**
- If Sentry's `debug: true`, internal logger, or an unhandled `console.log` writes to `stdout`, the client's JSON parser crashes instantly, disconnecting the MCP server.
- Sentry MUST be configured with `debug: false`, and any internal error logging MUST use `process.stderr.write()`.

## 1. Initializing Sentry in an MCP Server

```typescript
import * as Sentry from '@sentry/node';

export function initMcpSentry() {
  const dsn = process.env.SENTRY_DSN;
  if (!dsn || !dsn.trim()) return; // Zero-network offline no-op

  const projectId = dsn.trim().match(/\/(\d+)(?:$|[?#])/)?.[1];
  const tunnel = projectId ? `https://sentry.io/api/${projectId}/envelope/` : undefined;

  Sentry.init({
    dsn,
    tunnel, // Bypasses ISP DNS sinkholes
    debug: false, // CRITICAL: Never emit Sentry debug messages to stdout!
    tracesSampleRate: 1.0,
    beforeSend(event) {
      // Redact LLM prompt tokens and sensitive API keys in parameters
      if (event.extra?.arguments) {
        event.extra.arguments = redactMcpArguments(event.extra.arguments);
      }
      return event;
    },
  });

  Sentry.setTag('component', 'mcp-server');
  Sentry.setTag('transport', process.env.MCP_TRANSPORT || 'stdio');
}
```

## 2. Wrapping MCP Tool Handlers with Spans & Breadcrumbs

Wrap every `CallToolRequest` execution with structured spans and breadcrumbs:

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
  const sensitiveKeys = ['apiKey', 'token', 'authorization', 'password', 'secret', 'jwt'];

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
