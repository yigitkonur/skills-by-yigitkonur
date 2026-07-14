# Resource Model and Preflight

Use this file when the user is reasoning about Railway objects, pastes a Railway dashboard URL, or needs a safe preflight before any Railway action.

This is an adapted upstream guide. It explains Railway platform context, but it does not replace the local `railway 4.29.0` command reference for exact syntax.

## Railway object model

Railway questions get easier when the object hierarchy is explicit:

| Object | What it is | Why it matters in CLI work |
|---|---|---|
| Workspace | Billing and team boundary | Project creation and linking can be workspace-specific. |
| Project | Top-level app or system container | Most linking and service creation starts here. |
| Environment | Isolated config and deployment plane inside a project | Many commands need the correct environment scope. |
| Service | Deployable app or managed database | Most operational commands eventually target a service. |
| Bucket | S3-compatible object storage resource | This is an upstream feature area and may not exist in the local CLI snapshot. |
| Deployment | One release instance of a service in an environment | Logs, restart, redeploy, and rollback-like actions all pivot on deployments. |

## When a dashboard URL changes the routing

If the user pastes a Railway dashboard URL, do not assume the locally linked directory is the correct target.

Common URL shapes:

```text
https://railway.com/project/<PROJECT_ID>/service/<SERVICE_ID>
https://railway.com/project/<PROJECT_ID>/service/<SERVICE_ID>?environmentId=<ENV_ID>
```

Rules:

- If the URL includes `project` and `service`, treat those IDs as the target context.
- If `environmentId` is present, prefer it over the locally linked environment.
- If the URL points at a service but the user asks for exact local command syntax, still pair the answer with `references/cli/railway-cli-command-reference.md`.

## Prefer explicit selectors over mutable linking

When the user already knows the target project, environment, or service, prefer explicit selectors:

```bash
railway up --project <PROJECT> --environment <ENVIRONMENT> --service <SERVICE>
railway logs --service <SERVICE> --environment <ENVIRONMENT> --project <PROJECT>
railway ssh --service <SERVICE> --environment <ENVIRONMENT> --project <PROJECT>
```

Why:

- it avoids mutating the directory's linked state just to answer one question
- it is safer in shared or nested repos
- it keeps the answer tied to the actual target the user named

Use `railway link` only when the user explicitly wants to change persistent local context.

## Preflight checklist

Before operational Railway work, verify the smallest safe set:

```bash
command -v railway
railway whoami --json
railway --version
```

Then choose context discovery:

| Situation | Best next step |
|---|---|
| User provided a Railway dashboard URL or explicit IDs | Trust the URL or explicit IDs first; do not start from local `railway status`. |
| User is asking about the current linked directory | `railway status --json` |
| User asked for latest/current behavior | `references/research/version-drift.md` before answering |
| User asked for buckets, metrics, GraphQL gaps, or database analysis | `references/research/version-drift.md`, then the matching `references/upstream/` or `references/database/` file |

## Upstream-only feature guardrail

The upstream Railway platform surface is broader than the local `railway 4.29.0` snapshot in this workspace.

Read `references/research/version-drift.md` first when the request involves:

- buckets or object storage
- metrics
- GraphQL-only mutations
- newer commands shown in docs or release notes
- database-analysis playbooks rather than plain CLI access

State both facts when needed:

1. what exists in the local installed CLI snapshot
2. what exists only in newer upstream Railway guidance

## Best pairings

| If the user needs... | Pair this file with... |
|---|---|
| Link or create the right project/service context | `references/cli/context-projects-and-linking.md` |
| Decide between `up`, `deploy`, `redeploy`, `restart`, or `down` | `references/cli/deployments-and-releases.md` |
| Handle upstream setup questions like workspaces or buckets | `references/upstream/operations/setup.md` |
| Handle upstream build, monorepo, or builder questions | `references/upstream/operations/deploy.md` |
| Handle upstream config patch, networking, or domain questions | `references/upstream/operations/configure.md` |
| Handle metrics, recovery, or deeper triage questions | `references/upstream/operations/operate.md` |
| Handle docs, GraphQL, template search, or community research | `references/upstream/docs-and-api/request.md` |
| Handle database analysis and tuning | `references/database/analyze-db.md` |

## Guardrails

- Do not let this file override the local command reference for exact flags or subcommands.
- Do not assume a pasted Railway URL means the current directory is linked to the same target.
- Do not present buckets, metrics, or GraphQL-only operations as local `4.29.0` CLI facts without a version-drift note.
