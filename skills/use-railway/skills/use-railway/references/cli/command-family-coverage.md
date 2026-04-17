# Command Family Coverage

Use this file when you need a compact audit trail showing that every local top-level Railway CLI command family is accounted for by the skill's routed references.

This file is generated from `scripts/verify-use-railway-skill.mjs` against the extracted local `railway 4.29.0` command tree.

## Coverage summary

- Local top-level command families captured: `36`
- Coverage entries defined: `36`
- Primary workflow or reference routes used: `8`

For exact flags, aliases, possible values, and nested subcommands, always pair this matrix with `references/cli/railway-cli-command-reference.md`.

## Command family matrix

| Command | Aliases | Primary route | Secondary routes | Why this route exists |
|---|---|---|---|---|
| `add` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Add a service or managed database to the current project. |
| `completion` | None | `references/cli/local-development-and-shells.md` | `references/cli/railway-cli-command-reference.md` | Generate shell-completion scripts for supported shells. |
| `connect` | None | `references/cli/observability-and-access.md` | `references/cli/railway-cli-command-reference.md` | Open a database-native shell for a Railway database service. |
| `delete` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Delete a Railway project; distinct from unlinking the local directory. |
| `deploy` | None | `references/cli/deployments-and-releases.md` | `references/cli/railway-cli-command-reference.md` | Provision a Railway template into the project. |
| `deployment` | None | `references/cli/deployments-and-releases.md` | `references/cli/railway-cli-command-reference.md` | List deployment history or use deployment-scoped release commands. |
| `dev` | `develop` | `references/cli/local-development-and-shells.md` | `references/cli/railway-cli-command-reference.md` | Run Railway-backed services locally and manage local dev state. |
| `domain` | None | `references/cli/configuration-networking-and-scaling.md` | `references/cli/railway-cli-command-reference.md` | Generate Railway domains or attach custom domains to services. |
| `docs` | None | `references/cli/context-projects-and-linking.md` | `references/research/version-drift.md` | Open Railway documentation from the CLI. |
| `down` | None | `references/cli/deployments-and-releases.md` | `references/cli/railway-cli-command-reference.md` | Remove the latest deployment without deleting the project. |
| `environment` | `env` | `references/cli/configuration-networking-and-scaling.md` | `references/cli/railway-cli-command-reference.md` | Create, link, edit, inspect, or delete environments. |
| `init` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Create a new Railway project. |
| `link` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Associate the current directory with a Railway project context. |
| `list` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | List accessible Railway projects. |
| `login` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Authenticate the local Railway CLI. |
| `logout` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Clear the local Railway CLI session. |
| `logs` | None | `references/cli/observability-and-access.md` | `references/cli/railway-cli-command-reference.md` | Inspect build, deployment, or runtime logs with bounded fetches. |
| `open` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Open the current Railway project in the dashboard. |
| `project` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Use project-scoped list, link, and delete subcommands. |
| `run` | `local` | `references/cli/local-development-and-shells.md` | `references/cli/railway-cli-command-reference.md` | Run a single local command with Railway variables injected. |
| `service` | None | `references/cli/common-workflows.md` | `references/cli/context-projects-and-linking.md`<br>`references/cli/observability-and-access.md`<br>`references/cli/deployments-and-releases.md`<br>`references/cli/configuration-networking-and-scaling.md`<br>`references/cli/railway-cli-command-reference.md` | Split by subcommand: link, status, logs, redeploy, restart, and scale route to different guides. |
| `shell` | None | `references/cli/local-development-and-shells.md` | `references/cli/railway-cli-command-reference.md` | Open a local subshell with Railway variables available. |
| `ssh` | None | `references/cli/observability-and-access.md` | `references/cli/railway-cli-command-reference.md` | Open a service shell or run a remote command in a service container. |
| `status` | None | `references/cli/observability-and-access.md` | `references/cli/railway-cli-command-reference.md` | Inspect linked project and deployment health quickly. |
| `unlink` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Remove only the local directory association. |
| `up` | None | `references/cli/deployments-and-releases.md` | `references/cli/railway-cli-command-reference.md` | Upload and deploy code from the current directory. |
| `upgrade` | None | `references/cli/context-projects-and-linking.md` | `references/research/version-drift.md` | Upgrade the installed Railway CLI. |
| `variable` | `variables`, `vars`, `var` | `references/cli/configuration-networking-and-scaling.md` | `references/cli/railway-cli-command-reference.md` | List, set, or delete environment variables for a service. |
| `whoami` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Inspect the current logged-in Railway user and auth context. |
| `volume` | None | `references/cli/functions-and-volumes.md` | `references/cli/railway-cli-command-reference.md` | List, add, attach, detach, update, or delete Railway volumes. |
| `redeploy` | None | `references/cli/deployments-and-releases.md` | `references/cli/railway-cli-command-reference.md` | Rebuild and redeploy the latest service deployment. |
| `restart` | None | `references/cli/deployments-and-releases.md` | `references/cli/railway-cli-command-reference.md` | Restart the latest deployment without rebuilding. |
| `scale` | None | `references/cli/configuration-networking-and-scaling.md` | `references/cli/railway-cli-command-reference.md` | Set explicit per-region instance counts in local 4.29.0. |
| `check_updates` | None | `references/cli/context-projects-and-linking.md` | `references/cli/railway-cli-command-reference.md` | Inspect update-check behavior for the installed CLI. |
| `functions` | `function`, `func`, `fn`, `funcs`, `fns` | `references/cli/functions-and-volumes.md` | `references/cli/railway-cli-command-reference.md` | List, create, link, push, pull, or delete Railway functions. |
| `help` | None | `references/cli/railway-cli-command-reference.md` | `references/cli/railway-cli-live-help-snapshot.md` | Use the generated reference or raw snapshot when the user wants pure help output. |

## Audit notes

- `service` is intentionally routed through `references/cli/common-workflows.md` first because its nested subcommands split across linking, observability, deployment, and scaling concerns.
- `help` is covered by the generated command reference and the raw help snapshot rather than by a workflow guide.
- This matrix proves family coverage, not full flag-level coverage; the flag-complete source remains `references/cli/railway-cli-command-reference.md`.
