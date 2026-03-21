# Security Patterns

Security configuration for OpenClaw agents. Every production agent must have explicit security settings -- defaults are not sufficient for deployment.

## Exec approvals

The `exec` tool runs arbitrary shell commands. Without approval policies, an agent with exec access can do anything the underlying OS user can do.

### Approval modes

| Mode | Behavior | Use when |
|------|----------|----------|
| none | All exec calls run without approval | Trusted, isolated development environments only |
| prompt | User is prompted before each exec call | Interactive sessions where a human reviews commands |
| allowlist | Only pre-approved commands run; others are blocked | Production agents with predictable command patterns |
| blocklist | All commands run except blocked patterns | Agents that need flexibility but have known dangerous commands |

### Allowlist configuration

```yaml
security:
  exec:
    approval: allowlist
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

## Common security mistakes

| Mistake | Risk | Fix |
|---------|------|-----|
| No exec approval policy | Agent can run any command | Set approval to allowlist or prompt |
| Tool-loop detection disabled | Agent can make unlimited tool calls, running up costs | Enable with halt action |
| Full profile without justification | Maximum attack surface | Use the most restrictive profile that works |
| Secrets in IDENTITY.md | Secrets leak into LLM context | Use skills.entries.apiKey or env vars |
| No filesystem sandbox | Agent can read/write anywhere the OS user can | Set sandbox root |
| Open agent messaging | Any agent can message any other | Configure canMessage and canReceiveFrom |
| Elevated mode without timeout | Agent stays elevated indefinitely | Set timeout to 300 seconds or less |
| Blocklist instead of allowlist for exec | Novel dangerous commands are not caught | Use allowlist for production |
