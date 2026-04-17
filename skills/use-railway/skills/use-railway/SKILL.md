---
name: use-railway
description: Use skill if you are using Railway CLI for deploys, logs, environments, linking, scaling, SSH, database access, or installed-versus-upstream command questions.
---

# Use Railway

Use Railway CLI from evidence, not memory.

## Trigger boundary

Use this skill when the task is about:

- exact `railway` commands, flags, aliases, arguments, or nested subcommands
- choosing between nearby Railway CLI commands for deploys, logs, environments, domains, scaling, SSH, functions, volumes, or database access
- reconciling the installed Railway CLI with newer first-party Railway docs or releases
- using first-party Railway runbooks as supporting context for a CLI-first answer

Do not use this skill when:

- the task is purely dashboard-only, GraphQL-only, or API-only Railway work
- the job is general cloud architecture or infrastructure planning with no Railway CLI decision to make
- a generic shell, Git, or deployment skill can answer the question without Railway-specific context

## Non-negotiable rules

1. Treat the local extracted help snapshot as the source of truth for the installed binary.
2. Treat newer docs and releases as upstream context, not proof that a command exists locally.
3. Route to one workflow guide first, then pull exact flags from the command reference.
4. Explain close command splits when Railway has look-alike choices.
5. Stay read-safe by default; do not mutate Railway resources unless the user explicitly wants an operational action.
6. Never guess flags, aliases, or possible values from memory.

## Recommended workflow

### 1. Establish version scope

Run `railway --version` when version drift could matter.

Read `references/research/version-drift.md` first if:

- the user says `latest`, `current`, `today`, or `most recent`
- the docs show a command the installed CLI does not
- the question mentions newer families such as `skills`, `agent`, `bucket`, or `starship`

### 2. Choose the smallest reference set

- Exact syntax, flags, aliases, nested subcommands, arguments, or possible values:
  - `references/cli/railway-cli-command-reference.md`
- Raw help wording or formatting proof:
  - `references/cli/railway-cli-live-help-snapshot.md`
- Top-level completeness audit:
  - `references/cli/command-family-coverage.md`
- Workflow choice:
  - one matching `references/cli/*.md` router
  - then `references/cli/railway-cli-command-reference.md`
- Upstream Railway guidance beyond the installed CLI:
  - one matching file under `references/upstream/` or `references/database/`
  - plus `references/research/version-drift.md` when local and upstream may differ

### 3. Answer case by case

For each answer:

1. state whether the scope is local CLI, upstream Railway sources, or both
2. choose the best command or reference route
3. include exact flags, aliases, nested subcommands, or possible values when asked
4. explain the closest confusing alternative when needed
5. add a version-drift note only if it materially changes the answer

## Common decision splits

| Need | Read |
|---|---|
| `up` vs `deploy`, `redeploy` vs `restart`, or release rollback questions | `references/cli/deployments-and-releases.md` |
| `delete` vs `unlink`, `link` vs `init`, project setup, `add`, `open`, or auth/context | `references/cli/context-projects-and-linking.md` |
| `run` vs `shell` vs `dev`, shell completion, or local variable injection | `references/cli/local-development-and-shells.md` |
| `connect` vs `ssh`, `status`, or logs | `references/cli/observability-and-access.md` |
| `environment`, `variable`, `domain`, `scale`, or `service scale` | `references/cli/configuration-networking-and-scaling.md` |
| Functions or volumes | `references/cli/functions-and-volumes.md` |
| A vague "what Railway command should I use?" question | `references/cli/common-workflows.md` |
| Dashboard URL parsing, resource-model context, or safe preflight before acting | `references/upstream/resource-model-and-preflight.md` |
| First-party setup, deploy, configure, operate, docs/API, or DB runbooks | the matching file under `references/upstream/` or `references/database/` |

## Quick routing

- "What flags does `railway X` support?" -> `references/cli/railway-cli-command-reference.md`
- "Show the exact help text for `railway X`" -> `references/cli/railway-cli-live-help-snapshot.md`
- "Show me every local Railway command family this skill covers" -> `references/cli/command-family-coverage.md`
- "Which Railway command fits this task?" -> `references/cli/common-workflows.md`
- "I need to link, init, add, delete, or inspect project context" -> `references/cli/context-projects-and-linking.md`
- "I need to deploy, redeploy, restart, or roll back the latest deployment" -> `references/cli/deployments-and-releases.md`
- "I need `run`, `shell`, or `dev`" -> `references/cli/local-development-and-shells.md`
- "I need logs, status, `connect`, or `ssh`" -> `references/cli/observability-and-access.md`
- "I need env vars, config edits, domains, or scale" -> `references/cli/configuration-networking-and-scaling.md`
- "I need functions or volumes" -> `references/cli/functions-and-volumes.md`
- "The docs show a command I do not have" -> `references/research/version-drift.md`
- "I want Railway's own setup or deploy runbook, not just local CLI syntax" -> `references/upstream/operations/setup.md` or `references/upstream/operations/deploy.md`
- "I pasted a Railway dashboard URL and need a safe starting point" -> `references/upstream/resource-model-and-preflight.md`
- "I need first-party Railway database analysis guidance" -> `references/database/analyze-db.md`

## Refresh the local snapshot

When the Railway CLI changes, refresh the generated references from this skill directory:

```bash
node scripts/extract-railway-cli-help.mjs
railway --version
```

## Reference routing

| File | When to read |
|---|---|
| `references/cli/railway-cli-command-reference.md` | Exact command syntax, flags, aliases, arguments, nested subcommands, and possible values from the installed CLI. |
| `references/cli/railway-cli-live-help-snapshot.md` | Exact raw help wording, examples, or formatting proof matters. |
| `references/cli/command-family-coverage.md` | Auditing completeness or proving that every local top-level command family is routed. |
| `references/cli/common-workflows.md` | The user knows the job but not the right Railway command family yet. |
| `references/cli/context-projects-and-linking.md` | Auth, context, project discovery, `link`, `unlink`, `init`, `add`, `delete`, `open`, `docs`, `completion`, or `upgrade`. |
| `references/cli/deployments-and-releases.md` | `up`, template deploys, deployment history, `redeploy`, `restart`, or `down`. |
| `references/cli/local-development-and-shells.md` | `run`, `shell`, `dev`, `dev configure`, `dev clean`, or shell completion. |
| `references/cli/observability-and-access.md` | `status`, `logs`, `connect`, `ssh`, or service-level status/log routing. |
| `references/cli/configuration-networking-and-scaling.md` | `environment`, `variable`, `domain`, `scale`, or `service scale`. |
| `references/cli/functions-and-volumes.md` | Railway functions and volume workflows, including attach/detach/delete distinctions. |
| `references/upstream/resource-model-and-preflight.md` | Dashboard URLs, Railway resource-model context, or a safe preflight before choosing commands. |
| `references/upstream/operations/setup.md` | First-party Railway setup flows for projects, services, templates, buckets, or workspace setup. |
| `references/upstream/operations/deploy.md` | First-party Railway deploy flows for `up`, restart/redeploy, build config, Railpack, Dockerfiles, or monorepos. |
| `references/upstream/operations/configure.md` | First-party Railway configuration flows for environments, variables, domains, networking, or config patches. |
| `references/upstream/operations/operate.md` | First-party Railway operating flows for status, logs, metrics, health, or recovery. |
| `references/upstream/docs-and-api/request.md` | Official docs endpoints, community-search guidance, GraphQL gaps, or template discovery. |
| `references/database/analyze-db.md` | Railway database analysis routing or DB-type selection. |
| `references/database/analyze-db-postgres.md` | First-party Railway PostgreSQL analysis and tuning guidance. |
| `references/database/analyze-db-mysql.md` | First-party Railway MySQL analysis and tuning guidance. |
| `references/database/analyze-db-redis.md` | First-party Railway Redis analysis and tuning guidance. |
| `references/database/analyze-db-mongo.md` | First-party Railway MongoDB analysis and tuning guidance. |
| `references/research/version-drift.md` | Latest/current Railway CLI questions or upstream docs that exceed the installed local snapshot. |

## Output contract

Return answers in this order unless the user wants a different format:

1. scope line: local installed CLI, upstream official sources, or both
2. best command or routed next step
3. important flags, aliases, subcommands, or possible values
4. near-neighbor distinction when confusion is likely
5. version-drift note only when it changes the answer

## Guardrails

- Do not treat `railway deploy` and `railway up` as synonyms.
- Do not treat `railway delete` and `railway unlink` as synonyms.
- Do not treat `railway redeploy` and `railway restart` as synonyms.
- Do not present upstream-only commands as locally available without saying so explicitly.
- Do not default to dashboard instructions when the user asked about the CLI.
- Do not let the copied upstream runbooks override the local extracted CLI when the user is asking about the installed binary's exact command surface.
- Do not trust the linked directory over an explicit Railway dashboard URL or explicit project/environment/service identifiers.
- Do not mutate Railway resources unless the user explicitly asked for an operational action; this skill is reference-first.
- Do not use this skill for purely dashboard, GraphQL, or infrastructure-only Railway work unless the CLI question is central.
