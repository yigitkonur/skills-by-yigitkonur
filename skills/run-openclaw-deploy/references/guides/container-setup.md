# Container and Environment Setup

This guide covers deploying OpenClaw across all supported runtime environments.

## Critical requirements (verified from official OpenClaw docs)

| Requirement | Value | Source |
|-------------|-------|--------|
| **Node.js version** | **Supported: Node >=22**. Current official Docker examples build on `node:24-bookworm`. | `docs.openclaw.ai/`, `docs.openclaw.ai/install/docker` |
| **Primary config path** | `~/.openclaw/openclaw.json` on host installs; `/home/node/.openclaw/openclaw.json` inside containers | `docs.openclaw.ai/agent-workspace`, `docs.openclaw.ai/install/docker` |
| **Health endpoints** | `http://127.0.0.1:18789/healthz` and `/readyz` | `docs.openclaw.ai/install/docker` |
| **RAM (recommended)** | 4 GB recommended, 1.5-2 GB idle baseline | operator guidance |
| **Best OS** | Ubuntu 24.04 LTS remains a practical default | operator guidance |

**Compatibility rule:** host or source installs should run a supported Node major (`22.x` or `24.x`). Prebuilt containers already bundle the runtime, so verify **inside the container** with `docker exec ... node --version` instead of treating host Node as authoritative.

## Docker daemon and socket preflight

Before any Docker-based deployment:

```bash
docker info >/dev/null
docker version
docker context show
```

If `docker info` fails, stop and start the container runtime first. Common local setups:
- Docker Desktop
- OrbStack
- Colima or rootless Docker

Common socket paths to verify:
- `/var/run/docker.sock`
- `$HOME/.orbstack/run/docker.sock`
- `/run/user/$UID/docker.sock`

If OpenClaw sandboxing needs a non-default socket, set `OPENCLAW_DOCKER_SOCKET` before running the official Docker setup flow.

## Command paths by deployment style

Use the command path that matches how OpenClaw was installed. Do not assume the host has an `openclaw` binary just because the gateway is running.

### Host or bare-metal install

Use the host CLI directly:

```bash
openclaw --version
openclaw status --all
openclaw gateway status --json
openclaw health --json
```

### Official Docker Compose flow from an OpenClaw checkout

After `docker compose up -d openclaw-gateway`, use the dedicated CLI container for day-to-day commands:

```bash
docker compose run --rm openclaw-cli status --all
docker compose run --rm openclaw-cli gateway probe
docker compose exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"
```

Before the gateway container exists, run onboarding and config writes through `openclaw-gateway` with `--no-deps --entrypoint node`:

```bash
docker compose run --rm --no-deps --entrypoint node openclaw-gateway \
  dist/index.js config set gateway.mode local
```

### Generic image-only Docker / Podman deployment

HTTP probes and config-file inspection are the reliable baseline:

```bash
docker ps --filter name=openclaw-gateway
docker logs openclaw-gateway --tail 50
curl -fsS http://127.0.0.1:18789/healthz
docker exec openclaw-gateway node --version
docker exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"
docker exec openclaw-gateway sh -lc 'sed -n "1,200p" /home/node/.openclaw/openclaw.json'
```

Only use `docker exec openclaw-gateway openclaw ...` after you confirm the binary exists with `docker exec openclaw-gateway which openclaw`.

## Runtime options

| Runtime | Best for | Key consideration |
|---------|----------|-------------------|
| Docker Compose | Most deployments, safest route | Official setup flow, easiest path to sandbox support |
| Docker | Single-container deployments | Same as Compose but manual orchestration |
| Podman | Rootless container needs, security-sensitive | Drop-in Docker alternative, no daemon |
| Nix | Reproducible deployments, declarative config | Exact dependency pinning, no container overhead |
| Ansible | Multi-node fleet management | Automated provisioning across many hosts |
| Bare VPS | Simple single-instance | Direct control, must manage supported Node runtime manually |

## Docker Compose deployment (recommended)

Docker Compose is the safest and most commonly successful deployment route based on community reports.

### Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- At least 4GB RAM available (2GB absolute minimum, expect degraded performance)
- Persistent storage for configuration and data
- Ubuntu 24.04 LTS recommended (works out of box)

### Official repo-based flow (preferred when you have an OpenClaw checkout)

The official Docker docs expect you to run from the OpenClaw repo root:

```bash
./scripts/docker/setup.sh
```

To use the published image instead of building locally:

```bash
export OPENCLAW_IMAGE="ghcr.io/openclaw/openclaw:latest"
./scripts/docker/setup.sh
```

Key details from the official flow:
- onboarding writes provider keys and the generated gateway token into `.env`
- `OPENCLAW_GATEWAY_BIND=lan` is the default so `http://127.0.0.1:18789` on the host works with Docker port publishing
- `openclaw-cli` is a post-start tool; use `openclaw-gateway` with `--no-deps --entrypoint node` for pre-start onboarding or config writes

Manual equivalent:

```bash
docker build -t openclaw:local -f Dockerfile .
docker compose run --rm --no-deps --entrypoint node openclaw-gateway \
  dist/index.js onboard --mode local --no-install-daemon
docker compose run --rm --no-deps --entrypoint node openclaw-gateway \
  dist/index.js config set gateway.mode local
docker compose run --rm --no-deps --entrypoint node openclaw-gateway \
  dist/index.js config set gateway.bind lan
docker compose run --rm --no-deps --entrypoint node openclaw-gateway \
  dist/index.js config set gateway.controlUi.allowedOrigins \
  '["http://localhost:18789","http://127.0.0.1:18789"]' --strict-json
docker compose up -d openclaw-gateway
```

### Generic image-only Docker Compose

```yaml
version: "3.8"
services:
  openclaw-gateway:
    image: ghcr.io/openclaw/openclaw:latest
    container_name: openclaw-gateway
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./openclaw-home:/home/node/.openclaw
    ports:
      - "127.0.0.1:18789:18789"
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://127.0.0.1:18789/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Place provider keys in `.env`, and put policy/config in `./openclaw-home/openclaw.json` so it is mounted into the container at `/home/node/.openclaw/openclaw.json`:

```json
{
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "auth": {
      "mode": "token",
      "token": "${OPENCLAW_GATEWAY_TOKEN}"
    },
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789"
      ]
    }
  },
  "monitoring": {
    "cost": {
      "enabled": true,
      "daily_limit_usd": 50,
      "weekly_limit_usd": 250,
      "monthly_limit_usd": 800,
      "limit_action": "stop"
    }
  }
}
```

**CRITICAL Docker bridge rule:** keep the host publish on loopback with `127.0.0.1:18789:18789`, but do **not** leave `gateway.bind` at `loopback` inside the container. Use `lan` or `custom` there so the published port is reachable. Use bind mode values, not host aliases like `127.0.0.1` or `0.0.0.0`.

### Verifying Docker deployment

```bash
# Official Compose flow
docker compose ps
docker compose run --rm openclaw-cli status --all
docker compose exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"

# Generic container checks
docker ps --filter name=openclaw-gateway
docker logs openclaw-gateway --tail 50
curl -fsS http://127.0.0.1:18789/healthz
curl -fsS http://127.0.0.1:18789/readyz
docker exec openclaw-gateway node --version
docker exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"
docker stats openclaw-gateway --no-stream
docker exec openclaw-gateway sh -lc 'sed -n "1,200p" /home/node/.openclaw/openclaw.json'
```

## Docker single-container deployment

```bash
# Pull the latest OpenClaw image
docker pull ghcr.io/openclaw/openclaw:latest

# Run with localhost-only port binding
docker run -d \
  --name openclaw-gateway \
  --restart unless-stopped \
  --env-file ./.env \
  -v openclaw-home:/home/node/.openclaw \
  -p 127.0.0.1:18789:18789 \
  ghcr.io/openclaw/openclaw:latest
```

Create `/home/node/.openclaw/openclaw.json` in that volume before first start, and use the same `gateway.mode`, `gateway.bind`, `gateway.auth`, and `gateway.controlUi.allowedOrigins` pattern shown above.

## Reverse proxy setup (required for production)

OpenClaw has **no HTTPS by default**. A reverse proxy is required for TLS termination in production.

### Caddy (easiest)

```
openclaw.example.com {
    reverse_proxy localhost:18789
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
        proxy_pass http://127.0.0.1:18789;
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
podman pull ghcr.io/openclaw/openclaw:latest

podman run -d \
  --name openclaw-gateway \
  --restart unless-stopped \
  --env-file ./.env \
  -v openclaw-home:/home/node/.openclaw \
  -p 127.0.0.1:18789:18789 \
  ghcr.io/openclaw/openclaw:latest
```

The same bridge-network rule applies: host publishing stays on `127.0.0.1:18789:18789`, while the gateway inside the container should bind `lan` or `custom`.

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
        openclaw_home_dir: /opt/openclaw/.openclaw
```

## VPS bare-metal deployment

For simple single-instance deployments without containers:

1. Provision a VPS (Ubuntu 24.04 LTS recommended, minimum 4GB RAM)
2. **Install a supported Node runtime** (`22.x` or `24.x`)
3. Install OpenClaw runtime dependencies
4. Download and install OpenClaw
5. Configure as a systemd service for auto-restart
6. Set up a reverse proxy (Caddy or nginx) for TLS termination

```bash
# Install Node.js 22.x
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version  # Must show a supported runtime

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
EnvironmentFile=/etc/openclaw/env
# Provider keys and gateway token come from the env file or a secrets manager

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

- [ ] Supported runtime confirmed (`node --version` or `docker exec ... node --version`)
- [ ] OpenClaw process is running and restarting on failure
- [ ] Native installs use `gateway.bind: "loopback"` unless a trusted proxy/access layer requires something else
- [ ] Docker/Podman bridge installs publish `127.0.0.1:18789:18789` on the host and use `gateway.bind: "lan"` or `custom` inside the container
- [ ] Reverse proxy with TLS is in front of the gateway
- [ ] Gateway auth mode is reviewed; non-loopback binds use a token/password, and `mode: "none"` is reserved for trusted loopback-only setups
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
The container may be running but `gateway.bind` is still `loopback` inside the container, so the published host port has nothing listening behind it. Verify host publishing with `127.0.0.1:18789:18789`, then confirm the mounted config uses `gateway.bind: "lan"` or `custom` and hit `/healthz`.

### SE-02: Persistent data lost after container restart
If the OpenClaw home directory is not persisted, config, credentials, and workspace state are ephemeral. Always persist `/home/node/.openclaw`.

### SE-03: Wrong architecture image on ARM hosts
When deploying on ARM-based VPS (AWS Graviton, Apple Silicon), ensure you pull the correct architecture image. Use `--platform linux/arm64` if needed.

### SE-04: Node.js version mismatch on bare-metal
Ubuntu 22.04 and earlier ship Node.js 12-18 by default. Always install a supported runtime (`22.x` or `24.x`) from NodeSource or via `nvm`.

### SE-05: Gateway exposed to the internet without auth
Do not publish the gateway broadly. Keep host publishing on loopback and put a reverse proxy with auth in front before exposing remote access.
