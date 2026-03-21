# Tool Profiles

OpenClaw provides four preset tool profiles that define which tools an agent can access by default. Profiles are the starting point for tool configuration -- choose the closest match, then customize with allow/deny lists.

## Profile overview

### full

All 26 tools enabled. Both Layer 1 (core) and Layer 2 (advanced) tools are available.

**Use when:** The agent is a general-purpose assistant that may need any capability. Common for development agents in trusted environments.

**Risk:** Maximum attack surface. Every tool is a potential vector for unintended actions. Requires strong IDENTITY.md boundaries and security config to compensate.

**Layer 1 (core):** read, write, edit, apply_patch, exec, process, web_search, web_fetch
**Layer 2 (advanced):** browser, canvas, image, memory_search, memory_get, sessions, message, nodes, cron, gateway, tts, agents_list

### coding

All core tools plus code-relevant advanced tools. Focused on software development workflows.

**Use when:** The agent assists developers with coding tasks -- writing, debugging, refactoring, testing, and documentation.

**Layer 1 (core):** read, write, edit, apply_patch, exec, process, web_search, web_fetch
**Layer 2 (advanced):** browser, canvas, image

**Excluded:** memory_search, memory_get, sessions, message, nodes, cron, gateway, tts, agents_list

### messaging

Read-only filesystem access plus communication and web tools. No write access, no process management.

**Use when:** The agent handles communication, notifications, or information retrieval without modifying the workspace.

**Layer 1 (core):** read, web_search, web_fetch
**Layer 2 (advanced):** message, sessions, tts

**Excluded:** write, edit, apply_patch, exec, process, browser, canvas, image, memory_search, memory_get, nodes, cron, gateway, agents_list

### minimal

Read and exec only. The most restrictive preset.

**Use when:** The agent inspects, audits, or monitors without modifying anything. Exec is included for running read-only commands (ls, grep, test runners in dry-run mode).

**Layer 1 (core):** read, exec
**Layer 2 (advanced):** None

**Excluded:** All other tools

**Note:** Even `minimal` includes `exec`, which can run arbitrary commands. Pair with exec approval policies for true read-only behavior.

## Choosing a profile

```
What does the agent need to do?
|
+-- Read, write, and execute code?
|   +-- Needs browser/canvas/image? --------- coding
|   +-- Needs messaging/sessions? ------------ full (or coding + specific allows)
|   +-- Needs memory? ------------------------ full (or coding + memory allows)
|   +-- Just code tasks? --------------------- coding
|
+-- Communicate but not modify files?
|   +-- Needs web access? -------------------- messaging
|   +-- Chat-only? --------------------------- messaging
|
+-- Inspect/audit only?
|   +-- Needs to run commands? --------------- minimal (with exec approvals)
|   +-- Pure read? --------------------------- minimal (deny exec)
|
+-- Everything? ------------------------------- full (with strong security config)
```

## Profile customization patterns

Profiles are a starting point. Customize with allow/deny lists for precise control.

### Pattern: coding + memory

Start with `coding` profile, add memory tools:

```yaml
profile: coding
tools:
  allow:
    - memory_search
    - memory_get
```

### Pattern: coding without exec

Start with `coding` profile, remove exec for safety:

```yaml
profile: coding
tools:
  deny:
    - exec
    - process
```

### Pattern: minimal + web search

Read-only agent that can search the web:

```yaml
profile: minimal
tools:
  allow:
    - web_search
    - web_fetch
```

### Pattern: full with denied dangerous tools

General-purpose but block automation and multi-agent:

```yaml
profile: full
tools:
  deny:
    - cron
    - nodes
    - agents_list
    - gateway
```

## Layer 1 vs Layer 2 tools

### Layer 1 -- Core tools (8)

These are the fundamental building blocks. Most agents need some subset of these.

| Tool | Risk level | Notes |
|------|-----------|-------|
| read | Low | Cannot modify anything; safe for all agents |
| write | Medium | Can create/overwrite files; pair with IDENTITY.md boundaries |
| edit | Medium | Diff-based editing; safer than write for modifications |
| apply_patch | Medium | Multi-file patches; powerful but auditable |
| exec | High | Arbitrary command execution; always configure approval policies |
| process | High | Can start/stop/manage processes; requires trust |
| web_search | Low | Search queries only; no side effects |
| web_fetch | Medium | Can fetch arbitrary URLs; consider network restrictions |

### Layer 2 -- Advanced tools (18)

These extend the agent's capabilities beyond basic file and command operations.

| Tool | Risk level | Notes |
|------|-----------|-------|
| browser | High | Full browser automation; can interact with web applications |
| canvas | Low | Visual operations within the workspace |
| image | Low | Image generation/manipulation; cost implications |
| memory_search | Low | Read-only memory access |
| memory_get | Low | Read-only memory access |
| sessions | Medium | Can create/manage conversation sessions |
| message | Medium | Can send messages to users or other agents |
| nodes | High | Node graph management; complex orchestration |
| cron | High | Schedule recurring tasks; persistence implications |
| gateway | High | API gateway access; network boundary crossing |
| tts | Low | Text-to-speech; cost implications |
| agents_list | Low | Read-only listing of available agents |

## When to upgrade profiles

Signs the current profile is too restrictive:

- Agent repeatedly reports it cannot perform a requested action
- Workarounds are being used (e.g., asking the user to run commands instead of using exec)
- The agent's role has expanded beyond its original scope

Signs the current profile is too permissive:

- Agent has tools it never uses (check usage logs)
- Security audit flags unnecessary capabilities
- The agent's role has narrowed since initial setup

## Validation checklist

- [ ] Profile matches the agent's actual role (not aspirational capabilities)
- [ ] No tools are enabled "just in case"
- [ ] High-risk tools (exec, process, browser, cron, nodes, gateway) have justification
- [ ] Custom allow/deny lists are documented with rationale
- [ ] If using `full`, security patterns from `security-patterns.md` are also configured
- [ ] If using `minimal` with exec, approval policies are set
