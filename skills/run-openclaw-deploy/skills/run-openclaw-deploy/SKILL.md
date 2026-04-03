---
name: run-openclaw-deploy
description: Use skill if you are deploying OpenClaw to production — Docker containers, VPS setup, security hardening, gateway management, and monitoring.
---

# Deploy OpenClaw

Deploy, secure, and operate self-hosted OpenClaw instances across Docker, Podman, Nix, Ansible, or bare VPS environments.

## Trigger boundaries

### Use this skill when

- Deploying OpenClaw to a new server, VPS, or container environment
- Configuring Docker or Podman containers for sandbox isolation
- Hardening an OpenClaw instance (exec approvals, tool allow/deny lists, elevated mode)
- Managing the OpenClaw gateway (restart, security, channel routing)
- Setting up monitoring, health checks, or cost tracking
- Configuring LLM provider switching or multi-provider setups
- Setting up messaging channels (WhatsApp, Telegram, Slack, Discord, iMessage)
- Planning backup and disaster recovery for OpenClaw data
- Installing required binaries inside sandbox containers
- Connecting a remote macOS node for macOS-only skills

### Do not use this skill when

- Building a new OpenClaw skill from scratch -> use `build-openclaw-skill`
- Building an OpenClaw plugin -> use `build-openclaw-plugin`
- Configuring agent behavior or AGENTS.md/CLAUDE.md -> use `configure-openclaw` or `init-agent-config`
- Optimizing an MCP server's tool quality -> use `optimize-mcp-server`
- General infrastructure work unrelated to OpenClaw

## Non-negotiable rules

1. **Use a supported Node runtime.** Current official docs recommend Node `>=22`, and the current Docker image examples use `node:24-bookworm`. For source or bare-metal installs, use 22.x or 24.x. For container deployments, verify the runtime inside the container instead of assuming the host Node matters.
2. **Never expose the gateway directly.** Native installs can keep `gateway.bind: "loopback"`. Docker bridge deployments still need host publishing locked to `127.0.0.1:18789:18789`, but the gateway inside the container must bind `lan` or `custom` so the published port is actually reachable. Put authenticated HTTPS in front if remote access is required.
3. **Set API spending caps BEFORE connecting messaging channels.** Retry loops on reconnecting channels cause $300-600 bills.
4. **Never disable exec approvals in production** unless the operator explicitly accepts the risk and documents why.
5. **Never store secrets in plain text in config files.** Keep provider keys and gateway tokens in environment variables or SecretRefs. The policy/config that references them lives in `~/.openclaw/openclaw.json` or the mounted container equivalent.
6. **Audit all installed skills.** Treat community marketplaces as untrusted until reviewed. Pin versions, verify publishers, and prefer official or self-audited sources.
7. **Always verify container sandbox isolation** before running untrusted skills.
8. **Always test health checks** after any deployment or configuration change.
9. **Always back up configuration before making changes.** Updates are manual and config format changes between versions break things.

**Primary source-of-truth references:** official OpenClaw docs for [install/docker](https://docs.openclaw.ai/install/docker), [gateway configuration](https://docs.openclaw.ai/gateway/configuration), [CLI health](https://docs.openclaw.ai/cli/health), [CLI status](https://docs.openclaw.ai/cli/status), [CLI gateway](https://docs.openclaw.ai/cli/gateway), plus the GitHub advisories feed at `github.com/openclaw/openclaw/security/advisories`. Use community reports only as secondary signal.

## Decision tree

```
What deployment task do you need?
|
+-- Initial deployment
|   |
|   +-- Docker / Podman ---------------------- references/guides/container-setup.md
|   +-- VPS (bare metal, cloud VM) ----------- references/guides/container-setup.md (VPS section)
|   +-- Nix / Ansible ------------------------ references/guides/container-setup.md (alternative runtimes)
|   +-- Remote macOS node -------------------- references/guides/container-setup.md (macOS remote)
|
+-- Security hardening
|   |
|   +-- Exec approval policies --------------- references/guides/security-hardening.md
|   +-- Tool allow/deny lists ---------------- references/guides/security-hardening.md
|   +-- Elevated mode configuration ---------- references/guides/security-hardening.md
|   +-- Tool-loop detection ------------------ references/guides/security-hardening.md
|   +-- Sandbox isolation -------------------- references/guides/security-hardening.md
|   +-- OAuth2 integration ------------------- references/guides/security-hardening.md
|   +-- Gateway security --------------------- references/guides/security-hardening.md
|
+-- Gateway management
|   |
|   +-- Gateway restart / recovery ----------- references/guides/gateway-management.md
|   +-- Channel routing (messaging) ---------- references/guides/gateway-management.md
|   +-- LLM provider configuration ----------- references/guides/gateway-management.md
|   +-- Multi-provider switching ------------- references/guides/gateway-management.md
|
+-- Monitoring and operations
|   |
|   +-- Health checks ------------------------ references/guides/monitoring-and-ops.md
|   +-- LLM cost tracking ------------------- references/guides/monitoring-and-ops.md
|   +-- Backup and disaster recovery --------- references/guides/monitoring-and-ops.md
|   +-- Log management ----------------------- references/guides/monitoring-and-ops.md
|
+-- Container customization
|   |
|   +-- Installing binaries in sandbox ------- references/patterns/container-patterns.md
|   +-- Skill dependencies in containers ----- references/patterns/container-patterns.md
|   +-- setupCommand configuration ----------- references/patterns/container-patterns.md
|   +-- Volume mounts and persistence -------- references/patterns/container-patterns.md
```

## Workflow

### 1. Assess the current state

Before deploying or changing anything, understand what exists:

- **Host/native installs (host has `openclaw`)**
  - `openclaw --version`
  - `openclaw status --all`
  - `openclaw gateway status --json`
  - `openclaw doctor`
  - `test -f ~/.openclaw/openclaw.json && sed -n '1,200p' ~/.openclaw/openclaw.json`
- **Official Docker Compose installs (OpenClaw checkout + `openclaw-cli` service)**
  - `docker info >/dev/null` to confirm the daemon is reachable
  - `docker context show`
  - `docker compose ps`
  - `docker compose run --rm openclaw-cli status --all`
  - `docker compose exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"`
- **Generic Docker / Podman container installs**
  - `docker info >/dev/null` or `podman info >/dev/null`
  - `docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | rg openclaw` or `podman ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | rg openclaw`
  - `docker inspect openclaw-gateway --format '{{json .Mounts}}'`
  - `docker exec openclaw-gateway node --version`
  - `docker exec openclaw-gateway sh -lc 'test -f /home/node/.openclaw/openclaw.json && sed -n "1,200p" /home/node/.openclaw/openclaw.json'`
- **Bare-metal / systemd**
  - `systemctl --user status openclaw --no-pager || systemctl status openclaw --no-pager`
- **What to record**
  - active channels from the status command that matches the runtime
  - provider usage from the matching status/usage view
  - health from the matching deep-health command
  - config location and secrets wiring (`~/.openclaw/openclaw.json`, `~/.openclaw/.env`, container mounts, SecretRefs)

If `docker info` or `podman info` fails, stop before the deployment step and start the container runtime first. Common local fixes are Docker Desktop, OrbStack, or Colima/rootless Docker with the correct socket path.

If the host does not have an `openclaw` binary, do not improvise host-side commands. Use the container command path from `references/guides/container-setup.md`.

If this is a fresh deployment, skip to step 2. If modifying an existing instance, back up the current configuration first.

### 2. Route to the appropriate guide

Use the decision tree above to identify which reference file(s) to load. Load only what you need for the current task.

### 3. Execute the deployment or change

Follow the loaded reference guide. For every change:

1. Back up the current state
2. Apply the change
3. Verify the change works (health check, test message, tool invocation)
4. Document what changed and why

### 4. Verify and harden

After any deployment or configuration change:

- Run the health/status commands that match the runtime from `references/guides/container-setup.md` (`openclaw health --json` on host installs, `docker compose exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"` on official Compose, or HTTP probes plus config/log inspection on generic image-only deployments)
- Test at least one messaging channel end-to-end if channels are configured
- Verify exec approval behavior by attempting a command that should require approval
- Check provider usage visibility with the runtime-appropriate status view
- Run the matching gateway status/probe path for the runtime
- Review gateway security posture (see `references/guides/security-hardening.md`)

### 5. Set up ongoing operations

For production deployments, ensure:

- Health monitoring is configured and tested
- Backup schedule is in place
- Cost tracking is visible via `openclaw status --usage` and, where relevant, `/usage cost`
- Alert thresholds are defined for health and cost
- Recovery procedures are documented and tested

## Common pitfalls

| # | Pitfall | What goes wrong | Fix |
|---|---------|-----------------|-----|
| 1 | Using an unsupported host/runtime Node | OpenClaw fails to start, or custom builds drift from the supported runtime | Use Node 22.x or 24.x, or use the official container image; see `references/guides/container-setup.md` |
| 2 | Using `gateway.bind: "loopback"` inside a Docker bridge deployment | Docker publishes the host port, but the gateway only listens on container loopback so the service appears down | Keep host publishing on `127.0.0.1:18789:18789`, but set container `gateway.bind` to `lan` or `custom`; see `references/guides/container-setup.md` |
| 3 | No API spending cap before connecting channels | $300-600 bills from retry loops | Set `limit_action: "stop"` before any channel; see `references/guides/monitoring-and-ops.md` |
| 4 | Installing skills without auditing | Community marketplaces can ship malicious or compromised skills | Pin versions, audit code, verify publishers; see `references/guides/security-hardening.md` |
| 5 | Skipping exec approvals in production | Agents execute destructive commands without review | Enable exec approvals + `tools.exec.security: "allowlist"`; see `references/guides/security-hardening.md` |
| 6 | Gateway token stored in a broadly readable `.env` or echoed in logs | Token exposure leads to full gateway takeover | Lock down `.env` ownership during bootstrap, then move to Docker secrets or SecretRefs for long-lived production; see `references/guides/security-hardening.md` |
| 7 | Missing binaries in sandbox containers | Skills fail silently | Use `setupCommand`; see `references/patterns/container-patterns.md` |
| 8 | No reverse proxy (no HTTPS) | Traffic sent in plaintext | Use Caddy (easiest) or nginx; see `references/guides/container-setup.md` |
| 9 | No backup before config changes | Config corruption with no recovery | Always back up; see `references/guides/monitoring-and-ops.md` |
| 10 | No uptime monitoring | Slow failures go undetected for days | Set up external monitoring; see `references/guides/monitoring-and-ops.md` |
| 11 | WhatsApp without keepalive | Session disconnects after days of inactivity | Schedule keepalive; see `references/guides/gateway-management.md` |

## Do this, not that

| Do this | Not that |
|---------|----------|
| Verify the actual runtime (`node --version` on host installs, `docker exec ... node --version` in containers) | Assume the system Node.js version is correct |
| Use the runtime-specific CLI path (`openclaw`, `openclaw-cli`, or `node dist/index.js` in the gateway container) | Assume the host `openclaw` binary exists for every deployment |
| In Docker bridge deployments, keep host publishing on `127.0.0.1:18789:18789` but set in-container `gateway.bind` to `lan` or `custom`; use `gateway.bind: "loopback"` for native installs | Treat Docker port publishing and the gateway bind mode as the same setting |
| Set API spending caps with `limit_action: "stop"` before channels | Connect channels first and configure costs later |
| Keep the bootstrap `.env` private and prefer Docker secrets / SecretRefs for long-lived production | Leave the gateway token in a shared or repo-tracked env file |
| Pin skill versions and audit code before installing | Install popular skills without reviewing source |
| Set `tools.exec.security: "allowlist"` with specific commands | Leave exec in permissive mode |
| Enable exec approvals and test them before going live | Assume default settings are safe for production |
| Install skill-required binaries via setupCommand | Expect binaries to be available inside sandbox containers |
| Use Caddy or nginx as reverse proxy for TLS | Expose the gateway directly without HTTPS |
| Set up external uptime monitoring (UptimeRobot, etc.) | Rely only on internal health checks |
| Back up configuration before every change and update | Make changes and hope nothing breaks |
| Configure tool-loop detection for production workloads | Rely on agents to self-regulate their loop behavior |

## Reference routing

Load the smallest set that addresses the current task.

### Guides

| File | Read when |
|------|-----------|
| `references/guides/container-setup.md` | Deploying OpenClaw for the first time, setting up Docker/Podman, provisioning a VPS, configuring Nix/Ansible, or connecting a remote macOS node |
| `references/guides/security-hardening.md` | Configuring exec approvals, tool allow/deny lists, elevated mode, tool-loop detection, sandbox isolation, OAuth2, or gateway security |
| `references/guides/gateway-management.md` | Managing the gateway lifecycle, configuring messaging channels, switching LLM providers, or setting up multi-provider routing |
| `references/guides/monitoring-and-ops.md` | Setting up health checks, cost tracking, backup and recovery, log management, or alert configuration |

### Patterns

| File | Read when |
|------|-----------|
| `references/patterns/container-patterns.md` | Installing binaries inside sandbox containers, configuring setupCommand, managing skill dependencies in containers, or setting up volume mounts |

## Community skills

These community-maintained skills complement deployment operations. They are not part of this skill but may be useful:

- `openclaw-setup-guide` -- guided initial setup
- `solo-deploy` -- single-node deployment
- `instance-setup` -- instance provisioning
- `openclaw-health-audit` -- comprehensive health assessment
- `openclaw-cost-guardian` -- cost monitoring and alerts
- `finn-openclaw-backup` -- automated backup management

## Recovery paths

- **Gateway unresponsive:** Start with `openclaw gateway status --require-rpc` or `openclaw gateway probe --json`. If restart is needed, use `openclaw gateway restart`, `docker compose restart openclaw-gateway`, or `systemctl --user restart openclaw`. See `references/guides/gateway-management.md`.
- **Health check failing:** Run `openclaw health --json`, then check provider connectivity, messaging channel status, RAM (need 4 GB), and disk space. Use `curl -fsS http://127.0.0.1:18789/healthz` for a simple liveness check. See `references/guides/monitoring-and-ops.md`.
- **Unexpected API bill:** Immediately set `limit_action: "stop"` in cost config. Check for channel retry loops or runaway cron jobs. See `references/guides/monitoring-and-ops.md`.
- **Suspected compromise:** Update OpenClaw immediately. Rotate the gateway token. Audit installed skills. Check the current GitHub security advisories and release notes before restoring service. See `references/guides/security-hardening.md`.
- **WhatsApp disconnected:** Check session health. Set up keepalive cron. Monitor for message replay on reconnection. See `references/guides/gateway-management.md`.
- **Exec approvals blocking legitimate operations:** Review and adjust the approval policy, not disable it. See `references/guides/security-hardening.md`.
- **Container skills failing:** Verify required binaries are installed inside the container. Check `setupCommand` configuration. Verify the container runtime with `docker exec openclaw-gateway node --version`. See `references/patterns/container-patterns.md`.
- **LLM provider outage:** Switch to a backup provider via gateway configuration. See `references/guides/gateway-management.md`.
- **Configuration corrupted after update:** Restore from backup. Config format changes between versions. See `references/guides/monitoring-and-ops.md`.
