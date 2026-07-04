# Workflow: Multi-Server Hub with Audit Logging

**Goal:** front several upstream MCP servers behind a single endpoint and log every proxied tool call. Combine `server.proxy()` with two layers of middleware — Hono `server.use(...)` for HTTP request logging, and `server.use("mcp:tools/call", ...)` for MCP-protocol-level audit. Surface the audit log to clients via a hub-only tool. Modeled on `mcp-use/mcp-multi-server-hub`.

## Prerequisites

- mcp-use 1.26.0 or newer (`proxy()` is async and must be awaited).

## Layout

```
multi-server-hub/
├── package.json
├── index.ts
└── resources/
    └── hub-dashboard/
        └── widget.tsx
```

## `index.ts`

```typescript
import { MCPServer, text, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "multi-server-hub",
  version: "1.0.0",
  description: "Compose multiple MCP servers with audit logging",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

// ── HTTP middleware: request log ────────────────────────────────────────────

server.use(async (c, next) => {
  const start = Date.now();
  console.log(`→ ${c.req.method} ${c.req.url}`);
  await next();
  console.log(`← ${c.req.method} ${c.req.url} [${Date.now() - start}ms]`);
});

// ── MCP-operation middleware: audit every tools/call (proxied or local) ────

interface AuditEntry {
  tool: string;
  timestamp: string;
  duration: number;
}
const auditLog: AuditEntry[] = [];

server.use("mcp:tools/call", async (ctx, next) => {
  const start = Date.now();
  const result = await next();
  const entry: AuditEntry = {
    tool: ctx.params.name,
    timestamp: new Date().toISOString(),
    duration: Date.now() - start,
  };
  auditLog.push(entry);
  return result;
});

// ── Proxy upstream MCP servers ─────────────────────────────────────────────
// Configure via env or hard-coded here. Empty PROXY_CONFIG = local-only mode.

const PROXY_CONFIG: Record<string, { url?: string; command?: string; args?: string[] }> = {
  // weather: { url: "https://weather-mcp.example.com/mcp" },
  // calculator: { command: "node", args: ["./calc.js"] },
};

if (Object.keys(PROXY_CONFIG).length > 0) {
  await server.proxy(PROXY_CONFIG); // MUST be awaited (v1.21.0+)
}

// ── Hub-local tools ────────────────────────────────────────────────────────

server.tool(
  {
    name: "hub-status",
    description: "Show proxied servers and recent audit entries",
    schema: z.object({}),
    widget: { name: "hub-dashboard", invoking: "Loading…", invoked: "Ready" },
  },
  async () => {
    const proxiedServers = Object.keys(PROXY_CONFIG).map((name) => ({
      name,
      type: PROXY_CONFIG[name].url ? "http" : "stdio",
      url: PROXY_CONFIG[name].url ?? `stdio:${PROXY_CONFIG[name].command}`,
    }));
    return widget({
      props: {
        proxiedServers,
        auditLog: auditLog.slice(-20),
        totalCalls: auditLog.length,
      },
      output: text(
        `${proxiedServers.length} proxied servers; ${auditLog.length} total calls`
      ),
    });
  }
);

server.tool(
  {
    name: "hub-config-example",
    description: "Show example configuration for proxy servers",
    schema: z.object({}),
  },
  async () => text(
    `HTTP: weather: { url: "https://weather-mcp.example.com/mcp" }\n` +
      `STDIO: calculator: { command: "node", args: ["./calc-server.js"] }`
  )
);

server.tool(
  {
    name: "audit-log",
    description: "Show the recent audit log entries",
    schema: z.object({
      limit: z.number().int().min(1).max(100).default(10),
    }),
  },
  async ({ limit }) => {
    const entries = auditLog.slice(-limit);
    if (entries.length === 0) return text("(no calls recorded yet)");
    return text(
      entries
        .map((e) => `${e.timestamp}  ${e.tool}  ${e.duration}ms`)
        .join("\n")
    );
  }
);

server.listen().then(() => console.log("Multi-Server Hub running"));
```

## `resources/hub-dashboard/widget.tsx`

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

interface AuditEntry {
  tool: string;
  timestamp: string;
  duration: number;
}

interface Props {
  proxiedServers: { name: string; type: string; url: string }[];
  auditLog: AuditEntry[];
  totalCalls: number;
}

export const widgetMetadata: WidgetMetadata = {
  description: "Hub dashboard — proxied servers and audit log",
  props: z.object({
    proxiedServers: z.array(z.object({ name: z.string(), type: z.string(), url: z.string() })),
    auditLog: z.array(
      z.object({ tool: z.string(), timestamp: z.string(), duration: z.number() })
    ),
    totalCalls: z.number(),
  }),
  metadata: { prefersBorder: true },
};

function Inner() {
  const { props } = useWidget<Props>();
  return (
    <div className="p-4 bg-white dark:bg-gray-950 space-y-4">
      <section>
        <h2 className="text-sm font-semibold mb-2">
          Proxied servers ({props.proxiedServers.length})
        </h2>
        {props.proxiedServers.length === 0 ? (
          <p className="text-xs text-gray-500">No proxies configured.</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {props.proxiedServers.map((p) => (
              <li key={p.name} className="flex justify-between">
                <span className="font-mono">{p.name}</span>
                <span className="text-gray-500">{p.type} · {p.url}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section>
        <h2 className="text-sm font-semibold mb-2">
          Recent calls ({props.totalCalls} total)
        </h2>
        <ul className="space-y-1 text-xs font-mono">
          {props.auditLog.map((e, i) => (
            <li key={i} className="flex justify-between">
              <span className="text-blue-500">{e.tool}</span>
              <span className="text-gray-400">{e.duration}ms</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export default function HubDashboard() {
  return (
    <McpUseProvider autoSize>
      <Inner />
    </McpUseProvider>
  );
}
```

## Run

```bash
npm install && npm run dev
```

## Pattern recap

- `server.use(handler)` runs in the Hono HTTP pipeline.
- `server.use("mcp:tools/call", handler)` sees the meaningful MCP operation: tool name, arguments, duration.
- `await server.proxy(PROXY_CONFIG)` must finish before `listen()` so proxied tools are registered.
- The in-process `auditLog` is volatile; persist entries to Postgres or an SIEM in production.

## See also

- Canonical: `../31-canonical-examples/07-mcp-multi-server-hub.md`
- Plain proxy gateway (no audit): `06-multi-server-proxy-gateway.md`
- Hono routes alongside MCP: `../17-advanced/`
