# mcpc Quick Reference

This sheet is aligned to `@apify/mcpc 0.2.4`.

## Core syntax

| Task | Command |
|---|---|
| list sessions and profiles | `mcpc` |
| list sessions and profiles as JSON | `mcpc --json` |
| create a session | `mcpc connect <server> @session` |
| open the interactive shell | `mcpc shell @session` |
| create an OAuth profile | `mcpc login <server>` |
| delete an OAuth profile | `mcpc logout <server>` |
| show command help | `mcpc help [command] [subcommand]` |
| inspect a session | `mcpc @session` |
| show server info and commands | `mcpc @session help` |
| search all sessions | `mcpc grep <pattern>` |
| search one session | `mcpc @session grep <pattern>` |
| restart a session | `mcpc restart @session` |
| close a session | `mcpc close @session` |
| safe cleanup | `mcpc clean` |
| targeted cleanup | `mcpc clean sessions logs` |

## First commands for any new target

```bash
mcpc connect <server-or-file:entry> @check
mcpc @check
mcpc @check help
mcpc @check grep search
mcpc @check tools-list --full
```

If task support matters, add:

```bash
mcpc --json @check tools-list | jq '.[] | {name, taskSupport: (.execution.taskSupport // "unspecified")}'
```

## Server formats

| Target type | Example | Notes |
|---|---|---|
| remote HTTP target | `mcpc connect mcp.apify.com @apify` | `https://` is added automatically for non-local hosts |
| explicit HTTPS target | `mcpc connect https://research.yigitkonur.com/mcp @research` | use full path when the server is not on `/` |
| localhost HTTP target | `mcpc connect 127.0.0.1:3011/mcp @everything-http` | localhost keeps `http://` |
| config entry | `mcpc connect ~/.vscode/mcp.json:filesystem @fs` | config must use `mcpServers` |

## Session commands

| Area | Commands |
|---|---|
| discovery | `mcpc @s`, `mcpc @s help`, `mcpc @s grep search` |
| tools | `tools-list [--full]`, `tools-get <name>`, `tools-call <name> [args...]` |
| prompts | `prompts-list`, `prompts-get <name> [args...]` |
| resources | `resources-list`, `resources-read <uri>`, `resources-subscribe <uri>`, `resources-unsubscribe <uri>`, `resources-templates-list` |
| logging | `logging-set-level <level>` |
| health | `ping` |
| tasks | `tools-call --task`, `tools-call --detach`, `tasks-list`, `tasks-get <taskId>`, `tasks-cancel <taskId>` |

Aliases that still work: `tools`, `resources`, and `prompts`.
Teach the explicit `*-list` form first.

## Global options

| Option | Meaning |
|---|---|
| `-j`, `--json` | machine-readable output |
| `--verbose` | debug logging |
| `--profile <name>` | OAuth profile name |
| `--schema <file>` | validate tool or prompt schema |
| `--schema-mode <mode>` | `strict`, `compatible`, or `ignore` |
| `--timeout <seconds>` | request timeout |
| `--insecure` | skip TLS verification for self-signed or untrusted certs |
| `-v`, `--version` | show version |
| `-h`, `--help` | show help |

## `connect` options

| Option | Meaning |
|---|---|
| `-H`, `--header 'Key: Value'` | add HTTP header; can be repeated |
| `--profile <name>` | use a saved OAuth profile |
| `--no-profile` | disable default-profile auto-selection |
| `--proxy <[host:]port>` | start a local proxy bound to the session |
| `--proxy-bearer-token <token>` | require bearer auth for the proxy |
| `--x402` | enable x402 auto-payment |

## `login` options

| Option | Meaning |
|---|---|
| `--profile <name>` | profile name |
| `--scope "read write"` | request explicit OAuth scopes |
| `--client-id <id>` | static OAuth client ID |
| `--client-secret <secret>` | static OAuth client secret |

## `clean` forms

```bash
mcpc clean
mcpc clean sessions
mcpc clean profiles
mcpc clean logs
mcpc clean sessions logs
mcpc clean all
```

Without arguments, `mcpc clean` removes stale data only.

## x402 commands

```bash
mcpc x402 init
mcpc x402 import <private-key>
mcpc x402 info
mcpc x402 sign <payment-required>
mcpc x402 sign <payment-required> --amount 0.10 --expiry 120
mcpc x402 remove
```

## Argument shapes

| Form | Example | Use when |
|---|---|---|
| `key:=value` | `city:=Paris` | simple scalars or quoted JSON literals |
| inline JSON | `'{"queries":["OpenAI MCP"]}'` | full object payload |
| stdin JSON | `printf '%s' '{"queries":["OpenAI MCP"]}' | mcpc @s tools-call search-reddit` | scripting pipelines |

If a tool expects an array or object, send a JSON literal.
`queries:=OpenAI` is still a string, not `['OpenAI']`.

## Session states you will see in JSON output

- runtime JSON commonly shows `live`, `connecting`, `reconnecting`, `disconnected`, `crashed`, `unauthorized`, or `expired`
- persisted internal state uses a slightly different vocabulary; do not script against the on-disk file format unless you have to

## Unsupported or partial areas

- no `mcpc completions` command even if server capabilities show `completions`
- no dedicated roots configuration CLI even though some servers may expose roots-aware demo tools
- sampling demo tools may exist, but can still return `isError: true`
- no standalone `tasks-result` command after `--detach`
