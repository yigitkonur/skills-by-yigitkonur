# Verification & Testing

*Authoritative verification workflow for mcp-use v2 servers and ChatGPT MCP Apps.*

Official documentation:
- [CLI Reference](https://docs.mcp-use.com/v2/typescript/api-reference/cli-reference)
- [Client CLI Guide](https://docs.mcp-use.com/v2/typescript/tooling/client-cli)
- [Tunneling Guide](https://docs.mcp-use.com/tunneling)

---

## 1. Static Checks

Always verify types and production builds before committing or deploying:

```bash
# Refreshes mcp-env.d.ts live type-only imports and executes tsc --noEmit
# Note: Static tools must be exported constants (export const myTool = server.tool(...))
npx mcp-use typecheck

# Transpiles server to .mcp-use/build/index.js and bundles MCP App views
npx mcp-use build
```

---

## 2. Server & Capability Checks

Start the development server with live reload and the local web Inspector:

```bash
# Terminal 1: Start local development server with Inspector
npx mcp-use dev

# Expose server over public HTTPS WebSocket relay tunnel for testing in live ChatGPT / Claude
npx mcp-use dev --tunnel
```

> [!NOTE]
> - `--tunnel` creates a public WebSocket relay endpoint (`https://<adjective>-<color>.tunnel.mcp-use.run/mcp`). It is **not** authenticated by default unless the server configures OAuth.
> - The local web Inspector at `/mcp/inspector` is air-gapped from the public tunnel (returns HTTP 404 over the tunnel) to prevent unauthorized remote tool execution.
> - In `@mcp-use/cli` v2.7.2+, boolean flags reject inline values (`--tunnel=false` throws usage error `#2521`).

Use the built-in `mcp-use client` CLI to verify protocol capabilities from the terminal:

```bash
# Terminal 2: Save and connect local endpoint
npx mcp-use client connect dev http://localhost:3000/mcp

# List discovered tools
npx mcp-use client dev tools list

# Describe tool schema and metadata
npx mcp-use client dev tools describe lookup-inventory

# Call tool with string arguments (key=value)
npx mcp-use client dev tools call lookup-inventory sku=SKU-100

# Call tool with typed JSON arguments (key:=<json> for numbers, booleans, arrays, objects)
npx mcp-use client dev tools call lookup-inventory sku=SKU-100 limit:=5 active:=true

# Call tool with raw JSON object payload
npx mcp-use client dev tools call lookup-inventory '{"sku": "SKU-100", "limit": 5}'
```

> [!NOTE]
> `mcp-use client` does not have an `interactive` REPL command. Interactive testing of tools and live View rendering is performed through the browser-based web Inspector mounted at `http://localhost:3000/mcp/inspector`.

### CLI OAuth & Mixed-Auth Verification

When verifying OAuth-enabled or mixed-auth servers:

```bash
# Initiate browser-based OAuth authorization
npx mcp-use client dev auth login

# Check saved tokens, expiration, and granted scopes
npx mcp-use client dev auth status

# Clear saved credentials
npx mcp-use client dev auth logout
```

In scriptable or CI environments, running under `--json` avoids opening a browser: if authorization is required, the CLI exits with code 1, `error.code: "oauth_interaction_required"`, and remediation instructions in `error.details.nextSteps`.

---

## 3. View Verification & Automated Screenshots

Verify React View rendering, theme adaptation, and data flow. Capture visual screenshots of view-backed tools headlessly:

```bash
# Capture screenshot of the inventory-card view bound to lookup-inventory
npx mcp-use screenshot --server dev --tool lookup-inventory sku=SKU-100 --output ./screenshot.png

# Advanced capture options:
npx mcp-use screenshot --server dev --tool lookup-inventory sku=SKU-100 \
  --width 768 \
  --height 720 \
  --theme dark \
  --wait-for "[data-status='ready']" \
  --delay 500 \
  --json
```

Verify interactive states in the web Inspector (`http://localhost:3000/mcp/inspector`):
- Pending skeleton states while tool execution is in flight (`status === "pending"`).
- Ready state with correct `structuredContent` rendering (`status === "ready"`).
- Error state when `isError: true` or tool execution is cancelled (`status === "error"`, `ToolCancelledError`).
- Theme switching between light and dark modes (`[data-theme]`).
- Responsive layouts across mobile (`xs`, `sm`) and desktop (`md`, `lg`, `xl`) viewports.

---

## 4. Advanced & Security Verification

- **Mixed Auth**:
  - Public tools (`securitySchemes: [{ type: "noauth" }]`): Verify requests succeed without a token (`HTTP 200`).
  - Protected tools: Verify requests without a token return `HTTP 401 Unauthorized` (standard clients).
  - ChatGPT User-Agent: Verify `curl -H 'user-agent: ChatGPT/1.0'` against protected tools returns `HTTP 200` with `isError: true` and `_meta["mcp/www_authenticate"]`.
  - Token validation: Verify sending an invalid or expired token on any tool (even `noauth`) is strictly refused with `401`.
- **Elicitation**: Test multi-round interactive prompts, form-mode submission, URL-mode authorization, user accept, decline, and cancellation paths.
- **Skills over MCP**: Verify `skills/list` advertises discovered SEP-2640 skills and `mcp-use build` embeds the catalog without error.
