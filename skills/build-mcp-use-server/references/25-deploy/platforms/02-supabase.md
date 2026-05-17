# Supabase Edge Functions

Deploy as a Deno-based Edge Function. `MCPServer` auto-detects the Deno runtime and runs in stateless mode.

---

## 1. Prerequisites

- Supabase CLI (`npm install -D supabase` or `brew install supabase/tap/supabase`).
- Supabase account.
- Docker (required for static file bundling — known bug https://github.com/orgs/supabase/discussions/32815).
- Node.js or Bun for the local build.

---

## 2. Setup

```bash
npx create-mcp-use-app@latest your-project-name
cd your-project-name
npm install

supabase init
supabase login
supabase link --project-ref YOUR_PROJECT_REF

open -a Docker   # macOS — Docker must be running
docker info      # verify

supabase functions new mcp-server
```

---

## 3. Quick automated deploy

```bash
# Interactive
curl -fsSL https://url.mcp-use.com/supabase | bash

# Or scripted
curl -fsSL https://url.mcp-use.com/supabase -o deploy.sh
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID
# Optional: ./deploy.sh YOUR_PROJECT_ID my-function-name my-bucket-name
```

The script: validates CLI install, patches `config.toml`, builds with the right `MCP_URL` / `MCP_SERVER_URL`, copies artifacts, sets env vars, deploys, uploads widgets to storage.

---

## 4. Edge function code

Use `npm:` specifiers from `deno.json` to avoid Zod v3/v4 conflicts that surface from `esm.sh`:

```typescript
// supabase/functions/mcp-server/index.ts
import { MCPServer, text } from "npm:mcp-use/server";

const server = new MCPServer({
  name: "test-app",
  version: "1.0.0",
});

server.tool(
  { name: "get-my-city", description: "Get my city" },
  async () => text("My city is San Francisco"),
);

// Auto-detects Deno runtime, runs in stateless mode.
server.listen().catch(console.error);
```

For widgets, set `baseUrl` from env so widget assets load from the right origin:

```typescript
const PROJECT_REF = Deno.env.get("SUPABASE_PROJECT_REF") || "your-project-ref";
const BASE_URL =
  Deno.env.get("MCP_URL") ||
  `https://${PROJECT_REF}.supabase.co/functions/v1/mcp-server`;

const server = new MCPServer({
  name: "test-app",
  version: "1.0.0",
  baseUrl: BASE_URL,
});
```

---

## 5. `deno.json` — handle Zod conflicts

Preferred (`npm:` specifiers):

```json
{
  "imports": {
    "mcp-use/": "npm:mcp-use@latest/",
    "zod": "npm:zod@^4.2.0"
  }
}
```

Fallback if you must use `esm.sh`:

```json
{
  "imports": {
    "mcp-use/server": "https://esm.sh/mcp-use@latest/server?external=zod",
    "mcp-use/client": "https://esm.sh/mcp-use@latest/client?external=zod",
    "zod": "https://esm.sh/[email protected]",
    "zod/v3": "https://esm.sh/[email protected]",
    "zod/v4": "https://esm.sh/[email protected]",
    "zod/v4-mini": "https://esm.sh/[email protected]"
  }
}
```

The `TypeError: e.custom is not a function` error means a Zod v3/v4 conflict — fix via `npm:` specifiers.

---

## 6. Manual deploy (widget assets)

```bash
# Upload widget assets to Supabase Storage
supabase storage cp -r dist/resources/widgets ss://widgets/ --experimental
```

Set build-time env vars (these are baked in at `npm run build` — set them **before** building):

```bash
export MCP_URL="https://YOUR_REF.supabase.co/storage/v1/object/public/widgets"
export MCP_SERVER_URL="https://YOUR_REF.supabase.co/functions/v1/YOUR_FUNCTION_NAME"
export CSP_URLS="https://YOUR_REF.supabase.co"

npm run build
cp -r dist supabase/functions/mcp-server/
```

Configure `supabase/config.toml` to bundle static files:

```toml
[functions.mcp-server]
static_files = [
  "./functions/mcp-server/dist/**/*.html",
  "./functions/mcp-server/dist/mcp-use.json"
]
```

---

## 7. Runtime secrets

Set **before** deploying. Changes to secrets after deploy require a redeploy:

```bash
supabase secrets set MCP_URL="https://YOUR_REF.supabase.co/functions/v1/mcp-server" \
  --project-ref YOUR_REF

supabase secrets set CSP_URLS="https://YOUR_REF.supabase.co" \
  --project-ref YOUR_REF
```

---

## 8. Deploy

Docker must be running. `--use-docker` is required for static file bundling:

```bash
docker info  # verify
supabase functions deploy mcp-server --use-docker
```

MCP server URL: `https://YOUR_PROJECT_ID.supabase.co/functions/v1/mcp-server/mcp`

---

## 9. Client connection

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    supabase: {
      url: `https://YOUR_PROJECT_ID.supabase.co/functions/v1/mcp-server/mcp`,
      transport: "http",
      headers: {
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
    },
  },
});
```

---

## 10. Troubleshooting

| Symptom                                                   | Fix                                                |
|-----------------------------------------------------------|----------------------------------------------------|
| `TypeError: e.custom is not a function`                   | Zod v3/v4 conflict — switch to `npm:` specifiers.  |
| `"Initialising login role..."` 2-3 times                  | Normal — separate auth for link, widget upload, public upload. |
| Deploy hangs on `Initialising login role...`              | IP banned. Visit `https://supabase.com/dashboard/project/{PROJECT_ID}/database/settings#banned-ips`. |
| `Docker is required for widgets data`                     | Start Docker Desktop and retry.                    |
| OAuth/Supabase auth issues                                | See `27-troubleshooting/03-oauth-and-supabase-issues.md`. |

---

**Canonical doc:** https://manufact.com/docs/typescript/server/deployment/supabase
