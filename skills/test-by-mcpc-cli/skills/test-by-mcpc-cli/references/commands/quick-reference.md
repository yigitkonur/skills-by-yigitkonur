# mcpc Quick Reference

All commands, flags, and options for the `mcpc` CLI.

## Top-level commands

| Command | Description |
|---|---|
| `mcpc` | List active sessions and saved OAuth profiles |
| `mcpc <server> connect @<session>` | Create a persistent session |
| `mcpc @<session> close` | Close a session (kills bridge) |
| `mcpc @<session> restart` | Restart session (new connection) |
| `mcpc @<session> shell` | Open interactive shell |
| `mcpc login <server>` | OAuth login and save profile |
| `mcpc logout <server>` | Delete authentication profile |
| `mcpc --clean[=types]` | Clean up mcpc data |
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

### Resource commands

| Command | Description |
|---|---|
| `mcpc @s resources` | List resources |
| `mcpc @s resources-list` | List resources (alias) |
| `mcpc @s resources-read <uri>` | Read a resource |
| `mcpc @s resources-read <uri> > <file>` | Read resource to file via shell redirection |
| `mcpc @s resources-subscribe <uri>` | Subscribe to updates |
| `mcpc @s resources-unsubscribe <uri>` | Unsubscribe |
| `mcpc @s resources-templates-list` | List resource templates |

### Prompt commands

| Command | Description |
|---|---|
| `mcpc @s prompts` | List prompts |
| `mcpc @s prompts-list` | List prompts (alias) |
| `mcpc @s prompts-get <name> [args...]` | Get prompt with arguments |

### Utility commands

| Command | Description |
|---|---|
| `mcpc @s ping` | Check if server is alive |
| `mcpc @s help` | Show server info and capabilities |
| `mcpc @s logging-set-level <level>` | Set server logging level |
| `mcpc @s restart` | Restart session |
| `mcpc @s close` | Close session |

## Not supported by mcpc

These MCP capabilities have no CLI command — do not attempt them:

| MCP Capability | Why no command |
|---|---|
| `completion/complete` | Argument auto-completion — no `completions` command exists |
| `sampling` | Server-initiated LLM requests — client-side only |
| `roots` | Client root declarations — not applicable to CLI |
| Generic task lifecycle commands | `mcpc 0.1.11` does not expose `--task`, `--detach`, or `tasks-*` commands |

If the server advertises these capabilities, they simply cannot be tested via mcpc.

## Global flags

| Flag | Short | Description | Default |
|---|---|---|---|
| `--json` | `-j` | JSON output mode | off |
| `--config <file>` | `-c` | Load target from MCP config file | none |
| `--header "Key: Value"` | `-H` | Add HTTP header (repeatable) | none |
| `--verbose` | | Debug logging | off |
| `--profile <name>` | | OAuth profile name | `default` when available |
| `--timeout <seconds>` | | Request timeout | 300 |
| `--schema <file>` | | Validate against schema file | none |
| `--schema-mode <mode>` | | Schema validation: `strict`, `compatible`, `ignore` | `compatible` |
| `--version` | `-v` | Show version | |
| `--help` | `-h` | Show help | |

## Connect flags

| Flag | Description |
|---|---|
| `--header "Key: Value"` | Add HTTP header (repeatable) |
| `--profile <name>` | OAuth profile name |
| *(omit --profile and --header)* | Connect anonymously (no flag needed) |
| `--proxy [host:]port` | Start proxy MCP server |
| `--proxy-bearer-token <token>` | Require token for proxy |
| `--x402` | Enable x402 auto-payment |

## Login flags

| Flag | Description |
|---|---|
| `--profile <name>` | Profile name (default: "default") |

## Logout flags

| Flag | Description |
|---|---|
| `--profile <name>` | Profile to delete (default: "default") |

## Clean command

```bash
mcpc --clean                    # Safe cleanup only
mcpc --clean=sessions           # Remove all sessions
mcpc --clean=profiles           # Remove all OAuth profiles
mcpc --clean=logs               # Remove bridge logs
mcpc --clean=all                # Remove everything
```

## Server format

| Format | Example | Transport |
|---|---|---|
| URL | `https://mcp.example.com` | HTTP |
| Bare hostname | `mcp.example.com` | HTTP (https://) |
| Localhost | `localhost:3000` | HTTP (http://) |
| Config entry | `mcpc --config ~/.vscode/mcp.json server-name connect @session` | Stdio |
| Config entry | `mcpc --config ./config.json my-server connect @session` | Stdio |

## Argument format (`key:=value`)

`key:=value` only produces **scalar values**. For arrays/objects, use JSON literals or inline JSON.

| Example | Parsed as | Notes |
|---|---|---|
| `count:=10` | number `10` | |
| `enabled:=true` | boolean `true` | |
| `name:=hello` | string `"hello"` | |
| `id:='"123"'` | string `"123"` (forced) | |
| `items:='[1,2,3]'` | array `[1,2,3]` | JSON literal with shell quoting |
| `tags:='["a","b"]'` | array `["a","b"]` | JSON literal with shell quoting |
| `config:='{"k":"v"}'` | object `{"k":"v"}` | JSON literal with shell quoting |
| `'{"key":"val"}'` | inline JSON object | all-or-nothing, cannot mix with key:=value |
| (piped stdin) | JSON from stdin | |

**Common mistake:** `items:=hello` sends the string `"hello"`, NOT `["hello"]`. If the tool expects an array, this will fail with a validation error. Always check the tool schema first.

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

Exit codes reflect **mcpc CLI errors only**. MCP server errors return exit 0 with `isError: true` in JSON.

| Code | Meaning | Covers |
|---|---|---|
| 0 | CLI success (but check `isError` in JSON!) | Includes server validation errors, tool-not-found |
| 1 | Client error | Invalid CLI args, unknown mcpc command, session not found |
| 2 | Server error | Rare transport-level failures |
| 3 | Network error | Connection refused, timeout, DNS failure |
| 4 | Auth error | 401/403, expired token |

**In scripts, always check both:** `$?` for CLI errors AND `jq '.isError'` for server errors.

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
| `~/.mcpc/credentials.json` | Fallback credential storage |
| `~/.mcpc/shell-history` | Shell history |
| `~/.mcpc/bridges/@<name>.sock` | Bridge IPC sockets |
| `~/.mcpc/logs/bridge-<name>.log` | Bridge logs |

## Common recipes

```bash
# Quick smoke test
mcpc <server> connect @smoke && mcpc @smoke ping && mcpc @smoke tools-list && mcpc @smoke close

# List all tool names
mcpc @s tools-list --json | jq -r '.[].name'

# Count tools
mcpc @s tools-list --json | jq 'length'

# Call tool and extract text
mcpc @s tools-call my-tool arg:=val --json | jq -r '.content[0].text'

# Check if tool errored (MUST do this — exit code is 0 even for server errors)
mcpc @s tools-call my-tool '{"arg":"val"}' --json | jq '.isError // false'

# Verbose debugging
MCPC_VERBOSE=1 mcpc @s tools-call my-tool arg:=val

# Isolated test environment
MCPC_HOME_DIR=/tmp/test mcpc <server> connect @isolated
```
