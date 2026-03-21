# Risk and Security

Comprehensive risk management guide for OpenClaw multi-agent orchestration. Covers tool risk classification, confirmation protocols, hardware access, and security boundaries.

## Tool risk classification

Every orchestration tool has a risk level that determines the required confirmation protocol.

| Tool | Risk | Group | Side effects |
|---|---|---|---|
| `sessions_list` | LOW | `group:sessions` | None (read-only) |
| `sessions_history` | LOW | `group:sessions` | None (read-only) |
| `session_status` | LOW | `group:sessions` | None (read-only) |
| `agents_list` | LOW | -- | None (read-only) |
| `subagents` (status) | LOW | `group:sessions` | None (read-only) |
| `sessions_yield` | LOW | `group:sessions` | Blocks execution but no side effects |
| `subagents` (stop) | MEDIUM | `group:sessions` | Terminates a running session |
| `sessions_spawn` | HIGH | `group:sessions` | Creates a new agent with tool access |
| `sessions_send` | HIGH | `group:sessions` | Sends data that can trigger actions in another session |
| `message` | VERY HIGH | `group:messaging` | Sends irreversible messages to real humans on external platforms |
| `nodes` | VERY HIGH | -- | Controls physical hardware (screenshots, GPS, camera) on remote devices |

## Confirmation protocols by risk level

### LOW risk
- No explicit confirmation needed
- Proceed directly
- Log the action for audit trail

### MEDIUM risk
- State what you are about to do and why
- Proceed unless the context suggests caution
- Example: "I will stop sub-agent session X because it has completed its task."

### HIGH risk
- State the action, its consequences, and why it is needed
- Wait for user acknowledgment before proceeding
- Example: "I will spawn a new sub-agent with the coding profile to refactor /src/auth/. This gives it file write and shell access. Proceed?"

### VERY HIGH risk
- Present full details: action, target, content/scope, consequences, irreversibility
- Wait for explicit user confirmation
- Document the user's confirmation
- Example: "I will send this message to Slack #engineering: [preview]. This cannot be unsent. Confirm?"

## Tool profile security

Tool profiles are the primary mechanism for limiting sub-agent capabilities. They form a security boundary.

### Profile escalation rules

1. **Default to minimal.** Every sub-agent starts with the narrowest profile.
2. **Escalate on evidence.** Only expand the profile when a permission error demonstrates the need.
3. **Never pre-escalate.** Do not give a broader profile "in case" the sub-agent needs it later.
4. **Document escalations.** When you escalate a profile, record why.
5. **Separate concerns.** If a task needs both coding and messaging, consider splitting into two sub-agents with separate profiles rather than one with full access.

### Profile boundaries

| Profile | Can do | Cannot do |
|---|---|---|
| `minimal` | Read files, analyze data, answer questions | Write files, run commands, access network, send messages |
| `coding` | All minimal + write files, run shell, git operations | Send external messages, access hardware |
| `messaging` | Send messages via `message` and `sessions_send` | Write files, run commands, access hardware |
| Full | Everything | Nothing is restricted |

### Multi-profile tasks

When a task genuinely requires multiple capability domains:

**Option A: Split into sub-agents**
- Sub-agent 1 with `coding` profile does the code work
- Sub-agent 2 with `messaging` profile sends the notification
- Parent coordinates and passes results between them

**Option B: Full profile (last resort)**
- Use only when the task cannot be cleanly split
- Add extra monitoring: check `sessions_history` more frequently
- Set a tighter scope in the task description

Option A is preferred because it limits the blast radius of any individual sub-agent.

## Nodes: hardware access

The `nodes` tool provides cross-device hardware control. This is the highest-risk capability in the orchestration toolkit.

### Available capabilities

| Capability | What it does | Risk |
|---|---|---|
| Screenshot | Captures screen content from a remote device | VERY HIGH -- may capture sensitive information |
| GPS | Reads geographic location from a device | VERY HIGH -- privacy-sensitive |
| Camera | Captures images from a device camera | VERY HIGH -- privacy-sensitive |

### Nodes confirmation protocol

Before any `nodes` call:

1. **State the specific capability** needed (screenshot, GPS, camera)
2. **State the target device** (which node)
3. **State the purpose** (why this hardware access is needed)
4. **State what data will be captured** and how it will be used
5. **Confirm the data will not be sent to external platforms** unless separately approved
6. **Wait for explicit user confirmation**

### Nodes security rules

- Never access hardware capabilities without a clear, stated purpose
- Never combine `nodes` captures with `message` sends without separate confirmation for each
- Never store hardware-captured data beyond the immediate task scope
- Never access GPS or camera without a genuine task requirement (not for "testing" or "checking")
- If a sub-agent needs hardware access, it must be spawned with explicit user confirmation of the hardware capabilities it will use

## Multi-agent security considerations

### Session isolation

Each session has its own context and tool access. However:
- `sessions_send` can transmit data between sessions, breaking isolation
- A sub-agent with `coding` profile can potentially access files written by another sub-agent
- The parent session can read all sub-agent history via `sessions_history`

### Privilege escalation risks

Watch for these patterns:
- A `minimal` profile sub-agent requests data that only a `coding` profile agent could produce -- this may indicate a design problem
- A sub-agent asks to be re-spawned with a broader profile -- always verify the need
- Chains of `sessions_send` calls that effectively route data around profile restrictions

### Audit trail

For any orchestration involving HIGH or VERY HIGH risk tools:
1. Log which sub-agents were spawned and with what profiles
2. Log all inter-session messages sent
3. Log all external messages sent (platform, target, content summary)
4. Log all hardware accesses (capability, device, purpose)
5. Present the audit trail to the user at the end of the orchestration

## Security anti-patterns

| Anti-pattern | Correct approach |
|---|---|
| Spawning all sub-agents with full tool access | Use the narrowest profile per sub-agent |
| Skipping confirmation for HIGH/VERY HIGH tools | Always confirm based on risk level |
| Combining hardware capture with external messaging without separate confirmations | Confirm each independently |
| Storing hardware-captured data beyond task scope | Delete or scope data to the immediate need |
| Trusting sub-agent self-reports without inspecting history | Use `sessions_history` to audit actual behavior |
| Allowing sub-agents to escalate their own profiles | Only the parent session or user can authorize escalation |

## Incident response

If something goes wrong during orchestration:

1. **Stop all sub-agents** immediately via `subagents stop`
2. **Assess the impact:** What actions were taken? What data was sent? What was accessed?
3. **Report to the user:** Full transparency on what happened
4. **Do not attempt to "fix" by sending more messages or taking more actions** without user direction
5. **Preserve the audit trail:** Do not delete session histories
