# Container and Environment Setup

This guide covers deploying OpenClaw across all supported runtime environments.

## Runtime options

OpenClaw runs on any environment that supports its runtime requirements:

| Runtime | Best for | Key consideration |
|---------|----------|-------------------|
| Docker | Most deployments, sandbox isolation | Native sandbox support via containers |
| Podman | Rootless container needs, security-sensitive environments | Drop-in Docker alternative, no daemon |
| Nix | Reproducible deployments, declarative config | Exact dependency pinning, no container overhead |
| Ansible | Multi-node fleet management | Automated provisioning across many hosts |
| Bare VPS | Simple single-instance deployments | Direct control, no container abstraction |

## Docker deployment

### Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- At least 2GB RAM available for the container
- Persistent storage for configuration and data

### Basic deployment

```bash
# Pull the latest OpenClaw image
docker pull openclaw/openclaw:latest

# Run with essential configuration
docker run -d \
  --name openclaw \
  --restart unless-stopped \
  -v openclaw-data:/data \
  -v openclaw-config:/config \
  -e OPENCLAW_API_KEY="${OPENCLAW_API_KEY}" \
  -p 8080:8080 \
  openclaw/openclaw:latest
```

### Docker Compose deployment

For production, use Docker Compose to manage the full stack:

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
      # Add LLM provider keys as environment variables
      # Never put keys directly in this file
    ports:
      - "8080:8080"
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

### Verifying Docker deployment

```bash
# Check container is running
docker ps --filter name=openclaw

# View logs
docker logs openclaw --tail 50

# Check health endpoint
curl -f http://localhost:8080/health

# Test gateway connectivity
docker exec openclaw openclaw gateway status
```

## Podman deployment

Podman is a drop-in replacement for Docker with rootless container support.

```bash
# Pull and run with Podman (same flags as Docker)
podman pull openclaw/openclaw:latest

podman run -d \
  --name openclaw \
  --restart unless-stopped \
  -v openclaw-data:/data \
  -v openclaw-config:/config \
  -e OPENCLAW_API_KEY="${OPENCLAW_API_KEY}" \
  -p 8080:8080 \
  openclaw/openclaw:latest
```

Key differences from Docker:
- Runs rootless by default (no daemon, no root required)
- Systemd integration for service management
- Use `podman generate systemd` to create a systemd unit for auto-start

## Nix deployment

Nix provides reproducible, declarative deployments.

```nix
# Example Nix flake configuration for OpenClaw
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
# Example Ansible playbook
- hosts: openclaw_nodes
  roles:
    - role: openclaw
      vars:
        openclaw_version: latest
        openclaw_api_key: "{{ vault_openclaw_api_key }}"
        openclaw_data_dir: /opt/openclaw/data
        openclaw_config_dir: /opt/openclaw/config
```

Use Ansible when:
- Managing multiple OpenClaw instances
- Requiring consistent configuration across a fleet
- Needing automated provisioning and updates

## VPS bare-metal deployment

For simple single-instance deployments without containers:

1. Provision a VPS (Ubuntu 22.04+ recommended, minimum 2GB RAM)
2. Install OpenClaw runtime dependencies
3. Download and install OpenClaw
4. Configure as a systemd service for auto-restart
5. Set up a reverse proxy (nginx, Caddy) for TLS termination

```bash
# Example systemd service file
# /etc/systemd/system/openclaw.service
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

Some skills require macOS-specific tools (Xcode, macOS SDKs, platform-specific binaries). OpenClaw supports connecting a remote macOS node.

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

- [ ] OpenClaw process is running and restarting on failure
- [ ] Gateway is accessible and responding to health checks
- [ ] At least one LLM provider is configured and responding
- [ ] Secrets are stored in environment variables or a secrets manager, not in config files
- [ ] Persistent storage is configured for data and configuration
- [ ] Logs are accessible for debugging
- [ ] Firewall rules restrict access to necessary ports only
- [ ] Exec approvals are enabled (see security-hardening.md)
- [ ] Backup schedule is configured (see monitoring-and-ops.md)

## Steering experiences

### SE-01: Container starts but gateway is unreachable
The container may be running but the gateway port is not exposed or is blocked by firewall rules. Always verify port mapping (`-p 8080:8080`) and check host-level firewall rules.

### SE-02: Persistent data lost after container restart
If volumes are not configured, container data is ephemeral. Always mount named volumes for `/data` and `/config` directories.

### SE-03: Wrong architecture image on ARM hosts
When deploying on ARM-based VPS (AWS Graviton, Apple Silicon), ensure you pull the correct architecture image. Use `--platform linux/arm64` if needed.
