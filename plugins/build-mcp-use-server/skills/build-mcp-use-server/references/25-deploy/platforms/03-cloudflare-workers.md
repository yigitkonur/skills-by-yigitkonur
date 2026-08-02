# Cloudflare Workers

*Read this when deploying an mcp-use server to Cloudflare Workers.*

Cloudflare Workers operate in a V8 edge isolate environment, not Node. Serve generated View files through a Workers static-assets binding.

## Routing

Route `/mcp/_mcp-use/*` to the static binding. Route every other request to `server.fetch`.

The asset route strips the `/mcp/_mcp-use/` prefix before requesting the binding, mapping it to `.mcp-use/build/views/`.

## Build and Deploy

Build with the public MCP URL and asset origin:

```bash
MCP_URL=https://<worker>.<account>.workers.dev/mcp \
MCP_ASSETS_URL=https://<worker>.<account>.workers.dev \
npm run deploy
```

Configure `.mcp-use/build` as the asset directory in `wrangler.toml`:

```toml
name = "my-mcp-worker"
main = "src/index.ts"
compatibility_date = "2024-09-23"
assets = { directory = ".mcp-use/build" }
```

## Handler

Use the Web-standard Fetch boundary:

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "cloudflare-mcp",
  version: "1.0.0",
});

export default server.fetch;
```

Do not call `server.listen()` in a Worker.

## Verify

```bash
npx --yes mcp-use@beta screenshot \
  --mcp https://<worker>.<account>.workers.dev/mcp \
  --tool <tool-name> \
  --output cloudflare-live-view.png
```

A successful MCP request is not enough: confirm that the rendered View loads its generated assets.
