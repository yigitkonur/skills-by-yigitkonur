---
name: init-openclaw-agent
description: "Use this skill if you are configuring an OpenClaw agent workspace or agent-specific runtime policy: workspace files, tool profiles, allow/deny lists, skills loading, memory, or security settings."
---

# Configure OpenClaw Agent

Configure OpenClaw agents from the real runtime layout, not from assumptions. The executor should always know which machine owns the runtime, which workspace belongs to the target agent, and which file controls each behavior.

## Trigger boundary

Use this skill when the task involves:

- Setting up a new OpenClaw agent workspace
- Writing or revising workspace files such as `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, or memory files
- Choosing a tool profile (`full`, `coding`, `messaging`, `minimal`) for an agent
- Configuring tool allow/deny lists, provider-specific tool restrictions, or per-agent tool policy
- Setting up skill loading, extra skill directories, skill env vars, or bundled-skill allowlists
- Enabling memory tools or deciding where durable behavior should live in the workspace
- Hardening exec approvals, sandboxing, elevated access, or tool-loop detection
- Debugging why a tool is blocked, a skill is not loading, or the wrong workspace is active

Do NOT use this skill for:

- General agent config for non-OpenClaw systems such as `AGENTS.md` or `CLAUDE.md` outside OpenClaw
- Building or optimizing an MCP server
- Writing OpenClaw skills themselves
- Runtime orchestration, node graphs, or cron workflow design
- OpenClaw plugin development

## Non-negotiable rules

1. **Find the real runtime first.** Determine whether OpenClaw runs on the local host, a remote gateway host, or inside a container. Edit the real OpenClaw home for that runtime, not an assumed local copy.
2. **Keep workspace files separated by purpose.** `AGENTS.md` and memory files hold operating rules, `SOUL.md` holds persona and boundaries, `IDENTITY.md` holds name/theme/emoji/avatar, and `TOOLS.md` is guidance only.
3. **Prefer agent-specific config in multi-agent setups.** If the gateway hosts multiple agents, use `agents.list[].workspace`, `agents.list[].tools`, and `agents.list[].sandbox` for the target agent unless the user explicitly wants a global default.
4. **Start from the smallest working tool surface.** Pick the narrowest profile that fits, then add only the missing tools.
5. **Deny always wins.** Once a tool is denied at an earlier layer, a later allow cannot restore it.
6. **Treat host exec approvals as separate state.** Tool policy lives in `openclaw.json`, but host exec approvals and allowlists live in `exec-approvals.json` on the execution host.

## Canonical files and locations

- OpenClaw state normally lives under `~/.openclaw` on host installs
- Inside the official container images, the same state lives at `/home/node/.openclaw`; edit the mounted host directory or the in-container path that maps there
- Main runtime config is usually `openclaw.json` in that OpenClaw home and uses JSON5 syntax; if the CLI is available, confirm the active file with `openclaw config file` or the runtime's `OPENCLAW_CONFIG_PATH`
- Host exec approvals live in `exec-approvals.json` in that same OpenClaw home on the machine that actually executes host commands
- Default workspace path is `agents.defaults.workspace` and defaults to `~/.openclaw/workspace`
- Per-agent workspaces are set with `agents.list[].workspace`
- Shared skills live at `~/.openclaw/skills`; workspace-specific skills live at `<workspace>/skills`
- New config should use `agents.defaults` and `agents.list`; legacy `agent.*` keys may still exist and can be migrated with `openclaw doctor`

If the gateway runs remotely, all of these paths refer to the gateway host, not the laptop you are currently using.

## Decision tree

```
What part of the OpenClaw agent needs work?
|
+-- "Create or revise the agent workspace"
|   +-- Read references/workspace-files.md
|   +-- If name/theme/avatar only ---------- Read references/agent-identity.md
|   +-- Then follow: New Agent Setup workflow (below)
|
+-- "Choose or customize tool access"
|   +-- Read references/tool-profiles.md
|   +-- Need fine-grained restrictions? ---- Read references/tool-restrictions.md
|
+-- "Configure allow/deny lists"
|   +-- Global single-agent policy --------- tools.allow / tools.deny
|   +-- Multi-agent per-agent policy ------- agents.list[].tools.*
|   +-- Provider-specific limits ----------- tools.byProvider / agents.list[].tools.byProvider
|   +-- Read references/tool-restrictions.md
|
+-- "Set up skill loading"
|   +-- extraDirs / watch / allowBundled --- Read references/skills-loading.md
|   +-- Per-skill env or apiKey ------------ Read references/skills-loading.md
|   +-- Sandbox env mismatch? -------------- Read references/security-patterns.md
|
+-- "Configure memory or durable behavior"
|   +-- Workspace behavior files ----------- Read references/workspace-files.md
|   +-- memory_search / memory_get tools --- Read references/tool-profiles.md
|
+-- "Harden exec, sandbox, or loop safety"
|   +-- Host exec approvals ---------------- Read references/security-patterns.md
|   +-- Elevated mode ---------------------- Read references/security-patterns.md
|   +-- Sandbox boundaries ----------------- Read references/security-patterns.md
|   +-- Tool-loop detection ---------------- Read references/security-patterns.md
|
+-- "Debug config issues"
    +-- Tool blocked unexpectedly ---------- Read references/tool-restrictions.md
    +-- Skill not loading ------------------ Read references/skills-loading.md
    +-- Wrong workspace or agent ----------- Read references/workspace-files.md
    +-- Sandbox/elevated confusion --------- Read references/security-patterns.md
```

## New Agent Setup workflow

### Phase 0: Locate the target runtime and agent

Before you change anything:

1. Determine where the gateway actually runs: local host, remote host, or container
2. Confirm the active config path, then open the real `openclaw.json` for that runtime
3. Identify whether the task targets:
   - `agents.defaults.workspace` for the default agent, or
   - a specific `agents.list[]` entry for a named agent
4. Read the current workspace files that matter to the task:
   - `AGENTS.md`
   - `SOUL.md`
   - `IDENTITY.md`
   - `USER.md`
   - `TOOLS.md`
   - `MEMORY.md` and `memory/` if durable memory is in scope
5. If the task changes host exec approval behavior, read `exec-approvals.json` on the execution host too

If you cannot prove which runtime or workspace is active, stop and ask instead of inventing paths.

### Phase 1: Understand the agent's job

Before drafting config, answer these questions:

1. What does this agent do?
2. Who interacts with it?
3. Which behaviors must be durable across sessions?
4. Which tools does it actually need?
5. What must it never do?
6. Is it one agent in a larger multi-agent gateway?

### Phase 2: Shape the workspace files

Read `references/workspace-files.md`.

- Put rules, priorities, and memory-handling instructions in `AGENTS.md`
- Put persona, tone, and behavioral boundaries in `SOUL.md`
- Put user-specific preferences in `USER.md`
- Put identity metadata in `IDENTITY.md`
- Put local tool conventions in `TOOLS.md`
- Put durable facts or decisions in `MEMORY.md` or daily memory files

If the task is specifically about the agent's name, theme, emoji, or avatar, also read `references/agent-identity.md`.

### Phase 3: Select the base tool profile

Read `references/tool-profiles.md`.

Use the smallest fitting base profile:

| Profile | Includes | Best for |
|---------|----------|----------|
| `full` | no profile restriction | highly trusted agents that truly need broad access |
| `coding` | filesystem, runtime, sessions, memory, image | developer-facing agents |
| `messaging` | messaging plus session list/history/send/status | communication-only agents |
| `minimal` | `session_status` only | agents that should start nearly tool-less |

For a new local config, onboarding may write `tools.profile: "coding"` when unset. Do not assume that means `coding` is universally correct for the agent you are configuring.

### Phase 4: Apply tool restrictions

Read `references/tool-restrictions.md`.

Choose the right scope before editing:

1. Single-agent or global default policy: top-level `tools.*`
2. One agent inside a multi-agent gateway: `agents.list[].tools.*`
3. Provider-specific restrictions: `tools.byProvider` or `agents.list[].tools.byProvider`

Then apply the restriction model in this order:

1. Base profile
2. Provider profile override, if any
3. Allow/deny lists
4. Sandbox or sub-agent tool policy, if this runtime uses them

### Phase 5: Configure skills loading

Read `references/skills-loading.md`.

- Use `skills.load.extraDirs` for additional skill roots
- Use `skills.entries.<skillKey>` for per-skill `enabled`, `env`, `apiKey`, and custom `config`
- Use `skills.allowBundled` if bundled skills need an allowlist
- Confirm the entry key matches the skill name or its `metadata.openclaw.skillKey`

If the agent runs inside a sandbox, do not assume `skills.entries.*.env` reaches the sandboxed skill process. Route sandbox env through the sandbox config or image instead.

### Phase 6: Harden exec, sandbox, and loop safety

Read `references/security-patterns.md`.

At minimum, decide all of the following explicitly:

1. Host exec policy in `tools.exec.*`
2. Host exec approvals and allowlists in `exec-approvals.json`
3. Whether `tools.elevated` is enabled and who may use it
4. Whether the agent is sandboxed, and with what `workspaceAccess`
5. Whether `tools.loopDetection` should be enabled for this agent

### Phase 7: Validate the runtime change

After editing:

1. Run `openclaw doctor`
2. Run `openclaw status`
3. If multi-agent routing is involved, run `openclaw agents list --bindings`
4. If sandboxing or tool policy is involved, run `openclaw sandbox explain`
5. Run a small canary task that proves the intended behavior:
   - expected workspace files are active
   - denied tools stay blocked
   - allowed tools are usable
   - expected skills load
   - sandbox or elevated behavior matches intent
6. If the CLI is unavailable, stop after writing the draft and report runtime verification as blocked

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Writing persona, escalation rules, or tool policy in `IDENTITY.md` | Put persona/boundaries in `SOUL.md`, operating rules in `AGENTS.md`, and tool policy in `openclaw.json` |
| Editing the local `~/.openclaw` when the gateway runs elsewhere | Edit the gateway host or the mounted container path that owns the runtime |
| Assuming `minimal` includes read or exec | `minimal` starts with `session_status` only; allow extra tools explicitly |
| Using `group:web` to grant browser access | `browser` and `canvas` live in `group:ui`; `group:web` is only `web_search` and `web_fetch` |
| Expecting `skills.entries.*.env` to reach sandboxed skills | Use sandbox docker env or a custom sandbox image |
| Tightening `tools.exec` but leaving host approvals permissive | Update both `openclaw.json` and `exec-approvals.json` |
| Restricting one agent by editing only global `tools.*` in a multi-agent gateway | Put agent-specific restrictions in `agents.list[].tools.*` |

## Do this, not that

| Do this | Not that |
|---------|----------|
| Confirm the active runtime host and workspace before editing | Assume `~/.openclaw` on the current machine is authoritative |
| Keep workspace files split by purpose | Turn one file into a dumping ground for persona, policy, and secrets |
| Start with a restrictive profile and add only the missing tools | Use `full` for convenience and plan to tighten it later |
| Use agent-specific tool policy for named agents | Mutate global defaults when only one agent should change |
| Keep secrets in runtime config or secret refs, not workspace files | Put API keys in `AGENTS.md`, `SOUL.md`, or `IDENTITY.md` |
| Verify with `doctor`, `status`, and a canary task | Assume a JSON edit took effect correctly |

## Reference routing

Read the smallest reference set that unblocks the current decision:

| Need | Reference |
|------|-----------|
| Workspace file roles, where durable behavior belongs, memory file layout | `references/workspace-files.md` |
| Name/theme/emoji/avatar updates and identity sync | `references/agent-identity.md` |
| Choosing a base tool profile | `references/tool-profiles.md` |
| Allow/deny lists, tool groups, provider and agent precedence | `references/tool-restrictions.md` |
| Skill precedence, `extraDirs`, `skills.entries`, sandbox env boundaries | `references/skills-loading.md` |
| Exec approvals, elevated mode, sandboxing, loop detection, verification | `references/security-patterns.md` |

## Guardrails

- NEVER guess the runtime location or active workspace
- NEVER put secrets in workspace bootstrap files
- NEVER use `IDENTITY.md` as the place for rules or tool permissions
- NEVER assume global `tools.*` is the right edit scope in a multi-agent gateway
- ALWAYS update host exec approvals when host exec policy changes
- ALWAYS verify blocked-tool and allowed-tool behavior after access changes
- ALWAYS keep `SKILL.md` focused and push durable detail into the routed references
