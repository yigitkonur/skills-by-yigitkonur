# Agent Identity Setup

IDENTITY.md is the behavioral foundation of every OpenClaw agent. It lives at `~/.openclaw/workspace/IDENTITY.md` and defines who the agent is, what it does, and what it must never do. This file is loaded into the agent's system context at startup.

## Purpose

IDENTITY.md is NOT a technical configuration file. It defines:

- The agent's persona and communication style
- Behavioral boundaries and escalation rules
- Domain expertise and knowledge scope
- Audience awareness and tone adjustments
- What the agent should proactively do vs. what it should wait to be asked

Technical settings (tool profiles, allow/deny lists, skill loading) belong in workspace configuration, not here.

## Structure

A well-structured IDENTITY.md follows this pattern:

```markdown
# [Agent Name]

[One sentence: what this agent is and who it serves.]

## Role

[2-3 sentences expanding on the agent's primary function, domain, and value proposition.]

## Behavioral boundaries

### Always
- [Proactive behaviors the agent should exhibit]
- [Quality standards it must maintain]

### Never
- [Hard constraints that must not be violated]
- [Actions that require escalation instead]

### Ask before
- [Actions that need user confirmation]
- [Decisions with irreversible consequences]

## Communication style

[Tone, formality level, verbosity preferences, audience awareness.]

## Domain knowledge

[What the agent is an expert in. What it should admit it does not know.]

## Escalation

[When to stop and ask. When to hand off to another agent or human.]
```

## Writing principles

### Lead with role, not capabilities

```markdown
-- WRONG: Technical capability list
You have access to read, write, edit, exec, web_search, and memory tools.
You can execute shell commands and search the web.

-- RIGHT: Behavioral identity
You are a backend API specialist for the payments team. You help developers
build, debug, and optimize payment processing endpoints. You understand
PCI compliance requirements and flag potential violations proactively.
```

### State boundaries as behaviors, not config

```markdown
-- WRONG: Config-style restrictions
tools.deny: [write, apply_patch]
You cannot modify files.

-- RIGHT: Behavioral boundary
Never modify production configuration files directly. When a config change
is needed, generate a pull request description with the exact changes and
the rationale, then ask the developer to apply it.
```

### Be specific about escalation

```markdown
-- WRONG: Vague escalation
Ask the user if you are not sure.

-- RIGHT: Specific triggers
Ask before:
- Deleting any file or directory
- Running commands that modify the database
- Making network requests to external services not in the approved list
- Suggesting architectural changes that affect more than one service
```

### Keep it concise

Target under 80 lines. If the IDENTITY.md is growing beyond that, the agent's scope is probably too broad. Consider:

- Splitting into multiple specialized agents
- Moving domain-specific reference material to skill files
- Extracting repeated patterns into behavioral rules

## Memory integration

When memory tools are enabled (memory_search, memory_get), IDENTITY.md should include guidance on what the agent should remember:

```markdown
## Memory usage

Remember:
- User preferences for code style and formatting
- Project-specific conventions discovered during sessions
- Decisions made and their rationale

Do not persist:
- Temporary debugging state
- Credentials or secrets (even if the user shares them)
- Personal information beyond what is needed for the task
```

## Multi-agent identity

When the agent operates in a multi-agent system:

```markdown
## Multi-agent context

You are the code-review agent in a team of three:
- **planner**: Breaks down tasks into subtasks (you receive work from this agent)
- **coder**: Writes implementation code (you review this agent's output)
- **you (reviewer)**: Reviews code for correctness, style, and security

When reviewing:
- Focus on correctness and security; do not bikeshed style if it passes the linter
- If a change looks risky, flag it and suggest the planner re-scope
- Never modify code directly; return review comments to the coder
```

## Common mistakes

| Mistake | Why it is wrong | Fix |
|---------|----------------|-----|
| Listing available tools | Tools are configured elsewhere; this clutters the identity | Describe capabilities in behavioral terms |
| Copy-pasting from README | Agent context is not documentation; it is operational instructions | Write instructions that prevent mistakes |
| Including API keys or secrets | IDENTITY.md is loaded into LLM context and may leak | Use `skills.entries.{key}.apiKey` in workspace config |
| Being too vague ("be helpful") | Gives the agent no actionable constraints | State specific behaviors: always, never, ask-before |
| Making it too long (100+ lines) | Dilutes important instructions with noise | Cut to under 80 lines; move detail to skills or references |
| Mixing technical config with persona | Creates confusion about what is behavioral vs. structural | Keep IDENTITY.md behavioral; put config in workspace settings |

## Validation checklist

Before finalizing an IDENTITY.md:

- [ ] Under 80 lines
- [ ] Leads with role and audience, not tool lists
- [ ] Has explicit "always", "never", and "ask before" sections
- [ ] No secrets, API keys, or credentials
- [ ] No technical config that belongs in workspace settings
- [ ] Communication style is defined
- [ ] Escalation triggers are specific, not vague
- [ ] If multi-agent, relationships and handoff rules are clear
- [ ] If memory is enabled, memory usage guidance is included
