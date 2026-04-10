---
name: test-by-mcpc-cli
description: Use skill if you are testing or debugging MCP servers with mcpc 0.2.x across stdio or Streamable HTTP, including session setup, schemas, grep, tasks, and JSON scripting.
---

# Test MCP Servers with mcpc

Use `mcpc 0.2.x` as the operator-facing harness for MCP server testing.
This skill is written for the `0.2.0` through `0.2.4` command family, not the older `0.1.11` target-first CLI.

## Trigger Boundary

Use this skill when you need to:

- connect to a real MCP server over `stdio` or Streamable HTTP and verify the live surface
- inspect tools, prompts, resources, templates, logging, subscriptions, or instructions from `mcpc`
- reproduce auth, proxy, cleanup, task, or transport failures with the released CLI
- script repeatable smoke checks in `--json` mode
- compare a local stdio server with a deployed HTTP target

Do not use this skill when the main job is building the server or client itself.
Use `build-mcp-sdk`, `build-mcp-sdk-v2`, `build-mcp-use-server`, or `build-mcp-use-client` for implementation work.

## Prerequisites

```bash
mcpc --version
mcpc --help
```

Prefer `mcpc 0.2.x`.
This rewrite was verified against `0.2.4` and live-tested with:

- `https://research.yigitkonur.com/mcp`
- `@modelcontextprotocol/server-everything` over stdio and Streamable HTTP

If `mcpc` is missing, older, or your config shape is wrong, start with `references/guides/installation.md`.

## Minimal Read Sets

Do not load the whole skill by default.
Use one of these bundles first, then widen only if the task forces you to.

### Remote Streamable HTTP smoke test

Read these first:

- `references/commands/quick-reference.md`
- `references/guides/http-testing.md`
- `references/guides/discovery-search.md`
- `references/guides/tool-resource-testing.md`
- `references/guides/cleanup-maintenance.md`

### Local stdio plus task verification

Read these first:

- `references/commands/quick-reference.md`
- `references/guides/stdio-testing.md`
- `references/guides/async-tasks.md`
- `references/guides/everything-server.md`
- `references/guides/cleanup-maintenance.md`

### Auth, proxy, or payment edge cases

Read these first:

- `references/commands/quick-reference.md`
- `references/guides/authentication.md`
- `references/guides/proxy-testing.md`
- `references/guides/x402-payments.md`
- `references/guides/cleanup-maintenance.md`

## Command Family Change

The `0.2.x` CLI is session-first.
Always create or reuse a named session before you run MCP operations.

```bash
# Remote Streamable HTTP target
mcpc connect https://research.yigitkonur.com/mcp @research
mcpc @research ping
mcpc @research tools-list

# Local stdio target from a standard mcpServers config
mcpc connect .vscode/mcp.json:filesystem @fs
mcpc @fs tools-list
```

Treat these forms as stale `0.1.11` syntax drift:

- `mcpc mcp.example.com tools-list`
- `mcpc mcp.example.com connect @demo`
- `mcpc --config .vscode/mcp.json filesystem connect @demo`
- `mcpc --clean=sessions`

Route migration work to `references/patterns/session-first-syntax.md`.

## Standard Workflow

### 1. Verify the syntax family

- Confirm `mcpc --version` reports `0.2.x`.
- Confirm examples use `mcpc connect <server-or-file:entry> @session`.
- Treat old `--config file entry` and direct URL one-shot commands as obsolete.

### 2. Connect a stable session

```bash
# Remote URL; https:// is added automatically for non-local hosts
mcpc connect research.yigitkonur.com/mcp @research

# Localhost keeps http:// by default
mcpc connect 127.0.0.1:3011/mcp @everything-http

# Stdio via config entry
mcpc connect /tmp/everything-mcp.json:everything @everything-stdio
```

Use `--no-profile` when anonymous HTTP testing matters on a machine with saved OAuth profiles.

If `mcpc --json` already shows an older session for the same target and its status is not `live`, do not assume that session is still the right test entrypoint.
Either `mcpc restart @session` or create a fresh session with a new name.
For Everything-specific work, prefer a fresh stdio session unless you intentionally started the `streamableHttp` server yourself.

### 3. Inspect before deep testing

```bash
mcpc @research
mcpc @research help
mcpc @research grep search
mcpc @research tools-list --full
mcpc @research resources-list
mcpc @research prompts-list
```

Prefer `help` and `grep` before heavy `jq` pipelines.

### 4. Validate schema and argument shape

```bash
mcpc @research tools-get web-search
mcpc --json @research tools-get web-search | jq '.inputSchema'
mcpc @research prompts-get some-prompt --schema ./expected-prompt-schema.json
```

`key:=value` still works, but arrays and objects should be sent as inline JSON literals or full JSON payloads.
Route quoting edge cases to `references/patterns/argument-parsing.md`.

### 4b. Reality-check advertised capabilities

Do not trust `capabilities` alone.
Check the server info, the tool metadata, and one real call.

```bash
mcpc --json @research | jq '.capabilities'
mcpc --json @everything-http tools-list | jq '.[] | {name, taskSupport: (.execution.taskSupport // "unspecified")}'
```

Rules:

- if `completions` appears in server info, treat it as informational until you confirm the CLI actually exposes a command
- if tasks appear in capabilities, still inspect per-tool `execution.taskSupport`
- if a tool is marked `task:required`, prove it with one `--task` or `--detach` call before writing automation around it

### 5. Exercise the capability you care about

```bash
mcpc @research tools-call search-reddit '{"queries":["OpenAI MCP"]}' --json
mcpc @everything-http prompts-get args-prompt city:=Paris state:=Texas
mcpc @everything-http resources-read demo://resource/static/document/features.md
mcpc @everything-http logging-set-level debug
```

### 6. Treat JSON payloads as truth

```bash
RESULT=$(mcpc --json @everything-http tools-call trigger-sampling-request prompt:='"hello"')
echo "$RESULT" | jq '.isError // false'
```

A command can exit `0` and still carry `"isError": true`.

### 7. Use task mode deliberately

```bash
mcpc @everything-http tools-list --full
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' --task
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' --detach
mcpc @everything-http tasks-get <taskId>
```

Use `--task` when you need the final result in the CLI.
Use `--detach` when a task ID is enough.
`mcpc 0.2.4` does not have a standalone `tasks-result` command.

### 8. Close or clean explicitly

```bash
mcpc close @research
mcpc clean
mcpc clean sessions logs
```

Use `mcpc clean all` only for a real reset.

## High-Signal Rules

1. Connect first. If an example starts with `mcpc <server> tools-list`, it is stale.
2. Prefer native discovery with `mcpc @session`, `mcpc @session help`, and `mcpc grep` before custom JSON filtering.
3. Inspect `isError`, task status, and payload text instead of trusting human-mode success banners.
4. Use `--no-profile` to force anonymous HTTP tests when saved OAuth state would pollute the result.
5. Use `mcpc clean ...`, not legacy `--clean=...` flags.
6. If an old session is `disconnected`, `reconnecting`, `expired`, or `crashed`, do not reuse it blindly for a smoke test. Restart it or create a fresh session.
7. Treat HTTP+SSE endpoints as unsupported for `mcpc 0.2.x`; use Streamable HTTP or stdio instead.
8. Reach for `--insecure` only when the endpoint really uses a self-signed or otherwise untrusted certificate.
9. When a tool is marked `task:required`, expect plain `tools-call` to fail until you add `--task` or `--detach`.

## Capability Boundary

### Fully testable with first-class CLI support

- `stdio` and Streamable HTTP
- tools, prompts, resources, resource templates, logging, grep, proxy, x402, JSON scripting
- task-enabled tool execution with `--task`, `--detach`, `tasks-list`, `tasks-get`, and `tasks-cancel`

### Nuanced or partial in `mcpc 0.2.4`

- `roots`: the client advertises roots capability, so servers like Everything may expose helper tools, but `mcpc` has no dedicated CLI to configure roots
- `sampling`: servers may expose sampling demo tools because `mcpc` advertises sampling-related client capabilities, but the tool payload can still come back with `isError: true`
- `completions`: appears in server capabilities, but there is no `mcpc completions` command
- detached task results: `tasks-get` shows status, not the original tool result body

### Not a first-class mcpc workflow

- HTTP+SSE transport testing
- elicitation commands from the CLI
- standalone completion browsing
- standalone detached-result retrieval after `--detach`

## Reference Routing

Read the smallest relevant set for the branch you are in.

### Core guides

| File | Read when |
|---|---|
| `references/guides/installation.md` | Installing `mcpc`, checking version drift, Linux keychain notes, or config format confusion. |
| `references/guides/stdio-testing.md` | Testing a local stdio server from `mcpServers` config using `file:entry` syntax. |
| `references/guides/http-testing.md` | Testing remote or localhost Streamable HTTP endpoints, path issues, TLS, headers, or `--insecure`. |
| `references/guides/discovery-search.md` | Discovering tools, resources, prompts, and instructions with `help`, `grep`, and list calls. |
| `references/guides/tool-resource-testing.md` | Running tools, prompts, resources, templates, subscriptions, and logging checks. |
| `references/guides/async-tasks.md` | Using `--task`, `--detach`, and `tasks-*`, or debugging task-required tools. |
| `references/guides/authentication.md` | OAuth, bearer headers, profile selection, scopes, client credentials, and anonymous mode. |
| `references/guides/session-management.md` | Understanding session lifecycle, reconnect behavior, restart behavior, and multi-session workflows. |
| `references/guides/cleanup-maintenance.md` | Safe cleanup, hard resets, logs, and local mcpc hygiene. |
| `references/guides/proxy-testing.md` | Exposing a session as a local MCP proxy for sandboxes or agent code. |
| `references/guides/x402-payments.md` | Wallet setup, `x402 sign`, and `--x402` session behavior. |
| `references/guides/ci-cd-integration.md` | CI smoke tests, isolated `MCPC_HOME_DIR`, scripted assertions, and cleanup traps. |
| `references/guides/scripting-automation.md` | Shell automation patterns, error handling, JSON parsing, and reproducible scripts. |
| `references/guides/everything-server.md` | Verifying current `mcpc` behavior against the official Everything reference server. |
| `references/guides/capability-coverage.md` | Mapping advertised capabilities to actual `mcpc` commands and known gaps. |
| `references/guides/architecture.md` | High-level `mcpc` design, session-first routing, and capability negotiation. |
| `references/guides/bridge-internals.md` | Bridge process lifecycle, crash recovery, reconnect caveats, and log locations. |

### Commands, examples, and troubleshooting

| File | Read when |
|---|---|
| `references/commands/quick-reference.md` | You need the exact `0.2.4` syntax, flags, aliases, or cleanup forms fast. |
| `references/examples/real-world-workflows.md` | You want complete end-to-end workflows for real targets like Research Powerpack or Everything. |
| `references/examples/testing-recipes.md` | You want short copy-paste checks for smoke tests, schemas, tasks, grep, or cleanup. |
| `references/troubleshooting/common-errors.md` | You hit stale syntax, bad config shape, task-required failures, expired sessions, or transport mismatches. |

### Patterns and advanced details

| File | Read when |
|---|---|
| `references/patterns/session-first-syntax.md` | Translating `0.1.11` examples to `0.2.x` command-first syntax. |
| `references/patterns/argument-parsing.md` | Quoting arrays, objects, inline JSON, stdin, and `key:=value` edge cases. |
| `references/patterns/schema-validation.md` | Validating tool and prompt schemas in regression checks. |
| `references/patterns/config-resolution.md` | Understanding `mcpServers` config shape, `file:entry`, URL normalization, and path mistakes. |
| `references/patterns/auth-precedence.md` | Deciding between explicit headers, named profiles, default profile, `--no-profile`, and `--x402`. |
| `references/patterns/output-formatting.md` | Understanding human vs JSON mode, stderr behavior, exit-code caveats, and `isError`. |
| `references/patterns/jq-patterns.md` | Advanced JSON filtering after native `grep` and `help` are not enough. |
| `references/patterns/tool-filtering.md` | Complementing `grep` with `tools-list --json | jq` workflows. |
| `references/patterns/logging-debugging.md` | Using `--verbose`, bridge logs, and log inspection to explain failures. |
| `references/patterns/notification-handling.md` | Testing list-changed notifications, subscriptions, and server log messages. |
| `references/patterns/pagination-caching.md` | Understanding auto-pagination, tool cache refresh, and dynamic discovery behavior. |
| `references/patterns/python-integration.md` | Driving `mcpc` from Python subprocess workflows. |
| `references/patterns/shell-advanced.md` | Interactive shell behavior, discovery loops, and task usage inside `shell`. |
| `references/patterns/data-model.md` | The JSON shapes behind session info, task status, cached metadata, profiles, and storage. |

## Guardrails

- Do not teach `0.1.11` target-first syntax unless you are explicitly documenting migration.
- Do not tell users to test HTTP+SSE with `mcpc 0.2.x`; use Streamable HTTP or stdio instead.
- Do not assume `tasks-get` can recover the full detached result body.
- Do not treat a green success banner as proof that the server call succeeded.
- Do not assume advertised capabilities always mean polished CLI support.
- Do not run `mcpc clean all` casually on machines with saved profiles.
