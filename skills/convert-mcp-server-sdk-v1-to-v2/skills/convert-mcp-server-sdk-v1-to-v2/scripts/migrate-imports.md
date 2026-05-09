# migrate-imports.sh

Deterministic helper for the mechanical import portion of an MCP SDK v1 to v2 port.

## Use when

- Step 3 has reached direct v2 package imports.
- The migration is not staying on the v2 `@modelcontextprotocol/sdk` meta-package shim.
- You want a repeatable dry-run before editing import lines by hand.

## Avoid when

- The project intentionally remains on v1 import paths through the meta-package shim.
- Auth router, handler context, schemas, request-handler keys, or transport lifecycle are the main change. This script does not rewrite those.
- `@modelcontextprotocol/sdk/types.js` imports mix `McpError` or `ErrorCode` with request schemas. Split those imports manually first.

## Usage

```bash
# Preview only
bash scripts/migrate-imports.sh /path/to/project

# Apply changes
bash scripts/migrate-imports.sh --write /path/to/project
```

## Rewrite scope

- `@modelcontextprotocol/sdk/server/mcp.js` -> `@modelcontextprotocol/server`
- `@modelcontextprotocol/sdk/server/stdio.js` -> `@modelcontextprotocol/server`
- `@modelcontextprotocol/sdk/server/streamableHttp.js` -> `@modelcontextprotocol/node`
- `StreamableHTTPServerTransport` -> `NodeStreamableHTTPServerTransport` in files that import the v1 Streamable HTTP transport
- `@modelcontextprotocol/sdk/server/express.js` -> `@modelcontextprotocol/express`
- `@modelcontextprotocol/sdk/client/index.js` -> `@modelcontextprotocol/client`
- safe `McpError` / `ErrorCode` imports from `@modelcontextprotocol/sdk/types.js` -> `ProtocolError` / `ProtocolErrorCode` from `@modelcontextprotocol/core`

The helper prints warnings for auth-router paths, `SSEServerTransport`, and mixed v1/v2 imports. It only scans files under the supplied project directory.
