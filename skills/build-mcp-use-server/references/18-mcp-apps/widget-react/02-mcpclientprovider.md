# `<McpClientProvider>` — Widget-Owned MCP Client Connections

Use only when the widget itself opens its own MCP client connections to other servers (multi-server consoles, MCP-aware UIs). Most widgets do **not** need this — `useWidget().callTool` already routes through the host's MCP connection.

```tsx
import { McpClientProvider, LocalStorageProvider } from "mcp-use/react";

<McpClientProvider
  mcpServers={{
    linear: { url: "https://mcp.linear.app/sse" },
    github: { url: "https://mcp.github.com/mcp" },
  }}
  storageProvider={new LocalStorageProvider("my-servers")}
  enableRpcLogging={true}
>
  <App />
</McpClientProvider>
```

## When you actually need this

| Scenario | Use `McpClientProvider`? |
|---|---|
| Tool widget that calls back into its own server | No — use `callTool` from `useWidget` |
| Widget that calls a single arbitrary MCP server | No — use `useMcp({ url })` |
| Widget that connects to N user-configured MCP servers (a console, dashboard, switcher) | Yes |
| Widget that needs persistence of connection auth across reloads | Yes (with `storageProvider`) |

## Composition with `<McpUseProvider>`

`McpUseProvider` wraps the widget with the common shell. `McpClientProvider` wraps the part of the tree that needs multi-server access. Order is `McpUseProvider` outside, `McpClientProvider` inside:

```tsx
<McpUseProvider autoSize>
  <McpClientProvider mcpServers={{ linear: { url: "..." } }}>
    <ServerSwitcher />
  </McpClientProvider>
</McpUseProvider>
```

## Companion hooks

| Hook | Purpose |
|---|---|
| `useMcpClient()` | Access `servers`, `addServer`, `removeServer`, `updateServer`, `updateServerMetadata`, `getServer`, and `storageLoaded`. |
| `useMcpServer(id)` | Get a single server by id. Returns `undefined` if missing. Throws if used outside the provider. |
| `useMcp({ url })` | Single-server connection — alternative when you have one fixed server. |

## Default position

Most widgets should not include `McpClientProvider`. If you reach for it, justify why `useWidget().callTool` is insufficient — almost always the answer is that you are addressing a server other than the one rendering the widget.
