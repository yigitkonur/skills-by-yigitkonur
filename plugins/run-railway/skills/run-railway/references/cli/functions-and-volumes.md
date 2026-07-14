# Functions and Volumes

Use this file when the user wants Railway functions, cron-style function config, or persistent volume management.

All commands below are confirmed in the local `railway 4.29.0` snapshot. For exact flags and every alias, pair this file with `references/cli/railway-cli-command-reference.md`.

## Railway functions

The local `functions` command family covers listing, creation, linking, pushing, pulling, and deletion.

```bash
railway functions list
railway functions new
railway functions push
railway functions pull
railway functions link
railway functions delete
```

The parent command also accepts `-e, --environment <ENVIRONMENT>` before the subcommand when the target environment matters.

### Choose the right function command

| If the user wants to... | Prefer | Why |
|---|---|---|
| See existing functions | `railway functions list` | Read-only list view |
| Create a new function locally and remotely | `railway functions new` | Creation flow |
| Associate a local file path with an existing function | `railway functions link` | Linking flow without creating a new function |
| Push local changes | `railway functions push` | Upload local code |
| Pull remote function changes | `railway functions pull` | Sync down from Railway |
| Remove a function | `railway functions delete` | Destructive delete path |

### High-value function patterns

```bash
railway functions new --path <PATH> --name <NAME>
railway functions new --path <PATH> --name <NAME> --cron "<CRON>"
railway functions new --path <PATH> --name <NAME> --http true --serverless true
railway functions push --path <PATH>
railway functions push --path <PATH> --watch true
railway functions link --path <PATH> --function <FUNCTION>
railway functions pull --path <PATH>
railway functions delete --function <FUNCTION> --yes true
```

Useful local details:

- `functions new` supports `--cron`, `--http`, `--serverless`, and `--watch`
- `functions push` can watch and redeploy on save
- `functions list` has alias `ls`
- `functions new` has alias `create`
- `functions delete` has aliases `remove` and `rm`
- `functions push` has alias `up`

## Railway volumes

The local `volume` command family covers listing, adding, attaching, detaching, updating, and deleting volumes.

```bash
railway volume list
railway volume add
railway volume attach
railway volume detach
railway volume update
railway volume delete
```

The parent command accepts `--service <SERVICE>` and `--environment <ENVIRONMENT>` before the subcommand, so the full shape is often:

```bash
railway volume --service <SERVICE> --environment <ENVIRONMENT> <subcommand> ...
```

### Choose the right volume command

| If the user wants to... | Prefer | Why |
|---|---|---|
| See volumes | `railway volume list` | Read-only listing |
| Create a volume | `railway volume add` | Creation path |
| Attach an existing volume to a service | `railway volume attach` | Connection path |
| Detach a volume from a service but keep the volume | `railway volume detach` | Non-destructive disconnect |
| Rename or remount a volume | `railway volume update` | Mutation path without deletion |
| Permanently remove a volume | `railway volume delete` | Destructive delete path |

### High-value volume patterns

```bash
railway volume --service <SERVICE> add --mount-path /data
railway volume --service <SERVICE> attach --volume <VOLUME> --yes
railway volume --service <SERVICE> detach --volume <VOLUME> --yes
railway volume update --volume <VOLUME> --name <NAME> --mount-path /new-path --json
railway volume delete --volume <VOLUME> --yes
```

Useful local details:

- `volume add` takes `--mount-path`
- `volume attach`, `detach`, `update`, and `delete` all work with `--volume <VOLUME>`
- `volume delete` may require `--2fa-code` in non-interactive mode if 2FA is enabled
- `detach` removes the service attachment, while `delete` removes the volume itself

## Nearby-command traps

| Confusion | Correct choice | Why |
|---|---|---|
| "Create a new function" versus "link to an existing one" | `functions new` for creation, `functions link` for association | Different lifecycle steps |
| "Push local edits" versus "pull remote state" | `functions push` uploads, `functions pull` downloads | Opposite sync directions |
| "Detach a volume" versus "delete a volume" | `volume detach` keeps the volume, `volume delete` destroys it | High-risk distinction |
| "Rename/remount a volume" versus "recreate a volume" | `volume update` first | Less destructive path |

## Guardrails

- Put `--service` and `--environment` before the `volume` subcommand when scoping volumes.
- Treat `functions delete` and `volume delete` as destructive operations.
- Pair this file with `references/cli/deployments-and-releases.md` when a function change should be followed by deployment or verification work.

