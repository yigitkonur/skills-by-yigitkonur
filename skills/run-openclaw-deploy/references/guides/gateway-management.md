# Gateway Management

The gateway manages the OpenClaw instance and serves as the control plane for all agent interactions, messaging channels, and LLM provider routing.

## Gateway lifecycle

### Starting the gateway

The gateway starts automatically with the OpenClaw process. If it needs a manual restart:

```bash
# Use the gateway tool (preferred method)
openclaw gateway restart

# Or use the `gateway` tool from within an agent session
# The gateway tool can restart the gateway without restarting the entire instance
```

### When to restart the gateway

- After changing LLM provider configuration
- After adding or removing messaging channels
- After updating gateway security settings
- When the gateway becomes unresponsive
- After updating OpenClaw to a new version

### Gateway status check

```bash
# Check gateway status
openclaw gateway status

# Expected output includes:
# - Gateway state (running, stopped, error)
# - Connected channels
# - Active LLM provider
# - Uptime
# - Recent errors
```

## Messaging channel configuration

OpenClaw supports multiple messaging channels for agent interaction.

### Supported channels

| Channel | Authentication | Key features |
|---------|---------------|--------------|
| WhatsApp | WhatsApp Business API credentials | Rich media, end-to-end encryption |
| Telegram | Bot token from BotFather | Inline keyboards, file sharing |
| Slack | OAuth2 or bot token | Thread support, app integration |
| Discord | Bot token | Server/channel routing, slash commands |
| iMessage | Apple credentials on macOS node | Requires macOS, native Apple integration |

### Channel setup pattern

Every channel follows the same setup pattern:

1. **Register** with the platform (create bot/app, get credentials)
2. **Configure** credentials in OpenClaw (via environment variables)
3. **Route** the channel to the gateway
4. **Test** by sending a message through the channel
5. **Verify** the response arrives correctly

### Example: Slack channel configuration

```yaml
channels:
  slack:
    enabled: true
    credentials:
      bot_token: "${SLACK_BOT_TOKEN}"
      signing_secret: "${SLACK_SIGNING_SECRET}"
    # Route specific agent profiles to Slack
    default_agent: "general-assistant"
    # Channel-specific agent overrides
    channel_overrides:
      "#engineering": "code-assistant"
      "#support": "support-agent"
```

### Example: Telegram channel configuration

```yaml
channels:
  telegram:
    enabled: true
    credentials:
      bot_token: "${TELEGRAM_BOT_TOKEN}"
    default_agent: "general-assistant"
    # Restrict to specific Telegram chat IDs for security
    allowed_chats:
      - "123456789"
      - "-100987654321"  # Group chat
```

### iMessage channel (requires macOS node)

iMessage requires a macOS node because it depends on Apple's Messages framework:

- Configure a remote macOS node (see container-setup.md)
- Install iMessage dependencies on the macOS node
- Route the iMessage channel to the macOS node
- Test with a real iMessage conversation

## LLM provider configuration

OpenClaw supports 25+ LLM providers with single-config switching.

### Provider setup

```yaml
llm:
  # Primary provider
  primary:
    provider: "anthropic"
    model: "claude-sonnet-4-20250514"
    api_key: "${ANTHROPIC_API_KEY}"

  # Fallback provider (used when primary is unavailable)
  fallback:
    provider: "openai"
    model: "gpt-4o"
    api_key: "${OPENAI_API_KEY}"

  # Provider switching rules
  switching:
    # Switch to fallback after N consecutive failures
    failure_threshold: 3
    # Cooldown before retrying primary (seconds)
    cooldown_seconds: 300
    # Health check interval for providers
    health_check_interval: 60
```

### Switching providers

To switch the active LLM provider:

```bash
# Switch primary provider
openclaw config set llm.primary.provider openai
openclaw config set llm.primary.model gpt-4o

# Restart gateway to apply
openclaw gateway restart

# Verify the new provider is active
openclaw gateway status
```

### Multi-provider routing

Route different skills or channels to different providers:

```yaml
llm:
  routing:
    # Code-heavy skills use Claude
    skills:
      "build-*": { provider: "anthropic", model: "claude-sonnet-4-20250514" }
      "review-*": { provider: "anthropic", model: "claude-sonnet-4-20250514" }

    # General conversation uses a cost-effective model
    channels:
      slack: { provider: "openai", model: "gpt-4o-mini" }
      telegram: { provider: "anthropic", model: "claude-haiku" }

    # Default for anything not matched
    default: { provider: "anthropic", model: "claude-sonnet-4-20250514" }
```

### Provider health monitoring

Monitor LLM provider health to detect outages before they affect users:

```yaml
llm:
  monitoring:
    enabled: true
    # Ping providers periodically
    health_check_interval: 60
    # Alert if latency exceeds threshold
    latency_alert_ms: 5000
    # Alert if error rate exceeds threshold
    error_rate_alert_percent: 10
    # Use model-usage skill for cost tracking
    cost_tracking: true
```

## Gateway troubleshooting

### Gateway won't start

1. Check logs for error messages: `openclaw logs --tail 50`
2. Verify LLM provider credentials are set in environment variables
3. Check that required ports are not already in use
4. Verify configuration file syntax

### Gateway starts but channels are disconnected

1. Check channel credentials in environment variables
2. Verify the platform-side webhook URL points to your gateway
3. Check network connectivity from the gateway to the messaging platform
4. Review channel-specific logs for authentication errors

### Gateway is slow or timing out

1. Check LLM provider latency via `model-usage` skill
2. Review resource utilization (CPU, memory, network)
3. Check if tool-loop detection has been triggered
4. Consider switching to a faster LLM provider for latency-sensitive channels

### Provider failover not working

1. Verify fallback provider credentials are configured
2. Check that `switching.failure_threshold` is set correctly
3. Review logs for failover trigger events
4. Test failover manually by temporarily invalidating the primary provider key

## Gateway configuration best practices

- Always configure at least one fallback LLM provider
- Use channel-specific agent profiles to match the right agent to the right audience
- Set provider health check intervals based on your SLA requirements
- Route cost-sensitive channels to cost-effective models
- Keep gateway restart procedures documented and tested
- Monitor gateway uptime as a primary health indicator

## Steering experiences

### SE-01: Forgetting to restart gateway after config changes
Configuration changes are not applied until the gateway restarts. Always use `openclaw gateway restart` or the `gateway` tool after any configuration change.

### SE-02: Channel credentials in config files instead of env vars
Credentials placed directly in YAML config files are exposed if the config is version-controlled or backed up without encryption. Always use environment variable references.

### SE-03: No fallback provider configured
When the primary LLM provider has an outage, the entire instance goes down. Always configure at least one fallback provider with tested credentials.
