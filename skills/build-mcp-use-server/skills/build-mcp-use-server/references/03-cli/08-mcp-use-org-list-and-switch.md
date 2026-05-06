# `mcp-use org list`, `switch`, and `current`

Manage the active Manufact Cloud organization for `mcp-use deploy`. The active org is stored in `~/.mcp-use/config.json`.

## When you need this

You belong to more than one Manufact Cloud organization (personal + team, multiple clients, etc.) and `mcp-use deploy` keeps targeting the wrong one.

## `mcp-use org list`

List orgs the logged-in user belongs to. Useful as a sanity check before deploying.

```bash
mcp-use org list
```

Output (shape may vary by CLI version):

```
Personal (personal) [owner] ← active
Acme Team (acme-team) [member]
Client Alpha (client-alpha) [member]
```

The `← active` marker shows the active org. Run `mcp-use whoami` first if `org list` is empty — you may not be logged in.

## `mcp-use org switch`

Switch the active org interactively. In `@mcp-use/cli@3.1.2`, `org switch` takes no positional slug argument; it prints a numbered picker and stores the selected org.

```bash
mcp-use org switch
```

For non-interactive selection, use `mcp-use login --org <slug|id|name>` during auth or `mcp-use deploy --org <slug-or-id>` for one deploy.

## `mcp-use org current`

Show the active organization stored in `~/.mcp-use/config.json`:

```bash
mcp-use org current
```

After switching, all subsequent `mcp-use deploy` calls target the new org until you switch again or pass `--org <slug-or-id>` per-command on `deploy`.

## Per-command override

For a one-off deploy to a different org without changing the global default:

```bash
mcp-use deploy --org client-alpha
```

For repeated deploys to the same org, prefer `mcp-use org switch` and skip `--org` on every command — fewer flags, fewer typos.

## Multi-org workflow

```bash
mcp-use login
mcp-use org list                      # see what's available
mcp-use org switch                    # set the target interactively
mcp-use deploy --env-file .env.prod   # ships to client-alpha
mcp-use org current                   # confirm after switching
```

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `org list` empty | Not logged in | `mcp-use login` |
| `org switch` cannot select the intended org | You are not a member or auth info is stale | `mcp-use org list`; re-login if needed |
| `deploy` keeps hitting the wrong org | Forgot to switch | `mcp-use org list` to confirm the active org |

## See also

- `06-mcp-use-deploy.md` — what runs after the org is set
- `13-device-flow-login.md` — `login`, `whoami`, `logout`
