# Railway CLI Live Help Snapshot

- Source: `railway 4.29.0`
- Generated at: `2026-04-17T12:01:12.566Z`

## `railway`

```text
Interact with Railway via CLI

Usage: railway [COMMAND]

Commands:
  add            Add a service to your project
  completion     Generate completion script
  connect        Connect to a database's shell (psql for Postgres, mongosh for MongoDB, etc.)
  delete         Delete a project
  deploy         Provisions a template into your project
  deployment     Manage deployments
  dev            Run Railway services locally [aliases: develop]
  domain         Add a custom domain or generate a railway provided domain for a service
  docs           Open Railway Documentation in default browser
  down           Remove the most recent deployment
  environment    Create, delete or link an environment [aliases: env]
  init           Create a new project
  link           Associate existing project with current directory, may specify projectId as an argument
  list           List all projects in your Railway account
  login          Login to your Railway account
  logout         Logout of your Railway account
  logs           View build or deploy logs from a Railway deployment
  open           Open your project dashboard
  project        Manage projects
  run            Run a local command using variables from the active environment [aliases: local]
  service        Manage services
  shell          Open a local subshell with Railway variables available
  ssh            Connect to a service via SSH
  status         Show information about the current project
  unlink         Disassociate project from current directory
  up             Upload and deploy project from the current directory
  upgrade        Upgrade the Railway CLI to the latest version
  variable       Manage environment variables for a service [aliases: variables, vars, var]
  whoami         Get the current logged in user
  volume         Manage project volumes
  redeploy       Redeploy the latest deployment of a service
  restart        Restart the latest deployment of a service (without rebuilding)
  scale          
  check_updates  Test the update check
  functions      Manage project functions [aliases: function, func, fn, funcs, fns]
  help           Print this message or the help of the given subcommand(s)

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway add`

```text
Add a service to your project

Usage: railway add [OPTIONS]

Options:
  -d, --database <DATABASE>
          The name of the database to add
          
          [possible values: postgres, mysql, redis, mongo]

  -s, --service [<SERVICE>]
          The name of the service to create (leave blank for randomly generated)

  -r, --repo <REPO>
          The repo to link to the service

  -i, --image <IMAGE>
          The docker image to link to the service

  -v, --variables <VARIABLES>
          The "{key}={value}" environment variable pair to set the service variables. Example:
          
          railway add --service --variables "MY_SPECIAL_ENV_VAR=1" --variables "BACKEND_PORT=3000"

      --verbose [<VERBOSE>]
          Verbose logging
          
          [possible values: true, false]

      --json
          Output in JSON format

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version
```

## `railway check_updates`

```text
Test the update check

Usage: railway check_updates [OPTIONS]

Options:
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway completion`

```text
Generate completion script

Usage: railway completion <SHELL>

Arguments:
  <SHELL>  [possible values: bash, elvish, fish, powershell, zsh]

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway connect`

```text
Connect to a database's shell (psql for Postgres, mongosh for MongoDB, etc.)

Usage: railway connect [OPTIONS] [SERVICE_NAME]

Arguments:
  [SERVICE_NAME]  The name of the database to connect to

Options:
  -e, --environment <ENVIRONMENT>  Environment to pull variables from (defaults to linked environment)
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway delete`

```text
Delete a project

Usage: railway delete [OPTIONS]

Options:
  -p, --project <PROJECT>           The project ID or name to delete
  -y, --yes                         Skip confirmation dialog
      --json                        Output in JSON format
      --2fa-code <TWO_FACTOR_CODE>  2FA code for verification (required if 2FA is enabled in non-interactive mode)
  -h, --help                        Print help
  -V, --version                     Print version
```

## `railway deploy`

```text
Provisions a template into your project

Usage: railway deploy [OPTIONS]

Options:
  -t, --template <TEMPLATE>
          The code of the template to deploy

  -v, --variable <VARIABLE>
          The "{key}={value}" environment variable pair to set the template variables
          
          To specify the variable for a single service prefix it with "{service}." Example:
          
          railway deploy -t postgres -v "MY_SPECIAL_ENV_VAR=1" -v "Backend.Port=3000"

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version
```

## `railway deployment`

```text
Manage deployments

Usage: railway deployment <COMMAND>

Commands:
  list      List deployments for a service with IDs, statuses and other metadata
  up        Upload and deploy project from the current directory
  redeploy  Redeploy the latest deployment of a service
  help      Print this message or the help of the given subcommand(s)

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway dev`

```text
Run Railway services locally

Usage: railway dev [OPTIONS] [COMMAND]

Commands:
  up         Start services (default when no subcommand provided)
  down       Stop services
  clean      Stop services and remove volumes/data
  configure  Configure local code services
  help       Print this message or the help of the given subcommand(s)

Options:
  -v, --verbose  Show verbose domain replacement info (for default 'up' command)
  -h, --help     Print help
  -V, --version  Print version
```

## `railway docs`

```text
Open Railway Documentation in default browser

Usage: railway docs

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway domain`

```text
Add a custom domain or generate a railway provided domain for a service.

There is a maximum of 1 railway provided domain per service.

Usage: railway domain [OPTIONS] [DOMAIN]

Arguments:
  [DOMAIN]
          Optionally, specify a custom domain to use. If not specified, a domain will be generated.
          
          Specifying a custom domain will also return the required DNS records to add to your DNS settings

Options:
  -p, --port <PORT>
          The port to connect to the domain

  -s, --service <SERVICE>
          The name of the service to generate the domain for

      --json
          Output in JSON format

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version
```

## `railway down`

```text
Remove the most recent deployment

Usage: railway down [OPTIONS]

Options:
  -s, --service <SERVICE>          Service to remove the deployment from (defaults to linked service)
  -e, --environment <ENVIRONMENT>  Environment to remove the deployment from (defaults to linked environment)
  -y, --yes                        Skip confirmation dialog
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway environment`

```text
Create, delete or link an environment

Usage: railway environment [OPTIONS] [ENVIRONMENT] [COMMAND]

Commands:
  link    Link an environment to the current project
  new     Create a new environment
  delete  Delete an environment
  edit    Edit an environment's configuration
  config  Show environment configuration
  help    Print this message or the help of the given subcommand(s)

Arguments:
  [ENVIRONMENT]  The environment to link to

Options:
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway functions`

```text
Manage project functions

Usage: railway functions [OPTIONS] <COMMAND>

Commands:
  list    List functions [aliases: ls]
  new     Add a new function [aliases: create]
  delete  Delete a function [aliases: remove, rm]
  push    Push a new change to the function [aliases: up]
  pull    Pull changes from the linked function remotely
  link    Link a function manually
  help    Print this message or the help of the given subcommand(s)

Options:
  -e, --environment <ENVIRONMENT>  Environment ID/name
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway init`

```text
Create a new project

Usage: railway init [OPTIONS]

Options:
  -n, --name <NAME>            Project name
  -w, --workspace <WORKSPACE>  Workspace ID or name
      --json                   Output in JSON format
  -h, --help                   Print help
  -V, --version                Print version
```

## `railway link`

```text
Associate existing project with current directory, may specify projectId as an argument

Usage: railway link [OPTIONS]

Options:
  -e, --environment <ENVIRONMENT>  Environment to link to
  -p, --project <PROJECT>          Project to link to
  -s, --service <SERVICE>          The service to link to
  -t, --team <TEAM>                The team to link to (deprecated: use --workspace instead)
  -w, --workspace <WORKSPACE>      The workspace to link to
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway list`

```text
List all projects in your Railway account

Usage: railway list [OPTIONS]

Options:
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway login`

```text
Login to your Railway account

Usage: railway login [OPTIONS]

Options:
  -b, --browserless  Browserless login
  -h, --help         Print help
  -V, --version      Print version
```

## `railway logout`

```text
Logout of your Railway account

Usage: railway logout

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway logs`

```text
View build or deploy logs from a Railway deployment. This will stream logs by default, or fetch historical logs if the --lines, --since, or --until flags are provided.

Usage: railway logs [OPTIONS] [DEPLOYMENT_ID]

Arguments:
  [DEPLOYMENT_ID]
          Deployment ID to view logs from. Defaults to most recent successful deployment, or latest deployment if none succeeded

Options:
  -s, --service <SERVICE>
          Service to view logs from (defaults to linked service). Can be service name or service ID

  -e, --environment <ENVIRONMENT>
          Environment to view logs from (defaults to linked environment). Can be environment name or environment ID

  -d, --deployment
          Show deployment logs

  -b, --build
          Show build logs

      --json
          Output logs in JSON format. Each log line becomes a JSON object with timestamp, message, and any other attributes

  -n, --lines <LINES>
          Number of log lines to fetch (disables streaming)
          
          [aliases: --tail]

  -f, --filter <FILTER>
          Filter logs using Railway's query syntax
          
          Can be a text search ("error message" or "user signup"), attribute filters (@level:error, @level:warn), or a combination with the operators AND, OR, - (not). See https://docs.railway.com/guides/logs for full syntax.

      --latest
          Always show logs from the latest deployment, even if it failed or is still building

  -S, --since <TIME>
          Show logs since a specific time (disables streaming). Accepts relative times (e.g., 30s, 5m, 2h, 1d, 1w) or ISO 8601 timestamps (e.g., 2024-01-15T10:30:00Z)

  -U, --until <TIME>
          Show logs until a specific time (disables streaming). Same formats as --since

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version

Examples:

  railway logs                                                       # Stream live logs from latest deployment
  railway logs --build 7422c95b-c604-46bc-9de4-b7a43e1fd53d          # Stream build logs from a specific deployment
  railway logs --lines 100                                           # Pull last 100 logs without streaming
  railway logs --since 1h                                            # View logs from the last hour
  railway logs --since 30m --until 10m                               # View logs from 30 minutes ago until 10 minutes ago
  railway logs --since 2024-01-15T10:00:00Z                          # View logs since a specific timestamp
  railway logs --service backend --environment production            # Stream latest deployment logs from a specific service in a specific environment
  railway logs --lines 10 --filter "@level:error"                    # View 10 latest error logs
  railway logs --lines 10 --filter "@level:warn AND rate limit"      # View 10 latest warning logs related to rate limiting
  railway logs --json                                                # Get logs in JSON format
  railway logs --latest                                              # Stream logs from the latest deployment (even if failed/building)
```

## `railway open`

```text
Open your project dashboard

Usage: railway open [OPTIONS]

Options:
  -p, --print    Print the URL instead of opening it
  -h, --help     Print help
  -V, --version  Print version
```

## `railway project`

```text
Manage projects

Usage: railway project <COMMAND>

Commands:
  list    List all projects in your Railway account
  link    Link a project to the current directory
  delete  Delete a project
  help    Print this message or the help of the given subcommand(s)

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway redeploy`

```text
Redeploy the latest deployment of a service

Usage: railway redeploy [OPTIONS]

Options:
  -s, --service <SERVICE>  The service ID/name to redeploy from
  -y, --yes                Skip confirmation dialog
      --json               Output in JSON format
  -h, --help               Print help
  -V, --version            Print version
```

## `railway restart`

```text
Restart the latest deployment of a service (without rebuilding)

Usage: railway restart [OPTIONS]

Options:
  -s, --service <SERVICE>  The service ID/name to restart
  -y, --yes                Skip confirmation dialog
      --json               Output in JSON format
  -h, --help               Print help
  -V, --version            Print version
```

## `railway run`

```text
Run a local command using variables from the active environment

Usage: railway run [OPTIONS] [ARGS]...

Arguments:
  [ARGS]...  Args to pass to the command

Options:
  -s, --service <SERVICE>          Service to pull variables from (defaults to linked service)
  -e, --environment <ENVIRONMENT>  Environment to pull variables from (defaults to linked environment)
  -p, --project <PROJECT_ID>       Project ID to use (defaults to linked project)
      --no-local                   Skip local develop overrides even if docker-compose.yml exists
  -v, --verbose                    Show verbose domain replacement info
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway scale`

```text
Usage: railway scale [OPTIONS]

Options:
  -s, --service <SERVICE>
          The service to scale (defaults to linked service)
  -e, --environment <ENVIRONMENT>
          The environment the service is in (defaults to linked environment)
      --json
          Output in JSON format
      --europe-west4-drams3a <INSTANCES>
          Number of instances to run on europe-west4-drams3a
      --us-west2 <INSTANCES>
          Number of instances to run on us-west2
      --asia-southeast1-eqsg3a <INSTANCES>
          Number of instances to run on asia-southeast1-eqsg3a
      --us-east4-eqdc4a <INSTANCES>
          Number of instances to run on us-east4-eqdc4a
  -h, --help
          Print help
  -V, --version
          Print version
```

## `railway service`

```text
Manage services

Usage: railway service [SERVICE] [COMMAND]

Commands:
  link      Link a service to the current project
  status    Show deployment status for services
  logs      View logs from a service
  redeploy  Redeploy the latest deployment of a service
  restart   Restart the latest deployment of a service
  scale     Scale a service across regions
  help      Print this message or the help of the given subcommand(s)

Arguments:
  [SERVICE]  The service ID/name to link (deprecated: use 'service link' instead)

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway shell`

```text
Open a local subshell with Railway variables available

Usage: railway shell [OPTIONS]

Options:
  -s, --service <SERVICE>  Service to pull variables from (defaults to linked service)
      --silent             Open shell without banner
  -h, --help               Print help
  -V, --version            Print version
```

## `railway ssh`

```text
Connect to a service via SSH

Usage: railway ssh [OPTIONS] [COMMAND]...

Arguments:
  [COMMAND]...  Command to execute instead of starting an interactive shell

Options:
  -p, --project <PROJECT>
          Project to connect to (defaults to linked project)
  -s, --service <SERVICE>
          Service to connect to (defaults to linked service)
  -e, --environment <ENVIRONMENT>
          Environment to connect to (defaults to linked environment)
  -d, --deployment-instance <deployment-instance-id>
          Deployment instance ID to connect to (defaults to first active instance)
      --session [<SESSION_NAME>]
          SSH into the service inside a tmux session. Installs tmux if it's not installed. Optionally, provide a session name (--session name)
  -h, --help
          Print help
  -V, --version
          Print version
```

## `railway status`

```text
Show information about the current project

Usage: railway status [OPTIONS]

Options:
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway unlink`

```text
Disassociate project from current directory

Usage: railway unlink [OPTIONS]

Options:
  -s, --service  Unlink a service
  -y, --yes      Skip confirmation prompt
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway up`

```text
Upload and deploy project from the current directory

Usage: railway up [OPTIONS] [PATH]

Arguments:
  [PATH]  

Options:
  -d, --detach                     Don't attach to the log stream
  -c, --ci                         Stream build logs only, then exit (equivalent to setting $CI=true)
  -s, --service <SERVICE>          Service to deploy to (defaults to linked service)
  -e, --environment <ENVIRONMENT>  Environment to deploy to (defaults to linked environment)
  -p, --project <PROJECT_ID>       Project ID to deploy to (defaults to linked project)
      --no-gitignore               Don't ignore paths from .gitignore
      --path-as-root               Use the path argument as the prefix for the archive instead of the project directory
      --verbose                    Verbose output
      --json                       Output logs in JSON format (implies CI mode behavior)
  -m, --message <MESSAGE>          Message to attach to the deployment
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway upgrade`

```text
Upgrade the Railway CLI to the latest version

Usage: railway upgrade [OPTIONS]

Options:
      --check    Check install method without upgrading
  -h, --help     Print help
  -V, --version  Print version
```

## `railway variable`

```text
Manage environment variables for a service

Usage: railway variable [OPTIONS] [COMMAND]

Commands:
  list    List variables for a service
  set     Set a variable
  delete  Delete a variable
  help    Print this message or the help of the given subcommand(s)

Options:
  -s, --service <SERVICE>          The service to show/set variables for
  -e, --environment <ENVIRONMENT>  The environment to show/set variables for
  -k, --kv                         Show variables in KV format
      --set <SET>                  The "{key}={value}" environment variable pair to set the service variables (legacy, use 'variable set' instead)
      --set-from-stdin <KEY>       Set a variable with the value read from stdin (legacy, use 'variable set --stdin' instead)
      --json                       Output in JSON format
      --skip-deploys               Skip triggering deploys when setting variables
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway volume`

```text
Manage project volumes

Usage: railway volume [OPTIONS] <COMMAND>

Commands:
  list    List volumes
  add     Add a new volume
  delete  Delete a volume
  update  Update a volume
  detach  Detach a volume from a service
  attach  Attach a volume to a service
  help    Print this message or the help of the given subcommand(s)

Options:
  -s, --service <SERVICE>          Service ID
  -e, --environment <ENVIRONMENT>  Environment ID
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway whoami`

```text
Get the current logged in user

Usage: railway whoami [OPTIONS]

Options:
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway deployment list`

```text
List deployments for a service with IDs, statuses and other metadata

Usage: railway deployment list [OPTIONS]

Options:
  -s, --service <SERVICE>          Service name or ID to list deployments for (defaults to linked service)
  -e, --environment <ENVIRONMENT>  Environment to list deployments from (defaults to linked environment)
      --limit <LIMIT>              Maximum number of deployments to show (default: 20, max: 1000) [default: 20]
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway deployment redeploy`

```text
Redeploy the latest deployment of a service

Usage: railway deployment redeploy [OPTIONS]

Options:
  -s, --service <SERVICE>  The service ID/name to redeploy from
  -y, --yes                Skip confirmation dialog
      --json               Output in JSON format
  -h, --help               Print help
  -V, --version            Print version
```

## `railway deployment up`

```text
Upload and deploy project from the current directory

Usage: railway deployment up [OPTIONS] [PATH]

Arguments:
  [PATH]  

Options:
  -d, --detach                     Don't attach to the log stream
  -c, --ci                         Stream build logs only, then exit (equivalent to setting $CI=true)
  -s, --service <SERVICE>          Service to deploy to (defaults to linked service)
  -e, --environment <ENVIRONMENT>  Environment to deploy to (defaults to linked environment)
  -p, --project <PROJECT_ID>       Project ID to deploy to (defaults to linked project)
      --no-gitignore               Don't ignore paths from .gitignore
      --path-as-root               Use the path argument as the prefix for the archive instead of the project directory
      --verbose                    Verbose output
      --json                       Output logs in JSON format (implies CI mode behavior)
  -m, --message <MESSAGE>          Message to attach to the deployment
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway dev clean`

```text
Stop services and remove volumes/data

Usage: railway dev clean [OPTIONS]

Options:
  -o, --output <OUTPUT>  Output path for docker-compose.yml (defaults to ~/.railway/develop/<project_id>/docker-compose.yml)
  -h, --help             Print help
  -V, --version          Print version
```

## `railway dev configure`

```text
Configure local code services

Usage: railway dev configure [OPTIONS]

Options:
      --service <SERVICE>  Specific service to configure (by name)
      --remove [<REMOVE>]  Remove configuration for a service (optionally specify service name)
  -h, --help               Print help
  -V, --version            Print version
```

## `railway dev down`

```text
Stop services

Usage: railway dev down [OPTIONS]

Options:
  -o, --output <OUTPUT>  Output path for docker-compose.yml (defaults to ~/.railway/develop/<project_id>/docker-compose.yml)
  -h, --help             Print help
  -V, --version          Print version
```

## `railway dev up`

```text
Start services (default when no subcommand provided)

Usage: railway dev up [OPTIONS]

Options:
  -e, --environment <ENVIRONMENT>  Environment to use (defaults to linked environment)
  -o, --output <OUTPUT>            Output path for docker-compose.yml (defaults to ~/.railway/develop/<project_id>/docker-compose.yml)
      --dry-run                    Only generate docker-compose.yml, don't run docker compose up
      --no-https                   Disable HTTPS and pretty URLs (use localhost instead)
  -v, --verbose                    Show verbose domain replacement info
      --no-tui                     Disable TUI, stream logs to stdout instead
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway environment config`

```text
Show environment configuration

Usage: railway environment config [OPTIONS]

Options:
  -e, --environment <ENVIRONMENT>  Environment to show config for (defaults to linked)
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway environment delete`

```text
Delete an environment

Usage: railway environment delete [OPTIONS] [ENVIRONMENT]

Arguments:
  [ENVIRONMENT]  The environment to delete

Options:
  -y, --yes                         Skip confirmation dialog
      --json                        Output in JSON format
      --2fa-code <TWO_FACTOR_CODE>  2FA code for verification (required if 2FA is enabled in non-interactive mode)
  -h, --help                        Print help
  -V, --version                     Print version
```

## `railway environment edit`

```text
Edit an environment's configuration

Usage: railway environment edit [OPTIONS]

Options:
  -e, --environment <ENVIRONMENT>
          The environment to edit (defaults to linked environment)

  -s, --service-config <SERVICE> <PATH> <VALUE>
          Configure a service using dot-path notation
          
          Format: --service-config <SERVICE> <PATH> <VALUE>
          
          Examples: --service-config backend variables.API_KEY.value "secret" --service-config api deploy.startCommand "npm start" --service-config web source.image "nginx:latest"

  -m, --message <MESSAGE>
          Commit message for the changes

      --stage
          Stage changes without committing

      --json
          Output in JSON format

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version
```

## `railway environment link`

```text
Link an environment to the current project

Usage: railway environment link [OPTIONS] [ENVIRONMENT]

Arguments:
  [ENVIRONMENT]  The environment to link to

Options:
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway environment new`

```text
Create a new environment

Usage: railway environment new [OPTIONS] [NAME]

Arguments:
  [NAME]
          The name of the environment to create

Options:
  -d, --duplicate <DUPLICATE>
          The name/ID of the environment to duplicate
          
          [aliases: -c, --copy]

  -s, --service-config <SERVICE> <PATH> <VALUE>
          Configure a service using dot-path notation
          
          Format: --service-config <SERVICE> <PATH> <VALUE>
          
          Examples: --service-config backend variables.API_KEY.value "secret" --service-config api deploy.startCommand "npm start" --service-config web source.image "nginx:latest"

      --json
          Output in JSON format

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version
```

## `railway functions delete`

```text
Delete a function

Usage: railway functions delete [OPTIONS]

Options:
  -f, --function <FUNCTION>         The ID/name of the function you wish to delete
  -y, --yes [<YES>]                 Skip confirmation for deleting [possible values: true, false]
      --2fa-code <TWO_FACTOR_CODE>  2FA code for verification (required if 2FA is enabled in non-interactive mode)
  -h, --help                        Print help
  -V, --version                     Print version
```

## `railway functions link`

```text
Link a function manually

Usage: railway functions link [OPTIONS]

Options:
  -p, --path <PATH>          The path to the file
  -f, --function <FUNCTION>  The ID/name of the function you wish to link to
  -h, --help                 Print help
  -V, --version              Print version
```

## `railway functions list`

```text
List functions

Usage: railway functions list

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway functions new`

```text
Add a new function

Usage: railway functions new [OPTIONS]

Options:
  -p, --path <PATH>                The path to the function locally
  -n, --name <NAME>                The name of the function
  -c, --cron <CRON>                Cron schedule to run the function
      --http [<HTTP>]              Generate a domain [possible values: true, false]
  -s, --serverless [<SERVERLESS>]  Serverless (a.k.a sleeping) [possible values: true, false]
  -w, --watch [<WATCH>]            Watch for changes of the file and deploy upon save [possible values: true, false]
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway functions pull`

```text
Pull changes from the linked function remotely

Usage: railway functions pull [OPTIONS]

Options:
  -p, --path <PATH>  The path to the function
  -h, --help         Print help
  -V, --version      Print version
```

## `railway functions push`

```text
Push a new change to the function

Usage: railway functions push [OPTIONS]

Options:
  -p, --path <PATH>      The path to the function
  -w, --watch [<WATCH>]  Watch for changes of the file and deploy upon save [possible values: true, false]
  -h, --help             Print help
  -V, --version          Print version
```

## `railway project delete`

```text
Delete a project

Usage: railway project delete [OPTIONS]

Options:
  -p, --project <PROJECT>           The project ID or name to delete
  -y, --yes                         Skip confirmation dialog
      --json                        Output in JSON format
      --2fa-code <TWO_FACTOR_CODE>  2FA code for verification (required if 2FA is enabled in non-interactive mode)
  -h, --help                        Print help
  -V, --version                     Print version
```

## `railway project link`

```text
Link a project to the current directory

Usage: railway project link [OPTIONS]

Options:
  -e, --environment <ENVIRONMENT>  Environment to link to
  -p, --project <PROJECT>          Project to link to
  -s, --service <SERVICE>          The service to link to
  -t, --team <TEAM>                The team to link to (deprecated: use --workspace instead)
  -w, --workspace <WORKSPACE>      The workspace to link to
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway project list`

```text
List all projects in your Railway account

Usage: railway project list [OPTIONS]

Options:
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway service link`

```text
Link a service to the current project

Usage: railway service link [SERVICE]

Arguments:
  [SERVICE]  The service ID/name to link

Options:
  -h, --help     Print help
  -V, --version  Print version
```

## `railway service logs`

```text
View logs from a service

Usage: railway service logs [OPTIONS] [DEPLOYMENT_ID]

Arguments:
  [DEPLOYMENT_ID]
          Deployment ID to view logs from. Defaults to most recent successful deployment, or latest deployment if none succeeded

Options:
  -s, --service <SERVICE>
          Service to view logs from (defaults to linked service). Can be service name or service ID

  -e, --environment <ENVIRONMENT>
          Environment to view logs from (defaults to linked environment). Can be environment name or environment ID

  -d, --deployment
          Show deployment logs

  -b, --build
          Show build logs

      --json
          Output logs in JSON format. Each log line becomes a JSON object with timestamp, message, and any other attributes

  -n, --lines <LINES>
          Number of log lines to fetch (disables streaming)
          
          [aliases: --tail]

  -f, --filter <FILTER>
          Filter logs using Railway's query syntax
          
          Can be a text search ("error message" or "user signup"), attribute filters (@level:error, @level:warn), or a combination with the operators AND, OR, - (not). See https://docs.railway.com/guides/logs for full syntax.

      --latest
          Always show logs from the latest deployment, even if it failed or is still building

  -S, --since <TIME>
          Show logs since a specific time (disables streaming). Accepts relative times (e.g., 30s, 5m, 2h, 1d, 1w) or ISO 8601 timestamps (e.g., 2024-01-15T10:30:00Z)

  -U, --until <TIME>
          Show logs until a specific time (disables streaming). Same formats as --since

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version

Examples:

  railway logs                                                       # Stream live logs from latest deployment
  railway logs --build 7422c95b-c604-46bc-9de4-b7a43e1fd53d          # Stream build logs from a specific deployment
  railway logs --lines 100                                           # Pull last 100 logs without streaming
  railway logs --since 1h                                            # View logs from the last hour
  railway logs --since 30m --until 10m                               # View logs from 30 minutes ago until 10 minutes ago
  railway logs --since 2024-01-15T10:00:00Z                          # View logs since a specific timestamp
  railway logs --service backend --environment production            # Stream latest deployment logs from a specific service in a specific environment
  railway logs --lines 10 --filter "@level:error"                    # View 10 latest error logs
  railway logs --lines 10 --filter "@level:warn AND rate limit"      # View 10 latest warning logs related to rate limiting
  railway logs --json                                                # Get logs in JSON format
  railway logs --latest                                              # Stream logs from the latest deployment (even if failed/building)
```

## `railway service redeploy`

```text
Redeploy the latest deployment of a service

Usage: railway service redeploy [OPTIONS]

Options:
  -s, --service <SERVICE>  The service ID/name to redeploy from
  -y, --yes                Skip confirmation dialog
      --json               Output in JSON format
  -h, --help               Print help
  -V, --version            Print version
```

## `railway service restart`

```text
Restart the latest deployment of a service

Usage: railway service restart [OPTIONS]

Options:
  -s, --service <SERVICE>  The service ID/name to restart
  -y, --yes                Skip confirmation dialog
      --json               Output in JSON format
  -h, --help               Print help
  -V, --version            Print version
```

## `railway service scale`

```text
Scale a service across regions

Usage: railway service scale [OPTIONS]

Options:
  -s, --service <SERVICE>          The service to scale (defaults to linked service)
  -e, --environment <ENVIRONMENT>  The environment the service is in (defaults to linked environment)
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway service status`

```text
Show deployment status for services

Usage: railway service status [OPTIONS]

Options:
  -s, --service <SERVICE>          Service name or ID to show status for (defaults to linked service)
  -a, --all                        Show status for all services in the environment
  -e, --environment <ENVIRONMENT>  Environment to check status in (defaults to linked environment)
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway variable delete`

```text
Delete a variable

Usage: railway variable delete [OPTIONS] <KEY>

Arguments:
  <KEY>  The variable key to delete

Options:
  -s, --service <SERVICE>          The service to delete the variable from
  -e, --environment <ENVIRONMENT>  The environment to delete the variable from
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway variable list`

```text
List variables for a service

Usage: railway variable list [OPTIONS]

Options:
  -s, --service <SERVICE>          The service to list variables for
  -e, --environment <ENVIRONMENT>  The environment to list variables from
  -k, --kv                         Show variables in KV format
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway variable set`

```text
Set a variable

Usage: railway variable set [OPTIONS] <VARIABLES>...

Arguments:
  <VARIABLES>...  Variable(s) in KEY=VALUE format, or just KEY when using --stdin

Options:
  -s, --service <SERVICE>          The service to set the variable for
  -e, --environment <ENVIRONMENT>  The environment to set the variable in
      --stdin                      Read the value from stdin instead of the command line (only with single KEY)
      --skip-deploys               Skip triggering deploys when setting the variable
      --json                       Output in JSON format
  -h, --help                       Print help
  -V, --version                    Print version
```

## `railway volume add`

```text
Add a new volume

Usage: railway volume add [OPTIONS]

Options:
  -m, --mount-path <MOUNT_PATH>  The mount path of the volume
      --json                     Output in JSON format
  -h, --help                     Print help
  -V, --version                  Print version
```

## `railway volume attach`

```text
Attach a volume to a service

Usage: railway volume attach [OPTIONS]

Options:
  -v, --volume <VOLUME>  The ID/name of the volume you wish to attach
  -y, --yes              Skip confirmation dialog
      --json             Output in JSON format
  -h, --help             Print help
  -V, --version          Print version
```

## `railway volume delete`

```text
Delete a volume

Usage: railway volume delete [OPTIONS]

Options:
  -v, --volume <VOLUME>             The ID/name of the volume you wish to delete
  -y, --yes                         Skip confirmation dialog
      --json                        Output in JSON format
      --2fa-code <TWO_FACTOR_CODE>  2FA code for verification (required if 2FA is enabled in non-interactive mode)
  -h, --help                        Print help
  -V, --version                     Print version
```

## `railway volume detach`

```text
Detach a volume from a service

Usage: railway volume detach [OPTIONS]

Options:
  -v, --volume <VOLUME>  The ID/name of the volume you wish to detach
  -y, --yes              Skip confirmation dialog
      --json             Output in JSON format
  -h, --help             Print help
  -V, --version          Print version
```

## `railway volume list`

```text
List volumes

Usage: railway volume list [OPTIONS]

Options:
      --json     Output in JSON format
  -h, --help     Print help
  -V, --version  Print version
```

## `railway volume update`

```text
Update a volume

Usage: railway volume update [OPTIONS]

Options:
  -v, --volume <VOLUME>          The ID/name of the volume you wish to update
  -m, --mount-path <MOUNT_PATH>  The new mount path of the volume (optional)
  -n, --name <NAME>              The new name of the volume (optional)
      --json                     Output in JSON format
  -h, --help                     Print help
  -V, --version                  Print version
```

