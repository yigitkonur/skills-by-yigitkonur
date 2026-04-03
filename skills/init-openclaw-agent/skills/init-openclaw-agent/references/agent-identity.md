# Agent Identity Metadata

`IDENTITY.md` is the workspace file for the agent's visible identity, not its operating rules. Use it when the task is about the agent's name, theme, emoji, or avatar, or when you need to sync those values into `agents.list[].identity`.

## What `IDENTITY.md` is for

Use `IDENTITY.md` for:

- Agent name
- Theme or vibe
- Emoji
- Avatar reference

Keep these fields lightweight. The file should make it obvious how the agent should be presented, not how it should behave.

## What does NOT belong here

Do not put these in `IDENTITY.md`:

- Persona or tone rules
- Escalation rules
- Tool permissions
- Security policy
- Secrets
- Long behavioral instructions

Put those in:

- `SOUL.md` for persona, tone, and boundaries
- `AGENTS.md` for operating rules and priorities
- `openclaw.json` for tool and runtime policy

## Canonical path

`IDENTITY.md` lives at the workspace root:

- default workspace: `~/.openclaw/workspace/IDENTITY.md`
- named-agent workspace: `<workspace>/IDENTITY.md`

If the gateway runs remotely or in a container, edit the file on that runtime's workspace, not on the current laptop.

## Identity fields OpenClaw understands

OpenClaw maps identity metadata into `agents.list[].identity` with these fields:

- `name`
- `theme`
- `emoji`
- `avatar`

Avatar paths are workspace-relative when you use a local file.

## Working pattern

1. Read the existing `IDENTITY.md` if it exists
2. Preserve its current structure instead of inventing a new format
3. Update only the identity values the task actually requires
4. If config also tracks identity, sync it with:

```bash
openclaw agents set-identity --workspace <workspace> --from-identity
```

Or override specific fields directly:

```bash
openclaw agents set-identity --agent <agentId> --name "Agent Name" --emoji "" --avatar avatars/agent.png
```

## Decision guide

| Task | Edit |
|------|------|
| Rename the agent | `IDENTITY.md` and, if used, `agents.list[].identity.name` |
| Change the visible vibe/theme | `IDENTITY.md` and, if used, `agents.list[].identity.theme` |
| Add or update an avatar | `IDENTITY.md` and `agents.list[].identity.avatar` |
| Change tone, boundaries, or refusal behavior | `SOUL.md`, not `IDENTITY.md` |
| Change operating rules or memory behavior | `AGENTS.md`, not `IDENTITY.md` |

## Validation checklist

- [ ] `IDENTITY.md` only contains identity metadata
- [ ] Any avatar path is valid relative to the workspace, or is an explicit URL/data URI
- [ ] Config identity and workspace identity do not drift if both are in use
- [ ] Behavior rules were not accidentally moved into `IDENTITY.md`
