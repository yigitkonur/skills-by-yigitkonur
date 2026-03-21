# Security Patterns

Security configuration for OpenClaw agents. Every production agent must have explicit security settings -- defaults are not sufficient for deployment. Based on verified documentation from docs.openclaw.ai/gateway/configuration-reference and security advisories.

## Exec security -- verified config reference

The `exec` tool runs arbitrary shell commands. Without approval policies, an agent with exec access can do anything the underlying OS user can do.

The exec security mode is configured via `tools.exec.security`:

### Exec security modes (verified from docs)

| Mode | Config value | Behavior | Use when |
|------|-------------|----------|----------|
| Deny all | `tools.exec.security: "deny"` | Block all exec calls | Agents that must never run commands |
| Allowlist only | `tools.exec.security: "allowlist"` | Only allowlisted commands execute; all others blocked | Production agents with predictable command patterns |
| Full (elevated) | `tools.exec.security: "full"` | Allow everything -- this is elevated mode | Trusted, isolated development environments only |
| Ask (confirmation) | `exec.ask` | Prompt user for confirmation before each exec | Interactive sessions where a human reviews commands |

**Important:** `"allowlist"` means only explicitly allowlisted commands run. This is the recommended mode for production. `"full"` is elevated access and should be treated as a security risk.

### Allowlist configuration

```yaml
tools:
  exec:
    security: "allowlist"
security:
  exec:
    allowed:
      - "npm test"
      - "npm run lint"
      - "git status"
      - "git diff"
      - "ls *"
      - "cat *"
    patterns:
      - "^git (status|diff|log|show)"    # Regex patterns
      - "^npm (test|run lint|run build)"
```

**Rules for allowlists:**
- Use exact commands for predictable operations
- Use regex patterns for command families
- The `*` wildcard in allowed commands matches any arguments
- Any command not matching an allowed entry or pattern is blocked
- Log blocked commands for audit purposes

### Legacy approval modes

Older configurations may use the `security.exec.approval` key with these values:

| Mode | Behavior |
|------|----------|
| none | All exec calls run without approval |
| prompt | User is prompted before each exec call |
| allowlist | Only pre-approved commands run |
| blocklist | All commands run except blocked patterns |

### Blocklist configuration

```yaml
security:
  exec:
    approval: blocklist
    blocked:
      - "rm -rf"
      - "sudo"
      - "chmod 777"
      - "curl | sh"
      - "wget | sh"
    patterns:
      - "^rm\\s+-rf\\s+/"              # Block recursive delete from root
      - "^sudo\\s+"                     # Block all sudo
      - "\\|\\s*(sh|bash|zsh)"          # Block pipe to shell
      - ">(\\s*/dev/sd|\\s*/dev/disk)"  # Block writes to devices
```

**When to use blocklist vs allowlist:**
- Allowlist: agent has a known, limited set of commands (prefer this)
- Blocklist: agent needs broad command access but certain operations are forbidden

## Elevated mode

Elevated mode grants the agent additional privileges beyond its normal tool profile. This is a powerful override that should be used sparingly.

### Configuration

```yaml
security:
  elevated:
    enabled: false          # Default: disabled
    tools:
      - exec               # Only these tools get elevated privileges
      - write
    requireApproval: true   # Require user approval before entering elevated mode
    timeout: 300            # Auto-exit elevated mode after 300 seconds
    auditLog: true          # Log all actions taken in elevated mode
```

### Rules for elevated mode

1. **Never enable globally.** Restrict to specific tools that genuinely need elevated access.
2. **Always require approval.** The agent should not enter elevated mode without user confirmation.
3. **Set a timeout.** Elevated mode should auto-expire. 5 minutes (300s) is a reasonable default.
4. **Enable audit logging.** Every action in elevated mode should be logged for review.
5. **Document why.** If elevated mode is needed, explain the use case in comments.

## Tool-loop detection

Prevents agents from entering infinite or excessive tool-calling loops. This is critical for agents with exec or automation tools.

### Configuration

```yaml
security:
  toolLoop:
    enabled: true
    maxConsecutiveCalls: 10     # Max same-tool calls in a row
    maxTotalCalls: 50           # Max total tool calls per session turn
    cooldownMs: 1000            # Minimum time between same-tool calls
    action: halt                # What to do: halt, warn, or throttle
```

### Actions on detection

| Action | Behavior | Use when |
|--------|----------|----------|
| halt | Stop the agent and report the loop | Production: prevent runaway costs and side effects |
| warn | Log a warning but allow continuation | Development: identify loops without blocking |
| throttle | Insert delays between calls | Semi-trusted: slow down the loop so a human can intervene |

### Tuning thresholds

- **maxConsecutiveCalls:** How many times the same tool can be called consecutively. 10 is a reasonable default. Increase for tools like `read` that are naturally called repeatedly. Decrease for `exec`.
- **maxTotalCalls:** Total tool calls per turn. 50 covers most legitimate workflows. Increase for complex multi-step tasks.
- **cooldownMs:** Minimum gap between same-tool calls. 1000ms prevents rapid-fire but does not noticeably slow legitimate use. Decrease for latency-sensitive tools.

## Multi-agent sandbox

When multiple agents operate in the same OpenClaw environment, sandboxing controls what each agent can see and do.

### Sandbox boundaries

```yaml
security:
  sandbox:
    filesystem:
      root: /home/agent/workspace    # Agent cannot access files outside this path
      readOnly:
        - /home/agent/workspace/config   # Read-only directories within the sandbox
      forbidden:
        - /home/agent/workspace/.secrets  # Completely inaccessible
    network:
      allowedDomains:
        - "api.example.com"
        - "*.internal.example.com"
      deniedPorts:
        - 22    # SSH
        - 3306  # MySQL direct access
    agents:
      visible:
        - planner
        - coder
      canMessage:
        - planner    # Can send messages to planner
      canReceiveFrom:
        - planner    # Can receive messages from planner
        - coder      # Can receive messages from coder
```

### Agent visibility

| Setting | Effect |
|---------|--------|
| `agents.visible` | Which other agents this agent knows exist (via agents_list) |
| `agents.canMessage` | Which agents this agent can send messages to |
| `agents.canReceiveFrom` | Which agents can send messages to this agent |

If `agents.visible` is empty, the agent cannot see any other agents even if `agents_list` tool is enabled.

### Filesystem boundaries

- **root:** The agent's filesystem operations are confined to this directory tree
- **readOnly:** Directories the agent can read but not modify
- **forbidden:** Directories the agent cannot access at all (even with read tool)

### Network restrictions

- **allowedDomains:** Whitelist of domains for web_fetch, browser, and gateway tools
- **deniedPorts:** Blocked ports regardless of domain (prevents direct database access, SSH, etc.)

## Security configuration checklist for production

### Minimum viable security (all production agents)

- [ ] exec approval policy is set (not `none`)
- [ ] Tool-loop detection is enabled with `halt` action
- [ ] Tool profile matches actual needs (not `full` without justification)
- [ ] IDENTITY.md does not contain secrets
- [ ] skills.entries uses environment variables for secrets, not plaintext in config

### Enhanced security (sensitive environments)

- [ ] Elevated mode disabled or restricted to specific tools with timeout and audit logging
- [ ] Filesystem sandbox configured with appropriate root and forbidden paths
- [ ] Network restrictions configured with allowed domains
- [ ] Multi-agent visibility scoped (agents only see what they need)
- [ ] Exec allowlist used instead of blocklist
- [ ] Audit logging enabled for all security-relevant actions

### Multi-agent security

- [ ] Each agent has its own sandbox configuration
- [ ] Agent message routing is explicitly configured (not open)
- [ ] No agent has unrestricted visibility of all other agents
- [ ] Shared resources (filesystem paths, network endpoints) are explicitly documented
- [ ] No circular message routing that could create agent-to-agent loops

## Gateway security -- verified from docs

The OpenClaw gateway has critical security defaults that must be changed for production.

### Gateway binds 0.0.0.0 by default

**The gateway binds to all network interfaces (0.0.0.0) by default.** For production, bind to localhost (127.0.0.1) unless you specifically need external access.

### No authentication by default

**The gateway has no authentication enabled by default.** You must manually enable authentication. Without it, anyone with network access to the gateway can control the agent.

### Gateway controlUi security flags

These flags exist for development convenience and must NEVER be enabled in production:

| Flag | What it does | Production setting |
|------|-------------|-------------------|
| `gateway.controlUi.dangerouslyAllowHostHeaderOriginFallback` | Allows fallback to Host header for origin checks | NEVER enable in production |
| `gateway.controlUi.allowInsecureAuth` | Allows authentication without TLS | NEVER enable in production |
| `gateway.controlUi.dangerouslyDisableDeviceAuth` | Disables device-based authentication | NEVER enable in production |

### Gateway hardening checklist

- [ ] Bind gateway to `127.0.0.1`, not `0.0.0.0`
- [ ] Enable authentication
- [ ] Do not set any `dangerously*` flags
- [ ] Do not enable `allowInsecureAuth`
- [ ] Use TLS for all gateway connections
- [ ] Treat the gateway token as a crown jewel -- use Docker secrets or equivalent secret management

## Cron security

Cron configuration for agent scheduled tasks:

| Key | Type | Default | Description |
|---|---|---|---|
| `cron.enabled` | boolean | `true` | Enable cron scheduling |

Disable cron entirely by setting `cron.enabled: false` or via the environment variable `OPENCLAW_SKIP_CRON=1`.

For agents that do not need scheduled tasks, disable cron to reduce attack surface.

## Skills security config

Skills loading has security-relevant configuration:

| Key | Type | Default | Description |
|---|---|---|---|
| `skills.load.watch` | boolean | `true` | Watch for skill file changes and auto-reload |
| `skills.load.watchDebounceMs` | integer | `250` | Debounce interval for file watcher |
| `skills.load.extraDirs` | array | `[]` | Additional directories to load skills from |
| `skills.entries.<key>.enabled` | boolean | -- | Enable/disable a specific skill |
| `skills.entries.<key>.apiKey` | string | -- | API key for the skill (use secret management) |
| `skills.entries.<key>.env` | object | -- | Environment variables for the skill |
| `skills.entries.<key>.config` | object | -- | Additional config for the skill |
| `skills.allowBundled` | array | -- | Whitelist of bundled skills to allow (restrict which built-in skills load) |

**Use `skills.allowBundled` to restrict which bundled skills are available.** This prevents unknown or unnecessary bundled skills from loading.

## Real-world security threats -- from community reports

### ClawHavoc: malicious skills on ClawHub

Community audit (reported on Reddit) found **824 malicious skills on ClawHub, representing 12% of all published skills.** These skills contained:
- Data exfiltration payloads
- Credential theft mechanisms
- Unauthorized network access
- Backdoors disguised as utility functions

**Mitigation:** Always audit skills before installing. Pin skill versions. Verify the publisher. Use `skills.allowBundled` to whitelist only trusted bundled skills. Never blindly install skills from ClawHub without review.

### ClawJacked: CVE-2026-25253

**CVE-2026-25253 (CVSS 8.8)** -- ClawJacked vulnerability that affected **135,000+ OpenClaw instances**. This was a skill supply-chain attack that allowed:
- Remote code execution via crafted skill packages
- Privilege escalation through skill loading mechanisms
- Lateral movement across multi-agent deployments

**Mitigation:**
- Update OpenClaw to the patched version immediately
- Audit all installed skills for tampering
- Pin skill versions in configuration
- Monitor skill loading logs for unexpected loads
- Use `skills.allowBundled` to restrict bundled skills

### Gateway token as crown jewel

The gateway authentication token provides full control over the agent. Community consensus (Reddit):
- Treat the gateway token like a database root password
- Store in Docker secrets, Vault, or equivalent secret management
- Never commit to version control
- Rotate regularly
- Monitor for unauthorized usage

## Common security mistakes

| Mistake | Risk | Fix |
|---------|------|-----|
| No exec approval policy | Agent can run any command | Set `tools.exec.security: "allowlist"` |
| Tool-loop detection disabled | Agent can make unlimited tool calls, running up costs | Enable with halt action |
| Full profile without justification | Maximum attack surface | Use the most restrictive profile that works |
| Secrets in IDENTITY.md | Secrets leak into LLM context | Use skills.entries.apiKey or env vars |
| No filesystem sandbox | Agent can read/write anywhere the OS user can | Set sandbox root |
| Open agent messaging | Any agent can message any other | Configure canMessage and canReceiveFrom |
| Elevated mode without timeout | Agent stays elevated indefinitely | Set timeout to 300 seconds or less |
| Blocklist instead of allowlist for exec | Novel dangerous commands are not caught | Use allowlist for production |
| Gateway bound to 0.0.0.0 | Exposed to entire network | Bind to 127.0.0.1 |
| No gateway authentication | Anyone with network access controls the agent | Enable authentication |
| Unaudited ClawHub skills | 12% of ClawHub skills are malicious | Audit all skills, pin versions, verify publishers |
| Gateway token in version control | Full agent control compromised | Use Docker secrets or Vault |
| Not patching ClawJacked (CVE-2026-25253) | RCE affecting 135K+ instances | Update immediately, audit installed skills |
