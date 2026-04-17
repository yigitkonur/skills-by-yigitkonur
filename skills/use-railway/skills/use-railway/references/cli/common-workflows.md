# Common Workflows

Use this file when the user knows the Railway job they want done, but not the exact command yet.

This router is grounded in the locally extracted `railway 4.29.0` command surface. For exact flags, aliases, nested subcommands, and possible values, pair every path here with `references/cli/railway-cli-command-reference.md`.

## First routing rule

- If the user asks for the exact usage line, flags, aliases, possible values, or whether a subcommand exists, read `references/cli/railway-cli-command-reference.md` first.
- If the user asks for "latest", "current", or a command they saw in docs but not locally, read `references/research/version-drift.md` before answering.
- If the user asks about buckets, metrics, GraphQL gaps, dashboard URLs, or database analysis, read `references/research/version-drift.md` before routing into the upstream or database lanes.

## Case router

| User intent | Read next | Why |
|---|---|---|
| "Am I logged in?", "What project is linked here?", "How do I link or unlink this directory?", "How do I create a project or service?" | `references/cli/context-projects-and-linking.md` | Covers auth, linked context, project discovery, linking, creation, deletion, and utility commands. |
| "How do I deploy this code?", "How do I redeploy or restart?", "How do I list deployments?", "How do I roll back the latest deployment?" | `references/cli/deployments-and-releases.md` | Covers `up`, `deploy`, `deployment list`, `redeploy`, `restart`, and `down`, including look-alike command choices. |
| "How do I run this locally with Railway vars?", "How do I open a Railway shell?", "How does `railway dev` work?" | `references/cli/local-development-and-shells.md` | Covers local command injection, subshells, local service orchestration, and shell completion. |
| "How do I inspect health, logs, database shells, or SSH into a service?" | `references/cli/observability-and-access.md` | Covers `status`, `service status`, `logs`, `service logs`, `connect`, and `ssh`. |
| "How do I change env vars, edit config, create an environment, attach a domain, or scale replicas?" | `references/cli/configuration-networking-and-scaling.md` | Covers `environment`, `variable`, `domain`, `scale`, and `service scale`. |
| "How do Railway functions or volumes work?" | `references/cli/functions-and-volumes.md` | Covers `functions` and `volume` command families. |
| "I pasted a Railway dashboard URL", "What do project/service/environment IDs mean here?", "Should I link or just pass selectors?" | `references/upstream/resource-model-and-preflight.md` | Handles Railway object model, URL context, preflight, and when explicit selectors beat mutable linking. |
| "How do buckets, workspaces, or template-search setup flows work?" | `references/upstream/operations/setup.md` | Covers upstream Railway platform setup surface that goes beyond the local CLI help snapshot. |
| "How do Railpack, builder choice, Dockerfile mode, static sites, or monorepos work?" | `references/upstream/operations/deploy.md` | Covers upstream build and monorepo behavior that is broader than the local release guide. |
| "How do config patches, service wiring, private domains, or richer networking flows work?" | `references/upstream/operations/configure.md` | Covers upstream configuration semantics that extend the local env/domain/scale guide. |
| "How do I get metrics, follow a recovery playbook, or do deeper Railway troubleshooting?" | `references/upstream/operations/operate.md` | Covers upstream metrics and structured triage/recovery patterns. |
| "How do I use Railway docs, Central Station, GraphQL, or template search?" | `references/upstream/docs-and-api/request.md` | Covers official docs endpoints, community research, GraphQL-only gaps, and template discovery. |
| "How do I analyze a Railway database, not just open a shell?" | `references/database/analyze-db.md` | Routes into the copied first-party database-analysis runbooks. |

## Near-neighbor decisions

These are the places users most often mean one command but say another:

| If the user means... | Prefer | Not this | Why |
|---|---|---|---|
| Deploying the current directory | `railway up` | `railway deploy` | In the local CLI, `deploy` provisions templates; `up` uploads and deploys code from disk. |
| Provisioning a template like Postgres | `railway deploy --template <template>` | `railway up` | `deploy` is the template path, not the code-upload path. |
| Changing the linked project, environment, or service | `railway link`, `railway project link`, `railway environment link`, or `railway service link` | `railway init` | Linking changes local context; `init` creates a new project. |
| Removing only the local link | `railway unlink` | `railway delete` | `unlink` is local-only; `delete` removes a Railway project. |
| Rebuilding from the same source | `railway redeploy` | `railway restart` | `redeploy` rebuilds and deploys; `restart` only restarts the latest deployment. |
| Restarting without rebuilding | `railway restart` | `railway redeploy` | Use restart when config or runtime state changed but source did not. |
| Removing the latest deployment | `railway down` | `railway delete` | `down` removes the latest deployment, not the whole project. |
| One local command with Railway vars | `railway run` | `railway shell` or `railway dev` | `run` is for a single process. |
| An interactive local shell with Railway vars | `railway shell` | `railway run` or `railway dev` | `shell` opens a subshell; `run` executes once. |
| Local multi-service orchestration | `railway dev` | `railway run` or `railway shell` | `dev` manages local service startup and teardown. |
| Region-count scaling with explicit flags | `railway scale` | `railway service scale` | In local `4.29.0`, `scale` exposes region flags directly. |

## Safe defaults

- Prefer explicit `--project`, `--environment`, and `--service` selectors when the user is acting outside the linked directory context.
- Use bounded log fetches with `--lines`, `--since`, or `--until` unless the user explicitly wants a live stream.
- If the user pastes a Railway URL or names explicit IDs, pair the answer with `references/upstream/resource-model-and-preflight.md` before recommending any relink.
- Read `references/research/version-drift.md` before mentioning commands or features like `bucket`, `metrics`, `starship`, `skills`, `agent`, or database-analysis workflows, because they are not part of the local `4.29.0` snapshot.
