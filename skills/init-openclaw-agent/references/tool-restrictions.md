# Tool Restrictions

Tool restrictions are how you turn a profile into the exact tool surface an agent should have. The key rule is simple: every layer can narrow access, and denied tools stay denied.

All snippets in this reference are JSON5 fragments for the real `openclaw.json`.

## Core rule: deny always wins

If a tool appears in both allow and deny, it is denied.

```json5
{
  tools: {
    allow: ["web_search"],
    deny: ["web_search"],
  },
}
```

Result: `web_search` is denied.

## Where restrictions can live

| Scope | Keys |
|------|------|
| Global default | `tools.profile`, `tools.allow`, `tools.deny`, `tools.byProvider` |
| Per agent | `agents.list[].tools.profile`, `agents.list[].tools.allow`, `agents.list[].tools.deny`, `agents.list[].tools.byProvider` |
| Sandbox override | `tools.sandbox.tools` or `agents.list[].tools.sandbox.tools` |
| Sub-agent override | `tools.subagents.tools` |

## Effective filtering order

OpenClaw applies restrictions in this order:

1. Base profile
2. Provider profile override
3. Global allow/deny
4. Global provider allow/deny
5. Agent-specific allow/deny
6. Agent-specific provider allow/deny
7. Sandbox tool policy
8. Sub-agent tool policy

Earlier denies cannot be undone later.

## Allow and deny behavior

- `tools.allow` and `tools.deny` are case-insensitive
- `*` wildcards are supported
- `agents.list[].tools.*` is the safer place to restrict a single named agent
- `tools.byProvider` keys can be either `provider` or `provider/model`

## Tool groups

Use `group:*` shorthands when you want a whole category:

| Group | Expands to |
|------|------------|
| `group:runtime` | `exec`, `bash`, `process` |
| `group:fs` | `read`, `write`, `edit`, `apply_patch` |
| `group:sessions` | `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`, `sessions_yield`, `subagents`, `session_status` |
| `group:memory` | `memory_search`, `memory_get` |
| `group:web` | `web_search`, `web_fetch` |
| `group:ui` | `browser`, `canvas` |
| `group:automation` | `cron`, `gateway` |
| `group:messaging` | `message` |
| `group:nodes` | `nodes` |
| `group:openclaw` | all built-in OpenClaw tools |

Notes:

- `browser` is `group:ui`, not `group:web`
- `image` is not part of `group:ui`
- `bash` is accepted as an alias for `exec`, but `exec` is still the safest tool name to write explicitly in config

## Common patterns

### Read-only agent

```json5
{
  tools: {
    allow: ["read"],
    deny: ["write", "edit", "apply_patch", "exec", "process"],
  },
}
```

### Coding agent without network

```json5
{
  tools: {
    profile: "coding",
    deny: ["group:web", "browser"],
  },
}
```

### Messaging agent with only session coordination

```json5
{
  tools: {
    profile: "messaging",
    deny: ["read", "write", "edit", "apply_patch", "exec", "process", "browser"],
  },
}
```

### Provider-specific restriction

```json5
{
  tools: {
    profile: "coding",
    byProvider: {
      "google-antigravity": { profile: "minimal" },
      "openai/gpt-5.2": { allow: ["group:fs", "sessions_list"] },
    },
  },
}
```

### Restrict one agent in a multi-agent gateway

```json5
{
  agents: {
    list: [
      {
        id: "family",
        tools: {
          allow: ["read", "session_status"],
          deny: ["write", "edit", "apply_patch", "exec", "process", "browser", "gateway"],
        },
      },
    ],
  },
}
```

## Debugging blocked tools

When a tool is missing or blocked:

1. Check the active profile
2. Check global deny rules and group expansion
3. Check provider-specific restrictions
4. Check agent-specific restrictions if this is a named agent
5. Check sandbox or sub-agent tool policy if the agent runs there
6. Use `openclaw sandbox explain` when sandboxing is involved
7. Use `openclaw status` to confirm the runtime is loading the config you think it is

## Common mistakes

| Mistake | Why it is wrong | Fix |
|---------|-----------------|-----|
| Denying `group:web` to block browser | `group:web` does not include browser | Deny `browser` or `group:ui` |
| Editing only global `tools.*` for one named agent | Changes every agent that inherits the global default | Put the rule in `agents.list[].tools.*` |
| Expecting a later allow to override an earlier deny | OpenClaw only narrows access as it applies layers | Remove the deny or move the policy to the correct scope |
| Forgetting sandbox or sub-agent tool policy | The runtime may further narrow tools after your main allow/deny rules | Inspect sandbox and sub-agent policy too |

## Validation checklist

- [ ] The edit scope is correct: global vs per-agent
- [ ] No group shorthand accidentally blocks more than intended
- [ ] Provider-specific keys are spelled as `provider` or `provider/model`
- [ ] Denied tools still fail in a canary task
- [ ] Allowed tools are still present after sandbox or sub-agent filtering
