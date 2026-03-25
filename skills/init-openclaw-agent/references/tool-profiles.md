# Tool Profiles

Tool profiles are the starting point for an agent's tool surface. Pick the narrowest profile that fits the agent's job, then add or deny individual tools only where necessary.

All snippets in this reference are JSON5 fragments for the real `openclaw.json`. Use top-level `tools.*` for a single-agent runtime or global default, and `agents.list[].tools.*` when you are configuring one agent inside a multi-agent gateway.

## Profile facts that matter

- `tools.profile` sets the base allowlist before any allow/deny rules are applied
- `agents.list[].tools.profile` overrides the global profile for one agent
- `full` is effectively no profile restriction
- Local onboarding may write `tools.profile: "coding"` for a new local config when unset; do not treat that bootstrap choice as a design decision

## Profile overview

| Profile | Includes | Best for |
|---------|----------|----------|
| `full` | no restriction | highly trusted agents with genuinely broad needs |
| `coding` | `group:fs`, `group:runtime`, `group:sessions`, `group:memory`, `image` | coding, debugging, refactoring, analysis |
| `messaging` | `group:messaging`, `sessions_list`, `sessions_history`, `sessions_send`, `session_status` | chat, relay, notification, coordination |
| `minimal` | `session_status` | nearly tool-less agents or profiles that will be built up explicitly |

## Choosing a profile

```
What does the agent actually need to do?
|
+-- Works on files or code?
|   +-- Needs shell access? ---------------- coding
|   +-- Needs memory recall? -------------- coding
|   +-- Needs browser too? ---------------- coding + allow browser
|
+-- Mainly sends or relays messages?
|   +-- Needs session history? ------------ messaging
|   +-- Needs web search too? ------------- messaging + allow web_search/web_fetch
|
+-- Should start almost empty?
|   +-- Build the surface explicitly ------- minimal
|
+-- Truly broad trusted access? ------------ full
```

## Customization patterns

### Coding agent that also needs browser

```json5
{
  tools: {
    profile: "coding",
    allow: ["browser"],
  },
}
```

### Messaging agent with web lookup

```json5
{
  tools: {
    profile: "messaging",
    allow: ["web_search", "web_fetch"],
  },
}
```

### Minimal agent built into a read-only reviewer

```json5
{
  tools: {
    profile: "minimal",
    allow: ["read", "sessions_list", "sessions_history"],
    deny: ["write", "edit", "apply_patch", "exec", "process"],
  },
}
```

### Per-agent override in a multi-agent gateway

```json5
{
  agents: {
    list: [
      {
        id: "public",
        workspace: "~/.openclaw/workspace-public",
        tools: {
          profile: "messaging",
          allow: ["session_status"],
          deny: ["read", "write", "edit", "apply_patch", "exec", "process"],
        },
      },
    ],
  },
}
```

## When to move up or down

Move to a broader profile when:

- the agent repeatedly needs multiple tools outside its current profile
- you are compensating with long allow lists
- the role has changed permanently

Move to a narrower profile when:

- the agent never uses most of the enabled tools
- a security review flags unused capability
- the role has narrowed

## Common mistakes

| Mistake | Why it is wrong | Fix |
|---------|-----------------|-----|
| Assuming `minimal` means read-only shell access | `minimal` only includes `session_status` | Add the exact tools you want explicitly |
| Using `full` because you are not sure yet | Leaves the largest attack surface in place | Start narrower and expand intentionally |
| Forgetting that `browser` is outside `coding` | `coding` includes `image`, not browser/canvas | Allow `browser` explicitly if needed |
| Treating onboarding's default `coding` profile as the final answer | Bootstrap defaults are convenience, not policy | Re-evaluate the profile for the agent's actual role |

## Validation checklist

- [ ] The selected profile matches the agent's actual job
- [ ] Extra tools were added only when the base profile was too narrow
- [ ] Any high-risk tools have a clear reason
- [ ] The profile scope is correct: global default vs one named agent
