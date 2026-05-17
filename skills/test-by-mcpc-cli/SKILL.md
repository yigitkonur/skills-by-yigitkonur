---
name: test-by-mcpc-cli
description: Use skill if you are driving the mcpc CLI (0.2.x) to test, debug, or smoke-check an MCP server over stdio or Streamable HTTP.
---

# Test MCP Servers with mcpc

Drive `mcpc` 0.2.x as the operator-facing harness for any MCP server — stdio or Streamable HTTP. This skill owns the released CLI contract (`0.2.0`–`0.2.4`), session-first command shape, JSON scripting, task execution, and cleanup. It does not own writing the server or client itself.

## When to use this skill

- *Connecting to a real MCP server over stdio or Streamable HTTP and verifying the live surface with `mcpc connect … @session`*
- *Inspecting tools, prompts, resources, templates, logging, subscriptions, or instructions from `mcpc`*
- *Reproducing auth, proxy, cleanup, task, or transport failures with the released `mcpc 0.2.x` CLI*
- *Scripting repeatable smoke checks in `--json` mode, including CI assertions and `isError` parsing*
- *Comparing a local stdio server against a deployed Streamable HTTP target during release verification*
- *Translating older `0.1.11` target-first examples to current session-first syntax*

## Do NOT use this skill when

- *Building or refactoring server code* → use `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `build-mcp-use-server`
- *Building or refactoring client/agent code* → use `build-mcp-use-client` or `build-mcp-use-agent`
- *Running an agentic-quality / hardening / context-budget audit beyond CLI testing* → use `audit-agentic-mcp`
- *Porting an existing v1 server to v2* → use `convert-mcp-sdk-v1-to-v2`

## Source of truth

1. Confirm the running CLI: `mcpc --version` must report `0.2.x`. Older `0.1.11` syntax is structurally different and stale.
2. When docs and `mcpc --help` disagree, trust `mcpc --help <command>` on the version actually installed.
3. This skill was verified against `0.2.4` and live-tested against `https://research.yigitkonur.com/mcp` and `@modelcontextprotocol/server-everything` over stdio and Streamable HTTP.
4. If `mcpc` is missing, older, or your config shape is wrong, start with `references/guides/installation.md`. Establish the plain CLI path first, then layer wrappers back in only after the raw command path already works.

## Load-bearing rules

These rules apply across every workflow below. Violating any one of them is the most common failure mode in `mcpc 0.2.x`.

| # | Rule | Why |
|---|---|---|
| 1 | Always `connect` to a named `@session` before any MCP operation | `0.2.x` is session-first; target-first one-shot commands no longer exist |
| 2 | Treat `mcpc <server> tools-list` and `mcpc --config file entry connect @s` as stale `0.1.11` syntax | They will either fail or silently drift |
| 3 | Inspect `isError`, task status, and payload text — not the green human-mode banner | A command can exit `0` and still return `"isError": true` |
| 4 | Use `mcpc clean …`, never legacy `--clean=…` flags | The flag form is gone; `mcpc clean all` is destructive |
| 5 | Treat HTTP+SSE endpoints as unsupported; use Streamable HTTP or stdio | `mcpc 0.2.x` does not test HTTP+SSE as a first-class transport |
| 6 | Use `--no-profile` to force anonymous HTTP tests when saved OAuth would pollute the result | Profiles silently inject auth; anonymous reproduction needs explicit opt-out |
| 7 | If a tool is marked `task:required`, expect plain `tools-call` to fail until you add `--task` or `--detach` | The flag is mandatory, not optional |
| 8 | `mcpc 0.2.4` has no standalone `tasks-result` command — `tasks-get` returns status, not a detached result body | Plan around it: use `--task` if you need the result inline |
| 9 | If a session is `disconnected`, `reconnecting`, `expired`, or `crashed`, restart it or create a fresh one | Stale sessions silently corrupt smoke checks |
| 10 | Reach for `--insecure` only when the endpoint truly uses an untrusted certificate | It hides legitimate TLS regressions |

Stale syntax to refuse outright:

```text
mcpc mcp.example.com tools-list                          # 0.1.11 — drop
mcpc mcp.example.com connect @demo                        # 0.1.11 — drop
mcpc --config .vscode/mcp.json filesystem connect @demo   # 0.1.11 — drop
mcpc --clean=sessions                                     # legacy flag — drop
```

Translate to current shape using `references/patterns/session-first-syntax.md`.

## Minimal read sets

Do not load the whole skill by default. Pick one bundle, then widen only if the task forces you to.

| Branch | Read first |
|---|---|
| Remote Streamable HTTP smoke test | `references/commands/quick-reference.md`, `references/guides/http-testing.md`, `references/guides/discovery-search.md`, `references/guides/tool-resource-testing.md`, `references/guides/cleanup-maintenance.md` |
| Local stdio + task verification | `references/commands/quick-reference.md`, `references/guides/stdio-testing.md`, `references/guides/async-tasks.md`, `references/guides/everything-server.md`, `references/guides/discovery-search.md`, `references/guides/tool-resource-testing.md`, `references/guides/cleanup-maintenance.md` |
| Auth, proxy, or x402 payment edge cases | `references/commands/quick-reference.md`, `references/guides/authentication.md`, `references/guides/proxy-testing.md`, `references/guides/x402-payments.md`, `references/guides/cleanup-maintenance.md` |
| CI / scripted smoke tests | `references/commands/quick-reference.md`, `references/guides/ci-cd-integration.md`, `references/guides/scripting-automation.md`, `references/patterns/output-formatting.md`, `references/patterns/jq-patterns.md` |

## Standard workflow

### 1. Verify the syntax family

- `mcpc --version` reports `0.2.x`.
- Examples use `mcpc connect <server-or-file:entry> @session` shape.
- Validate the contract with plain `mcpc`, not a wrapper that may mangle quoting, TTY, or session state.

### 2. Connect a stable session

Default to a fresh `connect`. Reach for the session inventory only when reuse, cleanup, or stale-state diagnosis is the actual job.

```bash
# Remote URL; https:// is added automatically for non-local hosts
mcpc connect research.yigitkonur.com/mcp @research

# Localhost keeps http:// by default
mcpc connect 127.0.0.1:3011/mcp @everything-http

# Stdio via mcpServers config entry
mcpc connect /tmp/everything-mcp.json:everything @everything-stdio
```

Use `--no-profile` when anonymous HTTP testing matters on a machine with saved OAuth profiles.

To inspect an existing session, narrow the lookup to a single name instead of dumping the whole inventory:

```bash
mcpc
mcpc --json | jq '.sessions[] | select(.name == "@research")'
```

If an older session is not `live`, do not reuse it for a smoke test. Either `mcpc restart @session` or create a fresh session with a new name. If `mcpc restart @session` returns `Session not found`, stop retrying that name and create a fresh session immediately. For Everything-specific work, prefer a fresh stdio session unless you intentionally started the `streamableHttp` server yourself.

### 3. Inspect before deep testing

```bash
mcpc @research
mcpc @research help
mcpc @research grep search
mcpc @research tools-list --full
mcpc @research resources-list
mcpc @research prompts-list
```

Prefer `help` and `grep` before heavy `jq` pipelines. If acceptance criteria explicitly mention prompts, resources, or templates, add those list calls in the first pass instead of widening the read set later.

### 4. Validate schema and argument shape

```bash
mcpc @research tools-get web-search
mcpc --json @research tools-get web-search | jq '.inputSchema'
mcpc @research prompts-get some-prompt --schema ./expected-prompt-schema.json
```

`key:=value` still works, but arrays and objects should be sent as inline JSON literals or full JSON payloads. Route quoting edge cases to `references/patterns/argument-parsing.md`.

### 5. Reality-check advertised capabilities

Do not trust `capabilities` alone. Check server info, tool metadata, and one real call.

```bash
mcpc --json @research | jq '.capabilities'
mcpc --json @everything-http tools-list | jq '.[] | {name, taskSupport: (.execution.taskSupport // "unspecified")}'
```

- If `completions` appears in server info, treat it as informational until a CLI command is confirmed.
- If tasks appear in capabilities, still inspect per-tool `execution.taskSupport`.
- If a tool is marked `task:required`, prove it with one `--task` or `--detach` call before writing automation around it.

### 6. Exercise the capability you care about

```bash
mcpc --json @research tools-call search-reddit '{"queries":["OpenAI MCP"]}'
mcpc @everything-http prompts-get args-prompt city:=Paris state:=Texas
mcpc @everything-http resources-read demo://resource/static/document/features.md
mcpc @everything-http logging-set-level debug
```

### 7. Treat JSON payloads as truth

```bash
RESULT=$(mcpc --json @everything-http tools-call trigger-sampling-request prompt:='"hello"')
echo "$RESULT" | jq '.isError // false'
```

A command can exit `0` and still carry `"isError": true`. Always assert on payload, not exit code alone.

### 8. Use task mode deliberately

```bash
mcpc @everything-http tools-list --full
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' --task
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' --detach
mcpc @everything-http tasks-get <taskId>
```

Use `--task` when you need the final result in the CLI. Use `--detach` when a task ID is enough. `mcpc 0.2.4` does not have a standalone `tasks-result` command.

### 9. Close or clean explicitly

```bash
mcpc close @research
mcpc clean
mcpc clean sessions logs
```

Use `mcpc clean all` only for a real reset. Do not run `close` and `clean` for the same session in parallel.

## Capability boundary

What `mcpc 0.2.4` can and cannot test as a first-class workflow:

| Bucket | Coverage |
|---|---|
| **First-class** | stdio and Streamable HTTP transports; tools, prompts, resources, resource templates, logging, grep, proxy, x402; JSON scripting; task-enabled execution via `--task`, `--detach`, `tasks-list`, `tasks-get`, `tasks-cancel` |
| **Nuanced / partial** | `roots` (advertised, but no dedicated CLI to configure roots); `sampling` (demo tools may exist but can return `isError: true`); `completions` (advertised in server info, no `mcpc completions` command); detached task results (`tasks-get` returns status, not the original result body) |
| **Not first-class** | HTTP+SSE transport testing; elicitation commands from the CLI; standalone completion browsing; standalone detached-result retrieval after `--detach` |

Map advertised capabilities to actual CLI commands using `references/guides/capability-coverage.md`.

## Reference routing

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
| `references/guides/session-management.md` | Session lifecycle, reconnect behavior, restart behavior, and multi-session workflows. |
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
| `references/commands/quick-reference.md` | You need exact `0.2.4` syntax, flags, aliases, or cleanup forms fast. |
| `references/examples/real-world-workflows.md` | You want complete end-to-end workflows for real targets like Research Powerpack or Everything. |
| `references/examples/testing-recipes.md` | You want short copy-paste checks for smoke tests, schemas, tasks, grep, or cleanup. |
| `references/troubleshooting/common-errors.md` | You hit stale syntax, bad config shape, task-required failures, expired sessions, or transport mismatches. |

### Patterns and advanced details

| File | Read when |
|---|---|
| `references/patterns/session-first-syntax.md` | Translating `0.1.11` examples to `0.2.x` command-first syntax. |
| `references/patterns/argument-parsing.md` | Quoting arrays, objects, inline JSON, stdin, and `key:=value` edge cases. |
| `references/patterns/schema-validation.md` | Validating tool and prompt schemas in regression checks. |
| `references/patterns/config-resolution.md` | `mcpServers` config shape, `file:entry`, URL normalization, and path mistakes. |
| `references/patterns/auth-precedence.md` | Choosing between explicit headers, named profiles, default profile, `--no-profile`, and `--x402`. |
| `references/patterns/output-formatting.md` | Human vs JSON mode, stderr behavior, exit-code caveats, and `isError`. |
| `references/patterns/jq-patterns.md` | Advanced JSON filtering after native `grep` and `help` are not enough. |
| `references/patterns/tool-filtering.md` | Complementing `grep` with `tools-list --json | jq` workflows. |
| `references/patterns/logging-debugging.md` | Using `--verbose`, bridge logs, and log inspection to explain failures. |
| `references/patterns/notification-handling.md` | Testing list-changed notifications, subscriptions, and server log messages. |
| `references/patterns/pagination-caching.md` | Auto-pagination, tool cache refresh, and dynamic discovery behavior. |
| `references/patterns/python-integration.md` | Driving `mcpc` from Python subprocess workflows. |
| `references/patterns/shell-advanced.md` | Interactive shell behavior, discovery loops, and task usage inside `shell`. |
| `references/patterns/data-model.md` | JSON shapes behind session info, task status, cached metadata, profiles, and storage. |

## Guardrails

- Do not teach `0.1.11` target-first syntax unless explicitly documenting migration.
- Do not tell users to test HTTP+SSE with `mcpc 0.2.x`; use Streamable HTTP or stdio instead.
- Do not assume `tasks-get` can recover the full detached result body.
- Do not treat a green success banner as proof that the server call succeeded.
- Do not assume advertised capabilities always mean polished CLI support.
- Do not run `mcpc clean all` casually on machines with saved profiles.
- Treat proxy `/health` as a liveness probe only — verify proxy auth with a real MCP request on the exact release you ship before depending on it.
</content>
</invoke>