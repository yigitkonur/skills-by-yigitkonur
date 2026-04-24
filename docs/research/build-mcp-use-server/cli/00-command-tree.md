# mcp-use CLI v3.1.0 — Command Tree

Tree of every command with a one-line description. Verbatim `mcp-use --help` output appears at the bottom.

## Tree

```
mcp-use
├── build                          Build TypeScript server + MCP UI widgets for production
├── dev                            Run the dev server with auto-reload, HMR, and inspector
├── start                          Start the production server from a prior build
├── generate-types                 Write .mcp-use/tool-registry.d.ts with tool type defs
│
├── login                          Authenticate to mcp-use cloud (device flow or --api-key)
├── logout                         Clear the API key from ~/.mcp-use/config.json
├── whoami                         Print the currently authenticated user + active org
│
├── org                            Manage organizations
│   ├── list                         List your organizations
│   ├── switch                       Switch the active organization
│   └── current                      Show the currently active organization
│
├── deploy                         Deploy MCP server from GitHub to Manufact cloud
│
├── servers                        Manage cloud servers (Git-backed deploy targets)
│   ├── list (ls)                    List servers for the current org
│   ├── get <id-or-slug>             Show server details + recent deployments
│   ├── delete (rm) <server-id>      Delete a server and all its deployments
│   └── env                          Manage a server's environment variables
│       ├── list (ls)                  List env vars for a server
│       ├── add <KEY=VALUE>            Add an env var (supports --sensitive)
│       ├── update <var-id>            Update an env var (value/env/sensitive)
│       └── remove (rm) <var-id>       Delete an env var
│
├── deployments                    Manage cloud deployments
│   ├── list (ls)                    List all deployments
│   ├── get <deployment-id>          Show one deployment's details
│   ├── restart <deployment-id>      Trigger a new deployment on the same server
│   ├── delete (rm) <deployment-id>  Delete a deployment (irreversible)
│   ├── logs <deployment-id>         View runtime or build logs (-b, -f)
│   ├── stop <deployment-id>         Stop a running deployment
│   └── start <deployment-id>        Start a stopped deployment
│
├── client                         Interactive MCP client for terminal usage
│   ├── connect <url>                Connect to an MCP server over a transport
│   ├── disconnect [session]         Disconnect from a session (or all)
│   ├── sessions                     Manage CLI sessions
│   ├── tools                        List/call MCP tools
│   ├── resources                    List/read MCP resources
│   ├── prompts                      List/get MCP prompts
│   └── interactive                  Start interactive REPL mode
│
├── skills                         Manage mcp-use AI agent skills
│   ├── add                          Install mcp-use skills for AI agents
│   └── install                      Alias for 'add'
│
└── help [command]                 Display help for any command
```

## Verbatim `mcp-use --help`

```
Usage: mcp-use [options] [command]

Create and run MCP servers with ui resources widgets

Options:
  -V, --version             output the version number
  -h, --help                display help for command

Commands:
  build [options]           Build TypeScript and MCP UI widgets
  dev [options]             Run development server with auto-reload and inspector
  start [options]           Start production server
  login [options]           Login to mcp-use cloud
  logout                    Logout from Manufact cloud
  whoami                    Show current user information
  org                       Manage organizations
  deploy [options]          Deploy MCP server from GitHub to Manufact cloud
  client                    Interactive MCP client for terminal usage
  deployments               Manage cloud deployments
  servers                   Manage cloud servers (Git-backed deploy targets)
  skills                    Manage mcp-use AI agent skills
  generate-types [options]  Generate TypeScript type definitions for tools
                            (writes .mcp-use/tool-registry.d.ts)
  help [command]            display help for command
```

## Notes

- Two cloud hostnames show up in the help/copy: **mcp-use cloud** (backend) and **Manufact cloud** (web/dashboard). Both address the same product. Backend defaults to `https://cloud.mcp-use.com/api/v1`; web defaults to `https://manufact.com`. See `config-files/11-user-config-json.md` for overrides.
- `servers` + `deployments` form the cloud lifecycle pair: a **server** is the Git-backed deploy target; a **deployment** is an actual running build tied to a server.
- `org` commands and the `--org <slug|id|name>` flag (on `login`, `deploy`, `servers *`) drive multi-tenant usage.
