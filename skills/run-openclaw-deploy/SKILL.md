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

1. **Never expose the gateway without authentication.** Every public-facing gateway must have auth configured before going live.
2. **Never disable exec approvals in production** unless the operator explicitly accepts the risk and documents why.
3. **Never store secrets in plain text in config files.** Use environment variables or a secrets manager.
4. **Always verify container sandbox isolation** before running untrusted skills.
5. **Always test health checks** after any deployment or configuration change.
6. **Always back up configuration before making changes** to gateway, security, or provider settings.

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

- Check if OpenClaw is already running and which version
- Identify the runtime environment (Docker, Podman, Nix, bare VPS)
- List active messaging channels and integrations
- Check current security posture (exec approvals, tool lists, sandbox config)
- Review the existing gateway configuration
- Note which LLM provider(s) are configured

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

- Run the `healthcheck` skill to confirm the instance is operational
- Test at least one messaging channel end-to-end if channels are configured
- Verify exec approval behavior by attempting a command that should require approval
- Check `model-usage` skill output to confirm LLM provider is responding
- Review gateway security posture (see `references/guides/security-hardening.md`)

### 5. Set up ongoing operations

For production deployments, ensure:

- Health monitoring is configured and tested
- Backup schedule is in place
- Cost tracking is active via `model-usage`
- Alert thresholds are defined for health and cost
- Recovery procedures are documented and tested

## Common pitfalls

| # | Pitfall | What goes wrong | Fix |
|---|---------|-----------------|-----|
| 1 | Skipping exec approvals in production | Agents execute destructive commands without human review | Enable exec approvals; see `references/guides/security-hardening.md` |
| 2 | Missing binaries in sandbox containers | Skills fail silently when required tools are not installed | Use `agents.defaults.sandbox.docker.setupCommand`; see `references/patterns/container-patterns.md` |
| 3 | Gateway exposed without auth | Unauthorized access to the OpenClaw instance | Configure gateway authentication before exposing; see `references/guides/security-hardening.md` |
| 4 | No backup before config changes | Configuration corruption with no recovery path | Always back up before changes; see `references/guides/monitoring-and-ops.md` |
| 5 | Using a single LLM provider without fallback | Full outage when provider has downtime | Configure at least one backup provider; see `references/guides/gateway-management.md` |
| 6 | Ignoring tool-loop detection | Agents enter infinite loops consuming tokens and time | Enable tool-loop detection; see `references/guides/security-hardening.md` |
| 7 | Not testing health checks after deployment | Silent failures go undetected | Run `healthcheck` skill after every change; see `references/guides/monitoring-and-ops.md` |

## Do this, not that

| Do this | Not that |
|---------|----------|
| Enable exec approvals and test them before going live | Assume default settings are safe for production |
| Install all skill-required binaries via setupCommand | Expect binaries to be available inside sandbox containers |
| Configure gateway auth before exposing any endpoint | Open the gateway and plan to add auth later |
| Use environment variables or secrets manager for credentials | Put API keys and tokens directly in config files |
| Set up automated health checks and cost alerts | Wait for users to report that the instance is down |
| Test messaging channel integration end-to-end | Trust that a channel is working because config looks correct |
| Back up configuration before every change | Make changes and hope nothing breaks |
| Use the `gateway` tool to restart after config changes | Restart the entire server for gateway changes |
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

- **Gateway unresponsive:** Use the `gateway` tool to restart. If the tool is unavailable, restart the OpenClaw process directly. See `references/guides/gateway-management.md`.
- **Health check failing:** Run `healthcheck` skill for diagnostics. Check LLM provider connectivity, messaging channel status, and disk space. See `references/guides/monitoring-and-ops.md`.
- **Exec approvals blocking legitimate operations:** Review and adjust the approval policy, not disable it. See `references/guides/security-hardening.md`.
- **Container skills failing:** Verify required binaries are installed inside the container. Check `setupCommand` configuration. See `references/patterns/container-patterns.md`.
- **LLM provider outage:** Switch to a backup provider via gateway configuration. See `references/guides/gateway-management.md`.
- **Configuration corrupted:** Restore from backup. If no backup exists, rebuild from the deployment guide. See `references/guides/monitoring-and-ops.md`.
