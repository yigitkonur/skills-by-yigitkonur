# mcpc Quick Reference

All commands, flags, and options for the `mcpc` CLI.

## Top-level commands

| Command | Description |
|---|---|
| `mcpc` | List active sessions and saved OAuth profiles |
| `mcpc connect <server> @<session>` | Create a persistent session |
| `mcpc close @<session>` | Close a session (kills bridge) |
| `mcpc restart @<session>` | Restart session (new connection) |
| `mcpc shell @<session>` | Open interactive shell |
| `mcpc login <server>` | OAuth login and save profile |
| `mcpc logout <server>` | Delete authentication profile |
| `mcpc clean [resources...]` | Clean up mcpc data |
| `mcpc x402 [subcommand]` | Configure x402 payment wallet (experimental) |
| `mcpc help [command]` | Show help |
| `mcpc --version` | Show version |

## Session commands (after `@<session>`)

### Tool commands

| Command | Description |
|---|---|
| `mcpc @s tools` | List tools (summary) |
| `mcpc @s tools --full` | List tools with full schemas |
| `mcpc @s tools-list` | List tools (alias) |
| `mcpc @s tools-get <name>` | Get tool details and schema |
| `mcpc @s tools-call <name> [args...]` | Call a tool |
| `mcpc @s tools-call <name> --task` | Call tool as task (experimental) |
| `mcpc @s tools-call <name> --task --detach` | Start task, return immediately |

### Resource commands

| Command | Description |
|---|---|
| `mcpc @s resources` | List resources |
| `mcpc @s resources-list` | List resources (alias) |
| `mcpc @s resources-read <uri>` | Read a resource |
| `mcpc @s resources-read <uri> -o <file>` | Read resource to file |
| `mcpc @s resources-read <uri> --max-size <n>` | Read with size limit |
| `mcpc @s resources-subscribe <uri>` | Subscribe to updates |
| `mcpc @s resources-unsubscribe <uri>` | Unsubscribe |
| `mcpc @s resources-templates-list` | List resource templates |

### Prompt commands

| Command | Description |
|---|---|
| `mcpc @s prompts` | List prompts |
| `mcpc @s prompts-list` | List prompts (alias) |
| `mcpc @s prompts-get <name> [args...]` | Get prompt with arguments |

### Task commands (experimental)

| Command | Description |
|---|---|
| `mcpc @s tasks-list` | List active tasks |
| `mcpc @s tasks-get <taskId>` | Get task status |
| `mcpc @s tasks-cancel <taskId>` | Cancel a task |

### Utility commands

| Command | Description |
|---|---|
| `mcpc @s ping` | Check if server is alive |
| `mcpc @s help` | Show server info and capabilities |
| `mcpc @s logging-set-level <level>` | Set server logging level |
| `mcpc @s restart` | Restart session |
| `mcpc @s close` | Close session |

## Global flags

| Flag | Short | Description | Default |
|---|---|---|---|
| `--json` | `-j` | JSON output mode | off |
| `--verbose` | | Debug logging | off |
| `--timeout <seconds>` | | Request timeout | 300 |
| `--insecure` | | Skip TLS verification | off |
| `--schema <file>` | | Validate against schema file | none |
| `--schema-mode <mode>` | | Schema validation: `strict`, `compatible`, `ignore` | `compatible` |
| `--version` | `-v` | Show version | |
| `--help` | `-h` | Show help | |

## Connect flags

| Flag | Description |
|---|---|
| `--header "Key: Value"` | Add HTTP header (repeatable) |
| `--profile <name>` | OAuth profile name |
| `--no-profile` | Connect anonymously |
| `--proxy [host:]port` | Start proxy MCP server |
| `--proxy-bearer-token <token>` | Require token for proxy |
| `--x402` | Enable x402 auto-payment |

## Login flags

| Flag | Description |
|---|---|
| `--profile <name>` | Profile name (default: "default") |
| `--scope <scopes>` | OAuth scopes (space-separated) |
| `--client-id <id>` | Custom OAuth client ID |
| `--client-secret <secret>` | Custom OAuth client secret |

## Logout flags

| Flag | Description |
|---|---|
| `--profile <name>` | Profile to delete (default: "default") |

## Clean command

```bash
mcpc clean                    # Safe cleanup only
mcpc clean sessions           # Remove all sessions
mcpc clean profiles           # Remove all OAuth profiles
mcpc clean logs               # Remove bridge logs
mcpc clean all                # Remove everything
```

## Server format

| Format | Example | Transport |
|---|---|---|
| URL | `https://mcp.example.com` | HTTP |
| Bare hostname | `mcp.example.com` | HTTP (https://) |
| Localhost | `localhost:3000` | HTTP (http://) |
| Config entry | `~/.vscode/mcp.json:server-name` | Stdio |
| Config entry | `./config.json:my-server` | Stdio |

## Argument format (`key:=value`)

| Example | Parsed as |
|---|---|
| `count:=10` | number `10` |
| `enabled:=true` | boolean `true` |
| `name:=hello` | string `"hello"` |
| `id:='"123"'` | string `"123"` (forced) |
| `'{"key":"val"}'` | inline JSON object |
| (piped stdin) | JSON from stdin |

## Environment variables

| Variable | Purpose |
|---|---|
| `MCPC_VERBOSE` | Enable debug logging (`1`, `true`, `yes`) |
| `MCPC_JSON` | Enable JSON output mode |
| `MCPC_HOME_DIR` | Override `~/.mcpc` directory |
| `HTTP_PROXY` | HTTP proxy |
| `HTTPS_PROXY` | HTTPS proxy |
| `NO_PROXY` | Bypass proxy for hosts |

## Logging levels

Valid values for `logging-set-level`:

```
debug < info < notice < warning < error < critical < alert < emergency
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Client error (invalid args, unknown command) |
| 2 | Server error (tool failed, resource not found) |
| 3 | Network error (connection failed, timeout) |
| 4 | Auth error (invalid credentials, 401/403) |

## Session status indicators

| Icon | State | Meaning |
|---|---|---|
| 🟢 | live | Bridge running, server responding |
| 🟡 | disconnected | Bridge alive, server unreachable |
| 🟡 | crashed | Bridge process died |
| 🔴 | unauthorized | Auth rejected (401/403) |
| 🔴 | expired | Session ID rejected (404) |

## File locations

| Path | Purpose |
|---|---|
| `~/.mcpc/sessions.json` | Active session metadata |
| `~/.mcpc/profiles.json` | OAuth profile metadata |
| `~/.mcpc/credentials` | Fallback credential storage |
| `~/.mcpc/history` | Shell history |
| `~/.mcpc/bridges/<name>.sock` | Bridge IPC sockets |
| `~/.mcpc/logs/bridge-<name>.log` | Bridge logs |

## Common recipes

```bash
# Quick smoke test
mcpc connect <server> @smoke && mcpc @smoke ping && mcpc @smoke tools && mcpc close @smoke

# List all tool names
mcpc @s tools-list --json | jq -r '.[].name'

# Count tools
mcpc @s tools-list --json | jq 'length'

# Call tool and extract text
mcpc @s tools-call my-tool arg:=val --json | jq -r '.content[0].text'

# Check if tool errored
mcpc @s tools-call my-tool --json | jq '.isError // false'

# Verbose debugging
MCPC_VERBOSE=1 mcpc @s tools-call my-tool arg:=val

# Isolated test environment
MCPC_HOME_DIR=/tmp/test mcpc connect <server> @isolated
```
