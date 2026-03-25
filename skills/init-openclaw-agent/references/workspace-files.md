# Workspace Files and Durable Behavior

OpenClaw keeps runtime policy and workspace context in different places. This reference is the map for deciding which file to edit when you want behavior to persist.

## State dir vs workspace

These are different:

- OpenClaw home (`~/.openclaw` on host installs, `/home/node/.openclaw` in official containers) holds runtime config, credentials, sessions, approvals, and shared skills
- The agent workspace (`agents.defaults.workspace` or `agents.list[].workspace`) holds the files injected into the agent's prompt and the workspace-local skills

If the gateway runs remotely, both locations live on the gateway host.

## Workspace file map

| File | Use it for | Do not use it for |
|------|------------|-------------------|
| `AGENTS.md` | Operating rules, priorities, durable workflow guidance, memory-handling instructions | Name/theme metadata, runtime config, secrets |
| `SOUL.md` | Persona, tone, boundaries, "always/never/ask-before" behavior | Tool permissions, JSON config, API keys |
| `USER.md` | User identity, communication preferences, persistent audience context | Global policy or tool gating |
| `IDENTITY.md` | Name, theme, emoji, avatar | Persona, escalation rules, tool policy |
| `TOOLS.md` | Local wrapper commands, repo conventions, tool caveats, environment notes | Actual allow/deny policy |
| `MEMORY.md` | Curated long-term memory worth carrying across normal sessions | Secrets, transient debugging state |
| `memory/YYYY-MM-DD.md` | Daily logs or rolling short-term memory | Permanent policy |
| `skills/` | Workspace-only skills that should override shared or bundled versions | Shared skills for every agent on the machine |

Optional files:

- `HEARTBEAT.md` for short heartbeat instructions
- `BOOTSTRAP.md` for one-time first-run setup only

## What gets injected where

Normal sessions can read the workspace bootstrap files. Sub-agent sessions are much smaller: they inherit `AGENTS.md` and `TOOLS.md`, not the full workspace file set.

That has an important consequence:

- If a rule must survive sub-agent delegation, put it in `AGENTS.md`
- If a rule is mainly about persona or voice for the main agent, put it in `SOUL.md`

## Where durable behavior belongs

Use this decision map:

| Need | Put it in |
|------|-----------|
| "Always ask before destructive changes" | `AGENTS.md` or `SOUL.md`, depending on whether it is an operating rule or a persona boundary |
| "Speak tersely and directly" | `SOUL.md` |
| "The user prefers pnpm and flat bullets" | `USER.md` or `AGENTS.md` if it should apply operationally |
| "Use `./scripts/test-api.sh` instead of raw curl" | `TOOLS.md` |
| "Remember architectural decisions from prior sessions" | `AGENTS.md` plus `MEMORY.md` or daily memory files |
| "The agent is named WorkBot with a teal avatar" | `IDENTITY.md` |

## Writing guidelines

### `AGENTS.md`

Use concrete instructions:

- priorities
- operating rules
- escalation conditions
- memory habits
- durable repository conventions

Keep it practical. A literal agent should be able to act on it without reading between the lines.

### `SOUL.md`

Use it for:

- voice
- tone
- behavioral boundaries
- social stance
- what the agent should feel like to interact with

Keep config and tool names out of this file unless the wording is necessary for a behavioral boundary.

### `USER.md`

Use it for:

- how to address the user
- recurring preferences
- context about the human on the other side

Do not duplicate repo policy here.

### `TOOLS.md`

Use it for:

- local command wrappers
- tool caveats
- path conventions
- environment-specific notes

`TOOLS.md` explains tools. It does not grant or revoke them.

### Memory files

Good memory candidates:

- durable preferences
- stable project conventions
- recurring constraints
- decisions worth carrying forward

Bad memory candidates:

- secrets
- temporary logs
- one-off debugging noise
- anything the user asked not to retain

## Bootstrap and missing-file behavior

`openclaw setup`, `openclaw onboard`, or `openclaw configure` can create the workspace and seed the bootstrap files when they are missing.

If you manage the workspace files yourself, `agents.defaults.skipBootstrap: true` disables automatic creation of:

- `AGENTS.md`
- `SOUL.md`
- `TOOLS.md`
- `IDENTITY.md`
- `USER.md`
- `HEARTBEAT.md`
- `BOOTSTRAP.md`

## Validation checklist

- [ ] The active workspace path is known and correct
- [ ] Each instruction was placed in the right file
- [ ] No secrets were written into workspace files
- [ ] Rules that must survive sub-agent delegation live in `AGENTS.md`
- [ ] Tool policy changes were made in runtime config, not in workspace prose
