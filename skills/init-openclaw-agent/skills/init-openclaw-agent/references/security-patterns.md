# Security and Execution Patterns

Security for OpenClaw agents lives in more than one place. The fastest way to break a literal executor is to blur those boundaries. Use this reference to keep tool policy, host exec approvals, sandboxing, and elevated mode distinct.

All snippets in this reference are JSON5 fragments for the real `openclaw.json` unless a section explicitly says it belongs in `exec-approvals.json`.

## Security surface map

| Concern | Primary location | Notes |
|---------|------------------|-------|
| Tool availability | `tools.*` or `agents.list[].tools.*` | Deny wins; this is the main tool surface |
| Host exec defaults | `tools.exec.*` | Timeouts, strict-inline-eval, safe bins, default behavior |
| Host exec approvals and allowlists | `~/.openclaw/exec-approvals.json` on the execution host | Separate file from `openclaw.json` |
| Elevated host exec access | `tools.elevated` plus optional `agents.list[].tools.elevated` | Only matters when sandboxing is in play |
| Tool-loop detection | `tools.loopDetection` or `agents.list[].tools.loopDetection` | Disabled by default |
| Sandbox boundaries | `agents.defaults.sandbox` or `agents.list[].sandbox` | Controls where tools run and how much workspace they can see |

## Exec policy vs exec approvals

These are related but different:

- `tools.exec.*` defines how exec behaves in runtime config
- `exec-approvals.json` stores host-local approval defaults and allowlists

OpenClaw uses the stricter effective policy of the two. If you tighten one side and forget the other, the runtime may still behave differently than you intended.

## Host exec approvals

Exec approvals live in:

```text
~/.openclaw/exec-approvals.json
```

on the machine that actually executes host commands.

That may be:

- the gateway host
- a node host
- the macOS companion app host

Important facts:

- approvals are local to the execution host
- `ask` prompts fall back to deny if no approval UI is available and fallback stays at the default
- allowlist entries are stored under `agents.<id>.allowlist` in `exec-approvals.json`

Policy knobs you need to understand:

- `security`: `deny`, `allowlist`, `full`
- `ask`: `off`, `on-miss`, `always`
- `askFallback`: what happens when prompting is required but unavailable

If you are changing host exec posture, inspect both `openclaw.json` and `exec-approvals.json`.

## Runtime exec settings

The runtime-side config lives in `tools.exec`:

```json5
{
  tools: {
    exec: {
      backgroundMs: 10000,
      timeoutSec: 1800,
      notifyOnExit: true,
      strictInlineEval: true,
      safeBins: ["head", "tail", "tr", "wc"],
    },
  },
}
```

Use `strictInlineEval: true` when allowlisted interpreters such as `node` or `python3` should still require approval for `-e` or `-c` style inline evaluation.

## Elevated mode

`tools.elevated` is the gateway's baseline gate for host exec while sandboxed:

```json5
{
  tools: {
    elevated: {
      enabled: true,
      allowFrom: {
        whatsapp: ["+15555550123"],
        discord: ["123456789012345678"],
      },
    },
  },
}
```

Key rules:

- `agents.list[].tools.elevated` can only further restrict the global baseline
- elevated does not override tool deny rules; if `exec` is denied, elevated cannot bring it back
- `/elevated on|ask|full` changes per-session behavior, not config files
- `full` skips exec approvals; `on` and `ask` still respect them

If you do not want sandboxed agents to escape to host exec, disable elevated globally or per agent.

## Tool-loop detection

Tool-loop detection is disabled by default. Enable it explicitly for agents that can burn cost or cause side effects through repeated tool calls.

```json5
{
  tools: {
    loopDetection: {
      enabled: true,
      historySize: 30,
      warningThreshold: 10,
      criticalThreshold: 20,
      globalCircuitBreakerThreshold: 30,
      detectors: {
        genericRepeat: true,
        knownPollNoProgress: true,
        pingPong: true,
      },
    },
  },
}
```

Use per-agent overrides when one agent is much riskier than the others:

```json5
{
  agents: {
    list: [
      {
        id: "safe-runner",
        tools: {
          loopDetection: {
            enabled: true,
            warningThreshold: 8,
            criticalThreshold: 16,
          },
        },
      },
    ],
  },
}
```

## Sandboxing

Sandboxing belongs under `agents.defaults.sandbox` or `agents.list[].sandbox`, not under a generic `security` block.

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        scope: "agent",
        workspaceAccess: "none",
      },
    },
  },
}
```

Important behaviors:

- `workspaceAccess: "none"` keeps the real agent workspace out of the sandbox
- `workspaceAccess: "ro"` mounts the agent workspace read-only
- `workspaceAccess: "rw"` mounts it read/write
- tool allow/deny policy still applies before sandbox rules
- `tools.elevated` is the escape hatch that runs `exec` on the host instead of inside the sandbox

If you are debugging sandbox behavior, use:

```bash
openclaw sandbox explain
```

## Practical hardening patterns

### Read-only sandboxed agent

```json5
{
  agents: {
    list: [
      {
        id: "family",
        workspace: "~/.openclaw/workspace-family",
        sandbox: {
          mode: "all",
          scope: "agent",
          workspaceAccess: "ro",
        },
        tools: {
          allow: ["read"],
          deny: ["write", "edit", "apply_patch", "exec", "process", "browser"],
        },
      },
    ],
  },
}
```

### Public-facing agent with no filesystem or shell access

```json5
{
  agents: {
    list: [
      {
        id: "public",
        workspace: "~/.openclaw/workspace-public",
        sandbox: {
          mode: "all",
          scope: "agent",
          workspaceAccess: "none",
        },
        tools: {
          allow: ["sessions_list", "sessions_history", "sessions_send", "session_status"],
          deny: ["read", "write", "edit", "apply_patch", "exec", "process", "browser", "canvas", "nodes", "cron", "gateway", "image"],
        },
      },
    ],
  },
}
```

### Safe host exec baseline

Use both:

1. restrictive `tools.exec.*` in `openclaw.json`
2. per-agent allowlist plus `ask` policy in `exec-approvals.json`

Do not rely on only one of those layers.

## Verification flow

After security edits:

1. Run `openclaw doctor`
2. Run `openclaw status`
3. Run `openclaw sandbox explain` if sandboxing or elevated mode changed
4. Run a canary task that proves:
   - denied tools are blocked
   - approved tools still work
   - sandboxed agents stay in the expected environment
   - elevated access is unavailable for unauthorized senders
   - host exec prompts or allowlists behave as intended

## Common mistakes

| Mistake | Why it is wrong | Fix |
|---------|-----------------|-----|
| Editing only `tools.exec` and ignoring approvals | Host exec allowlists and ask policy live elsewhere | Update `exec-approvals.json` too |
| Putting sandbox config under a generic `security` block | OpenClaw reads sandboxing from `agents.defaults.sandbox` or `agents.list[].sandbox` | Move it to the correct config path |
| Assuming elevated mode overrides tool denies | Elevated changes where exec runs, not whether denied tools exist | Leave `exec` denied if the agent must never run commands |
| Enabling loop detection without a canary | False positives can block legitimate workflows | Test the agent's normal loop pattern after enabling it |

## Validation checklist

- [ ] The real execution host for approvals is known
- [ ] `openclaw.json` and `exec-approvals.json` agree on the intended host exec posture
- [ ] Sandbox config uses the correct `agents.defaults.sandbox` or `agents.list[].sandbox` path
- [ ] Elevated mode is either intentionally enabled with tight allowlists or intentionally disabled
- [ ] Loop detection is enabled only where it helps more than it harms
