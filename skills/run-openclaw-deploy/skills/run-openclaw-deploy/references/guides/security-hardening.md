# Security Hardening

This guide covers security features available in OpenClaw for production environments. Treat official docs and GitHub security advisories as primary sources. Community reports can highlight operator pain, but they are not source-of-truth for requirements or CVE scope.

## Primary security references

Before making security claims or deciding urgency, check:
- `https://docs.openclaw.ai/gateway/configuration`
- `https://docs.openclaw.ai/install/docker`
- `https://docs.openclaw.ai/cli/health`
- `https://docs.openclaw.ai/cli/gateway`
- `https://github.com/openclaw/openclaw/security/advisories`

### Key lessons from real-world incidents

1. **Do not publish the gateway directly** -- native installs can stay on `gateway.bind: "loopback"`, but Docker bridge deployments need host publishing on loopback and the container itself bound to `lan` or `custom`
2. **Authentication is required by default, but you still need to verify the chosen auth mode and token handling explicitly**
3. **No HTTPS by default** -- a reverse proxy is required for encrypted connections
4. **Updates are manual** -- there is no auto-update mechanism; config format changes occasionally break things
5. **Community skills are a real threat surface** -- audit and pin before production use

## Security posture assessment

Before hardening, assess the current posture:

| Check | Status | Action if missing |
|-------|--------|-------------------|
| Gateway reachability matches the runtime | **Critical** | Native: set `gateway.bind: "loopback"`. Docker bridge: publish `127.0.0.1:18789:18789` and set `gateway.bind: "lan"` or `custom` inside the container |
| Gateway authentication active | **Critical** | Configure before exposing any endpoint |
| Reverse proxy with TLS | **Critical** | Set up Caddy or nginx before going live |
| API spending caps set | **Critical** | Set BEFORE connecting messaging channels |
| Exec approvals enabled | Required for production | Enable immediately |
| Tool exec security set to allowlist | Required | Set `tools.exec.security: "allowlist"` |
| Gateway token secured | Required | Keep the bootstrap `.env` private, and prefer Docker secrets / SecretRefs for long-lived production |
| Skills audited | Required | Pin versions, verify publishers |
| Tool allow/deny lists configured | Recommended | Define based on use case |
| Sandbox isolation verified | Required for untrusted skills | Test container boundary |
| Tool-loop detection enabled | Recommended | Enable to prevent runaway agents |
| Elevated mode policy defined | Recommended | Restrict to specific skills |
| Secrets wired through `.env`, SecretRefs, or a secret manager | Required | Remove inline secrets from config files |

## Gateway security (highest priority)

The gateway is the most critical attack surface. Three settings decide whether your exposure is actually safe:

### 1. Reachability must match the runtime

**Fix:** native installs can stay on `gateway.bind: "loopback"`. Docker bridge installs should keep host publishing on loopback, but the container itself must listen on `lan` or `custom`.

Docker/Docker Compose:
```yaml
ports:
  - "127.0.0.1:18789:18789"
```

Gateway config:

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
  }
}
```

For native installs, change `gateway.bind` to `loopback` unless a different access layer requires otherwise.

### 2. Authentication mode must stay explicit

**Reality:** auth is required by default, and onboarding usually generates a token automatically. The risk comes from disabling auth (`gateway.auth.mode: "none"`) or losing control of the shared token/password.

**Fix:** keep token/password auth on non-loopback binds. Reserve `mode: "none"` for trusted loopback-only local setups.

### 3. No HTTPS by default

**Fix:** Place a reverse proxy (Caddy or nginx) in front of the gateway for TLS termination. See container-setup.md for examples.

### Gateway control UI security flags

When configuring a reverse proxy, these gateway flags may be needed but are dangerous:

```yaml
gateway:
  controlUi:
    dangerouslyAllowHostHeaderOriginFallback: false  # Only enable if proxy strips Origin header
    allowInsecureAuth: false                          # Only enable for local development
    dangerouslyDisableDeviceAuth: false               # Never enable in production
```

**Treat these flags as landmines.** Only enable them if you fully understand the implications and have compensating controls.

### Gateway token

The gateway token is the master credential for your OpenClaw instance.

- **Treat it as a crown jewel** -- compromise of this token means full instance takeover
- The official Docker onboarding flow writes the token to `.env`; keep that file private, never commit it, and lock ownership to the deployment user
- **For long-lived production, prefer Docker secrets, SecretRefs, or your secret manager** over a shared `.env`
- **Rotate regularly** and after any suspected compromise
- **Never log it** or include it in error reports

```yaml
# Docker Compose with secrets
services:
  openclaw-gateway:
    secrets:
      - gateway_token
    environment:
      - OPENCLAW_GATEWAY_TOKEN_FILE=/run/secrets/gateway_token

secrets:
  gateway_token:
    file: ./secrets/gateway_token.txt
```

## API spending caps and config placement

**Set API spending caps BEFORE connecting any messaging channels.**

Real-world operator reports document $300-600 bills caused by retry loops on messaging channels. When a channel disconnects and reconnects, pending messages can trigger a flood of API calls.

Put the policy in the main config file:
- Host/native installs: `~/.openclaw/openclaw.json`
- Container installs: the bind-mounted directory that becomes `/home/node/.openclaw/openclaw.json`

Keep secrets in `.env` or SecretRefs, not inline in the JSON/YAML policy file.

```json
{
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

See monitoring-and-ops.md for full cost tracking configuration.

## Tool execution security

### Exec allowlist (required for production)

Set tool execution to allowlist mode with specific commands only:

```yaml
tools:
  exec:
    security: "allowlist"
    allowlist:
      - "git status"
      - "git diff"
      - "git log"
      - "ls"
      - "cat"
      - "curl"
      # Add only commands your workflows actually need
```

**Never use `security: "any"` in production.** An allowlist prevents agents from executing arbitrary commands even if compromised.

### Exec approvals

Exec approvals require human confirmation before agents execute potentially destructive commands.

```yaml
security:
  exec_approvals:
    enabled: true
    mode: "destructive"
    rules:
      always_approve:
        - "rm -rf"
        - "git push --force"
        - "docker rm"
        - "DROP TABLE"
      auto_approve:
        - "git status"
        - "git diff"
        - "ls"
        - "cat"
    timeout_seconds: 300
```

### When to adjust exec approval mode

- **Development/testing:** `destructive` mode is usually sufficient
- **Production with trusted skills:** `destructive` mode with custom rules
- **Production with untrusted or community skills:** `all` mode
- **Never in production:** disabled entirely

## Skills security

### Community marketplace threat model

Community skill marketplaces can distribute malicious or compromised packages. Threats include:

- Data exfiltration (sending config/secrets to external servers)
- Credential harvesting
- Cryptocurrency mining
- Backdoor installation

### Skills security requirements

1. **Pin skill versions** -- never use `latest` or unpinned versions in production
2. **Audit installed skills** -- review the code of every skill before installation
3. **Verify publishers** -- only install from publishers you trust and can verify
4. **Use tool allowlists per skill** -- restrict what tools each skill can access
5. **Monitor skill behavior** -- watch for unexpected network calls or file access

```yaml
skills:
  my-trusted-skill:
    version: "1.2.3"  # Pinned, not "latest"
    tools:
      mode: "allow"
      allow:
        - "read_file"
        - "web_search"
```

## Tool allow/deny lists

### Allow list (whitelist) approach

```yaml
security:
  tools:
    mode: "allow"
    allow:
      - "read_file"
      - "search_code"
      - "web_search"
      - "health"
```

### Deny list (blacklist) approach

```yaml
security:
  tools:
    mode: "deny"
    deny:
      - "execute_shell"
      - "delete_file"
      - "modify_system"
```

### Per-skill tool restrictions

```yaml
skills:
  my-risky-skill:
    tools:
      mode: "allow"
      allow:
        - "read_file"
        - "web_search"
```

## Elevated mode

```yaml
security:
  elevated_mode:
    enabled: true
    allowed_skills:
      - "deploy-infrastructure"
      - "database-migration"
    requires_approval: true
    max_duration_seconds: 600
```

## Tool-loop detection

```yaml
security:
  tool_loop_detection:
    enabled: true
    max_identical_calls: 5
    max_calls_per_session: 200
    action: "pause"
```

## Sandbox isolation

```yaml
agents:
  defaults:
    sandbox:
      docker:
        enabled: true
        setupCommand: "apt-get update && apt-get install -y curl jq"
        memory: "512m"
        cpus: "1.0"
        network: "none"
        read_only: true
        tmpfs:
          - "/tmp"
          - "/var/tmp"
```

Key sandbox rules:
- Never run sandbox containers as root
- Always set resource limits (memory, CPU)
- Use `network: none` unless the skill genuinely needs network access
- Mount only the minimum required volumes
- Use read-only root filesystem with explicit tmpfs exceptions

## OAuth2 integration

```yaml
integrations:
  slack:
    oauth2:
      client_id: "${SLACK_CLIENT_ID}"
      client_secret: "${SLACK_CLIENT_SECRET}"
      scopes:
        - "chat:write"
        - "channels:read"
      callback_url: "https://your-openclaw.example.com/oauth/callback/slack"
```

OAuth2 security rules:
- Store client secrets in environment variables, never in config files
- Request minimum required scopes
- Rotate secrets on a regular schedule
- Monitor OAuth token usage for anomalies

## Reverse proxy configuration

### Caddy (easiest, recommended)

```
openclaw.example.com {
    reverse_proxy localhost:18789
}
```

Caddy automatically handles TLS certificate provisioning and renewal.

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

## Security hardening checklist

Before going live:

- [ ] Native installs use `gateway.bind: "loopback"`, or Docker bridge installs publish `127.0.0.1:18789:18789` while the container uses `gateway.bind: "lan"` or `custom`
- [ ] Gateway auth mode is reviewed; `mode: "none"` is limited to trusted loopback-only setups
- [ ] API spending caps configured and set to "stop" mode
- [ ] Reverse proxy with TLS in front of gateway
- [ ] `tools.exec.security: "allowlist"` with specific commands only
- [ ] Gateway token is not committed or world-readable; Docker secrets / SecretRefs are used for long-lived production where available
- [ ] All skills version-pinned and audited
- [ ] No skills from unverified publishers
- [ ] Exec approvals enabled and tested
- [ ] Tool allow/deny lists match the deployment's threat model
- [ ] Sandbox containers run as non-root with resource limits
- [ ] Tool-loop detection enabled
- [ ] Elevated mode restricted to specific skills
- [ ] OAuth2 secrets stored in environment variables
- [ ] Rate limiting configured at the reverse proxy
- [ ] Audit logging enabled for security events
- [ ] IP restrictions applied where feasible
- [ ] Supported runtime confirmed (`22.x` or `24.x`)
- [ ] OpenClaw updated to latest version (check for CVE patches)

## Steering experiences

### SE-01: Disabling exec approvals to unblock a skill
When a skill requires frequent approvals, operators sometimes disable exec approvals entirely. Instead, add specific commands to the `auto_approve` list after reviewing their safety.

### SE-02: Overly permissive tool allow list
Starting with "allow all" and planning to restrict later. Start restrictive and add tools as needed.

### SE-03: Sandbox network access left open
Skills that do not need network access should use `network: none`. Leaving the default network open exposes the container to outbound data exfiltration.

### SE-04: Gateway exposed without auth because "it's on a private network"
Private networks get compromised. Lateral movement from any host on the network gives full access. Always enable auth regardless of network trust level.

### SE-05: Installing popular skills without auditing
Popularity is not a security control. Always audit code before installation, even for highly-starred skills.
