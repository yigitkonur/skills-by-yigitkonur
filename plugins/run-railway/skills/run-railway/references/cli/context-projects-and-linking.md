# Context, Projects, and Linking

Use this file when the user is trying to identify Railway context, authenticate, create or link projects and services, or use the CLI utility commands around setup.

All commands below are confirmed in the local `railway 4.29.0` snapshot. For full option lists, read `references/cli/railway-cli-command-reference.md`.

## Start with identity and scope

Use these first when the user says "what am I linked to?" or "which account am I using?"

```bash
railway whoami
railway whoami --json
railway status
railway status --json
railway list
railway list --json
railway project list
railway project list --json
```

Choose between them like this:

| Need | Command | Notes |
|---|---|---|
| Current auth identity | `railway whoami` | Best first check for login state. |
| Linked project, environment, and service | `railway status` | Use `--json` when you need machine-readable context. |
| All accessible projects | `railway list` | Broad account-level project listing. |
| Project list from the `project` namespace | `railway project list` | Useful when already thinking in project subcommands. |

## When explicit IDs beat the linked directory

If the user pasted a Railway dashboard URL or already knows the project, environment, or service identifiers, do not default to relinking first.

Prefer explicit selectors like:

```bash
railway status --json
railway link --project <PROJECT> --environment <ENVIRONMENT> --service <SERVICE>
railway up --project <PROJECT> --environment <ENVIRONMENT> --service <SERVICE> --detach -m "<summary>"
railway logs --project <PROJECT> --environment <ENVIRONMENT> --service <SERVICE> --lines 200 --json
```

Decision rule:

| Situation | Prefer |
|---|---|
| The user wants to change persistent local context for this directory | `railway link` |
| The user is acting on one explicit remote target and does not want local state changed | explicit `--project`, `--environment`, and `--service` selectors |
| The user pasted a Railway dashboard URL | `references/upstream/resource-model-and-preflight.md` first, then the narrow command guide |

This keeps one-off answers from mutating the directory unnecessarily.

## Choose the right linking command

Railway has a few closely related link flows. Pick the narrowest one that matches the task.

| If the user wants to... | Prefer | Why |
|---|---|---|
| Link the current directory to a project, and optionally an environment or service too | `railway link` or `railway project link` | These are the full local-context commands. Both expose `--project`, `--environment`, `--service`, and `--workspace`. |
| Switch only the service within an already linked project | `railway service link [SERVICE]` | Keeps project context intact and only changes the linked service. |
| Switch only the environment within an already linked project | `railway environment link [ENVIRONMENT]` | Best when the project is right but the active environment is wrong. |
| Remove local directory association | `railway unlink` | Local-only cleanup; does not touch Railway resources. |

Common exact patterns:

```bash
railway link --project <PROJECT> --environment <ENVIRONMENT> --service <SERVICE>
railway project link --project <PROJECT> --workspace <WORKSPACE>
railway service link <SERVICE>
railway environment link <ENVIRONMENT>
railway unlink
```

## Create, provision, or add

These commands sound similar, but they do different jobs.

| If the user wants to... | Prefer | Why |
|---|---|---|
| Create a brand-new Railway project | `railway init` | This is the project-creation path. |
| Add a service inside an existing project | `railway add --service <SERVICE>` | Creates a service in the current project. |
| Add a managed database service | `railway add --database <postgres|mysql|redis|mongo>` | Database types are explicit in local help. |
| Bootstrap from a Railway template | `railway deploy --template <TEMPLATE>` | In local `4.29.0`, `deploy` is the template command, not the code-upload command. |

Common exact patterns:

```bash
railway init --name <PROJECT_NAME> --workspace <WORKSPACE>
railway add --service <SERVICE>
railway add --database postgres
railway add --service <SERVICE> --repo <REPO>
railway add --service <SERVICE> --image <IMAGE>
railway deploy --template <TEMPLATE>
```

Useful local `add` details:

- `--database` only accepts `postgres`, `mysql`, `redis`, or `mongo`.
- `--service` may be blank to let Railway generate a name.
- `--variables KEY=VALUE` can be passed multiple times during service creation.
- `--repo` and `--image` let the service start linked to a repo or image instead of being empty.

If the user is asking about workspaces, bucket/object storage, or richer setup heuristics than the local help exposes, pair this file with:

- `references/upstream/resource-model-and-preflight.md`
- `references/upstream/operations/setup.md`

## Delete versus unlink

This is the highest-risk confusion in this command group.

| Action | Command | Scope |
|---|---|---|
| Remove only the local directory association | `railway unlink` | Local working directory only |
| Delete a Railway project | `railway delete --project <PROJECT> --yes` | Remote project resource |

If the user says "disconnect this repo" or "stop using this directory," that is usually `unlink`, not `delete`.

## Utility commands in this area

These are small but still part of everyday Railway CLI navigation:

```bash
railway login
railway logout
railway open
railway docs
railway completion zsh
railway upgrade
railway check_updates --json
```

Use them like this:

| Need | Command |
|---|---|
| Sign in | `railway login` |
| Sign out | `railway logout` |
| Open the dashboard for the linked project | `railway open` |
| Open Railway docs in the browser | `railway docs` |
| Generate a completion script | `railway completion <bash|elvish|fish|powershell|zsh>` |
| Upgrade the installed CLI | `railway upgrade` |
| Inspect the updater path | `railway check_updates` |

## Guardrails

- Prefer explicit selectors when the user is not operating from the linked project directory.
- If the task is driven by a Railway dashboard URL, parse the target context before trusting the linked directory.
- Buckets are not part of the local `4.29.0` top-level help snapshot; read `references/research/version-drift.md` before routing bucket questions into upstream setup guidance.
- Do not answer with upstream-only commands from docs here; check `references/research/version-drift.md` first if the user mentions a command missing locally.
- Pair this file with `references/cli/railway-cli-command-reference.md` whenever the user asks for exact flags or possible values.
