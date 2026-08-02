# Inspector CLI

*Read this when running the Inspector standalone with command-line flags or environment variables.*

## Quick start

```bash
npx @mcp-use/inspector
```

This starts the Inspector on port 8080 and opens it in your browser at `http://localhost:8080`.

## Command-line flags

### `--url <url>`

Auto-connect to an MCP server when the Inspector starts.

```bash
npx @mcp-use/inspector --url http://localhost:3000/mcp
```

The Inspector will not wait for the server to respond before starting; it attempts the connection after the UI loads.

### `--port <port>`

Specify the starting port. Default is 8080. Valid range: 1–65535.

```bash
npx @mcp-use/inspector --port 9000
```

If the specified port is in use, the Inspector will try to find the next available port and display the actual port in the terminal.

### `--no-open`

Prevent the Inspector from automatically opening a browser tab. Useful in CI/CD pipelines and headless environments.

```bash
npx @mcp-use/inspector --no-open
```

You can combine flags:

```bash
npx @mcp-use/inspector --url http://localhost:3000/mcp --port 9000 --no-open
```

### `--help, -h`

Display help information and available options.

```bash
npx @mcp-use/inspector --help
```

## Environment variables

### `MCP_INSPECTOR_FRAME_ANCESTORS`

Configure which origins can embed the Inspector in iframes via the `frame-ancestors` CSP directive.

**Default behavior:**
- Development mode: `*` (allows all origins)
- Production mode: `'self'` (same-origin only)

**Format:** Space-separated list of origins or `*`

```bash
# Allow embedding from specific domains
MCP_INSPECTOR_FRAME_ANCESTORS="https://app.example.com https://dev.example.com" npx @mcp-use/inspector

# Allow all origins (development only)
MCP_INSPECTOR_FRAME_ANCESTORS="*" npx @mcp-use/inspector
```

### `MCP_URL`

Set the external base URL when running behind a reverse proxy (ngrok, E2B sandboxes, Cloudflare tunnels). This ensures widget asset URLs and Vite HMR WebSocket connections work correctly through the proxy.

```bash
# ngrok tunnel
MCP_URL=https://abc123.ngrok.io npx @mcp-use/inspector

# E2B sandbox
MCP_URL=https://3000-abc123.e2b.app npx @mcp-use/inspector
```

If not set, the Inspector generates a localhost URL automatically.
