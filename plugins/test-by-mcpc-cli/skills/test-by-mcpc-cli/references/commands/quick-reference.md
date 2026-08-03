# mcpc Quick Reference

This sheet is aligned to `@apify/mcpc 0.6.0`, verified against `mcpc help`
output from the installed 0.6.0 binary.
It documents raw `mcpc` behavior first.

## Core syntax

| Task | Command |
|---|---|
| list sessions and profiles | `mcpc` |
| list sessions and profiles as JSON | `mcpc --json` (or `-j`) |
| create a session | `mcpc connect <server> @session` |
| create an OAuth profile | `mcpc login <server>` |
| delete an OAuth profile | `mcpc logout <server>` |
| show command help | `mcpc help [command] [subcommand]` |
| show the built-in agent skill guide | `mcpc help --skill` |
| inspect a session | `mcpc @session` |
| show session commands | `mcpc @session help` |
| search all sessions | `mcpc grep <pattern>` |
| search one session | `mcpc @session grep <pattern>` |
| restart a session | `mcpc restart @session` |
| close a session | `mcpc close @session` |
| safe cleanup | `mcpc clean` |
| destructive targeted reset | `mcpc clean sessions logs` |

`shell` was removed in 0.4.0 — there is no interactive shell command anymore. Run
individual `mcpc @session <command>` invocations instead.

## First commands for any new target

```bash
mcpc connect <server-or-file:entry> @check
mcpc @check
mcpc @check help
mcpc @check grep search
mcpc @check tools-list --full
```

Start and stay with this raw CLI path — there is no shell wrapper to reintroduce.

If the machine has many saved sessions, skip the raw global dump unless reuse is the question.
Either connect a fresh isolated session first or filter by exact name:

```bash
mcpc --json | jq '.sessions[] | select(.name == "@check")'
```

If task support matters, add:

```bash
mcpc --json @check tools-list | jq '.[] | {name, taskSupport: (.execution.taskSupport // "unspecified")}'
```

## Server formats

| Target type | Example | Notes |
|---|---|---|
| remote HTTP target | `mcpc connect mcp.apify.com @apify` | `https://` is added automatically for non-local hosts |
| explicit HTTPS target | `mcpc connect https://research-mcp.yigitkonur.com/mcp @research` | use full path when the server is not on `/` |
| localhost HTTP target | `mcpc connect 127.0.0.1:3011/mcp @everything-http` | localhost keeps `http://` |
| config entry | `mcpc connect ~/.vscode/mcp.json:filesystem @fs` | config must use `mcpServers` |

## Session commands

| Area | Commands |
|---|---|
| discovery | `mcpc @s`, `mcpc @s help`, `mcpc @s grep search`, `mcpc @s server-discover` |
| tools | `tools-list [--full]`, `tools-get <name>`, `tools-call <name> [args...]` |
| prompts | `prompts-list`, `prompts-get <name> [args...]` |
| resources | `resources-list`, `resources-read <uri>`, `resources-subscribe <uri> <file>`, `resources-unsubscribe <uri>`, `resources-templates-list` |
| skills (server-published, SEP-2640) | `skills-list`, `skills-get <name> [--raw]` |
| logging | `logging-set-level <level>` (deprecated — see notes below) |
| health | `ping` |
| logs | `logs [-n N] [--follow] [--since 1h]` |
| tasks | `tools-call --task`, `tools-call --detach`, `tasks-list`, `tasks-get <taskId>`, `tasks-result <taskId>`, `tasks-cancel <taskId>` |

The `tools`/`resources`/`prompts` shorthand commands were REMOVED in v0.3.0 — only the
explicit `*-list` forms exist (`tools-list`, `resources-list`, `prompts-list`).

`tasks-result <taskId>` exists, works across process invocations, blocks until the task
reaches a terminal state, and returns the tool's real `CallToolResult` — not exclusive to
`--detach`, use it after any async task.

`skills-list`/`skills-get` (experimental, SEP-2640) read a server's own published
skills — unrelated to this skill pack. `server-discover` requires an MCP 2026-07-28
connection and fails on older ones; use `mcpc @session` there instead.

`logging-set-level` is deprecated as of 0.6.0 (MCP 2026-07-28 removed the underlying
`logging/setLevel` request) — still works on 2025-11-25 servers, errors on 2026-07-28.

Raw MCP JSON-RPC method names also work as silent aliases for session commands
(`tools/list` → `tools-list`, `logging/setLevel` → `logging-set-level`) — undocumented in
`--help`/"Did you mean?", but functional; teach the hyphenated form first.

## Global options

Exact list from `mcpc --help` — everything else (`--schema`, `--schema-mode`, `-H`,
`--no-profile`, `--proxy`, `--stdio`) is scoped to specific subcommands, not global.

| Option | Meaning |
|---|---|
| `-j`, `--json` | machine-readable output |
| `--verbose` | debug logging |
| `--profile <name>` | OAuth profile name |
| `--timeout <seconds>` | request timeout (default 60s) |
| `--max-chars <n>` | truncate human-readable output (ignored in `--json`) |
| `--insecure` | skip TLS verification for self-signed or untrusted certs |
| `-v`, `--version` | show version |
| `-h`, `--help` | show help |

`--schema <file>` / `--schema-mode <strict|compatible|ignore>` validate a tool's schema —
scoped to `tools-get` and `tools-call` only (removed from `prompts-get` since v0.2.5).

## `connect` options

| Option | Meaning |
|---|---|
| `-H`, `--header 'Key: Value'` | add HTTP header; can be repeated |
| `--profile <name>` | use a saved OAuth profile |
| `--no-profile` | disable default-profile auto-selection |
| `--proxy <[host:]port>` | start a local proxy bound to the session |
| `--proxy-bearer-token <token>` | configure a proxy bearer token; enforcement source-verified (DNS-rebinding-hardened since v0.5.0) |
| `--stdio` | include stdio (command-based) entries in a bulk config-file connect (skipped by default) |
| `--protocol-version <version>` | pin an exact MCP protocol version instead of auto-negotiating; connect fails if the server doesn't offer it |
| `--x402 [scheme]` | enable x402 auto-payment; `scheme` is `auto` (default), `upto`, or `exact` |

mcpc auto-negotiates the newest MCP protocol version both sides support, from
`2026-07-28` down to `2024-10-07`.

## `login` options

| Option | Meaning |
|---|---|
| `--profile <name>` | profile name |
| `--scope "read write"` | request explicit OAuth scopes |
| `--grant <type>` | `authorization-code` (default), `client-credentials`, or `id-jag` |
| `--client-id <id>` | static OAuth client ID |
| `--client-secret <secret>` | static OAuth client secret |
| `--client-key <pem-or-path>` | private key for `private_key_jwt` auth (client-credentials) |
| `--token-endpoint <url>` | OAuth token endpoint override (client-credentials only) |
| `--idp <url>` | enterprise IdP issuer URL (id-jag only) |
| `--idp-client-id`, `--idp-client-secret`, `--idp-scope` | id-jag-only IdP client identity + SSO scopes |
| `--client-metadata-url <url>` / `--no-client-metadata-url` | CIMD override / disable (falls back to DCR) |
| `--callback-host <host>` / `--callback-port <port>` | OAuth loopback callback host (`127.0.0.1` default, or `localhost`) and port |

`--grant client-credentials` is machine-to-machine auth for CI/CD and daemons.
`--grant id-jag` is Enterprise-Managed Authorization via corporate SSO.

## `clean` forms

```bash
mcpc clean
mcpc clean sessions
mcpc clean profiles
mcpc clean logs
mcpc clean sessions logs
mcpc clean all
```

Without arguments, `mcpc clean` removes stale data only. Every named target removes **all** records of that kind, including live sessions; use named forms only for intentional resets inside an isolated `MCPC_HOME_DIR`.
Do not parallelize `mcpc close @session` and `mcpc clean ...` for the same session.

## x402 commands

These are financial/credential actions, not harmless smoke checks. Use isolated state and prefer `x402 init` with a throwaway Base Sepolia wallet; obtain explicit authorization before importing/removing wallets, signing, approving, or paying. `mcpc 0.6.0` imports keys only through the positional argv argument — there is no secret-safe stdin/file/env option — so do not import real production keys for routine testing.

```bash
mcpc x402                    # bare: shows wallet info + funding QR (default since v0.5.0)
mcpc x402 init
mcpc x402 import <private-key>
mcpc x402 sign <payment-required>
mcpc x402 sign <payment-required> --amount 0.10 --expiry 120 --scheme upto
mcpc x402 remove
```

`mcpc x402 info` is deprecated since v0.5.0 in favor of bare `mcpc x402` (no
subcommand), which now shows wallet info + a funding QR code directly.
`--scheme <auto|upto|exact>` on `sign` selects the payment scheme (default `auto`).
`--no-approve` on `sign` skips the `upto` scheme's Permit2 allowance check and auto-approval.

## Argument shapes

| Form | Example | Use when |
|---|---|---|
| `key:=value` | `city:=Paris` | simple scalars or quoted JSON literals |
| inline JSON | `'{"queries":["OpenAI MCP"]}'` | full object payload |
| stdin JSON | `printf '%s' '{"queries":["OpenAI MCP"]}' | mcpc @s tools-call web-search` | scripting pipelines |

If a tool expects an array or object, send a JSON literal.
`queries:=OpenAI` is still a string, not `['OpenAI']`.

## Session states you will see in JSON output

- runtime JSON commonly shows `live`, `connecting`, `reconnecting`, `disconnected`, `crashed`, `unauthorized`, or `expired`
- persisted internal state uses a slightly different vocabulary; do not script against the on-disk file format unless you have to
- a dead bridge self-heals on the next command; a dead stdio child self-heals only through `ping` — otherwise expect `Not connected` (exit 2) until `mcpc restart @session`

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success; an unreachable `connect` can still return 0 while creating a `reconnecting` session |
| `1` | CLI/session failure; `grep` also uses 1 for no matches |
| `2` | MCP `isError:true` result on stdout, or timeout/no-result `{error,code}` on stderr |
| `3` / `4` | documented network / auth failures — not independently reproduced live |

## Unsupported or partial areas

- no `mcpc completions` command even if server capabilities show `completions`
- mcpc advertises no sampling/roots/elicitation client capabilities, so servers withhold
  any tool gated on them — e.g. Everything's `trigger-sampling-request`,
  `trigger-elicitation-request`, `get-roots-list` never appear in `tools-list` at all,
  even though the server's own instructions text mentions them
- on MCP 2026-07-28 connections: `logging-set-level` errors (protocol removed
  `logging/setLevel`), and every task command (`tasks-list`, `tasks-get`, `tasks-result`,
  `tasks-cancel`, `tools-call --task`/`--detach`) reports the tasks extension as not yet
  supported — both keep working unchanged on 2025-11-25 servers
- `--task`/`--detach` against a server without task support now fails outright (no more
  silent fallback to a synchronous call)
