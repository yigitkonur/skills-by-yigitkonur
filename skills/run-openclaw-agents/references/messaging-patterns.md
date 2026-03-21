# Messaging Patterns

Guide to sending cross-platform messages from OpenClaw agents using the `message` tool, including confirmation workflows and safety protocols.

## The message tool

```
message platform=PLATFORM target=TARGET content="message text"
```

**Risk level: VERY HIGH.** This tool sends real messages to real humans on external platforms. Every call has an irreversible effect.

**Group:** `group:messaging`

**Supported platforms:**
- Discord (channels, DMs)
- Slack (channels, DMs)
- Telegram (chats, groups)
- Other platforms as configured in the OpenClaw instance

## Mandatory confirmation protocol

**Never send a cross-platform message without explicit user confirmation.**

Before every `message` call, present:

1. **Platform and target:** Where the message will go (e.g., "Slack #engineering channel")
2. **Content preview:** The exact text that will be sent
3. **Timing context:** Why now (e.g., "sub-agent completed the deployment")
4. **Irreversibility notice:** "This message cannot be unsent. Confirm?"

Wait for the user to explicitly approve before executing.

**The only exception:** If the user has pre-authorized a specific messaging pattern at the start of the session (e.g., "send a Slack message to #deploys after every successful deployment"). In this case, follow the pre-authorized pattern exactly -- do not expand scope.

## Message composition guidelines

### Content quality

- Be concise and actionable. Agents should send messages that help recipients take action, not walls of text.
- Include context: what happened, why the message is being sent, what (if anything) the recipient should do.
- Format appropriately for the platform (Markdown for Slack/Discord, plain text for SMS).
- Never include sensitive data (tokens, passwords, internal paths) in cross-platform messages.

### Message templates by use case

**Status notification:**
```
[Project/Task Name] Status Update
- Status: [completed/failed/needs attention]
- Summary: [one sentence]
- Action needed: [yes/no, and what]
```

**Deployment notification:**
```
Deployment: [service name] [version]
- Environment: [staging/production]
- Status: [success/failure]
- Changes: [brief summary or link]
```

**Escalation:**
```
Attention needed: [brief description]
- Context: [what was being done]
- Issue: [what went wrong]
- Urgency: [low/medium/high]
- Recommended action: [what the recipient should do]
```

## Inter-session vs. cross-platform messaging

| Need | Tool | Risk |
|---|---|---|
| Send data between OpenClaw sessions | `sessions_send` | HIGH |
| Send messages to external platforms (Slack, Discord, etc.) | `message` | VERY HIGH |

**Decision rule:** If the recipient is another OpenClaw agent or session, use `sessions_send`. If the recipient is a human on an external platform, use `message`.

Do not use `message` as a workaround for inter-session communication. Do not use `sessions_send` to reach external platforms.

## Messaging in multi-agent workflows

### Sub-agent sends messages

When a sub-agent needs to send external messages:
- Spawn it with the `messaging` tool profile
- Include the exact message content and target in the task description
- The parent session should have already confirmed the message with the user

### Supervisor-controlled messaging

Preferred pattern for most workflows:
1. Sub-agents do their work with `minimal` or `coding` profiles (no messaging access)
2. Sub-agents return results to the supervisor
3. The supervisor composes the message based on results
4. The supervisor confirms with the user and sends via `message`

This keeps messaging authority centralized and auditable.

### Batch messaging

When multiple messages need to be sent (e.g., notifying multiple channels):
1. Compose all messages first
2. Present the full batch to the user for confirmation
3. Send them in sequence after approval
4. Confirm delivery of each

Do not partially send a batch without user awareness.

## Platform-specific considerations

### Discord
- Respect rate limits (5 messages per 5 seconds per channel)
- Use embeds for structured data when supported
- Be aware of message length limits (2000 characters)

### Slack
- Use Block Kit for structured messages when supported
- Respect workspace-level messaging policies
- Thread replies when adding to an existing conversation

### Telegram
- Be aware of message formatting differences (HTML or Markdown)
- Respect bot rate limits
- Group messages may require different permissions than DMs

## Messaging anti-patterns

| Anti-pattern | Correct approach |
|---|---|
| Sending messages without user confirmation | Always confirm platform, target, content, and timing |
| Including sensitive data in external messages | Sanitize all content; use links to internal systems instead |
| Using `message` for inter-agent communication | Use `sessions_send` for agent-to-agent |
| Giving sub-agents `messaging` profile by default | Only when the sub-agent's primary purpose is communication |
| Sending messages in a loop without batch confirmation | Present all messages as a batch, confirm once, then send |
| Expanding pre-authorized messaging scope | Stick exactly to what was pre-authorized |

## Recovery when messaging fails

1. **Delivery failure:** Check platform connectivity and target validity. Do not retry without informing the user.
2. **Wrong target:** If a message was sent to the wrong channel/person, immediately inform the user. The message cannot be unsent.
3. **Content error:** If the message content was wrong, inform the user and send a correction (with confirmation).
4. **Rate limiting:** Wait for the rate limit window to pass. Inform the user of the delay.
