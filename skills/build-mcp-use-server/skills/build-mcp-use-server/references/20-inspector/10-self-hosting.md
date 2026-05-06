# Self-Hosting

Deploy the Inspector to your own infrastructure. Use this for enterprise environments, air-gapped networks, custom domains, or any setup where the hosted `inspector.mcp-use.com` is not an option.

## Live preview

Try it first at [inspector.mcp-use.com](https://inspector.mcp-use.com/) before deciding whether to self-host.

## Docker (recommended)

The official image is published as `mcpuse/inspector:latest` on Docker Hub.

### One-liner

```bash
docker run -d -p 8080:8080 --name mcp-inspector mcpuse/inspector:latest
```

### Production form

```bash
docker run -d \
  --name mcp-inspector \
  -p 8080:8080 \
  -e NODE_ENV=production \
  --restart unless-stopped \
  mcpuse/inspector:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  mcp-inspector:
    image: mcpuse/inspector:latest
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - PORT=8080
      - MCP_INSPECTOR_FRAME_ANCESTORS=https://app.example.com https://dev.example.com
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Quick deploy: Railway

Railway has a one-click deploy template with automatic HTTPS and custom-domain support. Deploy from [railway.com](https://railway.com/deploy/nl4ZMa). See `../../../../../use-railway/` for Railway-specific operations.

## Environment variables

All optional. Defaults work out of the box.

| Variable | Default | Purpose |
|---|---|---|
| `NODE_ENV` | `production` | Node environment |
| `PORT` | `8080` | Listen port |
| `HOST` | `0.0.0.0` | Bind host |
| `MCP_INSPECTOR_FRAME_ANCESTORS` | `'self'` (prod), `*` (dev) | CSP `frame-ancestors` whitelist for embedding the Inspector or its widget iframes |

### `MCP_INSPECTOR_FRAME_ANCESTORS` examples

```bash
# Specific domains
-e MCP_INSPECTOR_FRAME_ANCESTORS="https://app.example.com https://dev.example.com"

# All origins (dev only — do NOT use in production-facing instances)
-e MCP_INSPECTOR_FRAME_ANCESTORS="*"

# Wildcards
-e MCP_INSPECTOR_FRAME_ANCESTORS="https://*.example.com http://localhost:*"
```

## Behind a reverse proxy

When fronting the Docker container with nginx, Caddy, or Traefik:

- Forward both HTTP and WebSocket (`Upgrade`/`Connection` headers) — Inspector uses WS for HMR proxy and connection liveness.
- Preserve the public origin via `X-Forwarded-Host` / `X-Forwarded-Proto` so OAuth callbacks resolve correctly.
- If the public URL differs from the container hostname, set `MCP_URL` (see `02-cli.md`) to the public-facing URL when running an MCP server alongside the inspector.

Example nginx fragment:

```nginx
location / {
  proxy_pass http://mcp-inspector:8080;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Authentication in front

The Inspector ships without built-in auth. For internet-facing instances, gate it at the proxy:

- nginx `auth_basic` or `auth_request`
- Cloudflare Access
- Traefik forward-auth middleware
- VPN-only ingress

Per-server credentials still live inside the Inspector (OAuth tokens, custom headers in `localStorage`).

## Persistence model

Inspector state — connected servers, OAuth tokens, custom headers, saved requests, console-proxy preference — lives entirely in browser `localStorage`, not on the server. The container itself is stateless. To migrate state, export configurations via **Copy Config** (see `03-connection-settings.md`) and paste into the new instance.

## Health check

The container exposes the inspector at `http://<host>:8080/`. The Compose example above polls that with `curl -f` every 30 s.

## Updating

```bash
docker pull mcpuse/inspector:latest
docker stop mcp-inspector && docker rm mcp-inspector
docker run -d -p 8080:8080 --name mcp-inspector mcpuse/inspector:latest
```

For Compose:

```bash
docker compose pull
docker compose up -d
```

## Support

- GitHub Issues: [github.com/mcp-use/mcp-use](https://github.com/mcp-use/mcp-use/issues)
- Discord: [discord.gg/XkNkSkMz3V](https://discord.gg/XkNkSkMz3V)

## See also

- `02-cli.md` — running locally without Docker.
- `08-integration.md` — auto-mounting in your own Express/Hono app.
- `../25-deploy/` — deploying the MCP server itself.
