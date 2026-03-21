# Security Hardening

This guide covers all security features available in OpenClaw for production environments.

## Security posture assessment

Before hardening, assess the current posture:

| Check | Status | Action if missing |
|-------|--------|-------------------|
| Exec approvals enabled | Required for production | Enable immediately |
| Tool allow/deny lists configured | Recommended | Define based on use case |
| Gateway authentication active | Required if exposed | Configure before exposing |
| Sandbox isolation verified | Required for untrusted skills | Test container boundary |
| Tool-loop detection enabled | Recommended | Enable to prevent runaway agents |
| Elevated mode policy defined | Recommended | Restrict to specific skills |
| OAuth2 configured for integrations | When applicable | Set up per-integration |
| Secrets in environment variables | Required | Migrate from config files |

## Exec approvals

Exec approvals require human confirmation before agents execute potentially destructive commands. This is the single most important security control for production OpenClaw.

### How exec approvals work

When enabled, any agent command that would modify the system (file writes, shell commands, API calls with side effects) is paused and presented to the operator for approval before execution.

### Configuration

```yaml
# In OpenClaw configuration
security:
  exec_approvals:
    enabled: true
    # Approval modes:
    # - "all" -- every command requires approval
    # - "destructive" -- only commands classified as destructive
    # - "custom" -- use rules below
    mode: "destructive"
    rules:
      # Always require approval for these patterns
      always_approve:
        - "rm -rf"
        - "git push --force"
        - "docker rm"
        - "DROP TABLE"
      # Auto-approve these safe patterns (use sparingly)
      auto_approve:
        - "git status"
        - "git diff"
        - "ls"
        - "cat"
    timeout_seconds: 300  # Auto-deny if no response in 5 minutes
```

### When to adjust exec approval mode

- **Development/testing:** `destructive` mode is usually sufficient
- **Production with trusted skills:** `destructive` mode with custom rules
- **Production with untrusted or community skills:** `all` mode
- **Never in production:** disabled entirely (unless operating in a fully isolated, ephemeral sandbox where destruction has zero impact)

### Approval channels

Exec approval requests can be routed to:
- The OpenClaw web interface
- Messaging channels (Slack, Discord, Telegram)
- Custom webhook endpoints

## Tool allow/deny lists

Control which tools agents can access.

### Allow list (whitelist) approach

Only explicitly permitted tools are available to agents:

```yaml
security:
  tools:
    mode: "allow"
    allow:
      - "read_file"
      - "search_code"
      - "web_search"
      - "healthcheck"
      # Add tools as needed
```

Use allow lists when:
- Running untrusted or community skills
- Compliance requirements restrict agent capabilities
- You want maximum control over agent actions

### Deny list (blacklist) approach

All tools available except explicitly blocked ones:

```yaml
security:
  tools:
    mode: "deny"
    deny:
      - "execute_shell"
      - "delete_file"
      - "modify_system"
```

Use deny lists when:
- Running trusted skills that need broad tool access
- You want to block specific dangerous tools while keeping flexibility

### Per-skill tool restrictions

Override global tool lists for specific skills:

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

Elevated mode grants expanded permissions for specific operations that require higher privileges.

### Configuration

```yaml
security:
  elevated_mode:
    enabled: true
    # Which skills can request elevation
    allowed_skills:
      - "deploy-infrastructure"
      - "database-migration"
    # Elevated mode always requires exec approval
    requires_approval: true
    # Maximum duration before auto-revocation
    max_duration_seconds: 600
```

### Rules for elevated mode

- Always require exec approval for elevated operations
- Limit which skills can request elevation
- Set a maximum duration to prevent indefinite elevated sessions
- Log all actions taken during elevated mode
- Revoke immediately when the task completes

## Tool-loop detection

Prevents agents from entering infinite loops that consume tokens and time.

### Configuration

```yaml
security:
  tool_loop_detection:
    enabled: true
    # Maximum consecutive identical tool calls
    max_identical_calls: 5
    # Maximum total tool calls per session
    max_calls_per_session: 200
    # Action when loop detected: "warn", "pause", "terminate"
    action: "pause"
```

### When loop detection triggers

- The agent calls the same tool with identical parameters repeatedly
- Total tool calls exceed the session limit
- A circular pattern of tool calls is detected

When triggered in `pause` mode, the session is suspended and the operator is notified. In `terminate` mode, the session ends immediately.

## Sandbox isolation

OpenClaw uses Docker containers as sandboxes for isolated execution.

### Verifying sandbox isolation

```bash
# From inside the container, verify isolation
# These should all fail or return restricted results:
docker exec openclaw-sandbox whoami        # Should NOT be root
docker exec openclaw-sandbox mount         # Should show minimal mounts
docker exec openclaw-sandbox ip addr       # Should show isolated network
```

### Sandbox configuration

```yaml
agents:
  defaults:
    sandbox:
      docker:
        enabled: true
        # Command to run when setting up the sandbox container
        setupCommand: "apt-get update && apt-get install -y curl jq"
        # Resource limits
        memory: "512m"
        cpus: "1.0"
        # Network isolation
        network: "none"  # or a restricted network
        # Read-only root filesystem
        read_only: true
        # Temporary writable directories
        tmpfs:
          - "/tmp"
          - "/var/tmp"
```

### Key sandbox rules

- Never run sandbox containers as root
- Always set resource limits (memory, CPU)
- Use `network: none` unless the skill genuinely needs network access
- Mount only the minimum required volumes
- Use read-only root filesystem with explicit tmpfs exceptions
- Install required binaries via `setupCommand`, not at runtime

## OAuth2 integration

Some OpenClaw integrations require OAuth2 authentication.

### Setup flow

1. Register an OAuth2 application with the service provider
2. Configure the client ID and secret in OpenClaw (via environment variables)
3. Set the callback URL to your OpenClaw gateway
4. Configure scopes based on minimum required permissions

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

### OAuth2 security rules

- Store client secrets in environment variables, never in config files
- Request minimum required scopes
- Rotate secrets on a regular schedule
- Monitor OAuth token usage for anomalies

## Gateway security

The gateway is the entry point to your OpenClaw instance. See openclaw.ai/gateway/security for the latest official documentation.

### Essential gateway security measures

1. **Authentication:** Always require authentication for gateway access
2. **TLS:** Terminate TLS at the gateway or reverse proxy level
3. **Rate limiting:** Prevent abuse and brute-force attempts
4. **IP restrictions:** Limit access to known IP ranges when possible
5. **Audit logging:** Log all gateway access attempts

### Reverse proxy configuration

For production, place a reverse proxy (nginx, Caddy, Traefik) in front of the gateway:

```nginx
# Example nginx reverse proxy with TLS and rate limiting
server {
    listen 443 ssl;
    server_name openclaw.example.com;

    ssl_certificate /etc/ssl/certs/openclaw.pem;
    ssl_certificate_key /etc/ssl/private/openclaw.key;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=openclaw:10m rate=10r/s;

    location / {
        limit_req zone=openclaw burst=20 nodelay;
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security hardening checklist

Before going live:

- [ ] Exec approvals enabled and tested
- [ ] Tool allow/deny lists match the deployment's threat model
- [ ] Gateway authentication configured
- [ ] TLS enabled for all external connections
- [ ] Sandbox containers run as non-root with resource limits
- [ ] Tool-loop detection enabled
- [ ] Elevated mode restricted to specific skills
- [ ] OAuth2 secrets stored in environment variables
- [ ] Rate limiting configured at the gateway or reverse proxy
- [ ] Audit logging enabled for security events
- [ ] IP restrictions applied where feasible
- [ ] Secrets rotated on a regular schedule

## Steering experiences

### SE-01: Disabling exec approvals to unblock a skill
When a skill requires frequent approvals, operators sometimes disable exec approvals entirely. Instead, add specific commands to the `auto_approve` list after reviewing their safety.

### SE-02: Overly permissive tool allow list
Starting with "allow all" and planning to restrict later. Start restrictive and add tools as needed.

### SE-03: Sandbox network access left open
Skills that do not need network access should use `network: none`. Leaving the default network open exposes the container to outbound data exfiltration.
