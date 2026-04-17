# Railway CLI Command Reference

- Source: live `railway` binary on this machine
- Version: `railway 4.29.0`
- Generated at: `2026-04-17T12:01:12.566Z`
- Extraction rule: recursively ran `railway [subcommand...] --help` for every discovered command while skipping `help` recursion to avoid loops
- Total command entries captured: `72`

## Top-level commands

| Subcommand | Aliases | Description |
|---|---|---|
| `add` | None | Add a service to your project |
| `completion` | None | Generate completion script |
| `connect` | None | Connect to a database's shell (psql for Postgres, mongosh for MongoDB, etc.) |
| `delete` | None | Delete a project |
| `deploy` | None | Provisions a template into your project |
| `deployment` | None | Manage deployments |
| `dev` | `develop` | Run Railway services locally |
| `domain` | None | Add a custom domain or generate a railway provided domain for a service |
| `docs` | None | Open Railway Documentation in default browser |
| `down` | None | Remove the most recent deployment |
| `environment` | `env` | Create, delete or link an environment |
| `init` | None | Create a new project |
| `link` | None | Associate existing project with current directory, may specify projectId as an argument |
| `list` | None | List all projects in your Railway account |
| `login` | None | Login to your Railway account |
| `logout` | None | Logout of your Railway account |
| `logs` | None | View build or deploy logs from a Railway deployment |
| `open` | None | Open your project dashboard |
| `project` | None | Manage projects |
| `run` | `local` | Run a local command using variables from the active environment |
| `service` | None | Manage services |
| `shell` | None | Open a local subshell with Railway variables available |
| `ssh` | None | Connect to a service via SSH |
| `status` | None | Show information about the current project |
| `unlink` | None | Disassociate project from current directory |
| `up` | None | Upload and deploy project from the current directory |
| `upgrade` | None | Upgrade the Railway CLI to the latest version |
| `variable` | `variables`, `vars`, `var` | Manage environment variables for a service |
| `whoami` | None | Get the current logged in user |
| `volume` | None | Manage project volumes |
| `redeploy` | None | Redeploy the latest deployment of a service |
| `restart` | None | Restart the latest deployment of a service (without rebuilding) |
| `scale` | None | None |
| `check_updates` | None | Test the update check |
| `functions` | `function`, `func`, `fn`, `funcs`, `fns` | Manage project functions |
| `help` | None | Print this message or the help of the given subcommand(s) |

## `railway`

- Usage: `railway [COMMAND]`
- Summary: Interact with Railway via CLI
- Depth: `0`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `add` | None | Add a service to your project |
| `completion` | None | Generate completion script |
| `connect` | None | Connect to a database's shell (psql for Postgres, mongosh for MongoDB, etc.) |
| `delete` | None | Delete a project |
| `deploy` | None | Provisions a template into your project |
| `deployment` | None | Manage deployments |
| `dev` | `develop` | Run Railway services locally |
| `domain` | None | Add a custom domain or generate a railway provided domain for a service |
| `docs` | None | Open Railway Documentation in default browser |
| `down` | None | Remove the most recent deployment |
| `environment` | `env` | Create, delete or link an environment |
| `init` | None | Create a new project |
| `link` | None | Associate existing project with current directory, may specify projectId as an argument |
| `list` | None | List all projects in your Railway account |
| `login` | None | Login to your Railway account |
| `logout` | None | Logout of your Railway account |
| `logs` | None | View build or deploy logs from a Railway deployment |
| `open` | None | Open your project dashboard |
| `project` | None | Manage projects |
| `run` | `local` | Run a local command using variables from the active environment |
| `service` | None | Manage services |
| `shell` | None | Open a local subshell with Railway variables available |
| `ssh` | None | Connect to a service via SSH |
| `status` | None | Show information about the current project |
| `unlink` | None | Disassociate project from current directory |
| `up` | None | Upload and deploy project from the current directory |
| `upgrade` | None | Upgrade the Railway CLI to the latest version |
| `variable` | `variables`, `vars`, `var` | Manage environment variables for a service |
| `whoami` | None | Get the current logged in user |
| `volume` | None | Manage project volumes |
| `redeploy` | None | Redeploy the latest deployment of a service |
| `restart` | None | Restart the latest deployment of a service (without rebuilding) |
| `scale` | None | None |
| `check_updates` | None | Test the update check |
| `functions` | `function`, `func`, `fn`, `funcs`, `fns` | Manage project functions |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway add`

- Usage: `railway add [OPTIONS]`
- Summary: Add a service to your project
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-d, --database <DATABASE>` | None | The name of the database to add | `postgres`, `mysql`, `redis`, `mongo` |
| `-s, --service [<SERVICE>]` | None | The name of the service to create (leave blank for randomly generated) | None |
| `-r, --repo <REPO>` | None | The repo to link to the service | None |
| `-i, --image <IMAGE>` | None | The docker image to link to the service | None |
| `-v, --variables <VARIABLES>` | None | The "{key}={value}" environment variable pair to set the service variables. Example:<br><br><br><br>railway add --service --variables "MY_SPECIAL_ENV_VAR=1" --variables "BACKEND_PORT=3000" | None |
| `--verbose [<VERBOSE>]` | None | Verbose logging | `true`, `false` |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help (see a summary with '-h') | None |
| `-V, --version` | None | Print version | None |

### `railway check_updates`

- Usage: `railway check_updates [OPTIONS]`
- Summary: Test the update check
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway completion`

- Usage: `railway completion <SHELL>`
- Summary: Generate completion script
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `<SHELL>` | None | None | `bash`, `elvish`, `fish`, `powershell`, `zsh` |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway connect`

- Usage: `railway connect [OPTIONS] [SERVICE_NAME]`
- Summary: Connect to a database's shell (psql for Postgres, mongosh for MongoDB, etc.)
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[SERVICE_NAME]` | None | The name of the database to connect to | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-e, --environment <ENVIRONMENT>` | None | Environment to pull variables from (defaults to linked environment) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway delete`

- Usage: `railway delete [OPTIONS]`
- Summary: Delete a project
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --project <PROJECT>` | None | The project ID or name to delete | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `--2fa-code <TWO_FACTOR_CODE>` | None | 2FA code for verification (required if 2FA is enabled in non-interactive mode) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway deploy`

- Usage: `railway deploy [OPTIONS]`
- Summary: Provisions a template into your project
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-t, --template <TEMPLATE>` | None | The code of the template to deploy | None |
| `-v, --variable <VARIABLE>` | None | The "{key}={value}" environment variable pair to set the template variables<br><br><br><br>To specify the variable for a single service prefix it with "{service}." Example:<br><br><br><br>railway deploy -t postgres -v "MY_SPECIAL_ENV_VAR=1" -v "Backend.Port=3000" | None |
| `-h, --help` | None | Print help (see a summary with '-h') | None |
| `-V, --version` | None | Print version | None |

### `railway deployment`

- Usage: `railway deployment <COMMAND>`
- Summary: Manage deployments
- Depth: `1`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `list` | None | List deployments for a service with IDs, statuses and other metadata |
| `up` | None | Upload and deploy project from the current directory |
| `redeploy` | None | Redeploy the latest deployment of a service |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway dev`

- Usage: `railway dev [OPTIONS] [COMMAND]`
- Summary: Run Railway services locally
- Depth: `1`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `up` | None | Start services (default when no subcommand provided) |
| `down` | None | Stop services |
| `clean` | None | Stop services and remove volumes/data |
| `configure` | None | Configure local code services |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-v, --verbose` | None | Show verbose domain replacement info (for default 'up' command) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway docs`

- Usage: `railway docs`
- Summary: Open Railway Documentation in default browser
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway domain`

- Usage: `railway domain [OPTIONS] [DOMAIN]`
- Summary: Add a custom domain or generate a railway provided domain for a service.
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[DOMAIN]` | None | Optionally, specify a custom domain to use. If not specified, a domain will be generated.<br><br><br><br>Specifying a custom domain will also return the required DNS records to add to your DNS settings | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --port <PORT>` | None | The port to connect to the domain | None |
| `-s, --service <SERVICE>` | None | The name of the service to generate the domain for | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help (see a summary with '-h') | None |
| `-V, --version` | None | Print version | None |

### `railway down`

- Usage: `railway down [OPTIONS]`
- Summary: Remove the most recent deployment
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | Service to remove the deployment from (defaults to linked service) | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to remove the deployment from (defaults to linked environment) | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway environment`

- Usage: `railway environment [OPTIONS] [ENVIRONMENT] [COMMAND]`
- Summary: Create, delete or link an environment
- Depth: `1`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `link` | None | Link an environment to the current project |
| `new` | None | Create a new environment |
| `delete` | None | Delete an environment |
| `edit` | None | Edit an environment's configuration |
| `config` | None | Show environment configuration |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[ENVIRONMENT]` | None | The environment to link to | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway functions`

- Usage: `railway functions [OPTIONS] <COMMAND>`
- Summary: Manage project functions
- Depth: `1`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `list` | `ls` | List functions |
| `new` | `create` | Add a new function |
| `delete` | `remove`, `rm` | Delete a function |
| `push` | `up` | Push a new change to the function |
| `pull` | None | Pull changes from the linked function remotely |
| `link` | None | Link a function manually |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-e, --environment <ENVIRONMENT>` | None | Environment ID/name | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway init`

- Usage: `railway init [OPTIONS]`
- Summary: Create a new project
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-n, --name <NAME>` | None | Project name | None |
| `-w, --workspace <WORKSPACE>` | None | Workspace ID or name | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway link`

- Usage: `railway link [OPTIONS]`
- Summary: Associate existing project with current directory, may specify projectId as an argument
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-e, --environment <ENVIRONMENT>` | None | Environment to link to | None |
| `-p, --project <PROJECT>` | None | Project to link to | None |
| `-s, --service <SERVICE>` | None | The service to link to | None |
| `-t, --team <TEAM>` | None | The team to link to (deprecated: use --workspace instead) | None |
| `-w, --workspace <WORKSPACE>` | None | The workspace to link to | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway list`

- Usage: `railway list [OPTIONS]`
- Summary: List all projects in your Railway account
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway login`

- Usage: `railway login [OPTIONS]`
- Summary: Login to your Railway account
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-b, --browserless` | None | Browserless login | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway logout`

- Usage: `railway logout`
- Summary: Logout of your Railway account
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway logs`

- Usage: `railway logs [OPTIONS] [DEPLOYMENT_ID]`
- Summary: View build or deploy logs from a Railway deployment. This will stream logs by default, or fetch historical logs if the --lines, --since, or --until flags are provided.
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[DEPLOYMENT_ID]` | None | Deployment ID to view logs from. Defaults to most recent successful deployment, or latest deployment if none succeeded | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | Service to view logs from (defaults to linked service). Can be service name or service ID | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to view logs from (defaults to linked environment). Can be environment name or environment ID | None |
| `-d, --deployment` | None | Show deployment logs | None |
| `-b, --build` | None | Show build logs | None |
| `--json` | None | Output logs in JSON format. Each log line becomes a JSON object with timestamp, message, and any other attributes | None |
| `-n, --lines <LINES>` | `--tail` | Number of log lines to fetch (disables streaming) | None |
| `-f, --filter <FILTER>` | None | Filter logs using Railway's query syntax<br><br><br><br>Can be a text search ("error message" or "user signup"), attribute filters (@level:error, @level:warn), or a combination with the operators AND, OR, - (not). See https://docs.railway.com/guides/logs for full syntax. | None |
| `--latest` | None | Always show logs from the latest deployment, even if it failed or is still building | None |
| `-S, --since <TIME>` | None | Show logs since a specific time (disables streaming). Accepts relative times (e.g., 30s, 5m, 2h, 1d, 1w) or ISO 8601 timestamps (e.g., 2024-01-15T10:30:00Z) | None |
| `-U, --until <TIME>` | None | Show logs until a specific time (disables streaming). Same formats as --since | None |
| `-h, --help` | None | Print help (see a summary with '-h') | None |
| `-V, --version` | None | Print version | None |

### `railway open`

- Usage: `railway open [OPTIONS]`
- Summary: Open your project dashboard
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --print` | None | Print the URL instead of opening it | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway project`

- Usage: `railway project <COMMAND>`
- Summary: Manage projects
- Depth: `1`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `list` | None | List all projects in your Railway account |
| `link` | None | Link a project to the current directory |
| `delete` | None | Delete a project |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway redeploy`

- Usage: `railway redeploy [OPTIONS]`
- Summary: Redeploy the latest deployment of a service
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service ID/name to redeploy from | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway restart`

- Usage: `railway restart [OPTIONS]`
- Summary: Restart the latest deployment of a service (without rebuilding)
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service ID/name to restart | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway run`

- Usage: `railway run [OPTIONS] [ARGS]...`
- Summary: Run a local command using variables from the active environment
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | Service to pull variables from (defaults to linked service) | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to pull variables from (defaults to linked environment) | None |
| `-p, --project <PROJECT_ID>` | None | Project ID to use (defaults to linked project) | None |
| `--no-local` | None | Skip local develop overrides even if docker-compose.yml exists | None |
| `-v, --verbose` | None | Show verbose domain replacement info | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway scale`

- Usage: `railway scale [OPTIONS]`
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service to scale (defaults to linked service) | None |
| `-e, --environment <ENVIRONMENT>` | None | The environment the service is in (defaults to linked environment) | None |
| `--json` | None | Output in JSON format | None |
| `--europe-west4-drams3a <INSTANCES>` | None | Number of instances to run on europe-west4-drams3a | None |
| `--us-west2 <INSTANCES>` | None | Number of instances to run on us-west2 | None |
| `--asia-southeast1-eqsg3a <INSTANCES>` | None | Number of instances to run on asia-southeast1-eqsg3a | None |
| `--us-east4-eqdc4a <INSTANCES>` | None | Number of instances to run on us-east4-eqdc4a | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway service`

- Usage: `railway service [SERVICE] [COMMAND]`
- Summary: Manage services
- Depth: `1`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `link` | None | Link a service to the current project |
| `status` | None | Show deployment status for services |
| `logs` | None | View logs from a service |
| `redeploy` | None | Redeploy the latest deployment of a service |
| `restart` | None | Restart the latest deployment of a service |
| `scale` | None | Scale a service across regions |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[SERVICE]` | None | The service ID/name to link (deprecated: use 'service link' instead) | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway shell`

- Usage: `railway shell [OPTIONS]`
- Summary: Open a local subshell with Railway variables available
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | Service to pull variables from (defaults to linked service) | None |
| `--silent` | None | Open shell without banner | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway ssh`

- Usage: `railway ssh [OPTIONS] [COMMAND]...`
- Summary: Connect to a service via SSH
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --project <PROJECT>` | None | Project to connect to (defaults to linked project) | None |
| `-s, --service <SERVICE>` | None | Service to connect to (defaults to linked service) | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to connect to (defaults to linked environment) | None |
| `-d, --deployment-instance <deployment-instance-id>` | None | Deployment instance ID to connect to (defaults to first active instance) | None |
| `--session [<SESSION_NAME>]` | None | SSH into the service inside a tmux session. Installs tmux if it's not installed. Optionally, provide a session name (--session name) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway status`

- Usage: `railway status [OPTIONS]`
- Summary: Show information about the current project
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway unlink`

- Usage: `railway unlink [OPTIONS]`
- Summary: Disassociate project from current directory
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service` | None | Unlink a service | None |
| `-y, --yes` | None | Skip confirmation prompt | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway up`

- Usage: `railway up [OPTIONS] [PATH]`
- Summary: Upload and deploy project from the current directory
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[PATH]` | None | None | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-d, --detach` | None | Don't attach to the log stream | None |
| `-c, --ci` | None | Stream build logs only, then exit (equivalent to setting $CI=true) | None |
| `-s, --service <SERVICE>` | None | Service to deploy to (defaults to linked service) | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to deploy to (defaults to linked environment) | None |
| `-p, --project <PROJECT_ID>` | None | Project ID to deploy to (defaults to linked project) | None |
| `--no-gitignore` | None | Don't ignore paths from .gitignore | None |
| `--path-as-root` | None | Use the path argument as the prefix for the archive instead of the project directory | None |
| `--verbose` | None | Verbose output | None |
| `--json` | None | Output logs in JSON format (implies CI mode behavior) | None |
| `-m, --message <MESSAGE>` | None | Message to attach to the deployment | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway upgrade`

- Usage: `railway upgrade [OPTIONS]`
- Summary: Upgrade the Railway CLI to the latest version
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--check` | None | Check install method without upgrading | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway variable`

- Usage: `railway variable [OPTIONS] [COMMAND]`
- Summary: Manage environment variables for a service
- Depth: `1`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `list` | None | List variables for a service |
| `set` | None | Set a variable |
| `delete` | None | Delete a variable |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service to show/set variables for | None |
| `-e, --environment <ENVIRONMENT>` | None | The environment to show/set variables for | None |
| `-k, --kv` | None | Show variables in KV format | None |
| `--set <SET>` | None | The "{key}={value}" environment variable pair to set the service variables (legacy, use 'variable set' instead) | None |
| `--set-from-stdin <KEY>` | None | Set a variable with the value read from stdin (legacy, use 'variable set --stdin' instead) | None |
| `--json` | None | Output in JSON format | None |
| `--skip-deploys` | None | Skip triggering deploys when setting variables | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway volume`

- Usage: `railway volume [OPTIONS] <COMMAND>`
- Summary: Manage project volumes
- Depth: `1`

### Subcommands

| Subcommand | Aliases | Description |
|---|---|---|
| `list` | None | List volumes |
| `add` | None | Add a new volume |
| `delete` | None | Delete a volume |
| `update` | None | Update a volume |
| `detach` | None | Detach a volume from a service |
| `attach` | None | Attach a volume to a service |
| `help` | None | Print this message or the help of the given subcommand(s) |

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | Service ID | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment ID | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

### `railway whoami`

- Usage: `railway whoami [OPTIONS]`
- Summary: Get the current logged in user
- Depth: `1`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway deployment list`

- Usage: `railway deployment list [OPTIONS]`
- Summary: List deployments for a service with IDs, statuses and other metadata
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | Service name or ID to list deployments for (defaults to linked service) | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to list deployments from (defaults to linked environment) | None |
| `--limit <LIMIT>` | None | Maximum number of deployments to show (default: 20, max: 1000) [default: 20] | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway deployment redeploy`

- Usage: `railway deployment redeploy [OPTIONS]`
- Summary: Redeploy the latest deployment of a service
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service ID/name to redeploy from | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway deployment up`

- Usage: `railway deployment up [OPTIONS] [PATH]`
- Summary: Upload and deploy project from the current directory
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[PATH]` | None | None | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-d, --detach` | None | Don't attach to the log stream | None |
| `-c, --ci` | None | Stream build logs only, then exit (equivalent to setting $CI=true) | None |
| `-s, --service <SERVICE>` | None | Service to deploy to (defaults to linked service) | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to deploy to (defaults to linked environment) | None |
| `-p, --project <PROJECT_ID>` | None | Project ID to deploy to (defaults to linked project) | None |
| `--no-gitignore` | None | Don't ignore paths from .gitignore | None |
| `--path-as-root` | None | Use the path argument as the prefix for the archive instead of the project directory | None |
| `--verbose` | None | Verbose output | None |
| `--json` | None | Output logs in JSON format (implies CI mode behavior) | None |
| `-m, --message <MESSAGE>` | None | Message to attach to the deployment | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway dev clean`

- Usage: `railway dev clean [OPTIONS]`
- Summary: Stop services and remove volumes/data
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-o, --output <OUTPUT>` | None | Output path for docker-compose.yml (defaults to ~/.railway/develop/<project_id>/docker-compose.yml) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway dev configure`

- Usage: `railway dev configure [OPTIONS]`
- Summary: Configure local code services
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--service <SERVICE>` | None | Specific service to configure (by name) | None |
| `--remove [<REMOVE>]` | None | Remove configuration for a service (optionally specify service name) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway dev down`

- Usage: `railway dev down [OPTIONS]`
- Summary: Stop services
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-o, --output <OUTPUT>` | None | Output path for docker-compose.yml (defaults to ~/.railway/develop/<project_id>/docker-compose.yml) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway dev up`

- Usage: `railway dev up [OPTIONS]`
- Summary: Start services (default when no subcommand provided)
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-e, --environment <ENVIRONMENT>` | None | Environment to use (defaults to linked environment) | None |
| `-o, --output <OUTPUT>` | None | Output path for docker-compose.yml (defaults to ~/.railway/develop/<project_id>/docker-compose.yml) | None |
| `--dry-run` | None | Only generate docker-compose.yml, don't run docker compose up | None |
| `--no-https` | None | Disable HTTPS and pretty URLs (use localhost instead) | None |
| `-v, --verbose` | None | Show verbose domain replacement info | None |
| `--no-tui` | None | Disable TUI, stream logs to stdout instead | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway environment config`

- Usage: `railway environment config [OPTIONS]`
- Summary: Show environment configuration
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-e, --environment <ENVIRONMENT>` | None | Environment to show config for (defaults to linked) | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway environment delete`

- Usage: `railway environment delete [OPTIONS] [ENVIRONMENT]`
- Summary: Delete an environment
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[ENVIRONMENT]` | None | The environment to delete | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `--2fa-code <TWO_FACTOR_CODE>` | None | 2FA code for verification (required if 2FA is enabled in non-interactive mode) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway environment edit`

- Usage: `railway environment edit [OPTIONS]`
- Summary: Edit an environment's configuration
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-e, --environment <ENVIRONMENT>` | None | The environment to edit (defaults to linked environment)<br><br><br><br>-s, --service-config <SERVICE> <PATH> <VALUE> Configure a service using dot-path notation<br><br><br><br>Format: --service-config <SERVICE> <PATH> <VALUE><br><br><br><br>Examples: --service-config backend variables.API_KEY.value "secret" --service-config api deploy.startCommand "npm start" --service-config web source.image "nginx:latest" | None |
| `-m, --message <MESSAGE>` | None | Commit message for the changes | None |
| `--stage` | None | Stage changes without committing | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help (see a summary with '-h') | None |
| `-V, --version` | None | Print version | None |

#### `railway environment link`

- Usage: `railway environment link [OPTIONS] [ENVIRONMENT]`
- Summary: Link an environment to the current project
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[ENVIRONMENT]` | None | The environment to link to | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway environment new`

- Usage: `railway environment new [OPTIONS] [NAME]`
- Summary: Create a new environment
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[NAME]` | None | The name of the environment to create | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-d, --duplicate <DUPLICATE>` | None | The name/ID of the environment to duplicate<br><br><br><br>[aliases: -c, --copy]<br><br><br><br>-s, --service-config <SERVICE> <PATH> <VALUE> Configure a service using dot-path notation<br><br><br><br>Format: --service-config <SERVICE> <PATH> <VALUE><br><br><br><br>Examples: --service-config backend variables.API_KEY.value "secret" --service-config api deploy.startCommand "npm start" --service-config web source.image "nginx:latest" | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help (see a summary with '-h') | None |
| `-V, --version` | None | Print version | None |

#### `railway functions delete`

- Usage: `railway functions delete [OPTIONS]`
- Summary: Delete a function
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-f, --function <FUNCTION>` | None | The ID/name of the function you wish to delete | None |
| `-y, --yes [<YES>]` | None | Skip confirmation for deleting | `true`, `false` |
| `--2fa-code <TWO_FACTOR_CODE>` | None | 2FA code for verification (required if 2FA is enabled in non-interactive mode) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway functions link`

- Usage: `railway functions link [OPTIONS]`
- Summary: Link a function manually
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --path <PATH>` | None | The path to the file | None |
| `-f, --function <FUNCTION>` | None | The ID/name of the function you wish to link to | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway functions list`

- Usage: `railway functions list`
- Summary: List functions
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway functions new`

- Usage: `railway functions new [OPTIONS]`
- Summary: Add a new function
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --path <PATH>` | None | The path to the function locally | None |
| `-n, --name <NAME>` | None | The name of the function | None |
| `-c, --cron <CRON>` | None | Cron schedule to run the function | None |
| `--http [<HTTP>]` | None | Generate a domain | `true`, `false` |
| `-s, --serverless [<SERVERLESS>]` | None | Serverless (a.k.a sleeping) | `true`, `false` |
| `-w, --watch [<WATCH>]` | None | Watch for changes of the file and deploy upon save | `true`, `false` |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway functions pull`

- Usage: `railway functions pull [OPTIONS]`
- Summary: Pull changes from the linked function remotely
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --path <PATH>` | None | The path to the function | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway functions push`

- Usage: `railway functions push [OPTIONS]`
- Summary: Push a new change to the function
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --path <PATH>` | None | The path to the function | None |
| `-w, --watch [<WATCH>]` | None | Watch for changes of the file and deploy upon save | `true`, `false` |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway project delete`

- Usage: `railway project delete [OPTIONS]`
- Summary: Delete a project
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-p, --project <PROJECT>` | None | The project ID or name to delete | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `--2fa-code <TWO_FACTOR_CODE>` | None | 2FA code for verification (required if 2FA is enabled in non-interactive mode) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway project link`

- Usage: `railway project link [OPTIONS]`
- Summary: Link a project to the current directory
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-e, --environment <ENVIRONMENT>` | None | Environment to link to | None |
| `-p, --project <PROJECT>` | None | Project to link to | None |
| `-s, --service <SERVICE>` | None | The service to link to | None |
| `-t, --team <TEAM>` | None | The team to link to (deprecated: use --workspace instead) | None |
| `-w, --workspace <WORKSPACE>` | None | The workspace to link to | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway project list`

- Usage: `railway project list [OPTIONS]`
- Summary: List all projects in your Railway account
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway service link`

- Usage: `railway service link [SERVICE]`
- Summary: Link a service to the current project
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[SERVICE]` | None | The service ID/name to link | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway service logs`

- Usage: `railway service logs [OPTIONS] [DEPLOYMENT_ID]`
- Summary: View logs from a service
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `[DEPLOYMENT_ID]` | None | Deployment ID to view logs from. Defaults to most recent successful deployment, or latest deployment if none succeeded | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | Service to view logs from (defaults to linked service). Can be service name or service ID | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to view logs from (defaults to linked environment). Can be environment name or environment ID | None |
| `-d, --deployment` | None | Show deployment logs | None |
| `-b, --build` | None | Show build logs | None |
| `--json` | None | Output logs in JSON format. Each log line becomes a JSON object with timestamp, message, and any other attributes | None |
| `-n, --lines <LINES>` | `--tail` | Number of log lines to fetch (disables streaming) | None |
| `-f, --filter <FILTER>` | None | Filter logs using Railway's query syntax<br><br><br><br>Can be a text search ("error message" or "user signup"), attribute filters (@level:error, @level:warn), or a combination with the operators AND, OR, - (not). See https://docs.railway.com/guides/logs for full syntax. | None |
| `--latest` | None | Always show logs from the latest deployment, even if it failed or is still building | None |
| `-S, --since <TIME>` | None | Show logs since a specific time (disables streaming). Accepts relative times (e.g., 30s, 5m, 2h, 1d, 1w) or ISO 8601 timestamps (e.g., 2024-01-15T10:30:00Z) | None |
| `-U, --until <TIME>` | None | Show logs until a specific time (disables streaming). Same formats as --since | None |
| `-h, --help` | None | Print help (see a summary with '-h') | None |
| `-V, --version` | None | Print version | None |

#### `railway service redeploy`

- Usage: `railway service redeploy [OPTIONS]`
- Summary: Redeploy the latest deployment of a service
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service ID/name to redeploy from | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway service restart`

- Usage: `railway service restart [OPTIONS]`
- Summary: Restart the latest deployment of a service
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service ID/name to restart | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway service scale`

- Usage: `railway service scale [OPTIONS]`
- Summary: Scale a service across regions
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service to scale (defaults to linked service) | None |
| `-e, --environment <ENVIRONMENT>` | None | The environment the service is in (defaults to linked environment) | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway service status`

- Usage: `railway service status [OPTIONS]`
- Summary: Show deployment status for services
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | Service name or ID to show status for (defaults to linked service) | None |
| `-a, --all` | None | Show status for all services in the environment | None |
| `-e, --environment <ENVIRONMENT>` | None | Environment to check status in (defaults to linked environment) | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway variable delete`

- Usage: `railway variable delete [OPTIONS] <KEY>`
- Summary: Delete a variable
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `<KEY>` | None | The variable key to delete | None |

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service to delete the variable from | None |
| `-e, --environment <ENVIRONMENT>` | None | The environment to delete the variable from | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway variable list`

- Usage: `railway variable list [OPTIONS]`
- Summary: List variables for a service
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service to list variables for | None |
| `-e, --environment <ENVIRONMENT>` | None | The environment to list variables from | None |
| `-k, --kv` | None | Show variables in KV format | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway variable set`

- Usage: `railway variable set [OPTIONS] <VARIABLES>...`
- Summary: Set a variable
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-s, --service <SERVICE>` | None | The service to set the variable for | None |
| `-e, --environment <ENVIRONMENT>` | None | The environment to set the variable in | None |
| `--stdin` | None | Read the value from stdin instead of the command line (only with single KEY) | None |
| `--skip-deploys` | None | Skip triggering deploys when setting the variable | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway volume add`

- Usage: `railway volume add [OPTIONS]`
- Summary: Add a new volume
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-m, --mount-path <MOUNT_PATH>` | None | The mount path of the volume | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway volume attach`

- Usage: `railway volume attach [OPTIONS]`
- Summary: Attach a volume to a service
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-v, --volume <VOLUME>` | None | The ID/name of the volume you wish to attach | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway volume delete`

- Usage: `railway volume delete [OPTIONS]`
- Summary: Delete a volume
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-v, --volume <VOLUME>` | None | The ID/name of the volume you wish to delete | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `--2fa-code <TWO_FACTOR_CODE>` | None | 2FA code for verification (required if 2FA is enabled in non-interactive mode) | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway volume detach`

- Usage: `railway volume detach [OPTIONS]`
- Summary: Detach a volume from a service
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-v, --volume <VOLUME>` | None | The ID/name of the volume you wish to detach | None |
| `-y, --yes` | None | Skip confirmation dialog | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway volume list`

- Usage: `railway volume list [OPTIONS]`
- Summary: List volumes
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |

#### `railway volume update`

- Usage: `railway volume update [OPTIONS]`
- Summary: Update a volume
- Depth: `2`

### Subcommands

No subcommands.

### Arguments

No positional arguments.

### Options

| Spec | Aliases | Description | Possible values |
|---|---|---|---|
| `-v, --volume <VOLUME>` | None | The ID/name of the volume you wish to update | None |
| `-m, --mount-path <MOUNT_PATH>` | None | The new mount path of the volume (optional) | None |
| `-n, --name <NAME>` | None | The new name of the volume (optional) | None |
| `--json` | None | Output in JSON format | None |
| `-h, --help` | None | Print help | None |
| `-V, --version` | None | Print version | None |
