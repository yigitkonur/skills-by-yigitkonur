# Integration and Add to Client

*Read this when mounting the Inspector in your own app, or when copying setup commands for ChatGPT, Claude Desktop, and other clients.*

## Auto-mounted in mcp-use

When using an mcp-use project, the Inspector is built-in development tooling — no extra dependency needed.

```bash
npm run dev
```

The CLI loads the Inspector supplied by `mcp-use`, serves its bundled UI locally at `http://localhost:3000/mcp/inspector`, and opens it in your browser. The Inspector is pre-configured to connect to your local server at `http://localhost:3000/mcp`.

For headless dev runs, use:

```bash
mcp-use dev --no-inspector
```

### Production

By default, production builds do not include the Inspector. To serve it on your production build's listener, opt in:

```bash
mcp-use build
mcp-use start --with-inspector
```

This does not change the build output or its manifest — the Inspector stays an internal tool.

## Manual integration with `mountInspector()`

For custom development servers, `mountInspector()` from `@mcp-use/inspector` provides the complete local Inspector (packaged UI, proxy, OAuth BFF, and callbacks). It can register on Hono/Express or return a framework-neutral Fetch handler.

### Hono example

```typescript
import { Hono } from "hono";
import { mountInspector } from "@mcp-use/inspector";

const app = new Hono();

// Your routes
app.get("/api/health", (c) => {
  return c.json({ status: "ok" });
});

// Mount inspector at /mcp/inspector
mountInspector(app, { basePath: "/mcp" });

export default app;
```

### Configuration options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `basePath` | string | `'/mcp'` | MCP prefix; Inspector mounts at `${basePath}/inspector` |
| `autoConnectUrl` | string \| null | Current origin + basePath | MCP server URL to auto-connect; `null` disables |
| `devMode` | boolean | `true` | Enables same-origin sandbox for MCP Apps widgets |
| `sandboxOrigin` | string \| null | undefined | Override sandbox origin for MCP Apps widgets |
| `oauthProxyAllowLoopback` | boolean | `true` | Permit local proxy/OAuth to loopback targets |

Each mounted Inspector enforces process-local rate limits: 120 proxy/OAuth requests and 600 asset requests per minute. Exhausted routes return `429 Too Many Requests` with `Retry-After`.

## Add to Client

After connecting a server, the Inspector provides **Add to Client** setup actions for supported clients (Claude Desktop, Cursor, VS Code, Claude Code, Gemini CLI, Codex CLI).

### Workflow

1. Open the **Add to Client** dropdown (top of the server panel).
2. Choose your client.
3. Follow the action (open a deep link, copy a command, or download a configuration file).

The Inspector uses the active connection settings when it prepares the client setup. Confirm the server URL and connection name before completing the action.

### Security note

The Inspector can call tools, read resources, and inspect prompts on any connected server. If you expose it on a network, keep it in local development only. Disable loopback proxying and put it behind the same access controls as other internal tools.
