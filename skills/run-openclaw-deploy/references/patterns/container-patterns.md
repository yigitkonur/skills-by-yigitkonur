# Container Patterns

Patterns for customizing OpenClaw sandbox containers, managing skill dependencies, and configuring persistent storage.

## Installing binaries in sandbox containers

Skills that run inside Docker sandbox containers can only use binaries available inside that container. The host system's binaries are not accessible from within the sandbox.

### Using setupCommand

The `agents.defaults.sandbox.docker.setupCommand` configuration runs when the sandbox container is initialized. Use it to install all binaries that skills require.

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
| Test the command independently first | Catch failures before they affect production |

### Example: optimized setupCommand

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

When different skills need different binaries, document the requirements:

| Skill | Required binaries | setupCommand addition |
|-------|-------------------|----------------------|
| Image processing skills | ImageMagick, ffmpeg | `apt-get install -y imagemagick ffmpeg` |
| Web scraping skills | Chrome/Chromium, Puppeteer deps | `apt-get install -y chromium` |
| Python-based skills | Python 3, pip, specific packages | `apt-get install -y python3 python3-pip && pip3 install <packages>` |
| Node.js skills | Node.js, npm, specific packages | `apt-get install -y nodejs npm && npm install -g <packages>` |
| Database skills | Client libraries (psql, mysql) | `apt-get install -y postgresql-client mysql-client` |

### Diagnosing missing binary errors

When a skill fails inside a container:

1. Check the error message -- look for "command not found" or "No such file or directory"
2. Identify the missing binary
3. Add it to `setupCommand`
4. Restart the sandbox container to apply
5. Test the skill again

```bash
# Debug: check what binaries are available inside the sandbox
docker exec openclaw-sandbox which curl jq git python3

# Debug: try running the missing command
docker exec openclaw-sandbox command-that-failed --version
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
# docker-compose.yml
services:
  openclaw:
    volumes:
      # Named volumes for persistence
      - openclaw-data:/data
      - openclaw-config:/config
      - openclaw-skills:/skills
      # tmpfs for temporary files
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

### Bind mounts for development

During development, bind mounts let you edit files on the host and see changes inside the container:

```yaml
services:
  openclaw:
    volumes:
      - ./config:/config
      - ./custom-skills:/skills
      - openclaw-data:/data
```

Do not use bind mounts in production. Named volumes are safer and do not depend on host directory structure.

## Sandbox networking patterns

### Network isolation levels

| Level | Configuration | Use case |
|-------|---------------|----------|
| No network | `network: none` | Maximum isolation, skills that only process local files |
| Internal only | Custom bridge network with no external access | Skills that communicate between containers but not externally |
| Restricted | Network with firewall rules limiting egress | Skills that need specific external endpoints (APIs) |
| Full | Default Docker network | Development only, never in production |

### Configuring restricted networking

```yaml
agents:
  defaults:
    sandbox:
      docker:
        # Allow only specific outbound connections
        network: "openclaw-restricted"
        # DNS resolution restricted to internal
        dns:
          - "8.8.8.8"
```

```yaml
# docker-compose.yml network definition
networks:
  openclaw-restricted:
    driver: bridge
    internal: false
    driver_opts:
      com.docker.network.bridge.enable_ip_masquerade: "true"
```

Combine with host-level firewall rules (iptables/nftables) for egress filtering.

## Multi-container patterns

### Skill-specific containers

For skills with heavy or conflicting dependencies, use separate containers:

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

### When to use skill-specific containers

- Binary dependencies conflict between skills
- A skill needs a specialized base image (GPU, specific OS libraries)
- Resource limits differ significantly between skills
- Isolation requirements differ (some skills need network, others do not)

## Container health and lifecycle

### Container restart policy

```yaml
# docker-compose.yml
services:
  openclaw:
    restart: unless-stopped
    # Alternative policies:
    # - "no" -- never restart (development)
    # - "always" -- restart even after manual stop
    # - "on-failure:5" -- restart up to 5 times on failure
```

### Container resource monitoring

```bash
# Check container resource usage
docker stats openclaw --no-stream

# Check container health status
docker inspect --format='{{.State.Health.Status}}' openclaw

# View container events
docker events --filter container=openclaw --since 1h
```

### Container update procedure

1. Pull the new image
2. Back up current configuration and data (see monitoring-and-ops.md)
3. Stop the current container
4. Start the new container with the same volume mounts
5. Run health checks
6. Roll back if health checks fail

```bash
# Update procedure
docker pull openclaw/openclaw:latest
docker stop openclaw
docker rm openclaw
docker run -d \
  --name openclaw \
  --restart unless-stopped \
  -v openclaw-data:/data \
  -v openclaw-config:/config \
  -e OPENCLAW_API_KEY="${OPENCLAW_API_KEY}" \
  -p 8080:8080 \
  openclaw/openclaw:latest

# Verify
curl -f http://localhost:8080/health
```

## Steering experiences

### SE-01: setupCommand runs on every container restart
If `setupCommand` runs on every restart, it adds startup latency. Consider building a custom image with pre-installed binaries for frequently used setups, or use Docker layer caching.

### SE-02: Container runs out of disk space
Temporary files from skill execution can fill up the container filesystem. Use tmpfs mounts for `/tmp` and set size limits. Monitor disk usage inside containers.

### SE-03: Container networking conflicts with host services
When the container's port mapping conflicts with host services, the container fails to start. Always check for port conflicts before deployment with `ss -tlnp` or `lsof -i :8080`.
