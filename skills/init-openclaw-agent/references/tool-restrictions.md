# Tool Restrictions

Fine-grained control over which tools an agent can use. Tool restrictions layer on top of profiles: the profile sets the baseline, and allow/deny lists adjust it.

## Core rule: deny ALWAYS wins over allow

If a tool appears in both `tools.allow` and `tools.deny`, it is **always denied**. This is non-negotiable and cannot be overridden. The deny list has absolute priority regardless of where the allow originates (profile, explicit allow, or provider config). Design your config with this in mind.

```yaml
# Result: web_search is DENIED (deny wins, always)
tools:
  allow:
    - web_search
  deny:
    - web_search
```

## Configuration hierarchy

Restrictions are evaluated in this order:

1. **Profile** sets the default allow list (default: `"coding"` for new local configs when unset)
2. **tools.allow** adds specific tools beyond the profile
3. **tools.deny** removes specific tools regardless of profile or allow list (deny ALWAYS wins)
4. **tools.byProvider** applies provider-scoped restrictions on top of everything

## tools.allow

Adds specific tools to the agent's available set, beyond what the profile provides.

```yaml
profile: minimal
tools:
  allow:
    - web_search      # Add individual tool
    - web_fetch       # Add another individual tool
    - group:memory    # Add entire tool group
```

**When to use:**
- The profile is almost right but missing 1-3 tools
- You need a specific advanced tool without upgrading the entire profile

**When NOT to use:**
- You need most tools from a higher profile -- just use that profile instead
- You are adding more than 5-6 tools -- reconsider the base profile choice

## tools.deny

Blocks specific tools regardless of profile or allow list. This is the strongest restriction.

```yaml
profile: coding
tools:
  deny:
    - exec           # Block individual tool
    - process        # Block another individual tool
    - group:automation  # Block entire group
```

**When to use:**
- A tool in the profile is dangerous for this agent's context
- Regulatory or policy requirements prohibit certain capabilities
- The agent's role does not justify a tool that the profile includes

**Best practice:** Always document WHY a tool is denied.

```yaml
tools:
  deny:
    - exec           # Agent handles user-facing chat; no shell access needed
    - cron           # No recurring tasks in this agent's scope
    - gateway        # Network boundary restricted by security policy
```

## Tool groups

Groups are shorthand for sets of related tools. Use them for broad allow/deny when individual tool listing would be verbose.

| Group | Includes | Typical use case |
|-------|----------|-----------------|
| `group:fs` | read, write, edit, apply_patch | Allow/deny all filesystem operations |
| `group:runtime` | exec, process | Allow/deny all command execution |
| `group:web` | web_search, web_fetch, browser, gateway | Allow/deny all network access |
| `group:ui` | canvas, image, tts | Allow/deny visual/audio tools |
| `group:memory` | memory_search, memory_get | Allow/deny memory access |
| `group:sessions` | sessions, agents_list | Allow/deny session management |
| `group:messaging` | message | Allow/deny sending messages |
| `group:nodes` | nodes | Allow/deny node graph management |
| `group:automation` | cron | Allow/deny scheduled tasks |

### Group + individual override

You can allow a group but deny specific tools within it:

```yaml
tools:
  allow:
    - group:web        # Allow all web tools
  deny:
    - browser          # But not browser automation
    - gateway          # And not gateway access
```

Result: agent gets web_search and web_fetch, but not browser or gateway.

You can also deny a group but allow specific tools within it:

```yaml
tools:
  deny:
    - group:fs         # Deny all filesystem tools
  allow:
    - read             # But allow reading
```

**Warning:** Since deny always wins, and `group:fs` expands to include `read`, the deny on `group:fs` will override the individual allow on `read`. To achieve this pattern, deny only the specific tools you want to block:

```yaml
tools:
  deny:
    - write
    - edit
    - apply_patch
  # read remains allowed via the profile
```

## tools.byProvider

Applies restrictions scoped to a specific provider. Useful when multiple providers are configured and you want different tool access per provider.

```yaml
tools:
  byProvider:
    openai:
      deny:
        - exec
        - process
    anthropic:
      allow:
        - group:fs
        - group:runtime
```

**When to use:**
- Different providers have different trust levels
- Compliance requires limiting capabilities per provider
- Testing a new provider with restricted access before full rollout

## Common restriction patterns

### Read-only agent

```yaml
profile: minimal
tools:
  deny:
    - exec           # Remove exec to make truly read-only
  allow:
    - web_search     # Allow searching for context
```

### Code assistant without network

```yaml
profile: coding
tools:
  deny:
    - group:web      # No network access
```

### Full agent with safety rails

```yaml
profile: full
tools:
  deny:
    - cron           # No scheduled tasks
    - nodes          # No node graph manipulation
    - gateway        # No direct API gateway access
    - agents_list    # No multi-agent discovery
```

### Multi-agent reviewer (receives work, returns comments)

```yaml
profile: minimal
tools:
  allow:
    - web_search     # Research context
    - memory_search  # Recall past reviews
    - memory_get     # Retrieve specific memories
    - message        # Send review comments to other agents
```

### Data analyst

```yaml
profile: minimal
tools:
  allow:
    - web_fetch      # Fetch data from APIs
    - web_search     # Research context
    - group:memory   # Remember analysis results
  deny:
    - exec           # Override minimal's exec -- no shell access
```

## Debugging tool access

When a tool is unexpectedly blocked:

1. **Check the deny list first.** Deny always wins. If the tool or its group is in `tools.deny`, it is blocked.
2. **Check the profile.** Is the tool included in the active profile?
3. **Check allow list.** If not in the profile, is it explicitly allowed?
4. **Check byProvider.** If provider-scoped restrictions exist, they may override global settings.
5. **Check group expansion.** A group deny expands to all member tools and overrides individual allows.

### Diagnostic steps

```
Tool "web_search" is blocked. Why?
|
+-- Is it in tools.deny? -------- YES -> That is why. Remove from deny to unblock.
|                                  NO -> Continue
+-- Is group:web in tools.deny? - YES -> That is why. Remove group deny or use individual denies.
|                                  NO -> Continue
+-- Is it in the profile? ------- YES -> Should be allowed. Check byProvider restrictions.
|                                  NO -> Continue
+-- Is it in tools.allow? ------- YES -> Should be allowed. Check byProvider restrictions.
|                                  NO -> That is why. Add to tools.allow.
```

## Validation checklist

- [ ] Every denied tool has a documented reason
- [ ] No tool appears in both allow and deny (unless intentionally denied)
- [ ] Group denies are intentional (they block ALL tools in the group)
- [ ] byProvider restrictions are tested per provider
- [ ] Actual tool access matches intended access after config changes
- [ ] The config is readable by future maintainers
