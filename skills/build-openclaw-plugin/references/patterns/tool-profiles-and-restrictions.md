# Tool Profiles and Restrictions

OpenClaw provides a layered access control system for tools: profiles set the baseline, allow/deny lists fine-tune access, and provider-specific restrictions add per-model rules.

## Layer 1: Tool profiles

Profiles define preset tool sets for different use cases. The active profile determines which tool groups are available by default.

### Profile definitions

**`full`** — All tools from all groups. No restrictions.

```
Includes: all groups (fs, runtime, web, ui, memory, sessions, messaging, nodes, automation, agents, media)
Use when: Unrestricted agent with full platform access
Risk: Highest — agent can do anything
```

**`coding`** — Tools for software development workflows.

```
Includes: group:fs + group:runtime + group:sessions + group:memory + group:media
Excludes: group:messaging, group:web, group:nodes, group:automation, group:agents, group:ui
Use when: Agent focuses on code reading, writing, execution, and testing
Risk: Medium — can access filesystem and run code
```

**`messaging`** — Tools for chat-focused agents.

```
Includes: group:messaging + session_list + session_history + session_send + session_status
Excludes: Everything else
Use when: Agent only needs to manage conversations
Risk: Low — limited to messaging operations
```

**`minimal`** — Absolute minimum for monitoring.

```
Includes: session_status only
Excludes: Everything else
Use when: Health checks, monitoring, status dashboards
Risk: Lowest — read-only session status
```

### Default behavior

New local configurations default to `tools.profile: "coding"` when no profile is explicitly set. Existing explicit profiles are preserved on upgrade.

### Exec security modes

The `tools.exec.security` config controls command execution policy:

| Mode | Behavior |
|---|---|
| `deny` | Block all host exec requests |
| `allowlist` | Allow only allowlisted commands (recommended for production) |
| `full` | Allow everything (equivalent to elevated mode) |

### Setting the active profile

The profile is set in the OpenClaw configuration, not in the plugin. As a plugin author, you should:

- Document which profile(s) your tools require
- Test your plugin under each relevant profile
- Handle gracefully when your tools are excluded by the active profile

### How profiles affect your plugin

When a user activates a profile that excludes your tool's group, the tool is not registered. Your plugin's `initialize()` still runs, but the tool is invisible to the model.

Design for this:

```typescript
// Good: Tool checks its own availability
const myTool: ToolDefinition = {
  name: 'web_scrape',
  group: 'group:web',  // Excluded in 'coding' and 'messaging' profiles
  // ...
};

// Your plugin should not assume this tool is always available
// Other tools in the plugin that don't depend on web_scrape should still work
```

## Layer 2: Allow/deny lists

Allow/deny lists provide fine-grained control on top of profiles.

### tools.alsoAllow (recommended for optional tools)

Adds tools to the active profile without creating a restrictive allowlist. Use this to enable plugin-provided tools like `lobster` or `llm-task` alongside core tools.

```json
{
  "tools": {
    "alsoAllow": ["lobster", "llm-task"]
  }
}
```

**Do NOT use `tools.allow` unless you want a restrictive allowlist that excludes core tools.** `tools.alsoAllow` adds on top of the profile; `tools.allow` replaces the profile baseline.

Per-agent: `agents.list[].tools.alsoAllow: ["lobster"]`

### tools.allow (restrictive)

Creates a restrictive allowlist. Only listed tools (plus profile defaults) are available. **Warning:** this excludes core tools not on the list.

```json
{
  "tools": {
    "allow": ["search_documents", "group:memory"]
  }
}
```

### tools.deny

Blacklists specific tools or groups. Listed tools are blocked regardless of profile or allow list.

```json
{
  "tools": {
    "deny": ["delete_file", "group:runtime"]
  }
}
```

### Resolution order

```
1. Start with the active profile's tool set
2. Apply allow list (adds tools/groups)
3. Apply deny list (removes tools/groups)
4. Deny ALWAYS wins over allow
```

**Example:** If `tools.allow` includes `execute_command` but `tools.deny` includes `group:runtime`, and `execute_command` belongs to `group:runtime`, then `execute_command` is DENIED.

### As a plugin author

You do not control allow/deny lists — the OpenClaw operator does. But you should:

- Assign tools to the correct group so operators can manage them logically
- Document each tool's group membership in your plugin README
- Never assume a tool is available at runtime — check for registration errors
- Design tools to be independently useful (not all-or-nothing dependencies)

## Layer 3: Provider-specific restrictions

The `tools.byProvider` configuration restricts which tools are available based on the active model provider.

```json
{
  "tools": {
    "byProvider": {
      "openai": {
        "deny": ["execute_shell"]
      },
      "anthropic": {
        "allow": ["group:fs", "group:runtime"]
      }
    }
  }
}
```

This is used when:

- Certain models cannot handle certain tool schemas reliably
- Security policies differ per model provider
- Some tools are only tested with specific models

### Resolution with provider restrictions

```
1. Start with profile + allow/deny resolution
2. Apply provider-specific allow/deny for the active provider
3. Provider deny still overrides provider allow
```

## Tool group membership

When registering tools, assign each to the most appropriate group:

| If your tool... | Assign to |
|---|---|
| Reads/writes files or directories | `group:fs` |
| Executes code or shell commands | `group:runtime` |
| Makes HTTP requests or scrapes web pages | `group:web` |
| Renders UI or displays content | `group:ui` |
| Stores/retrieves persistent memory | `group:memory` |
| Manages sessions | `group:sessions` |
| Sends or receives messages | `group:messaging` |
| Operates on workflow nodes | `group:nodes` |
| Triggers automated actions | `group:automation` |
| Spawns or manages sub-agents | `group:agents` |
| Processes audio, video, or images | `group:media` |

### Custom groups

If none of the built-in groups fit, you can define a custom group:

```json
{
  "name": "query_database",
  "group": "group:database"
}
```

Custom groups are NOT included in any predefined profile. They must be explicitly allowed by the operator. Document this requirement clearly.

## Testing under restrictions

When developing a plugin, test under multiple restriction configurations:

1. **Full profile, no lists** — verify all tools work
2. **Coding profile** — verify non-coding tools degrade gracefully
3. **Minimal profile** — verify the plugin does not crash
4. **Deny your tool's group** — verify the plugin still initializes
5. **Allow only specific tools** — verify partial tool sets work

```bash
# Test with different profiles by changing OpenClaw config
# Profile: minimal
OPENCLAW_TOOL_PROFILE=minimal openclaw start

# Deny a group
OPENCLAW_TOOLS_DENY=group:web openclaw start
```

## Common mistakes

| Mistake | Impact | Fix |
|---|---|---|
| Not assigning a group | Tool unreachable via group-based allow/deny | Always set `group` on every tool |
| Assuming tools are always available | Plugin crashes when a tool is denied | Check registration status, handle absence |
| Putting all tools in one custom group | Operators cannot granularly control access | Use built-in groups where possible |
| Ignoring provider restrictions | Tool breaks with certain models | Test with multiple providers |
| Hard-coding profile assumptions | Plugin breaks when profile changes | Design for graceful degradation |
