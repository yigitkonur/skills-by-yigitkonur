# Container Patterns

Patterns for customizing OpenClaw sandbox containers, managing skill dependencies, and configuring persistent storage.

## Critical container requirements

| Requirement | Value |
|-------------|-------|
| **Node.js** | Supported runtime `>=22`; current official Docker examples use Node 24 |
| **RAM** | 4 GB recommended, 1.5-2 GB absolute minimum |
| **Gateway reachability** | Keep host publishing on `127.0.0.1:18789:18789`, but set `gateway.bind` to `lan` or `custom` inside bridge-networked containers |
| **Recommended OS** | Ubuntu 24.04 LTS base image works out of box |

## Installing binaries in sandbox containers

Skills that run inside Docker sandbox containers can only use binaries available inside that container. The host system's binaries are not accessible from within the sandbox.

### Using setupCommand

The `agents.defaults.sandbox.docker.setupCommand` configuration runs when the sandbox container is initialized.

```yaml
agents:
  defaults:
    sandbox:
      docker:
        setupCommand: |
          apt-get update && apt-get install -y \
            curl \
            jq \
            git \
            python3 \
            python3-pip \
            nodejs \
            npm \
            imagemagick \
            ffmpeg
```

### setupCommand best practices

| Practice | Why |
|----------|-----|
| Combine commands with `&&` | Single RUN layer, smaller image, faster startup |
| Pin package versions when stability matters | Reproducible builds across restarts |
| Use `--no-install-recommends` | Smaller container, faster startup |
| Clean up package cache | Reduces container size |
| Test the command independently first | Catch failures before production |

### Optimized setupCommand example

```yaml
agents:
  defaults:
    sandbox:
      docker:
        setupCommand: |
          apt-get update && \
          apt-get install -y --no-install-recommends \
            curl \
            jq \
            git \
            python3 \
            python3-pip && \
          pip3 install --no-cache-dir requests pyyaml && \
          apt-get clean && \
          rm -rf /var/lib/apt/lists/*
```

### Per-skill binary requirements

| Skill | Required binaries | setupCommand addition |
|-------|-------------------|----------------------|
| Image processing | ImageMagick, ffmpeg | `apt-get install -y imagemagick ffmpeg` |
| Web scraping | Chrome/Chromium, Puppeteer deps | `apt-get install -y chromium` |
| Python-based | Python 3, pip, specific packages | `apt-get install -y python3 python3-pip && pip3 install <packages>` |
| Node.js | Node.js, npm, specific packages | `apt-get install -y nodejs npm && npm install -g <packages>` |
| Database | Client libraries | `apt-get install -y postgresql-client mysql-client` |

### Diagnosing missing binary errors

```bash
# Debug: check available binaries
docker exec openclaw-sandbox which curl jq git python3

# Debug: verify Node.js version
docker exec openclaw-sandbox node --version
# Must show a supported runtime
```

## Volume mounts and persistence

### Data persistence patterns

| Mount | Purpose | Recommended mode |
|-------|---------|-----------------|
| `/data` | Agent data, conversations, logs | Read-write, persistent named volume |
| `/home/node/.openclaw` | OpenClaw config, credentials, sessions, workspace | Read-write, persistent named volume |
| `/home/node/.openclaw/skills` | Custom skill definitions | Read-write, persistent named volume |
| `/tmp` | Temporary skill working files | tmpfs (ephemeral, fast) |

### Docker volume configuration

```yaml
services:
  openclaw-gateway:
    volumes:
      - openclaw-data:/data
      - openclaw-home:/home/node/.openclaw
    tmpfs:
      - /tmp:size=512m

volumes:
  openclaw-data:
    driver: local
  openclaw-home:
    driver: local
```

### Bind mounts when host-visible state is required

```yaml
services:
  openclaw-gateway:
    volumes:
      - ./openclaw-home:/home/node/.openclaw
      - openclaw-data:/data
```

Named volumes are the safer default for opaque gateway data. Use bind mounts intentionally when you need host-visible `openclaw.json` or workspace state for backup, inspection, or GitOps, and then lock ownership/permissions on the host.

## Production Docker Compose with security

Complete example incorporating all security and operational requirements:

```yaml
version: "3.8"
services:
  openclaw-gateway:
    image: ghcr.io/openclaw/openclaw:latest
    container_name: openclaw-gateway
    restart: unless-stopped
    volumes:
      - openclaw-data:/data
      - openclaw-home:/home/node/.openclaw
    tmpfs:
      - /tmp:size=512m
    env_file:
      - .env
    secrets:
      - gateway_token
    ports:
      # CRITICAL: localhost only
      - "127.0.0.1:18789:18789"
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://127.0.0.1:18789/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

volumes:
  openclaw-data:
  openclaw-home:

secrets:
  gateway_token:
    file: ./secrets/gateway_token.txt
```

The mounted `/home/node/.openclaw/openclaw.json` should set `gateway.bind` to `lan` or `custom` for bridge-published containers. Keep the host publish on `127.0.0.1:18789:18789`; do not confuse that with the in-container bind mode.

## Tool execution security in containers

Configure tool execution as an allowlist inside containers:

```yaml
tools:
  exec:
    security: "allowlist"
    allowlist:
      - "git status"
      - "git diff"
      - "ls"
      - "cat"
      - "curl"
```

**Never use `security: "any"` in production containers.** Even inside a sandbox, an agent with unrestricted exec can exfiltrate data or consume resources.

## Sandbox networking patterns

### Network isolation levels

| Level | Configuration | Use case |
|-------|---------------|----------|
| No network | `network: none` | Maximum isolation, local-only processing |
| Internal only | Custom bridge, no external access | Inter-container communication only |
| Restricted | Firewall-limited egress | Skills needing specific API endpoints |
| Full | Default Docker network | **Development only, never production** |

### Configuring restricted networking

```yaml
agents:
  defaults:
    sandbox:
      docker:
        network: "openclaw-restricted"
        dns:
          - "8.8.8.8"
```

## Multi-container patterns

### Skill-specific containers

For skills with heavy or conflicting dependencies:

```yaml
agents:
  skills:
    image-processing:
      sandbox:
        docker:
          image: "openclaw/sandbox-imagemagick:latest"
          setupCommand: "pip3 install pillow opencv-python"
    web-scraping:
      sandbox:
        docker:
          image: "openclaw/sandbox-chrome:latest"
          setupCommand: "npm install -g puppeteer"
```

## Container health and lifecycle

### Container restart policy

```yaml
services:
  openclaw-gateway:
    restart: unless-stopped
    # Alternatives:
    # - "no" -- development only
    # - "always" -- restart even after manual stop
    # - "on-failure:5" -- restart up to 5 times on failure
```

### Container resource monitoring

```bash
# Check resource usage
docker stats openclaw-gateway --no-stream

# Verify idle memory is 1.5-2 GB (4 GB recommended available)
# If memory exceeds 3 GB, investigate runaway skills or tool loops

# Check health status
docker inspect --format='{{.State.Health.Status}}' openclaw-gateway

# View events
docker events --filter container=openclaw-gateway --since 1h
```

### Container update procedure

1. Pull the new image
2. **Read release notes for breaking config changes**
3. Back up current configuration and data
4. Stop the current container
5. Start the new container with the same volume mounts
6. Run health checks
7. **Verify supported runtime**: `docker exec openclaw-gateway node --version`
8. Roll back if health checks fail

```bash
docker pull ghcr.io/openclaw/openclaw:latest
docker stop openclaw-gateway
docker rm openclaw-gateway
docker run -d \
  --name openclaw-gateway \
  --restart unless-stopped \
  -v openclaw-data:/data \
  -v openclaw-home:/home/node/.openclaw \
  --env-file ./.env \
  -p 127.0.0.1:18789:18789 \
  ghcr.io/openclaw/openclaw:latest

# Verify
curl -fsS http://127.0.0.1:18789/healthz
docker exec openclaw-gateway node --version
docker exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"
```

## Steering experiences

### SE-01: setupCommand runs on every container restart
If `setupCommand` runs on every restart, it adds startup latency. Consider building a custom image with pre-installed binaries, or use Docker layer caching.

### SE-02: Container runs out of disk space
Temporary files from skill execution can fill up the container filesystem. Use tmpfs mounts for `/tmp` with size limits.

### SE-03: Container networking conflicts with host services
Port conflicts prevent container startup. Check with `ss -tlnp` or `lsof -i :18789` before deployment.

### SE-04: Container uses wrong Node.js version
Always verify `node --version` shows a supported runtime inside the container after updates. Some custom base images may drift below the supported floor.
