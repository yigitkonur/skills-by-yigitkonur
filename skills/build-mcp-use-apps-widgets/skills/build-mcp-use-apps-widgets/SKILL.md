---
name: build-mcp-use-apps-widgets
description: Use skill if you are routed through the deprecated mcp-use widget skill path and should switch to build-mcp-use-server.
---

# Deprecated: Build MCP Use Apps Widgets

This skill is a compatibility shim for the former `build-mcp-use-apps-widgets` install path.

Prefer `build-mcp-use-server` when it is installed. Its `18-mcp-apps/` references now own MCP Apps widgets, ChatGPT Apps compatibility, `useWidget`, `useCallTool`, streaming tool props, CSP, widget recipes, and widget anti-patterns.

If this deprecated skill is installed alone, do not dead-end. Use the local fallback below.

## Standalone Fallback

When building mcp-use widgets from this shim:

1. Register widgets with `server.uiResource({ type: "mcpApps", ... })` for new code.
2. Return widget tool results with `widget({ props, output, metadata })`; do not hand-roll `structuredContent` and `_meta`.
3. Wrap React widgets in `<McpUseProvider autoSize>`.
4. Read host-delivered data with `useWidget()`; treat `props` as partial while `isPending`.
5. Call server tools from widgets with `useCallTool(name)` or `useWidget().callTool`; do not `fetch("/mcp")` from the iframe.
6. Put public widget data in `props`, model-visible text in `output` or `message`, and private non-secret UI hydration in `metadata`.
7. Declare external origins in widget CSP metadata: `connectDomains` for APIs/WebSockets, `resourceDomains` for scripts/styles/images/fonts, `frameDomains` for iframes, and `baseUriDomains` for `<base href>`.
8. Keep a text fallback for clients that do not support widgets.

## Minimal Server Pattern

```typescript
import { MCPServer, text, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "widget-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.uiResource({
  type: "mcpApps",
  name: "status-widget",
  htmlTemplate: `
    <!doctype html>
    <html>
      <body>
        <div id="root"></div>
        <script type="module" src="/resources/status-widget.js"></script>
      </body>
    </html>
  `,
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],
      resourceDomains: ["https://cdn.example.com"],
    },
    autoResize: true,
    prefersBorder: true,
  },
});

server.tool(
  {
    name: "show_status",
    description: "Show current service status",
    schema: z.object({ service: z.string() }),
  },
  async ({ service }) =>
    widget({
      props: { service, status: "ok" },
      output: text(`${service} is ok`),
    })
);

await server.listen(3000);
```

## Minimal React Widget Pattern

```tsx
import { McpUseProvider, useCallTool, useWidget } from "mcp-use/react";

type StatusProps = { service: string; status: string };

function StatusWidget() {
  const { props, isPending } = useWidget<StatusProps>();
  const refresh = useCallTool("show_status");

  if (isPending) return <div>Loading...</div>;

  return (
    <section>
      <strong>{props.service}</strong>
      <span>{props.status}</span>
      <button onClick={() => refresh.callTool({ service: props.service })}>
        Refresh
      </button>
    </section>
  );
}

export default function App() {
  return (
    <McpUseProvider autoSize>
      <StatusWidget />
    </McpUseProvider>
  );
}
```

## Migration Note

For complete guidance, install the replacement skill:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-server
```
