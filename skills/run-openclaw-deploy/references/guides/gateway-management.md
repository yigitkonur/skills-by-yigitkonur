# Gateway Management

The gateway manages the OpenClaw instance and serves as the control plane for all agent interactions, messaging channels, and LLM provider routing.

## Critical gateway facts

| Fact | Detail |
|------|--------|
| **Default bind address** | `0.0.0.0` -- exposes to all interfaces. MUST bind to `localhost` |
| **Default auth** | None -- must enable manually |
| **Default HTTPS** | None -- need reverse proxy (Caddy easiest) |
| **Updates** | Manual only -- config format changes break things occasionally |

See security-hardening.md for full gateway security configuration including the `dangerouslyAllowHostHeaderOriginFallback`, `allowInsecureAuth`, and `dangerouslyDisableDeviceAuth` flags.

## Gateway lifecycle

### Starting the gateway

The gateway starts automatically with the OpenClaw process. If it needs a manual restart:

```bash
# Use the gateway tool (preferred method)
openclaw gateway restart

# Or use the `gateway` tool from within an agent session
```

### When to restart the gateway

- After changing LLM provider configuration
- After adding or removing messaging channels
- After updating gateway security settings
- When the gateway becomes unresponsive
- After updating OpenClaw to a new version

**Warning:** Config format changes between OpenClaw versions occasionally break things. Always back up configuration before updating and restart.

### Gateway status check

```bash
openclaw gateway status

# Expected output includes:
# - Gateway state (running, stopped, error)
# - Connected channels
# - Active LLM provider
# - Uptime
# - Recent errors
```

## Messaging channel configuration

### Supported channels

| Channel | Authentication | Key features | Known issues |
|---------|---------------|--------------|--------------|
| WhatsApp | WhatsApp Business API credentials | Rich media, E2E encryption | **Disconnects after a few days without activity** -- must keep session alive |
| Telegram | Bot token from BotFather | Inline keyboards, file sharing | Stable |
| Slack | OAuth2 or bot token | Thread support, app integration | Stable |
| Discord | Bot token | Server/channel routing, slash commands | Stable |
| iMessage | Apple credentials on macOS node | Requires macOS, native Apple integration | Requires remote macOS node |

### WhatsApp session keepalive

WhatsApp connections disconnect after a few days of inactivity. This is a known platform behavior reported by multiple operators.

**Mitigations:**
- Schedule a periodic keepalive message via cron (e.g., every 12 hours)
- Set up monitoring alerts for WhatsApp channel disconnection
- Configure auto-reconnect in the channel settings
- Be aware that reconnection can trigger message replay, which combined with no spending caps can cause large API bills

### Channel setup pattern

Every channel follows the same setup pattern:

1. **Register** with the platform (create bot/app, get credentials)
2. **Set API spending caps** before connecting (see monitoring-and-ops.md)
3. **Configure** credentials in OpenClaw (via environment variables)
4. **Route** the channel to the gateway
5. **Test** by sending a message through the channel
6. **Verify** the response arrives correctly
7. **Set up monitoring** for channel health

### Example: Slack channel configuration

```yaml
channels:
  slack:
    enabled: true
    credentials:
      bot_token: "${SLACK_BOT_TOKEN}"
      signing_secret: "${SLACK_SIGNING_SECRET}"
    default_agent: "general-assistant"
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
    allowed_chats:
      - "123456789"
      - "-100987654321"
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
  primary:
    provider: "anthropic"
    model: "claude-sonnet-4-20250514"
    api_key: "${ANTHROPIC_API_KEY}"

  fallback:
    provider: "openai"
    model: "gpt-4o"
    api_key: "${OPENAI_API_KEY}"

  switching:
    failure_threshold: 3
    cooldown_seconds: 300
    health_check_interval: 60
```

### Switching providers

```bash
openclaw config set llm.primary.provider openai
openclaw config set llm.primary.model gpt-4o

# Restart gateway to apply
openclaw gateway restart

# Verify the new provider is active
openclaw gateway status
```

### Multi-provider routing

```yaml
llm:
  routing:
    skills:
      "build-*": { provider: "anthropic", model: "claude-sonnet-4-20250514" }
      "review-*": { provider: "anthropic", model: "claude-sonnet-4-20250514" }
    channels:
      slack: { provider: "openai", model: "gpt-4o-mini" }
      telegram: { provider: "anthropic", model: "claude-haiku" }
    default: { provider: "anthropic", model: "claude-sonnet-4-20250514" }
```

### Provider health monitoring

```yaml
llm:
  monitoring:
    enabled: true
    health_check_interval: 60
    latency_alert_ms: 5000
    error_rate_alert_percent: 10
    cost_tracking: true
```

## Gateway troubleshooting

### Gateway won't start

1. Check logs for error messages: `openclaw logs --tail 50`
2. **Verify Node.js v22** is installed: `node --version`
3. Verify LLM provider credentials are set in environment variables
4. Check that required ports are not already in use
5. Verify configuration file syntax (format changes between versions)
6. Check RAM: need at least 1.5-2 GB idle, 4 GB recommended

### Gateway starts but channels are disconnected

1. Check channel credentials in environment variables
2. Verify the platform-side webhook URL points to your gateway
3. Check network connectivity from the gateway to the messaging platform
4. Review channel-specific logs for authentication errors
5. **WhatsApp specifically:** check if session expired due to inactivity

### Gateway is slow or timing out

1. Check LLM provider latency via `model-usage` skill
2. Review resource utilization (need 4 GB RAM recommended)
3. Check if tool-loop detection has been triggered
4. Consider switching to a faster LLM provider for latency-sensitive channels

### Provider failover not working

1. Verify fallback provider credentials are configured
2. Check that `switching.failure_threshold` is set correctly
3. Review logs for failover trigger events
4. Test failover manually by temporarily invalidating the primary provider key

## Gateway configuration best practices

- **Always bind to localhost** -- never expose the gateway directly to the internet
- Always configure at least one fallback LLM provider
- **Set API spending caps before connecting channels** -- retry loops cause $300-600 bills
- Use channel-specific agent profiles to match the right agent to the right audience
- Set provider health check intervals based on your SLA requirements
- Route cost-sensitive channels to cost-effective models
- Keep gateway restart procedures documented and tested
- Monitor gateway uptime as a primary health indicator (slow failure is worse than immediate)
- **Set up uptime monitoring** (UptimeRobot, Better Uptime, etc.) -- essential for production

## Steering experiences

### SE-01: Forgetting to restart gateway after config changes
Configuration changes are not applied until the gateway restarts. Always use `openclaw gateway restart` after any configuration change.

### SE-02: Channel credentials in config files instead of env vars
Credentials placed directly in YAML config files are exposed if the config is version-controlled or backed up without encryption. Always use environment variable references.

### SE-03: No fallback provider configured
When the primary LLM provider has an outage, the entire instance goes down. Always configure at least one fallback provider.

### SE-04: WhatsApp session drops after inactivity
WhatsApp disconnects after a few days without activity. Set up a cron-based keepalive and monitoring alerts for channel health.

### SE-05: Spending spike from channel reconnection
When a messaging channel reconnects after an outage, queued messages can trigger a burst of LLM API calls. Set spending caps with `limit_action: "stop"` before this happens.
