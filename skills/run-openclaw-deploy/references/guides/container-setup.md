# Container and Environment Setup

This guide covers deploying OpenClaw across all supported runtime environments.

## Critical requirements (verified from official docs + community reports)

| Requirement | Value | Source |
|-------------|-------|--------|
| **Node.js version** | **v22 required** (not 18, not 20) | Reddit r/selfhosted, confirmed in docs |
| **RAM (idle)** | 1.5-2 GB minimum | Reddit r/selfhosted |
| **RAM (recommended)** | 4 GB | Reddit r/selfhosted |
| **Best OS** | Ubuntu 24.04 LTS | Works out of box with Docker Compose |

**Node.js v22 is non-negotiable.** OpenClaw will fail to start or exhibit undefined behavior on Node.js 18 or 20. If deploying bare-metal, verify with `node --version` before proceeding.

## Runtime options

| Runtime | Best for | Key consideration |
|---------|----------|-------------------|
| Docker Compose | Most deployments, safest route | Native sandbox support, easiest setup |
| Docker | Single-container deployments | Same as Compose but manual orchestration |
| Podman | Rootless container needs, security-sensitive | Drop-in Docker alternative, no daemon |
| Nix | Reproducible deployments, declarative config | Exact dependency pinning, no container overhead |
| Ansible | Multi-node fleet management | Automated provisioning across many hosts |
| Bare VPS | Simple single-instance | Direct control, must manage Node.js v22 manually |

## Docker Compose deployment (recommended)

Docker Compose is the safest and most commonly successful deployment route based on community reports.

### Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- At least 4GB RAM available (2GB absolute minimum, expect degraded performance)
- Persistent storage for configuration and data
- Ubuntu 24.04 LTS recommended (works out of box)

### Production Docker Compose

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
    environment:
      - OPENCLAW_API_KEY=${OPENCLAW_API_KEY}
      # CRITICAL: Set API spending caps BEFORE connecting any channels
      # Retry loops on messaging channels can cause $300-600 bills
      # See monitoring-and-ops.md for cost alert configuration
    ports:
      # CRITICAL: Bind to localhost only, NOT 0.0.0.0
      # The gateway binds to 0.0.0.0 by default, exposing it to all interfaces
      - "127.0.0.1:8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  openclaw-data:
  openclaw-config:
```

**CRITICAL port binding:** The default `-p 8080:8080` binds to `0.0.0.0`, exposing the gateway to all network interfaces. Always use `127.0.0.1:8080:8080` and place a reverse proxy in front. See security-hardening.md for reverse proxy setup.

### Verifying Docker deployment

```bash
# Check container is running
docker ps --filter name=openclaw

# View logs
docker logs openclaw --tail 50

# Check health endpoint (should return from localhost only)
curl -f http://localhost:8080/health

# Verify Node.js version inside container
docker exec openclaw node --version
# Must show v22.x.x

# Check memory usage
docker stats openclaw --no-stream
# Idle should be 1.5-2 GB, warn if under 4 GB available

# Test gateway connectivity
docker exec openclaw openclaw gateway status
```

## Docker single-container deployment

```bash
# Pull the latest OpenClaw image
docker pull openclaw/openclaw:latest

# Run with localhost-only port binding
docker run -d \
  --name openclaw \
  --restart unless-stopped \
  -v openclaw-data:/data \
  -v openclaw-config:/config \
  -e OPENCLAW_API_KEY="${OPENCLAW_API_KEY}" \
  -p 127.0.0.1:8080:8080 \
  openclaw/openclaw:latest
```

## Reverse proxy setup (required for production)

OpenClaw has **no HTTPS by default**. A reverse proxy is required for TLS termination in production.

### Caddy (easiest)

```
openclaw.example.com {
    reverse_proxy localhost:8080
}
```

Caddy automatically provisions and renews TLS certificates via Let's Encrypt.

### nginx

```nginx
server {
    listen 443 ssl;
    server_name openclaw.example.com;

    ssl_certificate /etc/ssl/certs/openclaw.pem;
    ssl_certificate_key /etc/ssl/private/openclaw.key;

    limit_req_zone $binary_remote_addr zone=openclaw:10m rate=10r/s;

    location / {
        limit_req zone=openclaw burst=20 nodelay;
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Podman deployment

Podman is a drop-in replacement for Docker with rootless container support.

```bash
podman pull openclaw/openclaw:latest

podman run -d \
  --name openclaw \
  --restart unless-stopped \
  -v openclaw-data:/data \
  -v openclaw-config:/config \
  -e OPENCLAW_API_KEY="${OPENCLAW_API_KEY}" \
  -p 127.0.0.1:8080:8080 \
  openclaw/openclaw:latest
```

Key differences from Docker:
- Runs rootless by default (no daemon, no root required)
- Systemd integration for service management
- Use `podman generate systemd` to create a systemd unit for auto-start

## Nix deployment

Nix provides reproducible, declarative deployments.

```nix
{
  description = "OpenClaw deployment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    openclaw.url = "github:openclaw/openclaw";
  };

  outputs = { self, nixpkgs, openclaw }: {
    nixosConfigurations.server = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        openclaw.nixosModules.default
        {
          services.openclaw = {
            enable = true;
            settings = {
              # Configuration here
            };
          };
        }
      ];
    };
  };
}
```

Benefits of Nix deployment:
- Exact dependency versions locked in flake.lock
- Atomic rollbacks if deployment fails
- No container overhead
- Declarative full-system configuration

## Ansible deployment

For multi-node fleet management:

```yaml
- hosts: openclaw_nodes
  roles:
    - role: openclaw
      vars:
        openclaw_version: latest
        openclaw_api_key: "{{ vault_openclaw_api_key }}"
        openclaw_data_dir: /opt/openclaw/data
        openclaw_config_dir: /opt/openclaw/config
```

## VPS bare-metal deployment

For simple single-instance deployments without containers:

1. Provision a VPS (Ubuntu 24.04 LTS recommended, minimum 4GB RAM)
2. **Install Node.js v22** (not 18, not 20)
3. Install OpenClaw runtime dependencies
4. Download and install OpenClaw
5. Configure as a systemd service for auto-restart
6. Set up a reverse proxy (Caddy or nginx) for TLS termination

```bash
# Install Node.js v22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version  # Must show v22.x.x

# Example systemd service file
# /etc/systemd/system/openclaw.service
```

```ini
[Unit]
Description=OpenClaw Agent Runtime
After=network.target

[Service]
Type=simple
User=openclaw
Group=openclaw
WorkingDirectory=/opt/openclaw
ExecStart=/opt/openclaw/bin/openclaw serve
Restart=always
RestartSec=5
Environment=OPENCLAW_API_KEY=<from-secrets-manager>
EnvironmentFile=/etc/openclaw/env

[Install]
WantedBy=multi-user.target
```

## Remote macOS node

Some skills require macOS-specific tools (Xcode, macOS SDKs, platform-specific binaries).

### When to use a remote macOS node

- Skills that invoke Xcode build tools
- Skills that require macOS-only CLI tools
- iOS/macOS development workflows
- Skills that interact with macOS system APIs

### Setup considerations

- The macOS node must be reachable from the OpenClaw instance (SSH or direct network)
- Required binaries must be installed on the macOS node itself
- Configure the OpenClaw instance to route macOS-dependent skills to the remote node
- Monitor the macOS node separately since it runs outside the main container

## Post-deployment checklist

After deploying by any method:

- [ ] Node.js v22 confirmed (`node --version` shows v22.x.x)
- [ ] OpenClaw process is running and restarting on failure
- [ ] Gateway is bound to localhost only (not 0.0.0.0)
- [ ] Reverse proxy with TLS is in front of the gateway
- [ ] Gateway authentication is enabled (no auth by default -- see security-hardening.md)
- [ ] API spending caps are set BEFORE connecting messaging channels
- [ ] At least one LLM provider is configured and responding
- [ ] Secrets are stored in environment variables or Docker secrets, not in config files
- [ ] Persistent storage is configured for data and configuration
- [ ] Logs are accessible for debugging
- [ ] Firewall rules restrict access to necessary ports only
- [ ] Exec approvals are enabled (see security-hardening.md)
- [ ] Backup schedule is configured (see monitoring-and-ops.md)
- [ ] RAM is at least 4GB (2GB absolute minimum, degraded performance)

## Steering experiences

### SE-01: Container starts but gateway is unreachable
The container may be running but the gateway port is not exposed or is blocked by firewall rules. Always verify port mapping and check host-level firewall rules.

### SE-02: Persistent data lost after container restart
If volumes are not configured, container data is ephemeral. Always mount named volumes for `/data` and `/config` directories.

### SE-03: Wrong architecture image on ARM hosts
When deploying on ARM-based VPS (AWS Graviton, Apple Silicon), ensure you pull the correct architecture image. Use `--platform linux/arm64` if needed.

### SE-04: Node.js version mismatch on bare-metal
OpenClaw requires Node.js v22. Ubuntu 22.04 and earlier ship Node.js 12-18 by default. Always install from NodeSource or use nvm to get v22.

### SE-05: Gateway exposed to the internet without auth
The gateway binds to 0.0.0.0 by default and has no authentication enabled by default. Bind to localhost and put a reverse proxy with auth in front before exposing any port.
