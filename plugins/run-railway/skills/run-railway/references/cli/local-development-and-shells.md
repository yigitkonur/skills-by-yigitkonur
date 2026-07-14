# Local Development and Shells

Use this file when the user wants Railway environment variables locally, an interactive shell with Railway context, local multi-service development, or shell completion output.

All commands below are confirmed in the local `railway 4.29.0` snapshot. For exact flag lists, pair this file with `references/cli/railway-cli-command-reference.md`.

## Choose `run` vs `shell` vs `dev`

| If the user wants to... | Prefer | Why |
|---|---|---|
| Run one local command with Railway variables injected | `railway run` | Single-process path |
| Open an interactive subshell with Railway variables available | `railway shell` | Long-lived shell session |
| Start or manage local Railway-backed services | `railway dev` | Multi-service local orchestration |

## Run one command with Railway variables

Use `railway run` when the user wants to execute a single local command inside Railway context.

Exact usage from local help:

```text
railway run [OPTIONS] [ARGS]...
```

Key selectors:

```bash
railway run --service <SERVICE> --environment <ENVIRONMENT> --project <PROJECT_ID> <command...>
```

Important details:

- `--service`, `--environment`, and `--project` let you override linked defaults.
- `--no-local` skips local develop overrides, even if a `docker-compose.yml` exists.
- `--verbose` shows verbose domain replacement info.

## Open a Railway-backed subshell

Use `railway shell` when the user wants a shell with Railway variables already present.

```bash
railway shell
railway shell --service <SERVICE>
railway shell --silent
```

Local nuance worth remembering:

- `shell` exposes `--service`, but not an `--environment` flag in local `4.29.0`
- The active environment therefore comes from the linked context
- `--silent` suppresses the startup banner

## Local service orchestration with `railway dev`

`railway dev` is the local multi-service command family.

```bash
railway dev
railway dev up
railway dev down
railway dev clean
railway dev configure
```

Use the subcommands like this:

| Need | Command | Notes |
|---|---|---|
| Start services locally | `railway dev` or `railway dev up` | `up` is the default when no subcommand is given |
| Stop local services | `railway dev down` | Keeps generated state around |
| Stop services and remove local volumes/data | `railway dev clean` | Destructive to local dev state |
| Configure local code services | `railway dev configure` | Best for service-specific local setup |

High-value local `dev up` options:

| Option | Use when |
|---|---|
| `--environment <ENVIRONMENT>` | The local dev session should mirror a specific Railway environment |
| `--dry-run` | The user wants only the generated `docker-compose.yml` |
| `--no-https` | The user wants localhost-style URLs instead of HTTPS/pretty URLs |
| `--no-tui` | The user wants logs streamed to stdout instead of the TUI |
| `--output <OUTPUT>` | The compose file location should be overridden |

`railway dev configure` supports:

```bash
railway dev configure --service <SERVICE>
railway dev configure --remove
railway dev configure --remove <SERVICE>
```

## Completion scripts

Use `railway completion` when the user wants shell completion output rather than runtime behavior:

```bash
railway completion bash
railway completion zsh
railway completion fish
railway completion powershell
railway completion elvish
```

## Nearby-command traps

| Confusion | Correct choice | Why |
|---|---|---|
| "Run this one command with Railway vars" versus "open me a shell" | `run` for one command, `shell` for an interactive shell | Different session models |
| "Use Railway vars locally" versus "start the local dev stack" | `run` or `shell` for variable injection, `dev` for service orchestration | `dev` is a much broader workflow |
| "Stop local services" versus "wipe the local dev state" | `dev down` stops, `dev clean` removes data too | `clean` is the destructive local option |

