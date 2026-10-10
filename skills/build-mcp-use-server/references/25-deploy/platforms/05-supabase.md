# Supabase Edge Functions

*Read this when deploying an mcp-use server and Views to Supabase Edge Functions.*

Edge Functions run on a Deno-compatible runtime. `MCPServer` exposes the Web-standard `fetch(Request)` boundary that runtime needs; the function forwards requests to `server.fetch` and never calls `listen()`. Requires Node.js >= 22.22.2 to run the `mcp-use` build, and the Supabase CLI (`supabase login`) with a linked project. Docker is required only for local bundling/serving — Supabase can also bundle server-side through its API.

## Set Up the Function

```bash
supabase init
supabase login
supabase link --project-ref YOUR_PROJECT_REF
supabase functions new mcp-server
```

## Match `basePath` to the Gateway Prefix

The public URL includes the gateway prefix `/functions/v1/mcp-server`. Give the server a `basePath` that matches the full pathname the function receives:

```typescript
// index.ts
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "supabase-edge-mcp",
  version: "1.0.0",
  basePath: "/functions/v1/mcp-server/mcp",
});

export default server;
```

If a custom domain or gateway rewrite changes the pathname the function actually receives, change `basePath` to match — and use that same pathname in client configs.

## Build

The build creates `.mcp-use/build/{index.js,manifest.json,views/}`. Without Views, build normally:

```bash
npm run typecheck
npm run build
```

With Views, create a public Supabase Storage bucket (e.g. `widgets`) first and point the build at its public URL prefix:

```bash
PROJECT_REF="YOUR_PROJECT_REF"
ASSETS_URL="https://${PROJECT_REF}.supabase.co/storage/v1/object/public/widgets"
MCP_ASSETS_URL="${ASSETS_URL}" npm run build
```

Copy the build output into the Edge Function directory — the deployed import target is `supabase/functions/mcp-server/.mcp-use/build/index.js`, not a `dist/` artifact:

```bash
mkdir -p supabase/functions/mcp-server/.mcp-use
cp -R .mcp-use/build supabase/functions/mcp-server/.mcp-use/
```

## Map npm Imports in Deno

The build keeps package imports external, so Deno needs an import map. Write `supabase/functions/mcp-server/deno.json`:

```json
{
  "imports": {
    "mcp-use": "npm:mcp-use@beta",
    "mcp-use/": "npm:mcp-use@beta/",
    "zod": "npm:zod@^4.4.3"
  }
}
```

## Forward Requests to `server.fetch`

Replace `supabase/functions/mcp-server/index.ts`:

```typescript
import server from "./.mcp-use/build/index.js";

Deno.serve((request) => server.fetch(request));
```

`server.fetch` returns a Web `Response` — no Node listener, adapter, or port involved.

## Upload View and Public Assets

Storage must preserve the URL hierarchy `mcp-use build` embedded in the manifest:

```text
widgets/
└── functions/v1/mcp-server/mcp/
    └── _mcp-use/
        ├── views/<view-name>/...
        └── public/...
```

For a View named `animal-card`:

```bash
supabase storage cp -r \
  .mcp-use/build/views/animal-card/ \
  "ss:///widgets/functions/v1/mcp-server/mcp/_mcp-use/views/animal-card/" \
  --experimental

supabase storage cp -r \
  .mcp-use/build/views/public/ \
  "ss:///widgets/functions/v1/mcp-server/mcp/_mcp-use/public/" \
  --experimental
```

Repeat the first command per View directory. Keep the generated path hierarchy intact rather than flattening it — View bundles must load from `<basePath>/_mcp-use/views/<name>/...` and public assets from `<basePath>/_mcp-use/public/...`.

There is no `static_files` bundling step here — Views ship through a Storage bucket, not the function's own bundle.

## Set Runtime Secrets

```bash
supabase secrets set \
  MCP_URL="https://YOUR_PROJECT_REF.supabase.co" \
  MCP_ASSETS_URL="https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/public/widgets" \
  --project-ref YOUR_PROJECT_REF
```

`MCP_URL` is the public server origin (used for server-origin resolution and View `connectDomains`); the MCP path itself comes from `basePath`. `MCP_ASSETS_URL` is the Storage/CDN prefix used both at build time (rewrites the View manifest) and at runtime (added to `resourceDomains`) — use the same value in both places.

## Gateway Authentication

Supabase gateway JWT verification and MCP authentication are separate layers. For a public demo, disable the gateway check:

```toml
[functions.mcp-server]
verify_jwt = false
```

For a protected function, leave the gateway check enabled and have the MCP client send the required Supabase authorization header. Never put a service-role key in a browser or public MCP client.

## Test and Deploy

```bash
deno check supabase/functions/mcp-server/index.ts
supabase functions serve mcp-server   # local serve, requires Docker
supabase functions deploy mcp-server  # --use-docker forces local bundling; --use-api forces server-side bundling
```

The hosted MCP endpoint is:

```text
https://YOUR_PROJECT_REF.supabase.co/functions/v1/mcp-server/mcp
```

Not `https://<ref>.supabase.co/functions/v1/mcp` — the function name (`mcp-server`) is part of the path.

## Verify

```bash
MCP_ENDPOINT="https://YOUR_PROJECT_REF.supabase.co/functions/v1/mcp-server/mcp"
npx mcp-use client connect supabase-edge "${MCP_ENDPOINT}" --no-oauth
npx mcp-use client supabase-edge tools list

npx --yes mcp-use@beta screenshot \
  --mcp "${MCP_ENDPOINT}" \
  --tool <tool-name> \
  --output supabase-live-view.png
```

Confirm the rendered View, not only the function's HTTP status — a missing or mis-pathed Storage upload can leave tool calls working while View assets return 404.

## Troubleshooting

- **Function 404:** verify the project reference, function name, and that `basePath` matches the full request pathname.
- **MCP route 404:** confirm the client URL includes the trailing `/mcp`.
- **View asset 404:** compare the Storage object hierarchy against `<basePath>/_mcp-use/views/` and `<basePath>/_mcp-use/public/`.
- **Bundle too large:** inspect with `deno info`; try `supabase functions deploy mcp-server --use-docker` for local bundling.
