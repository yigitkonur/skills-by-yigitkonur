# Self-Hosting with Docker

*Read this when you need to run the Inspector on your own infrastructure.*

The Inspector is available as a self-hosted Docker image for enterprise deployments, air-gapped environments, or when you need a stable custom domain.

## Quick start

```bash
docker run -d -p 127.0.0.1:8080:8080 --name mcp-inspector mcpuse/inspector:latest
```

Then open `http://localhost:8080` in your browser.

## Docker Compose

```yaml
services:
  mcp-inspector:
    image: mcpuse/inspector:latest
    ports:
      - "127.0.0.1:8080:8080"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/inspector"]
      interval: 30s
      timeout: 10s
      retries: 3
```

The Docker image is based on `node:20-alpine` and includes `wget` (from BusyBox) for healthchecks.

## Port configuration

The container always listens on port `8080` — the image's start command pins this, so the `PORT` environment variable has no effect.

To serve on a different host port, remap it with Docker:

```bash
docker run -d -p 127.0.0.1:3001:8080 mcpuse/inspector:latest
```

`NODE_ENV=production` is already set in the image; no environment variables are required.

## Security

The Inspector can call tools, read resources, and inspect prompts on any connected server.

**Important:** The examples bind to `127.0.0.1` so the Inspector is only reachable from the host itself. If you need remote access, put it behind a reverse proxy with authentication and TLS, or restrict access with firewall rules — do not publish port 8080 on all interfaces.

## Air-gapped installation

For hosts without Docker registry access, transfer the image as a tarball:

```bash
# On a connected host
docker pull mcpuse/inspector:latest
docker save mcpuse/inspector:latest -o mcp-inspector.tar

# On the air-gapped host
docker load -i mcp-inspector.tar
docker run -d -p 127.0.0.1:8080:8080 mcpuse/inspector:latest
```

## Connecting to servers

When connecting from a self-hosted Inspector to an MCP server on another host, the browser must be able to reach the server directly, or use the Inspector's proxy connection mode. See `03-connection-settings.md` for when to use each.

## Official image

The official Docker image is published at [`mcpuse/inspector`](https://hub.docker.com/r/mcpuse/inspector) on Docker Hub.
