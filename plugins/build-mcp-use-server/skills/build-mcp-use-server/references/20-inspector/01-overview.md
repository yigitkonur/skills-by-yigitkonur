# Inspector Overview

The MCP Inspector is a browser-based testing UI for MCP servers. Connect to one or many servers, exercise tools, browse resources and prompts, run a chat session against a connected LLM, and observe raw JSON-RPC traffic — all without writing a client.

## Hosted vs self-hosted vs auto-mounted

| Form | URL | When to use |
|---|---|---|
| Hosted | `https://inspector.mcp-use.com/` | Quick-start, no install. Connect to any reachable MCP server URL. |
| CLI | `npx @mcp-use/inspector` | Local one-shot debugging. Auto-opens browser. See `02-cli.md`. |
| Auto-mounted (mcp-use) | `http://localhost:<port>/inspector` | Default when running `mcp-use dev` or `MCPServer.listen()`. See `08-integration.md`. |
| Self-hosted (Docker) | `http://your-host:8080/` | Air-gapped, enterprise, custom domain. See `10-self-hosting.md`. |

All four are the same UI built from the same package; the running mode controls only how it is served.

## Dashboard

The dashboard is the entry view. Two panes:

- **Connected Servers** (left) — saved connections with status indicator (green / yellow / red / gray). Buttons per server: Inspect, Disconnect, Remove.
- **Connect** (right) — form for new connections: transport, URL, connection type, authentication, custom headers.

Connections are saved to browser `localStorage` and auto-reconnect on reload. **Clear All** wipes them.

## Server Detail View

Click **Inspect** on a connected server to open its tabbed view. Tabs:

| Tab | Purpose |
|---|---|
| Tools | List, inspect schema, execute tools. Save executions as named saved requests. |
| Resources | Browse static and template resources. Read content. |
| Prompts | List prompts, fill argument templates, render. |
| Chat | BYOK LLM chat (Anthropic / OpenAI / Google) with tool-calling visualization. |
| Sampling | Test server-initiated sampling requests. |
| Elicitation | Render and respond to server-initiated input requests (SEP-1330). |
| Notifications | Stream of server notifications. |
| Playground | Free-form raw JSON-RPC sandbox. |

The active tab is reflected in the URL as `?tab=…`, so refreshes and shared links restore the view. Server display names are editable from the connection form and update labels everywhere without disconnecting.

## Key features

- **Multi-server**: connect to many MCP servers simultaneously.
- **OAuth**: full flow with single-tab redirect, popup fallback, secure token storage.
- **Saved Requests**: persist tool calls with arguments for replay.
- **Command Palette** (`Cmd/Ctrl+K`): fuzzy-search tools, prompts, resources, saved requests, servers, "Open in Client" actions, docs links. See `06-command-palette.md`.
- **RPC Logging**: bottom-of-sidebar panel that streams every JSON-RPC frame with direction, method, timestamp, and expandable payload. See `07-rpc-logging.md`.
- **Add to Client**: header button that hands the current server config to Cursor / VS Code / Claude Desktop / Claude Code / Gemini CLI / Codex CLI via deep link, `.mcpb` file, or copied CLI command.
- **OpenAI Apps SDK**: full widget rendering with `window.openai` emulation. See `09-debugging-chatgpt-apps.md`.
- **Embedded mode**: render the inspector inside an iframe with reduced chrome via `?embedded=true`. See `04-url-parameters.md`.
- **Persistency**: connections, headers, OAuth tokens, request timeouts, saved requests, console-proxy preference — all in `localStorage`.

## Connection types

- **Direct** — browser talks directly to the MCP endpoint. Default. Use for local dev and public endpoints.
- **Via Proxy** — traffic routed through `/inspector/api/proxy`. Use behind corporate proxies or when CORS blocks direct.
- **Auto-Switch** — try Direct first, fall back to Via Proxy automatically.

Detail in `03-connection-settings.md`.

## When to reach for the Inspector

- A new server: smoke-test tools, resources, prompts before wiring a real client.
- A failing tool: inspect the request payload, response, and any error in RPC Logging.
- An OAuth-protected server: drive the auth flow once and inspect with persisted tokens.
- A widget-bearing tool: render the widget, switch protocols, simulate device/locale/CSP. See `11-protocol-toggle-and-csp-mode.md` and `12-device-and-locale-panels.md`.
- An LLM integration: validate tool selection and argument shape from the Chat tab before shipping.

## When not to

- Headless CI assertions — use `mcpc` or programmatic curl scripts instead. The Inspector is interactive.
- Long-running load tests — it is a debugger, not a load tool.

**Canonical doc:** [https://manufact.com/docs/inspector](https://manufact.com/docs/inspector)
