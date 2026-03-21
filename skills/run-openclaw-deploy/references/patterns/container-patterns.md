# Container Patterns

Patterns for customizing OpenClaw sandbox containers, managing skill dependencies, and configuring persistent storage.

## Critical container requirements

| Requirement | Value |
|-------------|-------|
| **Node.js** | v22 required (container image must include v22, not 18 or 20) |
| **RAM** | 4 GB recommended, 1.5-2 GB absolute minimum |
| **Port binding** | `127.0.0.1:8080:8080` -- never `0.0.0.0` |
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
# Must show v22.x.x
```

## Volume mounts and persistence

### Data persistence patterns

| Mount | Purpose | Recommended mode |
|-------|---------|-----------------|
| `/data` | Agent data, conversations, logs | Read-write, persistent named volume |
| `/config` | OpenClaw configuration | Read-write, persistent named volume |
| `/skills` | Custom skill definitions | Read-write, persistent named volume |
| `/tmp` | Temporary skill working files | tmpfs (ephemeral, fast) |

### Docker volume configuration

```yaml
services:
  openclaw:
    volumes:
      - openclaw-data:/data
      - openclaw-config:/config
      - openclaw-skills:/skills
    tmpfs:
      - /tmp:size=512m

volumes:
  openclaw-data:
    driver: local
  openclaw-config:
    driver: local
  openclaw-skills:
    driver: local
```

### Bind mounts for development only

```yaml
services:
  openclaw:
    volumes:
      - ./config:/config
      - ./custom-skills:/skills
      - openclaw-data:/data
```

Do not use bind mounts in production. Named volumes are safer.

## Production Docker Compose with security

Complete example incorporating all security and operational requirements:

```yaml
version: "3.8"
services:
  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw
    restart: unless-stopped
    volumes:
      - openclaw-data:/data
      - openclaw-config:/config
      - openclaw-skills:/skills
    tmpfs:
      - /tmp:size=512m
    environment:
      - OPENCLAW_API_KEY=${OPENCLAW_API_KEY}
    secrets:
      - gateway_token
    ports:
      # CRITICAL: localhost only
      - "127.0.0.1:8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
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
  openclaw-config:
  openclaw-skills:

secrets:
  gateway_token:
    file: ./secrets/gateway_token.txt
```

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
  openclaw:
    restart: unless-stopped
    # Alternatives:
    # - "no" -- development only
    # - "always" -- restart even after manual stop
    # - "on-failure:5" -- restart up to 5 times on failure
```

### Container resource monitoring

```bash
# Check resource usage
docker stats openclaw --no-stream

# Verify idle memory is 1.5-2 GB (4 GB recommended available)
# If memory exceeds 3 GB, investigate runaway skills or tool loops

# Check health status
docker inspect --format='{{.State.Health.Status}}' openclaw

# View events
docker events --filter container=openclaw --since 1h
```

### Container update procedure

1. Pull the new image
2. **Read release notes for breaking config changes**
3. Back up current configuration and data
4. Stop the current container
5. Start the new container with the same volume mounts
6. Run health checks
7. **Verify Node.js v22**: `docker exec openclaw node --version`
8. Roll back if health checks fail

```bash
docker pull openclaw/openclaw:latest
docker stop openclaw
docker rm openclaw
docker run -d \
  --name openclaw \
  --restart unless-stopped \
  -v openclaw-data:/data \
  -v openclaw-config:/config \
  -e OPENCLAW_API_KEY="${OPENCLAW_API_KEY}" \
  -p 127.0.0.1:8080:8080 \
  openclaw/openclaw:latest

# Verify
curl -f http://localhost:8080/health
docker exec openclaw node --version
```

## Steering experiences

### SE-01: setupCommand runs on every container restart
If `setupCommand` runs on every restart, it adds startup latency. Consider building a custom image with pre-installed binaries, or use Docker layer caching.

### SE-02: Container runs out of disk space
Temporary files from skill execution can fill up the container filesystem. Use tmpfs mounts for `/tmp` with size limits.

### SE-03: Container networking conflicts with host services
Port conflicts prevent container startup. Check with `ss -tlnp` or `lsof -i :8080` before deployment.

### SE-04: Container uses wrong Node.js version
Always verify `node --version` shows v22 inside the container after updates. Some base images may ship older versions.
