# Observability and Access

Use this file when the user wants health checks, deployment status, logs, database shells, or service SSH access.

All commands below are confirmed in the local `railway 4.29.0` snapshot. For exact flag lists and full option sets, pair this file with `references/cli/railway-cli-command-reference.md`.

## Start broad, then narrow

These are the safest first reads when the user says "what is wrong?" or "is this service healthy?"

```bash
railway status
railway status --json
railway service status --all --json
railway deployment list --limit 20 --json
```

Use them like this:

| Need | Command | Notes |
|---|---|---|
| Linked project summary | `railway status` | Smallest context-level health check |
| Deployment status for one or more services | `railway service status` | Use `--all` for the whole environment |
| Recent deployment history and IDs | `railway deployment list` | Good bridge into logs or restart decisions |

## Choose `status` vs `service status`

| If the user wants... | Prefer | Why |
|---|---|---|
| The overall linked project/environment summary | `railway status` | Broad context snapshot |
| Deployment status for one service or all services | `railway service status` | Service-level deployment status command |

`railway service status` is the better choice when the user mentions one service by name or asks about all services in an environment.

## Logging rules

Railway log commands stream indefinitely by default. Use bounded fetches unless the user explicitly wants a live stream.

```bash
railway logs --lines 100
railway logs --build --lines 200
railway logs --since 1h --lines 400
railway logs --service <SERVICE> --environment <ENVIRONMENT> --lines 200 --json
railway service logs --service <SERVICE> --lines 200 --filter "@level:error" --json
```

### Choose `logs` vs `service logs`

Both paths expose the same local log surface. Use whichever matches the user’s phrasing or current namespace.

| Need | Command |
|---|---|
| General deployment logs path | `railway logs` |
| Service-oriented logs path | `railway service logs` |

### High-value log flags

| Flag | Use when |
|---|---|
| `--lines <N>` | Fetch a bounded number of lines and avoid streaming |
| `--since <TIME>` | Look back over a relative or ISO 8601 time window |
| `--until <TIME>` | Close the time window |
| `--filter <FILTER>` | Restrict to errors, warnings, or text matches |
| `--build` | Build logs matter more than runtime logs |
| `--deployment` | Deployment logs, not build logs |
| `--latest` | The latest deployment matters even if it failed or is still building |
| `--json` | You need structured log records |

Useful local log examples from help:

```bash
railway logs --lines 10 --filter "@level:error"
railway logs --since 30m --until 10m
railway logs --latest
```

## Metrics and deeper analysis

The local `4.29.0` CLI snapshot is strong on status, logs, `connect`, and `ssh`, but not on metrics queries or database tuning.

Route like this:

| If the user wants... | Read next |
|---|---|
| Resource usage metrics across services or environments | `references/research/version-drift.md`, then `references/upstream/operations/operate.md` or `references/upstream/docs-and-api/request.md` |
| Database performance analysis, query tuning, or deep health review | `references/research/version-drift.md`, then `references/database/analyze-db.md` |
| Only a database shell | stay in this file and use `railway connect` |
| Only a service shell or remote command | stay in this file and use `railway ssh` |

## Choose `connect` vs `ssh`

These are not interchangeable.

| If the user wants to... | Prefer | Why |
|---|---|---|
| Open the database-native shell for a Railway database | `railway connect [SERVICE_NAME]` | Uses the database shell for the managed database type |
| Open a service shell or run a remote command in a service container | `railway ssh [COMMAND]...` | General service-shell access |

Common exact patterns:

```bash
railway connect <DATABASE_SERVICE>
railway connect --environment <ENVIRONMENT> <DATABASE_SERVICE>
railway ssh --service <SERVICE>
railway ssh --service <SERVICE> --environment <ENVIRONMENT> --project <PROJECT>
railway ssh --service <SERVICE> --deployment-instance <INSTANCE_ID>
railway ssh --service <SERVICE> --session
```

`ssh` nuances confirmed locally:

- `--deployment-instance` targets a specific active instance
- `--session` opens or joins a tmux session and can optionally name it
- positional `COMMAND...` lets the user run a command instead of starting an interactive shell

## Fast troubleshooting sequence

When the user asks for debugging flow instead of one command:

1. Run `railway status --json` for linked context.
2. Run `railway service status --all --json` or target one service.
3. Use `railway deployment list --service <SERVICE> --json` to get deployment IDs and statuses.
4. Pull bounded logs with `railway logs --service <SERVICE> --lines 200 --json`.
5. Switch to `--build` if the failure happened before runtime.
6. Use `connect` for database-shell inspection or `ssh` for service-shell inspection.

## Failure classification before recovery

Once the first bounded log fetch is in hand, classify the problem before suggesting fixes:

| Failure class | Typical signal | Read next |
|---|---|---|
| Build failure | Fails before the process starts, build logs matter most | `references/cli/deployments-and-releases.md` and, if needed, `references/upstream/operations/deploy.md` |
| Runtime failure | Build succeeded, app crashes or misbehaves | stay here for logs and shell access, then pair with `references/cli/configuration-networking-and-scaling.md` |
| Config-driven failure | Something broke after env or config changes | `references/cli/configuration-networking-and-scaling.md` |
| Networking failure | Domain, port, or service-to-service traffic looks wrong | `references/cli/configuration-networking-and-scaling.md` and, if upstream-only, `references/upstream/operations/configure.md` |
| Database health or performance failure | Shell access is not enough; the user wants diagnosis or tuning | `references/database/analyze-db.md` |

## Guardrails

- Do not leave `logs` streaming unless the user explicitly wants a live tail.
- Use `connect` only for database services; use `ssh` for application containers.
- Do not invent a local metrics command if the user asks for metrics; route through version drift and the upstream operate/request guides instead.
- Pair this file with `references/cli/deployments-and-releases.md` when the user needs both diagnosis and recovery actions.
