---
name: init-openclaw-agent
description: Use skill if you are configuring an OpenClaw agent — IDENTITY.md, tool profiles, allow/deny lists, skills loading, memory, and security settings.
---

# Configure OpenClaw

Configure OpenClaw agent workspaces from evidence, not defaults. Every setting should reflect the agent's actual role, the tools it needs, and the security posture the deployment requires.

## Trigger boundary

Use this skill when the task involves:

- Setting up a new OpenClaw agent workspace from scratch
- Writing or revising an agent's IDENTITY.md
- Choosing a tool profile (full, coding, messaging, minimal) or customizing one
- Configuring tool allow/deny lists or tool group restrictions
- Setting up skill loading, extra skill directories, or skill environment variables
- Configuring memory tools (memory_search, memory_get)
- Hardening security: exec approvals, elevated mode, tool-loop detection
- Setting up multi-agent sandboxing or agent visibility
- Debugging why a tool is blocked or a skill is not loading

Do NOT use this skill for:

- General agent config for non-OpenClaw systems (AGENTS.md, CLAUDE.md) -- use init-agent-config
- Building or optimizing an MCP server -- use optimize-mcp-server
- Writing Claude Code skills -- use build-skills
- Runtime orchestration, node graphs, or cron scheduling (those are runtime concerns, not config)
- OpenClaw plugin development (that is code, not configuration)

## Non-negotiable rules

1. **Inspect the workspace first.** Read existing config files before changing anything. Never overwrite working config blindly.
2. **Principle of least privilege.** Start with the minimal tool profile and permissions the agent actually needs. Expand only with justification.
3. **Deny always wins.** If a tool appears in both `tools.allow` and `tools.deny`, deny takes precedence. Document this when configuring mixed lists.
4. **Skill precedence is fixed.** workspace > managed/local > bundled > extra dirs. Do not fight the load order; design around it.
5. **IDENTITY.md is the agent's soul.** It defines persona, boundaries, and behavioral constraints. It is not a dumping ground for technical config.
6. **Security settings are non-optional for production.** Exec approvals, tool-loop detection, and sandbox boundaries must be explicitly configured, not left at defaults.

## Decision tree

```
What aspect of OpenClaw agent config needs work?
|
+-- "Set up a new agent workspace"
|   +-- Read references/agent-identity.md
|   +-- Read references/tool-profiles.md
|   +-- Follow: New Agent Setup workflow (below)
|
+-- "Choose or customize tool profiles"
|   +-- Which profile fits?
|   |   +-- General-purpose agent ----------- full profile
|   |   +-- Code-focused agent -------------- coding profile
|   |   +-- Chat/notification agent --------- messaging profile
|   |   +-- Restricted/auditing agent ------- minimal profile
|   +-- Need per-tool control? -------------- Read references/tool-restrictions.md
|   +-- Need provider-level restrictions? --- Read references/tool-restrictions.md (byProvider section)
|
+-- "Configure allow/deny lists"
|   +-- Broad restrictions by category ------ Use tool groups (group:fs, group:web, etc.)
|   +-- Fine-grained per-tool control ------- Use tools.allow / tools.deny
|   +-- Provider-specific limits ------------ Use tools.byProvider
|   +-- Read references/tool-restrictions.md
|
+-- "Set up skill loading"
|   +-- Adding external skill directories --- skills.load.extraDirs
|   +-- Configuring skill env/API keys ------ skills.entries.{key}.env, skills.entries.{key}.apiKey
|   +-- Skill not loading? ----------------- Check precedence: workspace > managed/local > bundled > extra
|   +-- Tuning watcher -------------------- skills.load.watchDebounceMs (default 250ms)
|   +-- Read references/skills-loading.md
|
+-- "Configure memory"
|   +-- Enable memory search/retrieval ------ memory_search, memory_get tools
|   +-- Memory scoping and retention -------- Read references/agent-identity.md (memory section)
|
+-- "Harden security"
|   +-- Exec approval policies -------------- Read references/security-patterns.md
|   +-- Elevated mode control --------------- Read references/security-patterns.md
|   +-- Tool-loop detection ----------------- Read references/security-patterns.md
|   +-- Multi-agent sandbox boundaries ------ Read references/security-patterns.md
|
+-- "Debug config issues"
    +-- Tool blocked unexpectedly ----------- Check deny list, profile, and group membership
    +-- Skill not loading ------------------- Check precedence order and extraDirs path
    +-- Memory not working ------------------ Verify memory tools are in allow list
    +-- Read references/tool-restrictions.md and references/skills-loading.md
```

## New Agent Setup workflow

### Phase 1: Understand the agent's role

Before touching any config file, answer these questions:

1. **What does this agent do?** (code assistant, chat bot, automation runner, auditor, etc.)
2. **Who interacts with it?** (developers, end users, other agents, automated pipelines)
3. **What tools does it need?** Map required capabilities to OpenClaw's tool layers
4. **What must it never do?** Define hard boundaries upfront
5. **Is it part of a multi-agent system?** Determine sandbox and visibility requirements

### Phase 2: Write IDENTITY.md

Read `references/agent-identity.md` for the full guide. Key principles:

- Lead with the agent's role and boundaries in plain language
- State what the agent should and should not do -- behavioral constraints, not technical lists
- Include tone, audience awareness, and escalation rules
- Keep it under 80 lines; if it grows, the agent's scope is too broad

### Phase 3: Select tool profile

Read `references/tool-profiles.md` to choose the right base profile.

| Profile | Layer 1 (core) | Layer 2 (advanced) | Best for |
|---------|----------------|-------------------|----------|
| full | All 8 core tools | All advanced tools | General-purpose agents with broad capability needs |
| coding | All 8 core tools | browser, canvas, image | Developer-facing agents focused on code tasks |
| messaging | read, write, web_search, web_fetch | message, sessions, tts | Communication and notification agents |
| minimal | read, exec | None | Auditing, read-only inspection, locked-down agents |

After selecting a base profile, customize with allow/deny lists if the profile is not an exact fit.

### Phase 4: Configure tool restrictions

Read `references/tool-restrictions.md` for allow/deny patterns.

Apply restrictions in this order:

1. Start with the closest matching profile
2. Add specific tools to `tools.allow` if the profile is missing something you need
3. Add specific tools to `tools.deny` for anything that must be blocked regardless of profile
4. Use tool group shorthand for broad categories (`group:fs`, `group:web`, etc.)
5. Use `tools.byProvider` for provider-level restrictions if applicable

### Phase 5: Set up skills

Read `references/skills-loading.md` for the loading configuration.

- Define `skills.load.extraDirs` for any external skill directories
- Configure per-skill env vars and API keys in `skills.entries`
- Set `watchDebounceMs` if the default watcher timing causes issues
- Verify skill precedence: workspace skills shadow managed/local, which shadow bundled, which shadow extra dirs

### Phase 6: Harden security

Read `references/security-patterns.md` for the full security configuration guide.

At minimum for any production agent:

- Enable exec approvals for commands that modify the system
- Configure tool-loop detection thresholds
- Set explicit sandbox boundaries for multi-agent setups
- Review elevated mode settings and restrict to specific tools if enabled

## OpenClaw tool inventory

### Layer 1 -- Core tools (8)

| Tool | Group | Purpose |
|------|-------|---------|
| read | group:fs | Read files from the workspace |
| write | group:fs | Write files to the workspace |
| edit | group:fs | Edit files with diff-based patches |
| apply_patch | group:fs | Apply multi-file patches |
| exec | group:runtime | Execute shell commands |
| process | group:runtime | Manage running processes |
| web_search | group:web | Search the web |
| web_fetch | group:web | Fetch content from URLs |

### Layer 2 -- Advanced tools (18)

| Tool | Group | Purpose |
|------|-------|---------|
| browser | group:web | Browser automation |
| canvas | group:ui | Visual canvas operations |
| image | group:ui | Image generation and manipulation |
| memory_search | group:memory | Search agent memory |
| memory_get | group:memory | Retrieve specific memories |
| sessions | group:sessions | Manage conversation sessions |
| message | group:messaging | Send messages to users or agents |
| nodes | group:nodes | Manage node graphs |
| cron | group:automation | Schedule recurring tasks |
| gateway | group:web | API gateway operations |
| tts | group:ui | Text-to-speech |
| agents_list | group:sessions | List available agents in multi-agent setups |

### Tool groups

Use these shorthand references in allow/deny config:

| Group | Tools included |
|-------|---------------|
| `group:fs` | read, write, edit, apply_patch |
| `group:runtime` | exec, process |
| `group:web` | web_search, web_fetch, browser, gateway |
| `group:ui` | canvas, image, tts |
| `group:memory` | memory_search, memory_get |
| `group:sessions` | sessions, agents_list |
| `group:messaging` | message |
| `group:nodes` | nodes |
| `group:automation` | cron |

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Putting technical config in IDENTITY.md | IDENTITY.md is behavioral; tool config goes in workspace settings |
| Using `full` profile "just in case" | Start with `minimal` or `coding` and add only what the agent demonstrably needs |
| Forgetting deny always wins | If a tool is in both allow and deny, it is denied. Remove it from deny explicitly |
| Wrong skill precedence assumptions | workspace > managed/local > bundled > extra dirs. A workspace skill always wins |
| Not setting exec approvals in production | Any agent with exec access can run arbitrary commands. Always configure approval policies |
| Putting API keys in IDENTITY.md | Use `skills.entries.{key}.apiKey` or environment variables, never inline in identity |
| Over-broad tool groups | `group:web` includes browser. If you only need web_search, allow it individually |
| Ignoring watchDebounceMs | Rapid skill changes can cause reload storms. Set debounce to 500-2000ms for active development |

## Do this, not that

| Do this | Not that |
|---------|----------|
| Inspect existing workspace config before making changes | Overwrite config files with a template |
| Start with the most restrictive profile that works | Use `full` and deny what you do not want |
| Use tool groups for broad categories, individual tools for fine-grained control | Mix both inconsistently in the same config |
| Keep IDENTITY.md focused on persona and boundaries | Turn IDENTITY.md into a technical specification |
| Configure security settings explicitly | Rely on defaults for production agents |
| Use `skills.entries.{key}.apiKey` for secrets | Hardcode API keys in skill directories or identity files |
| Test tool access after config changes | Assume config changes take effect without verification |
| Document why a tool is denied | Leave unexplained deny entries that confuse future maintainers |

## Reference routing

Read the smallest reference set that unblocks the current decision:

| Need | Reference |
|------|-----------|
| Writing or revising IDENTITY.md, persona definition, behavioral constraints | `references/agent-identity.md` |
| Choosing a tool profile, understanding Layer 1 vs Layer 2 tools | `references/tool-profiles.md` |
| Configuring allow/deny lists, tool groups, provider restrictions | `references/tool-restrictions.md` |
| Setting up skill directories, env vars, API keys, precedence, watcher | `references/skills-loading.md` |
| Exec approvals, elevated mode, tool-loop detection, sandbox boundaries, multi-agent security | `references/security-patterns.md` |

**Quick-start mapping:**

| Scenario | Start with | Then read |
|----------|-----------|-----------|
| Brand new agent | `references/agent-identity.md` | `references/tool-profiles.md` |
| Locking down an existing agent | `references/tool-restrictions.md` | `references/security-patterns.md` |
| Adding skills to an agent | `references/skills-loading.md` | -- |
| Security audit of agent config | `references/security-patterns.md` | `references/tool-restrictions.md` |
| Debugging blocked tools | `references/tool-restrictions.md` | `references/tool-profiles.md` |

## Guardrails

- NEVER configure an agent without reading its existing config first.
- NEVER use the `full` tool profile in production without documenting why each advanced tool is needed.
- NEVER put secrets (API keys, tokens, credentials) in IDENTITY.md or skill source files.
- NEVER disable exec approvals in production without explicit sign-off from the user.
- NEVER assume tool groups are stable across OpenClaw versions -- verify group membership against the current runtime.
- ALWAYS test tool access after changing allow/deny lists.
- ALWAYS set tool-loop detection for agents with exec or automation tools.
- ALWAYS document the rationale for deny entries so future maintainers understand the restrictions.
- PREFER individual tool allows over broad group allows when the agent needs only 1-2 tools from a group.
- PREFER the most restrictive working profile over a permissive one that "might be needed later."
