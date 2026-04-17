# Deployments and Releases

Use this file when the user wants to ship code, provision a template, inspect deployment history, rebuild, restart, or remove the latest deployment.

All commands below are confirmed in the local `railway 4.29.0` snapshot. For every exact flag and nested path, pair this file with `references/cli/railway-cli-command-reference.md`.

## Pick the right release command

| If the user wants to... | Prefer | Why |
|---|---|---|
| Upload the current directory and deploy it | `railway up` | This is the code-upload path. |
| Provision a template like Postgres | `railway deploy --template <TEMPLATE>` | In local `4.29.0`, `deploy` is the template path. |
| List prior deployments | `railway deployment list` | Best history view. |
| Rebuild and redeploy the latest deployment | `railway redeploy` | Full rebuild cycle. |
| Restart the latest deployment without rebuilding | `railway restart` | Process restart only. |
| Remove the most recent deployment | `railway down` | Removes the latest deployment, not the project. |

## Deploy the current directory

These are the high-value `up` patterns:

```bash
railway up --detach -m "<summary>"
railway up --ci -m "<summary>"
railway up --service <SERVICE> --environment <ENVIRONMENT> --detach -m "<summary>"
railway up --project <PROJECT_ID> --environment <ENVIRONMENT> --service <SERVICE> --detach -m "<summary>"
```

Important `up` distinctions:

| Option | Use when |
|---|---|
| `--detach` | The user wants the deploy kicked off without staying attached to logs. |
| `--ci` | The user wants build logs streamed until the build completes. |
| `--json` | Machine-readable log output is needed; local help says this implies CI-style behavior. |
| `--project`, `--environment`, `--service` | The deploy must target something other than the linked defaults. |
| `--path-as-root` | The path argument itself should become the archive root. |
| `--no-gitignore` | The user explicitly wants ignored files included in the upload. |

If the question shifts from "which release command?" to "how does Railway build this repo?", pair this file with `references/upstream/operations/deploy.md` after checking `references/research/version-drift.md`.

## Template provisioning

When the user says "deploy Postgres", "add Redis from a template", or "provision a template", route here instead of `up`:

```bash
railway deploy --template <TEMPLATE>
railway deploy --template <TEMPLATE> --variable KEY=VALUE
```

`deploy` is not the same as `up` in the local CLI:

- `deploy` provisions a Railway template into the project
- `up` uploads and deploys source from the current directory

## History, rebuild, restart, remove

These commands work together as the release-management set:

```bash
railway deployment list --service <SERVICE> --environment <ENVIRONMENT> --limit 20 --json
railway redeploy --service <SERVICE> --yes
railway restart --service <SERVICE> --yes
railway down --service <SERVICE> --environment <ENVIRONMENT> --yes
```

Use them like this:

| Need | Command | Meaning |
|---|---|---|
| Recent deployment IDs and statuses | `railway deployment list` | Read-only history and status view |
| Fresh build from the same source | `railway redeploy` | Rebuild + redeploy |
| Restart running container only | `railway restart` | No rebuild |
| Remove latest deployment from a service | `railway down` | Deployment removal only |

The service namespace exposes matching nested paths too:

```bash
railway service redeploy --service <SERVICE> --yes
railway service restart --service <SERVICE> --yes
```

Use the top-level path unless the user is already working inside `service` subcommands.

## Nearby-command traps

| Confusion | Correct choice | Why |
|---|---|---|
| "Deploy this folder" versus "deploy a template" | `up` for folders, `deploy --template` for templates | Same word, different command families |
| "Redeploy" versus "restart" | `redeploy` rebuilds; `restart` does not | This is the most important release distinction |
| "Down" versus "delete" | `down` removes only the latest deployment | `delete` is for projects, not releases |

## Build, builder, and monorepo depth

These details matter when the user is past the simple `up` versus `deploy` choice and is asking why a build behaves the way it does.

Upstream Railway guidance adds three especially useful patterns:

| If the user means... | Prefer | Why |
|---|---|---|
| "This package lives in a subdirectory and does not depend on the rest of the repo" | `source.rootDirectory` guidance from `references/upstream/operations/deploy.md` | Best fit for isolated monorepo services. |
| "This service depends on shared workspace packages" | shared-monorepo build/start-command patterns from `references/upstream/operations/deploy.md` | Restrictive `rootDirectory` can hide shared code. |
| "Only some paths should trigger redeploys" | `build.watchPatterns` guidance from `references/upstream/operations/deploy.md` | Prevents unrelated packages from redeploying every service. |

Stable examples worth preserving from the upstream lane:

- builder selection: `RAILPACK` versus `DOCKERFILE`
- pinned build/runtime language versions via Railpack variables
- static-site output directory behavior
- shared-versus-isolated monorepo strategy

Use the upstream deploy guide for those platform details, but keep this file primary for the installed CLI's release-command choices.

## What to read next

- For logs and verification after a deploy, read `references/cli/observability-and-access.md`
- For env vars or config changes that should happen before the next deploy, read `references/cli/configuration-networking-and-scaling.md`
- For builder choice, Railpack variables, Dockerfile paths, static sites, or monorepo behavior, read `references/upstream/operations/deploy.md`
- For exact flag lists, read `references/cli/railway-cli-command-reference.md`
